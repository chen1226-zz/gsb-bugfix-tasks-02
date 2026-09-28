# 10995 · 背压缺失（ingest）

接口：`Ingest(capacity, service_time)` 的 `.offer(item)` / `.pump()` / `.metrics()` /
`.latency_p99()`。

| 文件 | 说明 |
| --- | --- |
| `ingest.py` | 待修复的模块 |
| `burst_test.py` | 复现脚本：10 倍突发流量 |
| `tests/test_ingest.py` | unittest 用例 |

## 已知现象

流量突发时内存单调上涨直到 OOM，P99 从 50ms 恶化到数秒；低流量下一切正常。

## 运行

```
python3 burst_test.py
python3 -m unittest tests/test_ingest.py -v
```
