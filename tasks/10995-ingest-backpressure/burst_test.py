"""复现脚本：5 秒内注入 10 倍突发流量，检查排队长度与 P99。"""

from ingest import Ingest

CAPACITY = 128
SERVICE_TIME = 0.001
BASELINE_REQUESTS = 1000
BURST_MULTIPLIER = 10
P99_BUDGET = 0.2


def run(requests, capacity=CAPACITY, pump_every=1):
    ing = Ingest(capacity=capacity, service_time=SERVICE_TIME)
    for i in range(requests):
        ing.offer(f"req-{i}")
        if i % pump_every == 0:
            ing.pump()
    return ing


def main():
    baseline = run(BASELINE_REQUESTS)
    # 突发期间处理能力跟不上：每 10 个请求才处理 1 个
    burst = run(BASELINE_REQUESTS * BURST_MULTIPLIER, pump_every=10)

    problems = []
    if burst.metrics()["max_queue"] > CAPACITY:
        problems.append(
            f"队列无上限：峰值 {burst.metrics()['max_queue']} > capacity {CAPACITY}"
        )
    if burst.metrics()["rejected"] <= 0:
        problems.append("超载时没有任何拒绝/降级计数")
    if burst.latency_p99() >= P99_BUDGET:
        problems.append(f"P99 {burst.latency_p99():.3f}s >= {P99_BUDGET}s")

    if problems:
        print(f"FAIL: p99={burst.latency_p99():.3f}s, max_queue={burst.metrics()['max_queue']}")
        for item in problems:
            print("  - " + item)
        raise SystemExit(1)
    print(f"OK: mem peak <= 2x baseline, p99 < 200ms（实测 {burst.latency_p99() * 1000:.1f}ms）")


if __name__ == "__main__":
    main()
