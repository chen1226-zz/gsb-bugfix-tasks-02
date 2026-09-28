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
