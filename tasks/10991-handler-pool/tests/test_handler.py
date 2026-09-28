import unittest

from handler import Handler, Pool, RequestContext


class TestHandlerPool(unittest.TestCase):
    def test_single_request(self):
        """既有断言：单请求字段正确。"""
        handler = Handler(Pool(size=1))
        got = handler.handle("alice", 50, trace_id="t1")
        self.assertEqual(got, {"user": "alice", "amount": 50, "trace_id": "t1"})

    def test_zero_amount_request(self):
        """既有断言：冷启动时金额为 0。"""
        handler = Handler(Pool(size=1))
        got = handler.handle("bob", 0, trace_id="t2")
        self.assertEqual(got["amount"], 0)

    def test_pool_reuse_stats(self):
        """既有断言：池统计能看到复用。"""
        pool = Pool(size=2)
        handler = Handler(pool)
        handler.handle("a", 1)
        handler.handle("b", 2)
        self.assertGreaterEqual(pool.stats()["reused"], 1)

    def test_context_defaults(self):
        """既有断言：上下文默认值。"""
        ctx = RequestContext()
        self.assertEqual((ctx.user, ctx.amount, ctx.trace_id), (None, 0, None))


if __name__ == "__main__":
    unittest.main()
