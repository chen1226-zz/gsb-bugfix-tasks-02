"""按间隔触发持久化任务。

对外接口（不得更改签名）：
    Scheduler(path=None)
        .add(task_id, interval, first_at)
        .tick(now) -> [(task_id, slot)]
        .pending() -> dict
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
        fired = []
        for task_id, job in self.jobs.items():
            if now >= job["next_at"]:
                fired.append((task_id, job["next_at"]))
                job["next_at"] = now + job["interval"]
        self._save()
        return fired

    def pending(self):
        return {tid: job["next_at"] for tid, job in self.jobs.items()}

    def _save(self):
        if not self.path:
            return
        blob = {
            tid: {"interval": job["interval"], "first_at": job["first_at"]}
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
                "next_at": job["first_at"],
            }
