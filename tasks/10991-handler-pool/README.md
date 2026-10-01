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

## 泄漏路径（根因）

`RequestContext` 只有 4 个槽位，池里全是「冷」对象，所以小数据量的单测看不到问题；
一旦对象开始复用，两个缺陷叠加就会泄漏：

1. **部分赋值**：旧 `handle` 只在 `amount > 0` 时写 `ctx.amount`，不带金额的请求
   会读到上一请求残留的金额；其余字段同理（`trace_id=None` 的分支）。
2. **回收不清零**：旧 `Pool.release` 原样把 ctx 放回，入池对象仍携带着
   `user / amount / trace_id`；而且旧代码在返回前 `release`，一旦 `handle` 中途
   抛异常或被取消（`KeyboardInterrupt` 等），ctx 直接丢失或带着脏数据滞留。

## 修复后的重置契约

- `RequestContext.reset()` 是唯一的清零入口，必须覆盖 `__slots__` 的全部字段
  （`user=None, amount=0, trace_id=None`）；新增字段时必须同步更新。
- **回收即清零**：`Pool.release` 先 `reset()` 再入锁入池；
  **取出再清零**：`Pool.acquire` 弹出后再 `reset()` 一次作为防御。
- `Handler.handle` 用 `try/finally` 包裹，正常返回、异常抛出、执行被取消三条
  路径都会归还并清零 ctx。
- 不做深拷贝、不增加分配：2000 次请求 `stats()["created"]` 不增长
  （见 `tests/test_handler.py` 的 `test_allocation_bounded`）。

## 运行

```
python3 leak_demo.py
python3 -m unittest tests/test_handler.py -v
```

或直接执行验收命令：

```
python3 -m unittest discover -s tests
```
