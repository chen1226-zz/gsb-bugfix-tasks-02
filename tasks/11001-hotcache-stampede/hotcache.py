"""热点数据缓存，TTL 到期后回源。

对外接口（不得更改签名）：
    HotCache(origin, ttl=1.0, jitter=0.0, clock=None)
        .get(key)
        .stats() -> dict
"""

import random
import threading
import time


class HotCache:
    def __init__(self, origin, ttl=1.0, jitter=0.0, clock=None):
        self.origin = origin
        self.ttl = float(ttl)
        self.jitter = float(jitter)
        self._clock = clock or time.monotonic
        self._data = {}
        self._lock = threading.Lock()
        self.refreshes = 0
        self.hits = 0
        self.rng = random.Random(20260928)

    def get(self, key):
        now = self._clock()
        entry = self._data.get(key)
        if entry is not None and now < entry[1]:
            with self._lock:
                self.hits += 1
            return entry[0]

        value = self.origin(key)
        with self._lock:
            self.refreshes += 1
        self._data[key] = (value, now + self.ttl)
        return value

    def stats(self):
        with self._lock:
            return {"refreshes": self.refreshes, "hits": self.hits, "keys": len(self._data)}
