"""本机假上游：可配置处理时延与在途上限，用于测试背压传播。

不联网、不依赖第三方库。send() 模拟一次转发，耗时 latency 秒；
在途请求超过 max_inflight 时抛 BackpressureError，模拟上游自我保护。
"""

import time


class BackpressureError(Exception):
    """上游在途请求超限，拒绝接收。"""


class FakeUpstream:
    def __init__(self, latency=0.0, max_inflight=1024):
        self.latency = latency
        self.max_inflight = max_inflight
        self.inflight = 0
        self.received = []

    def send(self, item):
        if self.inflight >= self.max_inflight:
            raise BackpressureError("upstream inflight limit reached")
        self.inflight += 1
        try:
            if self.latency > 0:
                time.sleep(self.latency)
            self.received.append(item)
        finally:
            self.inflight -= 1
