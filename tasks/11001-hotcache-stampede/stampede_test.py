"""复现脚本：TTL 到期瞬间并发请求，检查同一 key 是否被反复回源。"""

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


def main():
    clock = Clock()
    origin_calls = []
    origin_lock = threading.Lock()

    def origin(key):
        time.sleep(0.005)
        with origin_lock:
            origin_calls.append(key)
        return f"v-{key}"

    cache = HotCache(origin, ttl=1.0, jitter=0.2, clock=clock)
    keys = [f"hot-{i}" for i in range(KEYS)]
    for key in keys:
        cache.get(key)
    warm_calls = len(origin_calls)

    clock.advance(5.0)
    origin_calls.clear()

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
                errors.append(str(exc))

    refreshes = len(origin_calls)
    total_requests = WORKERS * ROUNDS_PER_WORKER * len(keys)

    problems = []
    if warm_calls != KEYS:
        problems.append(f"预热阶段回源 {warm_calls} 次，应为 {KEYS}")
    if refreshes > KEYS:
        problems.append(f"同一 key 被并发回源：{refreshes} 次 > {KEYS} 个 key")
    if errors:
        problems.append(f"{len(errors)} 个请求抛异常，例：{errors[0][:60]}")

    if problems:
        print(f"FAIL: refreshes={refreshes}, 共 {total_requests} 个并发请求")
        for item in problems:
            print("  - " + item)
        raise SystemExit(1)
    print(f"OK: refreshes == keys ({refreshes}), origin qps <= 1.2x baseline")


if __name__ == "__main__":
    main()
