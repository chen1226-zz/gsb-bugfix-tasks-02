"""接收请求、排队后转发给上游。

对外接口（不得更改签名）：
    Ingest(capacity=1000, service_time=0.001)
        .offer(item) -> bool
        .pump()      -> 处理一个排队的请求
        .metrics()   -> dict
        .latency_p99() -> float（秒）

超载策略：快速失败（reject-new）。队列满时 offer 立即返回 False 并计入
rejected，调用方可据此返回 503/重试，而不是让请求在内存里无限堆积。
"""

import time
from collections import deque

_LATENCY_SAMPLES = 4096  # 滑动窗口，避免指标本身成为内存增长点


class Ingest:
    def __init__(self, capacity=1000, service_time=0.001):
        self.capacity = capacity
        self.service_time = service_time
        self.queue = deque()
        self.processed = 0
        self.rejected = 0
        self.dropped = 0  # 预留给 drop-oldest 降级策略；当前策略下恒为 0
        self.max_queue = 0
        self._waits = deque(maxlen=_LATENCY_SAMPLES)

    def offer(self, item):
        """入队；队列已满时快速失败，返回 False。"""
        if len(self.queue) >= self.capacity:
            self.rejected += 1
            return False
        self.queue.append((time.monotonic(), item))
        if len(self.queue) > self.max_queue:
            self.max_queue = len(self.queue)
        return True

    def pump(self):
        if not self.queue:
            return None
        enqueued_at, item = self.queue.popleft()
        self._waits.append(time.monotonic() - enqueued_at)
        self.processed += 1
        return item

    def latency_p99(self):
        """最近若干次 pump 的实际排队等待时间 P99（秒）。"""
        if not self._waits:
            return 0.0
        ordered = sorted(self._waits)
        rank = min(len(ordered) - 1, int(0.99 * (len(ordered) - 1) + 0.5))
        return ordered[rank]

    def metrics(self):
        return {
            "queued": len(self.queue),
            "max_queue": self.max_queue,
            "processed": self.processed,
            "rejected": self.rejected,
            "dropped": self.dropped,
        }
