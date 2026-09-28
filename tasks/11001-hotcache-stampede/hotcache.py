"""多实例共享的热点缓存：TTL 到期后回源，可降级返回旧值。

共享状态放在 sqlite 里（`db_path`），表结构见 README：
    hotcache(key TEXT PRIMARY KEY, value TEXT, version INTEGER,
             expires_at REAL, refreshing_until REAL)

对外接口（不得更改签名）：
    HotCache(origin, ttl=1.0, jitter=0.0, stale_ttl=0.5, db_path=None, clock=None)
        .get(key)
        .stats() -> {"refreshes", "hits", "stale_served", "keys"}

约定：
  * 同一个 key 在任意时刻最多只允许有一个实例回源（跨进程也算）；
  * 回源失败且该 key 有已知值时返回旧值并计入 stale_served，否则抛出；
  * TTL 到期但仍在 stale_ttl 窗口内时，立刻返回旧值并在后台补一次刷新；
  * 写回时必须按版本号做 CAS，不能把别人写的新值覆盖回去。
"""

import random
import sqlite3
import threading
import time


class HotCache:
    def __init__(self, origin, ttl=1.0, jitter=0.0, stale_ttl=0.5, db_path=None, clock=None):
        self.origin = origin
        self.ttl = float(ttl)
        self.jitter = float(jitter)
        self.stale_ttl = float(stale_ttl)
        self.db_path = db_path
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
            return {
                "refreshes": self.refreshes,
                "hits": self.hits,
                "stale_served": self.stale_served,
                "keys": len(self._data),
            }
