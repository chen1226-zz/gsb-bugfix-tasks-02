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


class TestSchedulerRobustness(unittest.TestCase):
    """新增用例：时钟异常、重启恢复、慢任务、取消/重排。"""

    def test_clock_rollback_neither_dups_nor_loses(self):
        """时钟回拨：水位不动，追平后恰好触发一次。"""
        sched = Scheduler()
        sched.add("job", 10.0, 5.0)
        self.assertEqual(sched.tick(5.0), [("job", 5.0)])
        self.assertEqual(sched.tick(3.0), [])
        self.assertEqual(sched.tick(14.9), [])
        self.assertEqual(sched.tick(15.0), [("job", 15.0)])
        self.assertEqual(sched.tick(15.0), [])

    def test_clock_jump_forward_catches_up_each_slot_once(self):
        """时钟前跳：补齐跳过的全部槽位，且不重复。"""
        sched = Scheduler()
        sched.add("job", 10.0, 0.0)
        fired = sched.tick(35.0)
        self.assertEqual(
            fired, [("job", 0.0), ("job", 10.0), ("job", 20.0), ("job", 30.0)]
        )
        self.assertEqual(sched.pending()["job"], 40.0)
        self.assertEqual(sched.tick(35.0), [])

    def test_restart_resumes_from_persisted_watermark(self):
        """重启恢复：已触发槽位不重放，水位对齐到持久化值。"""
        path = os.path.join(tempfile.mkdtemp(), "jobs.json")
        sched = Scheduler(path)
        sched.add("job", 10.0, 0.0)
        self.assertEqual(sched.tick(10.0), [("job", 0.0), ("job", 10.0)])
        reloaded = Scheduler(path)
        self.assertEqual(reloaded.pending()["job"], 20.0)
        self.assertEqual(reloaded.tick(15.0), [])
        self.assertEqual(reloaded.tick(25.0), [("job", 20.0)])

    def test_restart_catches_up_slots_missed_while_down(self):
        """宕机期间错过的槽位在重启后补触发，且仅一次。"""
        path = os.path.join(tempfile.mkdtemp(), "jobs.json")
        Scheduler(path).add("job", 10.0, 0.0)
        reloaded = Scheduler(path)
        self.assertEqual(
            reloaded.tick(25.0), [("job", 0.0), ("job", 10.0), ("job", 20.0)]
        )
        again = Scheduler(path)
        self.assertEqual(again.tick(25.0), [])
        self.assertEqual(again.pending()["job"], 30.0)

    def test_task_slower_than_interval(self):
        """任务耗时超过间隔：下一次 tick 补齐积压槽位。"""
        sched = Scheduler()
        sched.add("job", 1.0, 0.0)
        self.assertEqual(sched.tick(0.0), [("job", 0.0)])
        self.assertEqual(sched.tick(2.5), [("job", 1.0), ("job", 2.0)])
        self.assertEqual(sched.pending()["job"], 3.0)

    def test_readd_reschedules_and_cancels_old_slot(self):
        """取消/重排：重新 add 后旧水位作废，按新计划触发。"""
        sched = Scheduler()
        sched.add("job", 10.0, 5.0)
        self.assertEqual(sched.tick(5.0), [("job", 5.0)])
        sched.add("job", 10.0, 100.0)
        self.assertEqual(sched.pending()["job"], 100.0)
        self.assertEqual(sched.tick(50.0), [])
        self.assertEqual(sched.tick(100.0), [("job", 100.0)])
