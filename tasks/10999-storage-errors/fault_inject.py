"""复现脚本：在每一个持久化环节注入故障，检查错误是否被吞掉。"""

import os
import tempfile
import unittest.mock as mock

from storage import Storage


def run(label, patcher, expect_retryable):
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


def main():
    cases = [
        (
            "open 失败（磁盘满）",
            mock.patch("builtins.open", side_effect=OSError(28, "No space left on device")),
            True,
        ),
        (
            "fsync 失败",
            mock.patch("storage.os.fsync", side_effect=OSError(5, "Input/output error")),
            True,
        ),
        (
            "目录不可写",
            mock.patch("builtins.open", side_effect=PermissionError(13, "Permission denied")),
            False,
        ),
    ]

    problems = []
    for label, patcher, retryable in cases:
        problems.extend(run(label, patcher, retryable))

    if problems:
        print(f"FAIL: {len(problems)} 处错误被吞掉")
        for item in problems[:3]:
            print("  - " + item)
        raise SystemExit(1)
    print(f"OK: {len(cases)} fault points, 0 swallowed errors")


if __name__ == "__main__":
    main()
