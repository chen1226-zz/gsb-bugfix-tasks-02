# 10990 · 重试风暴（client）

接口：`Client(transport, max_attempts, base_delay, clock, sleeper).call(req)`；
上层 `Service(client, attempts).handle(req)`。

| 文件 | 说明 |
| --- | --- |
| `client.py` | 待修复的模块 |
| `fake_downstream.py` | 本机假下游 |
| `storm_demo.py` | 复现脚本：放大系数 / 熔断 / 恢复 |
| `tests/test_client.py` | unittest 用例 |

## 已知现象

下游某接口开始返回 5xx 之后，整体请求量放大 5–8 倍，把上游彻底打挂；上游恢复后，
本服务仍长时间维持高负载。

## 运行

```
python3 storm_demo.py
python3 -m unittest tests/test_client.py -v
```
