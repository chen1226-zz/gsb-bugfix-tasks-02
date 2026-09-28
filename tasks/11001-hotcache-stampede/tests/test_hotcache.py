import unittest

from hotcache import HotCache


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class TestHotCache(unittest.TestCase):
    def test_caches_within_ttl(self):
        """既有断言：TTL 内命中缓存，不回源。"""
        clock = Clock()
        calls = []
        cache = HotCache(lambda k: calls.append(k) or f"v-{k}", ttl=10.0, clock=clock)
        cache.get("a")
        cache.get("a")
        self.assertEqual(calls, ["a"])
        self.assertEqual(cache.stats()["hits"], 1)

    def test_refreshes_after_ttl(self):
        """既有断言：TTL 到期后回源。"""
        clock = Clock()
        calls = []
        cache = HotCache(lambda k: calls.append(k) or f"v-{k}", ttl=1.0, clock=clock)
        cache.get("a")
        clock.t = 2.0
        cache.get("a")
        self.assertEqual(len(calls), 2)

    def test_keys_are_independent(self):
        """既有断言：不同 key 各自回源一次。"""
        clock = Clock()
        calls = []
        cache = HotCache(lambda k: calls.append(k) or k, ttl=10.0, clock=clock)
        cache.get("a")
        cache.get("b")
        self.assertEqual(sorted(calls), ["a", "b"])


if __name__ == "__main__":
    unittest.main()
