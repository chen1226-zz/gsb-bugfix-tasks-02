"""本机假下游：可切换“故障 / 恢复”。"""


class FakeDownstream:
    def __init__(self):
        self.calls = 0
        self.healthy = False

    def __call__(self, request):
        from client import TransientError

        self.calls += 1
        if not self.healthy:
            raise TransientError("downstream 503")
        return {"ok": request}
