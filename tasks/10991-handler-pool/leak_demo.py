"""复现脚本：交替执行带金额与不带金额的请求，检查字段是否串到下一个请求。"""

from handler import Handler, Pool

ROUNDS = 1000


def main():
    pool = Pool(size=4)
    handler = Handler(pool)
    leaked = 0
    example = None

    for i in range(ROUNDS):
        if i % 2 == 0:
            got = handler.handle(f"u{i}", 100, trace_id=f"t{i}")
            if got["amount"] != 100:
                leaked += 1
                example = example or (i, got)
        else:
            got = handler.handle(f"u{i}", 0, trace_id=f"t{i}")
            if got["amount"] != 0 or got["user"] != f"u{i}" or got["trace_id"] != f"t{i}":
                leaked += 1
                example = example or (i, got)

    if leaked:
        print(f"FAIL: {ROUNDS} rounds, {leaked} leaked fields")
        print(f"  例：第 {example[0]} 轮 -> {example[1]}")
        raise SystemExit(1)
    print(f"OK: {ROUNDS} rounds, 0 leaked fields")


if __name__ == "__main__":
    main()
