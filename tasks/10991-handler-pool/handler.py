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
        self.reset()

    def reset(self):
        """重置契约：复用前必须清零的全部字段。

        user / amount / trace_id 任一残留都会泄漏到下一个请求，
        因此这里必须覆盖 __slots__ 中的每一个字段。
        """
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
                ctx = self._free.pop()
                ctx.reset()  # 防御性清零：保证取出的对象一定是干净的
                return ctx
        self.created += 1
        return RequestContext()

    def release(self, ctx):
        ctx.reset()  # 回收即清零：入池对象不得携带上一请求的数据
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
        try:
            ctx.user = user
            if amount > 0:
                ctx.amount = amount
            ctx.trace_id = trace_id
            return {"user": ctx.user, "amount": ctx.amount, "trace_id": ctx.trace_id}
        finally:
            # 正常返回、异常抛出、执行被取消（如 KeyboardInterrupt）
            # 都必须把 ctx 归还池中，且 release 内部负责清零。
            self.pool.release(ctx)
