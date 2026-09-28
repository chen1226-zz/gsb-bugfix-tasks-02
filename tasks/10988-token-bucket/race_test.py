"""复现脚本：固定时间窗内连续放行次数不得超过 burst + rate × 时长。"""

from ratebucket import TokenBucket

ROUNDS = 100
CALLS = 1000
RATE = 10.0
BURST = 10.0
WINDOW = 1.0


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def main():
    worst = None
    for _ in range(ROUNDS):
        clock = Clock()
        bucket = TokenBucket(RATE, BURST, clock=clock)
        bucket.allow("k")          # 在 t=0 建立这个 key 的桶
        clock.t = WINDOW
        allowed = sum(1 for _ in range(CALLS) if bucket.allow("k"))
        limit = BURST + RATE * WINDOW
        if allowed > limit:
            worst = (allowed, limit)
            break

    if worst:
        allowed, limit = worst
        print(f"FAIL: allowed={allowed} > burst + rate*elapsed = {limit}")
        raise SystemExit(1)
    print("OK: allowed <= burst + rate*elapsed")


if __name__ == "__main__":
    main()
