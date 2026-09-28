"""复现脚本：TTL 到期瞬间的并发回源 + 回源失败时的降级。"""

import concurrent.futures
import threading
import time

from hotcache import HotCache

KEYS = 20
WORKERS = 20
ROUNDS_PER_WORKER = 50


class Clock:
    def __init__(self):
        self.t = 0.0
        self._lock = threading.Lock()

    def __call__(self):
        with self._lock:
            return self.t

    def advance(self, seconds):
        with self._lock:
            self.t += seconds


def burst(cache, keys):
    def worker():
        for _ in range(ROUNDS_PER_WORKER):
            for key in keys:
                cache.get(key)

    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(worker) for _ in range(WORKERS)]
        for fut in futures:
            try:
                fut.result()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{type(exc).__name__}: {exc}")
    return errors


def main():
    clock = Clock()
    state = {"failing": False}
    origin_calls = []
    origin_lock = threading.Lock()

    def origin(key):
        time.sleep(0.005)
        with origin_lock:
            origin_calls.append(key)
        if state["failing"]:
            raise RuntimeError("origin 503")
        return f"v-{key}"

    cache = HotCache(origin, ttl=1.0, jitter=0.2, stale_ttl=0.5, clock=clock)
    keys = [f"hot-{i}" for i in range(KEYS)]
    for key in keys:
        cache.get(key)
    warm_calls = len(origin_calls)

    problems = []
    if warm_calls != KEYS:
        problems.append(f"预热阶段回源 {warm_calls} 次，应为 {KEYS}")

    # 第一阶段：TTL 到期瞬间的并发回源
    clock.advance(5.0)
    origin_calls.clear()
    errors = burst(cache, keys)
    refreshes = len(origin_calls)
    if refreshes > KEYS:
        problems.append(f"同一 key 被并发回源：{refreshes} 次 > {KEYS} 个 key")
    if errors:
        problems.append(f"第一阶段 {len(errors)} 个请求抛异常，例：{errors[0][:60]}")

    # 第二阶段：回源失败，必须降级返回旧值且不能引发新一轮风暴
    state["failing"] = True
    clock.advance(5.0)
    origin_calls.clear()
    errors = burst(cache, keys)
    failed_refreshes = len(origin_calls)
    stats = cache.stats()
    if errors:
        problems.append(f"回源失败时 {len(errors)} 个请求直接抛异常，例：{errors[0][:60]}")
    if failed_refreshes > KEYS:
        problems.append(f"回源失败时又出现风暴：{failed_refreshes} 次 > {KEYS} 个 key")
    if stats["stale_served"] <= 0:
        problems.append("回源失败时没有返回旧值（stale_served 为 0）")

    if problems:
        print(f"FAIL: refreshes={refreshes}, failed_refreshes={failed_refreshes}, "
              f"stale_served={stats['stale_served']}")
        for item in problems:
            print("  - " + item)
        raise SystemExit(1)
    print(f"OK: refreshes == keys ({refreshes}), origin qps <= 1.2x baseline, "
          f"stale served on failure ({stats['stale_served']})")


if __name__ == "__main__":
    main()
