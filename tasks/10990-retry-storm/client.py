"""对下游的调用与重试。

对外接口（不得更改签名）：
    TransientError
    Client(transport, max_attempts=3, base_delay=0.0, clock=None, sleeper=None)
        .call(request)
        .stats() -> dict
    Service(client, attempts=3).handle(request)
"""

import time


class TransientError(Exception):
    pass


class Client:
    def __init__(self, transport, max_attempts=3, base_delay=0.0, clock=None, sleeper=None):
        self.transport = transport
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self._clock = clock or time.monotonic
        self._sleeper = sleeper or (lambda s: None)
        self.calls = 0

    def call(self, request):
        last = None
        for attempt in range(self.max_attempts):
            self.calls += 1
            try:
                return self.transport(request)
            except TransientError as exc:
                last = exc
                self._sleeper(self.base_delay * (2 ** attempt))
        raise last

    def stats(self):
        return {"calls": self.calls}


class Service:
    def __init__(self, client, attempts=3):
        self.client = client
        self.attempts = attempts
        self.handled = 0

    def handle(self, request):
        self.handled += 1
        last = None
        for _ in range(self.attempts):
            try:
                return self.client.call(request)
            except TransientError as exc:
                last = exc
        raise last
