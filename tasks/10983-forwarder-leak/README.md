# 10983 · 长跑转发服务句柄泄漏（forwarder）

`forwarder.py` 是带重试的转发服务。接口：`Forwarder(host, port, attempts, timeout)` 的
`.forward(payload)` / `.stats()` / `.shutdown()`。

| 文件 | 说明 |
| --- | --- |
| `forwarder.py` | 待修复的模块 |
| `soak_test.py` | 复现脚本：反复走失败路径，观察句柄与线程 |
| `tests/test_forwarder.py` | unittest 用例 |

## 已知现象

跑几个小时后线程数、打开的文件句柄与连接数持续增长，最终 OOM 或被系统拒绝创建
连接；只压测 5 分钟看不出问题。

## 运行

```
python3 soak_test.py
python3 -m unittest tests/test_forwarder.py -v
```
