# 10989 · HTTP 客户端连接复用（fetch）

接口：`Client(host, port, timeout)` 的 `.get(path)` / `.close()`。

| 文件 | 说明 |
| --- | --- |
| `fetch.py` | 待修复的模块 |
| `fake_server.py` | 本机假服务端（把路径原样作为响应体） |
| `interop_stress.py` | 复现脚本：多线程并发请求 |
| `tests/test_fetch.py` | unittest 用例 |

## 已知现象

高并发下偶发拿到不属于自己的响应（字段串包、body 被截断），同时打开的套接字
缓慢增长；低并发不重现。

## 运行

```
python3 interop_stress.py
python3 -m unittest tests/test_fetch.py -v
```
