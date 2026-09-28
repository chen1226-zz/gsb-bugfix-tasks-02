# 10999 · 持久化错误被吞（storage）

`storage.py` 负责把记录写入文件并返回结果。

接口：`Storage(root)` 的 `.write(name, data)` / `.read(name)` / `.exists(name)`。
`write` 返回 `{"ok": bool, "retryable": bool, "error": str | None}`。

| 文件 | 说明 |
| --- | --- |
| `storage.py` | 待修复的模块 |
| `fault_inject.py` | 复现脚本：在 open / fsync / 目录不可写等环节注入故障 |
| `tests/test_storage.py` | unittest 用例 |

## 已知现象

磁盘写满或权限异常时接口仍返回成功，重启后数据就丢了；平时监控里错误计数一直是 0，
完全看不出问题。

## 运行

```
python3 fault_inject.py
python3 -m unittest tests/test_storage.py -v
```
