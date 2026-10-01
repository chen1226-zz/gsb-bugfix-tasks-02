"""按间隔触发持久化任务。

对外接口（不得更改签名）：
    Scheduler(path=None)
        .add(task_id, interval, first_at)
        .tick(now) -> [(task_id, slot)]
        .pending() -> dict

设计要点：
    每个任务维护单调水位 next_at（下一个待触发槽位的绝对时间）。
    tick(now) 触发所有满足 slot <= now 的槽位（补触发），每触发一个
    槽位就把水位推进到 slot + interval，并立即持久化。槽位身份即其
    计划时刻，水位只前进不后退，因此每个槽位恰好触发一次：
      - 时钟回拨：now < next_at，不触发，水位不动，时钟追平后照常触发；
      - 时钟前跳 / 任务耗时超过间隔：while 循环补齐 (old, now] 全部槽位；
      - 进程重启：水位随定义一起落盘，重载后从未触发的槽位继续对齐。
"""

import json
import os


class Scheduler:
    def __init__(self, path=None):
        self.path = path
        self.jobs = {}
        if path and os.path.exists(path):
            self._load()

    def add(self, task_id, interval, first_at):
        self.jobs[task_id] = {
            "interval": float(interval),
            "first_at": float(first_at),
            "next_at": float(first_at),
        }
        self._save()

    def tick(self, now):
        now = float(now)
        fired = []
        for task_id, job in self.jobs.items():
            slot = job["next_at"]
            while slot <= now:
                fired.append((task_id, slot))
                slot += job["interval"]
            job["next_at"] = slot
        if fired:
            self._save()
        return fired

    def pending(self):
        return {tid: job["next_at"] for tid, job in self.jobs.items()}

    def _save(self):
        if not self.path:
            return
        blob = {
            tid: {
                "interval": job["interval"],
                "first_at": job["first_at"],
                "next_at": job["next_at"],
            }
            for tid, job in self.jobs.items()
        }
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(blob, fh)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self.path)

    def _load(self):
        with open(self.path, encoding="utf-8") as fh:
            blob = json.load(fh)
        for tid, job in blob.items():
            self.jobs[tid] = {
                "interval": job["interval"],
                "first_at": job["first_at"],
                # 兼容旧格式（无水位字段）：退化为 first_at
                "next_at": job.get("next_at", job["first_at"]),
            }
