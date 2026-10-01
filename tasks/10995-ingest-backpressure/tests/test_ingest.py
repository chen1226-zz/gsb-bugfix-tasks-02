import unittest

from ingest import Ingest


class TestIngest(unittest.TestCase):
    def test_offer_then_pump(self):
        """既有断言：先入队再处理。"""
        ing = Ingest(capacity=8)
        self.assertTrue(ing.offer("a"))
        self.assertEqual(ing.pump(), "a")

    def test_pump_empty_returns_none(self):
        """既有断言：空队列返回 None。"""
        self.assertIsNone(Ingest(capacity=8).pump())

    def test_metrics_count_processed(self):
        """既有断言：处理计数正确。"""
        ing = Ingest(capacity=8)
        for i in range(3):
            ing.offer(i)
        ing.pump()
        ing.pump()
        self.assertEqual(ing.metrics()["processed"], 2)


if __name__ == "__main__":
    unittest.main()


class TestBackpressure(unittest.TestCase):
    """新增用例：突发流量、慢消费者、慢上游、恢复期。"""

    def _drive(self, ing, offers, pump_every):
        for i in range(offers):
            ing.offer(f"req-{i}")
            if i % pump_every == 0:
                ing.pump()
        return ing

    def test_burst_rejects_and_bounds_memory(self):
        """突发流量：队列有界，超载部分被拒绝，P99 低于预算。"""
        ing = Ingest(capacity=128, service_time=0.001)
        self._drive(ing, offers=10000, pump_every=10)
        m = ing.metrics()
        self.assertLessEqual(m["max_queue"], 128)
        self.assertGreater(m["rejected"], 0)
        self.assertEqual(m["processed"] + m["rejected"] + m["queued"], 10000)
        self.assertLess(ing.latency_p99(), 0.2)

    def test_slow_consumer_keeps_queue_bounded(self):
        """慢消费者：消费速度远低于到达速度时，队列不无限增长。"""
        ing = Ingest(capacity=64)
        self._drive(ing, offers=5000, pump_every=50)
        m = ing.metrics()
        self.assertLessEqual(m["queued"], 64)
        self.assertGreater(m["rejected"], 0)
        # 低流量下不拒绝：突发结束后单独 offer 成功
        while ing.pump() is not None:
            pass
        self.assertTrue(ing.offer("after-drain"))

    def test_slow_upstream_propagates_backpressure(self):
        """上游变慢：转发速度受限时，ingest 侧快速失败而非堆积。"""
        from fake_upstream import FakeUpstream

        upstream = FakeUpstream(latency=0.002)
        ing = Ingest(capacity=32)
        for i in range(200):
            accepted = ing.offer(i)
            # 上游慢：每 20 个请求才转发一次
            if i % 20 == 0:
                item = ing.pump()
                if item is not None:
                    upstream.send(item)
        m = ing.metrics()
        self.assertGreater(m["rejected"], 0)
        self.assertLessEqual(m["max_queue"], 32)
        self.assertEqual(len(upstream.received), m["processed"])
        # 排空后上游最终收到全部已处理请求
        while True:
            item = ing.pump()
            if item is None:
                break
            upstream.send(item)
        self.assertEqual(len(upstream.received), ing.metrics()["processed"])

    def test_recovery_after_burst(self):
        """恢复期：突发结束后队列排空，offer 恢复成功，指标一致。"""
        ing = Ingest(capacity=16)
        self._drive(ing, offers=1000, pump_every=100)
        self.assertGreater(ing.metrics()["rejected"], 0)
        while ing.pump() is not None:
            pass
        m = ing.metrics()
        self.assertEqual(m["queued"], 0)
        self.assertEqual(m["processed"] + m["rejected"], 1000)
        # 恢复正常流量
        self.assertTrue(ing.offer("new"))
        self.assertEqual(ing.pump(), "new")
