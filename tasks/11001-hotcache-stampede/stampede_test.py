"""复现脚本：跨进程 single-flight + 写回版本 + SWR 立刻返回旧值。"""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time

from hotcache import HotCache

KEYS = 20
PROCS = 4
SWR_WAIT = 0.1

SCHEMA = """
CREATE TABLE IF NOT EXISTS hotcache (
  key               TEXT PRIMARY KEY,
  value             TEXT,
  version           INTEGER NOT NULL DEFAULT 0,
  expires_at        REAL    NOT NULL DEFAULT 0,
  refreshing_until  REAL    NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS calls (key TEXT);
"""

CHILD = r"""
import sqlite3, sys, time
from hotcache import HotCache

db, count = sys.argv[1], int(sys.argv[2])

def origin(key):
    conn = sqlite3.connect(db, timeout=30)
    conn.execute("INSERT INTO calls (key) VALUES (?)", (key,))
    conn.commit()
    conn.close()
    time.sleep(0.01)
    return "v-" + key

cache = HotCache(origin, ttl=1.0, jitter=0.0, stale_ttl=0.5, db_path=db)
for i in range(count):
    cache.get("hot-%d" % i)
"""


def make_db():
    path = os.path.join(tempfile.mkdtemp(), "cache.db")
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    for i in range(KEYS):
        conn.execute(
            "INSERT INTO hotcache (key, value, version, expires_at, refreshing_until) "
            "VALUES (?, NULL, 0, 0, 0)",
            (f"hot-{i}",),
        )
    conn.commit()
    conn.close()
    return path


def check_crossproc(db_path):
    procs = [
        subprocess.Popen(
            [sys.executable, "-c", CHILD, db_path, str(KEYS)],
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        for _ in range(PROCS)
    ]
    for proc in procs:
        proc.wait(timeout=120)

    conn = sqlite3.connect(db_path)
    total_calls = conn.execute("SELECT COUNT(*) FROM calls").fetchone()[0]
    rows = conn.execute("SELECT key, value, version FROM hotcache").fetchall()
    conn.close()

    problems = []
    if total_calls != KEYS:
        problems.append(f"跨进程回源了 {total_calls} 次，应为 {KEYS}（每个 key 只允许一次）")
    bad = [key for key, value, version in rows if value is None or version != 1]
    if bad:
        problems.append(f"{len(bad)} 个 key 没被正确写回（应为 value 非空且 version=1）")
    return problems


def check_swr():
    """刚过期但还在 stale_ttl 窗口内时，必须立刻返回旧值。"""
    path = os.path.join(tempfile.mkdtemp(), "swr.db")
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    now = time.time()
    conn.execute(
        "INSERT INTO hotcache (key, value, version, expires_at, refreshing_until) "
        "VALUES ('swr', 'old-value', 1, ?, 0)",
        (now - 0.1,),
    )
    conn.commit()
    conn.close()

    calls = []

    def origin(key):
        calls.append(key)
        time.sleep(0.3)
        return "new-value"

    cache = HotCache(origin, ttl=1.0, jitter=0.0, stale_ttl=2.0, db_path=path, clock=time.time)
    started = time.perf_counter()
    value = cache.get("swr")
    elapsed = time.perf_counter() - started

    problems = []
    if value != "old-value":
        problems.append(f"SWR 窗口内应返回旧值，实际返回 {value!r}")
    if elapsed > SWR_WAIT:
        problems.append(f"SWR 窗口内应立刻返回（<{SWR_WAIT}s），实际用了 {elapsed:.3f}s")

    deadline = time.time() + 3.0
    while time.time() < deadline:
        conn = sqlite3.connect(path)
        row = conn.execute("SELECT value FROM hotcache WHERE key='swr'").fetchone()
        conn.close()
        if row and row[0] == "new-value":
            break
        time.sleep(0.05)
    else:
        problems.append("后台刷新没有把新值写回去")

    if len(calls) != 1:
        problems.append(f"SWR 触发了 {len(calls)} 次回源，应为 1 次")
    return problems


def check_failure_fallback():
    """回源失败时必须降级返回旧值。"""
    path = os.path.join(tempfile.mkdtemp(), "fail.db")
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.execute(
        "INSERT INTO hotcache (key, value, version, expires_at, refreshing_until) "
        "VALUES ('bad', 'last-good', 1, 0, 0)"
    )
    conn.commit()
    conn.close()

    def origin(key):
        raise RuntimeError("origin 503")

    cache = HotCache(origin, ttl=1.0, jitter=0.0, stale_ttl=0.5, db_path=path, clock=time.time)
    problems = []
    try:
        value = cache.get("bad")
    except Exception as exc:  # noqa: BLE001
        return [f"回源失败时把异常抛给了调用方: {type(exc).__name__}: {exc}"]
    if value != "last-good":
        problems.append(f"回源失败应降级返回旧值，实际 {value!r}")
    if cache.stats()["stale_served"] <= 0:
        problems.append("回源失败时没有计入 stale_served")
    return problems


def main():
    db_path = make_db()
    problems = []
    problems += check_crossproc(db_path)
    problems += check_swr()
    problems += check_failure_fallback()

    if problems:
        print(f"FAIL: {len(problems)} 处不符合预期")
        for item in problems[:4]:
            print("  - " + item)
        raise SystemExit(1)
    print(f"OK: cross-process refreshes == keys ({KEYS}), version == 1, "
          f"swr served stale immediately, failure fell back to last good value")


if __name__ == "__main__":
    main()
