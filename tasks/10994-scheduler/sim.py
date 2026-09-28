"""复现脚本：任务在给定窗口内必须恰好触发一次（不重不漏）。"""

import os
import random
import tempfile

from scheduler import Scheduler

ROUNDS = 200
INTERVAL = 1.0


def one_round(rnd):
    path = os.path.join(tempfile.mkdtemp(), "jobs.json")
    sched = Scheduler(path)
    sched.add("job", INTERVAL, 0.0)

    ticks = [0.0]
    t = 0.0
    for _ in range(6):
        t += rnd.choice([0.3, 1.0, 1.7, 2.5])
        ticks.append(round(t, 6))
    restart_at = rnd.randrange(1, len(ticks))

    fired = []
    for index, now in enumerate(ticks):
        if index == restart_at:
            sched = Scheduler(path)      # 模拟进程重启
        for task_id, slot in sched.tick(now):
            fired.append((task_id, round(slot, 6)))

    highest = int(max(ticks) // INTERVAL)
    expected = {round(k * INTERVAL, 6) for k in range(highest + 1)}
    got = [slot for _, slot in fired]
    dup = len(got) - len(set(got))
    missed = len(expected - set(got))
    extra = len(set(got) - expected)
    return dup, missed, extra


def main():
    rnd = random.Random(20260928)
    total_dup = total_missed = total_extra = 0
    for _ in range(ROUNDS):
        dup, missed, extra = one_round(rnd)
        total_dup += dup
        total_missed += missed
        total_extra += extra
        if dup or missed or extra:
            break

    if total_dup or total_missed or total_extra:
        print(
            f"FAIL: {ROUNDS} schedules, dup={total_dup} missed={total_missed} extra={total_extra}"
        )
        raise SystemExit(1)
    print(f"OK: {ROUNDS} schedules, 0 dup, 0 missed")


if __name__ == "__main__":
    main()
