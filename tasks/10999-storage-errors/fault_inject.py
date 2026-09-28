"""复现脚本：故障注入 + 原子性 + 半截追加记录。"""

import os
import tempfile
import unittest.mock as mock

from storage import Storage


def check_swallowed(label, patcher, expect_retryable):
    with tempfile.TemporaryDirectory() as root:
        storage = Storage(root)
        with patcher:
            result = storage.write("a.txt", "payload")
        problems = []
        if result.get("ok"):
            problems.append(f"{label}: 写入失败却返回 ok=True")
        if result.get("error") in (None, ""):
            problems.append(f"{label}: 没有把错误信息返回给调用方")
        elif bool(result.get("retryable")) != expect_retryable:
            problems.append(
                f"{label}: retryable 应为 {expect_retryable}，实际 {result.get('retryable')}"
            )
        return problems


def check_atomicity():
    """写入中途失败时，旧内容不能被破坏。"""
    with tempfile.TemporaryDirectory() as root:
        storage = Storage(root)
        storage.write("a.txt", "original")
        with mock.patch("storage.os.fsync", side_effect=OSError(28, "No space left on device")):
            storage.write("a.txt", "brand-new-content")
        after = storage.read("a.txt")
        if after != "original":
            return [f"原子性: 写入失败后旧内容被破坏（现在读到 {after!r}）"]
    return []


def check_torn_tail():
    """追加过程中进程被杀，尾部半截记录不能被当成有效数据。"""
    with tempfile.TemporaryDirectory() as root:
        storage = Storage(root)
        for index in range(3):
            storage.append("log", {"i": index})
        with open(os.path.join(root, "log"), "ab") as fh:
            fh.write(b'{"i": 4, "note": "tor')      # 模拟被截断的最后一条
        try:
            records = storage.read_records("log")
        except Exception as exc:  # noqa: BLE001
            return [f"半截记录: read_records 抛了 {type(exc).__name__}: {exc}"]
        if records != [{"i": 0}, {"i": 1}, {"i": 2}]:
            return [f"半截记录: 期望 3 条完整记录，实际 {records}"]
    return []


def main():
    problems = []
    problems += check_swallowed(
        "open 失败（磁盘满）",
        mock.patch("builtins.open", side_effect=OSError(28, "No space left on device")),
        True,
    )
    problems += check_swallowed(
        "fsync 失败",
        mock.patch("storage.os.fsync", side_effect=OSError(5, "Input/output error")),
        True,
    )
    problems += check_swallowed(
        "目录不可写",
        mock.patch("builtins.open", side_effect=PermissionError(13, "Permission denied")),
        False,
    )
    problems += check_atomicity()
    problems += check_torn_tail()

    if problems:
        print(f"FAIL: {len(problems)} 处不符合预期")
        for item in problems[:4]:
            print("  - " + item)
        raise SystemExit(1)
    print("OK: 3 fault points + atomicity + torn tail, 0 problems")


if __name__ == "__main__":
    main()
