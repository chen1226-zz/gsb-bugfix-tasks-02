# 11001 · 热点缓存击穿（hotcache）

接口：`HotCache(origin, ttl, jitter, clock)` 的 `.get(key)` / `.stats()`。

| 文件 | 说明 |
| --- | --- |
| `hotcache.py` | 待修复的模块 |
| `stampede_test.py` | 复现脚本：TTL 到期瞬间的并发回源 |
| `tests/test_hotcache.py` | unittest 用例 |

## 已知现象

整点批量过期时下游 QPS 冲到平时的 20 倍，接口 P99 崩溃；平时一切正常。

## 运行

```
python3 stampede_test.py
python3 -m unittest tests/test_hotcache.py -v
```
