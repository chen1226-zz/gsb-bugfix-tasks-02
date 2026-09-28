# 10986 · 二进制协议兼容（wire）

`wire.py` 定义自定义二进制消息格式，服务端与客户端共用。
接口：`encode(msg, version)` / `decode(data, version)` / `Message(name, age, email)`。

| 文件 | 说明 |
| --- | --- |
| `wire.py` | 待修复的模块 |
| `interop.py` | 复现脚本：v1/v2 兼容矩阵 |
| `tests/test_wire.py` | unittest 用例 |

## 已知现象

服务端升到 v2（新增一个可选字段）后，旧版解析新报文会字段错位，偶尔还抛异常；
新版之间互通正常。

## 运行

```
python3 interop.py
python3 -m unittest tests/test_wire.py -v
```
