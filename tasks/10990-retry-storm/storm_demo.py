"""复现脚本：下游全故障时的请求放大系数、熔断状态与恢复时间。"""

from client import Client, Service, TransientError
from fake_downstream import FakeDownstream

REQUESTS = 200
RECOVER_REQUESTS = 20


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def main():
    clock = Clock()
    downstream = FakeDownstream()
    client = Client(downstream, max_attempts=2, base_delay=0.0, clock=clock, sleeper=lambda s: None)
    service = Service(client, attempts=3)   # 上层也有重试：真实环境里两层叠在一起

    for i in range(REQUESTS):
        try:
            service.handle(f"req-{i}")
        except TransientError:
            pass

    amplification = downstream.calls / REQUESTS
    state = getattr(client, "state", "always-closed")
    breaker_opened = state in ("open", "half-open")

    downstream.healthy = True
    clock.t += 1.0
    ok = 0
    for i in range(RECOVER_REQUESTS):
        try:
            service.handle(f"after-{i}")
            ok += 1
        except TransientError:
            pass

    problems = []
    if amplification > 2:
        problems.append(f"放大系数 {amplification:.1f} > 2（上游被打 {downstream.calls} 次）")
    if not breaker_opened:
        problems.append("连续失败后没有熔断")
    if ok != RECOVER_REQUESTS:
        problems.append(f"下游恢复后只成功 {ok}/{RECOVER_REQUESTS}")

    if problems:
        print("FAIL: " + "; ".join(problems))
        raise SystemExit(1)
    print(f"OK: amplification <= 2 (实测 {amplification:.2f}), circuit opened, recovered in <1.0s")


if __name__ == "__main__":
    main()
