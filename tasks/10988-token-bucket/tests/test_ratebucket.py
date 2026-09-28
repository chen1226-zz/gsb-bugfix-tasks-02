import unittest

from ratebucket import TokenBucket


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class TestTokenBucket(unittest.TestCase):
    def test_burst_then_reject(self):
        """既有断言：突发额度用完后开始拒绝。"""
        b = TokenBucket(1.0, 3.0, clock=Clock())
        self.assertEqual([b.allow("k") for _ in range(4)], [True, True, True, False])

    def test_refills_over_time(self):
        """既有断言：时间推进后可以再次放行。"""
        clock = Clock()
        b = TokenBucket(1.0, 1.0, clock=clock)
        self.assertTrue(b.allow("k"))
        self.assertFalse(b.allow("k"))
        clock.t = 1.5
        self.assertTrue(b.allow("k"))

    def test_keys_are_independent(self):
        """既有断言：不同 key 互不影响。"""
        b = TokenBucket(1.0, 1.0, clock=Clock())
        self.assertTrue(b.allow("a"))
        self.assertTrue(b.allow("b"))


if __name__ == "__main__":
    unittest.main()
