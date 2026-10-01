import unittest
import threading
import tracemalloc

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

    def test_no_leak_after_reuse(self):
        """复用后上一请求的字段不得带入下一请求。"""
        handler = Handler(Pool(size=1))
        handler.handle("alice", 999, trace_id="t1")
        got = handler.handle("bob", 0)
        self.assertEqual(got, {"user": "bob", "amount": 0, "trace_id": None})

    def test_release_returns_clean_context(self):
        """release 后入池对象必须已按重置契约清零。"""
        pool = Pool(size=1)
        ctx = pool.acquire()
        ctx.user, ctx.amount, ctx.trace_id = "alice", 42, "t"
        pool.release(ctx)
        self.assertEqual((ctx.user, ctx.amount, ctx.trace_id), (None, 0, None))

    def test_exception_path_releases_clean_context(self):
        """handle 抛异常时 ctx 仍被归还且清零，后续请求不受影响。"""
        pool = Pool(size=1)
        handler = Handler(pool)
        handler.handle("alice", 100, trace_id="t1")
        with self.assertRaises(TypeError):
            handler.handle("bad", None)  # None > 0 抛 TypeError
        self.assertEqual(pool.stats()["free"], 1)
        got = handler.handle("bob", 0)
        self.assertEqual(got, {"user": "bob", "amount": 0, "trace_id": None})

    def test_concurrent_reuse_no_leak(self):
        """并发复用：每个线程的响应必须等于自己的输入。"""
        pool = Pool(size=4)
        handler = Handler(pool)
        errors = []

        def worker(tid):
            for i in range(200):
                amount = 100 + tid if i % 2 == 0 else 0
                want = {"user": f"u{tid}", "amount": amount, "trace_id": f"t{tid}"}
                got = handler.handle(f"u{tid}", amount, trace_id=f"t{tid}")
                if got != want:
                    errors.append((tid, i, want, got))

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])

    def test_allocation_bounded(self):
        """复用模式下分配次数与内存不得随请求数线性增长。"""
        pool = Pool(size=4)
        handler = Handler(pool)
        handler.handle("warmup", 1)
        created_before = pool.stats()["created"]
        tracemalloc.start()
        before = tracemalloc.get_traced_memory()[0]
        for i in range(2000):
            handler.handle(f"u{i}", i % 7)
        after = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        self.assertEqual(pool.stats()["created"], created_before)
        self.assertLess(after - before, 1_000_000)


if __name__ == "__main__":
    unittest.main()
