# 10994 · 任务调度重复与漏触发（scheduler）

接口：`Scheduler(path)` 的 `.add(task_id, interval, first_at)` / `.tick(now)` / `.pending()`。
`tick(now)` 返回本轮触发的 `(task_id, slot)` 列表。

| 文件 | 说明 |
| --- | --- |
| `scheduler.py` | 待修复的模块 |
| `sim.py` | 复现脚本：随机 tick 间隔 + 中途重启 |
| `tests/test_scheduler.py` | unittest 用例 |

## 已知现象

一是长跑时偶发同一任务被触发两次；二是系统时钟被回拨或进程重启后，部分任务再也
触发不了（永久漏触发）。

## 运行

```
python3 sim.py
python3 -m unittest tests/test_scheduler.py -v
```
