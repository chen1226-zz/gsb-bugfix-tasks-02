"""接收请求、排队后转发给上游。

对外接口（不得更改签名）：
    Ingest(capacity=1000, service_time=0.001)
        .offer(item) -> bool
        .pump()      -> 处理一个排队的请求
        .metrics()   -> dict
        .latency_p99() -> float（秒）
"""

from collections import deque


class Ingest:
    def __init__(self, capacity=1000, service_time=0.001):
        self.capacity = capacity
        self.service_time = service_time
        self.queue = deque()
        self.processed = 0
        self.rejected = 0
        self.max_queue = 0

    def offer(self, item):
        self.queue.append(item)
        if len(self.queue) > self.max_queue:
            self.max_queue = len(self.queue)
        return True

    def pump(self):
        if not self.queue:
            return None
        self.processed += 1
        return self.queue.popleft()

    def latency_p99(self):
        return self.max_queue * self.service_time

    def metrics(self):
        return {
            "queued": len(self.queue),
            "max_queue": self.max_queue,
            "processed": self.processed,
            "rejected": self.rejected,
        }
