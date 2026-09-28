# 10991 · 对象池复用泄漏（handler）

接口：`Pool(size)` 的 `.acquire()` / `.release(ctx)`；`Handler(pool).handle(user, amount, trace_id)`。

| 文件 | 说明 |
| --- | --- |
| `handler.py` | 待修复的模块 |
| `leak_demo.py` | 复现脚本：交替执行两种请求 |
| `tests/test_handler.py` | unittest 用例 |

## 已知现象

偶发把上一个请求的数据（用户名、金额等字段）带进下一个请求的响应里；数据体量越大
越容易出现；小数据量的单元测试全绿。

## 运行

```
python3 leak_demo.py
python3 -m unittest tests/test_handler.py -v
```
