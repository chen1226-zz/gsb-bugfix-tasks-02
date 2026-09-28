import os
import tempfile
import unittest

from scheduler import Scheduler


class TestScheduler(unittest.TestCase):
    def test_add_and_fire_once(self):
        """既有断言：到点触发一次。"""
        sched = Scheduler()
        sched.add("job", 10.0, 5.0)
        self.assertEqual(sched.tick(4.9), [])
        self.assertEqual(sched.tick(5.0), [("job", 5.0)])

    def test_pending_reflects_next_time(self):
        """既有断言：pending 返回下一次触发时间。"""
        sched = Scheduler()
        sched.add("job", 10.0, 5.0)
        self.assertEqual(sched.pending()["job"], 5.0)

    def test_persisted_definition_survives_reload(self):
        """既有断言：重载后任务定义仍在。"""
        path = os.path.join(tempfile.mkdtemp(), "jobs.json")
        Scheduler(path).add("job", 10.0, 5.0)
        self.assertIn("job", Scheduler(path).pending())


if __name__ == "__main__":
    unittest.main()
