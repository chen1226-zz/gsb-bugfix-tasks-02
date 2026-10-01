# 10994 · 任务调度重复与漏触发（scheduler）

接口：`Scheduler(path)` 的 `.add(task_id, interval, first_at)` / `.tick(now)` / `.pending()`。
`tick(now)` 返回本轮触发的 `(task_id, slot)` 列表。

| 文件 | 说明 |
| --- | --- |
| `scheduler.py` | 已修复的模块 |
| `sim.py` | 复现脚本：随机 tick 间隔 + 时钟回拨 + 中途重启（1000 轮） |
| `tests/test_scheduler.py` | unittest 用例 |

## 根因

旧实现有两个互相叠加的缺陷：

1. **水位锚定在到达时刻**：`tick` 里 `next_at = now + interval`，把下一次触发
   锚定在「本次 tick 到达的墙钟」而非计划栅格上。tick 迟到（任务耗时超过间隔、
   时钟前跳）时，`(旧 next_at, now]` 之间的槽位被直接跳过——永久漏触发；
   同时锚点随到达时间漂移，长跑后同一槽位可能被判定两次——偶发重复。
2. **水位不落盘**：持久化文件只存 `interval/first_at`，`_load` 把 `next_at`
   重置为 `first_at`。进程重启后所有已触发槽位被重放（重复），而重启前被
   跳过的槽位再也回不来（漏触发）。时钟回拨本身不丢状态，但放大了以上两点。

## 设计：幂等触发 + 持久化水位

每个任务维护单调水位 `next_at`（下一个待触发槽位的绝对计划时刻），
槽位身份 = 其计划时刻。状态机（每个任务独立）：

```
            add / 重排                    slot <= now（含补触发循环）
  (无) ───────────────► READY(next_at) ──────────────────────┐
                              ▲                              │ 触发 (tid, slot)
                              │   next_at = slot + interval  ▼
                              └────────────────────────  FIRE(slot)
            now < next_at：自环，不触发、水位不动（时钟回拨安全）
```

- **幂等**：水位只前进不后退；`slot <= now` 的每个槽位被触发的同时水位越过它，
  同一槽位不可能再次满足触发条件。同一 `now` 重复 tick 返回空。
- **持久化水位**：`next_at` 随任务定义一起写入（tmp 文件 + fsync + `os.replace`
  原子替换）。重启后 `_load` 恢复水位：`<= next_at` 的槽位视为已触发不重放，
  `(next_at, now]` 区间（宕机期间错过）的槽位由补触发循环恰好补一次。
- **取消/重排**：重新 `add` 同一 `task_id` 会把水位重置为新 `first_at`，
  旧计划作废。

## 运行

```
python3 sim.py                            # OK: 1000 schedules, 0 dup, 0 missed
python3 -m unittest discover -s tests     # OK（9 用例）
```
