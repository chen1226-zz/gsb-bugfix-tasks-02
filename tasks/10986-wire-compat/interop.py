"""复现脚本：v1/v2 编码 × v1/v2 解码的兼容矩阵。"""

import wire
from wire import Message

PAYLOADS = [
    Message("a", 1, ""),
    Message("bob", 250, "bob@example.com"),
    Message("carol", 65535, ""),
    Message("丁一", 42, "ding@example.com"),
    Message("e", 0, ""),
    Message("frank", 1000, "f@example.com"),
]


def expect(enc_v, dec_v, msg):
    """v1 编码不带 email，v1 解码也不认 email，其余情况按原值。"""
    email = "" if (enc_v == 1 or dec_v == 1) else msg.email
    return Message(msg.name, msg.age, email)


def main():
    cases = 0
    bad = []
    for msg in PAYLOADS:
        for enc_v in (1, 2):
            blob = wire.encode(msg, enc_v)
            for dec_v in (1, 2):
                cases += 1
                try:
                    got = wire.decode(blob, dec_v)
                except Exception as exc:  # noqa: BLE001
                    bad.append((enc_v, dec_v, msg.as_tuple(), f"{type(exc).__name__}: {exc}"))
                    continue
                want = expect(enc_v, dec_v, msg)
                if got.as_tuple() != want.as_tuple():
                    bad.append((enc_v, dec_v, want.as_tuple(), got.as_tuple()))

    if bad:
        print(f"FAIL: {cases - len(bad)}/{cases} cases")
        for enc_v, dec_v, want, got in bad[:3]:
            print(f"  编 v{enc_v} → 解 v{dec_v}  期望 {want}  实际 {got}")
        raise SystemExit(1)
    print(f"OK: {cases}/{cases} cases")


if __name__ == "__main__":
    main()
