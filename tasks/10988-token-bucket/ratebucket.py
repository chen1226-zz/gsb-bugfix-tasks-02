"""多键令牌桶限流器。

对外接口（不得更改签名）：
    TokenBucket(rate, burst, idletime=60.0, clock=None)
        .allow(key, n=1) -> bool
        .retry_after(key) -> float
        .stats() -> dict
"""

import threading
import time


class TokenBucket:
    def __init__(self, rate, burst, idletime=60.0, clock=None):
        self.rate = float(rate)
        self.burst = float(burst)
        self.idletime = float(idletime)
        self._clock = clock or time.time
        self._buckets = {}
        self._lock = threading.Lock()
        self.allowed = 0
        self.rejected = 0

    def _refill(self, tokens, last, now):
        elapsed = now - last
        if elapsed > 0:
            return min(self.burst, tokens + elapsed * self.rate)
        return tokens

    def allow(self, key, n=1):
        with self._lock:
            now = self._clock()
            tokens, last = self._buckets.get(key, (self.burst, now))
            tokens = self._refill(tokens, last, now)
            if tokens >= n:
                self._buckets[key] = (tokens - n, last)
                self.allowed += 1
                return True
            self._buckets[key] = (tokens, last)
            self.rejected += 1
            return False

    def retry_after(self, key):
        with self._lock:
            tokens, _ = self._buckets.get(key, (self.burst, self._clock()))
            if tokens >= 1:
                return 0.0
            return round((1 - tokens) / self.rate, 6)

    def stats(self):
        with self._lock:
            return {"allowed": self.allowed, "rejected": self.rejected, "keys": len(self._buckets)}
