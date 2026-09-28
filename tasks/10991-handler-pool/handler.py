"""用对象池复用请求/响应对象。

对外接口（不得更改签名）：
    RequestContext()            字段：user, amount, trace_id
    Pool(size=4).acquire() / .release(ctx) / .stats()
    Handler(pool).handle(user, amount) -> dict
"""

import threading


class RequestContext:
    __slots__ = ("user", "amount", "trace_id")

    def __init__(self):
        self.user = None
        self.amount = 0
        self.trace_id = None


class Pool:
    def __init__(self, size=4):
        self._free = [RequestContext() for _ in range(size)]
        self._lock = threading.Lock()
        self.created = size
        self.reused = 0

    def acquire(self):
        with self._lock:
            if self._free:
                self.reused += 1
                return self._free.pop()
        self.created += 1
        return RequestContext()

    def release(self, ctx):
        with self._lock:
            self._free.append(ctx)

    def stats(self):
        with self._lock:
            return {"free": len(self._free), "created": self.created, "reused": self.reused}


class Handler:
    def __init__(self, pool):
        self.pool = pool

    def handle(self, user, amount, trace_id=None):
        ctx = self.pool.acquire()
        ctx.user = user
        if amount > 0:
            ctx.amount = amount
        ctx.trace_id = trace_id
        result = {"user": ctx.user, "amount": ctx.amount, "trace_id": ctx.trace_id}
        self.pool.release(ctx)
        return result
