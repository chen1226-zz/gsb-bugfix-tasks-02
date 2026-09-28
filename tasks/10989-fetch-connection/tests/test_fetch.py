import unittest

from fake_server import FakeServer
from fetch import Client


class TestFetch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = FakeServer().start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_single_request(self):
        """既有断言：单请求返回路径内容。"""
        client = Client("127.0.0.1", self.server.port, timeout=5.0)
        self.assertEqual(client.get("/hello"), b"/hello")
        client.close()

    def test_sequential_requests(self):
        """既有断言：顺序请求结果正确。"""
        client = Client("127.0.0.1", self.server.port, timeout=5.0)
        for i in range(5):
            self.assertEqual(client.get(f"/s{i}"), f"/s{i}".encode())
        client.close()

    def test_count_increases(self):
        """既有断言：计数随请求增加。"""
        client = Client("127.0.0.1", self.server.port, timeout=5.0)
        client.get("/a")
        client.get("/b")
        self.assertEqual(client.count, 2)
        client.close()


if __name__ == "__main__":
    unittest.main()
