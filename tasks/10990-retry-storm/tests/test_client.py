import unittest

from client import Client, Service, TransientError


class Flaky:
    def __init__(self, fail_times):
        self.left = fail_times
        self.calls = 0

    def __call__(self, request):
        self.calls += 1
        if self.left > 0:
            self.left -= 1
            raise TransientError("boom")
        return request


class TestClient(unittest.TestCase):
    def test_success_first_try(self):
        """既有断言：一次成功。"""
        client = Client(Flaky(0), max_attempts=3)
        self.assertEqual(client.call("a"), "a")

    def test_retries_until_success(self):
        """既有断言：失败后重试可以成功。"""
        transport = Flaky(2)
        client = Client(transport, max_attempts=3)
        self.assertEqual(client.call("a"), "a")
        self.assertEqual(transport.calls, 3)

    def test_raises_after_exhausting_attempts(self):
        """既有断言：始终失败时抛出 TransientError。"""
        client = Client(Flaky(99), max_attempts=2)
        with self.assertRaises(TransientError):
            client.call("a")


if __name__ == "__main__":
    unittest.main()
