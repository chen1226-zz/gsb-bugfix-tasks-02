# 10995 · 背压缺失（ingest）

接口：`Ingest(capacity, service_time)` 的 `.offer(item)` / `.pump()` / `.metrics()` /
`.latency_p99()`。

| 文件 | 说明 |
| --- | --- |
| `ingest.py` | 已修复：有界队列 + 快速失败 |
| `burst_test.py` | 复现脚本：10 倍突发流量 |
| `fake_upstream.py` | 本机假上游（可配时延/在途上限），用于测试 |
| `tests/test_ingest.py` | unittest 用例 |

## 根因

原实现中 `offer()` 无条件 `append` 到无界 `deque`，`capacity` 形同虚设。
突发期间生产速度 > 消费速度，队列单调增长：内存随请求数线性上涨直到 OOM；
同时 `latency_p99()` 以 `max_queue * service_time` 估算，队列越深尾延迟越高，
P99 从 50ms 恶化到数秒。低流量下消费跟得上，所以问题不暴露。

## 修复与取舍

- **有界队列**：`offer()` 在 `len(queue) >= capacity` 时不再入队，内存占用
  上限为 O(capacity)，与流量无关。
- **超载策略 = 快速失败（reject-new）**：队列满时 `offer()` 立即返回 `False`
  并计入 `rejected`，调用方可立刻返回 503/重试。选它而非 drop-oldest（降级）
  或无限排队，理由：
  - 失败反馈最快，调用方能及时止损，不会在系统内部积压"注定超时"的请求；
  - drop-oldest 会静默丢弃已接受的请求，破坏"已受理必处理"的语义；
  - 排队等待只会把延迟成本转嫁给上游调用方的超时预算。
- **真实时延指标**：`pump()` 记录每个请求的实际排队等待（滑动窗口 4096 条，
  有界），`latency_p99()` 返回样本 P99，替代原来的理论估算。
- **可观测指标**：`metrics()` 暴露 `queued`（当前排队长度）、`max_queue`
  （峰值）、`processed`、`rejected`（拒绝数）、`dropped`（丢弃数，预留给
  drop-oldest 策略，当前策略下恒为 0）。
- **代价**：突发期间超出容量的请求被拒绝（表现为 4xx/5xx 给调用方），
  这是用"可预期的少量拒绝"换"系统不 OOM、P99 有界"。

## 运行

```
python3 burst_test.py                    # OK: mem peak <= 2x baseline, p99 < 200ms
python3 -m unittest discover -s tests    # 7 个用例全部通过
```
