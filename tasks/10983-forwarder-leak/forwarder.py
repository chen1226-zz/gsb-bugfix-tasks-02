"""长跑转发服务（转发 + 重试）。

对外接口（不得更改签名）：
    Forwarder(host, port, attempts=3, timeout=1.0)
        .forward(payload) -> bytes
        .shutdown()
        .stats() -> dict
"""

import socket
import threading


class Forwarder:
    def __init__(self, host, port, attempts=3, timeout=1.0):
        self.host = host
        self.port = port
        self.attempts = attempts
        self.timeout = timeout
        self._inflight = []
        self._lock = threading.Lock()
        self.ok = 0
        self.failed = 0

    def _connect(self):
        sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        with self._lock:
            self._inflight.append(sock)
        return sock

    def _send_once(self, payload):
        sock = self._connect()
        sock.sendall(payload)
        return sock.recv(65536)

    def forward(self, payload):
        last_error = None
        for _ in range(self.attempts):
            try:
                data = self._send_once(payload)
            except OSError as exc:
                last_error = exc
                continue
            with self._lock:
                self.ok += 1
            return data
        with self._lock:
            self.failed += 1
        raise last_error

    def stats(self):
        with self._lock:
            return {"ok": self.ok, "failed": self.failed, "inflight": len(self._inflight)}

    def shutdown(self):
        return None
