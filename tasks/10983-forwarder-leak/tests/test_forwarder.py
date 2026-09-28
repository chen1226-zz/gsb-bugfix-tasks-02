import socket
import threading
import unittest

from forwarder import Forwarder


class Echo(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(8)
        self.port = self.sock.getsockname()[1]

    def run(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            data = conn.recv(4096)
            conn.sendall(b"echo:" + data)
            conn.close()


class TestForwarder(unittest.TestCase):
    def test_successful_forward(self):
        """既有断言：转发成功返回上游回包。"""
        echo = Echo()
        echo.start()
        fwd = Forwarder("127.0.0.1", echo.port, attempts=1, timeout=1.0)
        self.assertEqual(fwd.forward(b"hi"), b"echo:hi")

    def test_stats_counts_success(self):
        """既有断言：成功次数计入 ok。"""
        echo = Echo()
        echo.start()
        fwd = Forwarder("127.0.0.1", echo.port, attempts=1, timeout=1.0)
        fwd.forward(b"a")
        self.assertEqual(fwd.stats()["ok"], 1)

    def test_failure_raises_oserror(self):
        """既有断言：连不上时抛 OSError。"""
        fwd = Forwarder("127.0.0.1", 1, attempts=1, timeout=0.2)
        with self.assertRaises(OSError):
            fwd.forward(b"x")


if __name__ == "__main__":
    unittest.main()
