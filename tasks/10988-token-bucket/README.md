# 10988 · 令牌桶限流器（ratebucket）

多键令牌桶。接口：`TokenBucket(rate, burst, idletime, clock)` 的 `.allow(key, n)` /
`.retry_after(key)` / `.stats()`。

| 文件 | 说明 |
| --- | --- |
| `ratebucket.py` | 待修复的模块 |
| `race_test.py` | 复现脚本：时间窗内放行次数 |
| `tests/test_ratebucket.py` | unittest 用例 |

## 已知现象

一是并发压测时单位时间内放行的请求数超过配置容量；二是系统时钟被回拨几秒后，
部分 key 被长时间误判为「额度耗尽」。单线程测试全绿。

## 运行

```
python3 race_test.py
python3 -m unittest tests/test_ratebucket.py -v
```
