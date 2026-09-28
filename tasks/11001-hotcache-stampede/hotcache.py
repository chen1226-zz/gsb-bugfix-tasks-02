"""热点数据缓存，TTL 到期后回源。

对外接口（不得更改签名）：
    HotCache(origin, ttl=1.0, jitter=0.0, stale_ttl=0.5, clock=None)
        .get(key)
        .stats() -> {"refreshes", "hits", "stale_served", "keys"}

约定：同一个 key 并发回源只允许一次；回源失败时若有已知旧值，返回旧值并计数，
否则把异常抛给调用方。
"""

import random
import threading
import time


class HotCache:
    def __init__(self, origin, ttl=1.0, jitter=0.0, stale_ttl=0.5, clock=None):
        self.origin = origin
        self.ttl = float(ttl)
        self.jitter = float(jitter)
        self.stale_ttl = float(stale_ttl)
        self._clock = clock or time.monotonic
        self._data = {}
        self._lock = threading.Lock()
        self.refreshes = 0
        self.hits = 0
        self.stale_served = 0
        self.rng = random.Random(20260928)

    def get(self, key):
        now = self._clock()
        entry = self._data.get(key)
        if entry is not None and now < entry[1]:
            self.hits += 1
            return entry[0]

        value = self.origin(key)
        self.refreshes += 1
        self._data[key] = (value, now + self.ttl)
        return value

    def stats(self):
        return {
            "refreshes": self.refreshes,
            "hits": self.hits,
            "stale_served": self.stale_served,
            "keys": len(self._data),
        }
