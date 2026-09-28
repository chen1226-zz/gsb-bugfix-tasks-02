"""复现脚本：多线程复用连接并发请求，检查响应是否串包与句柄是否回落。"""

import os
import threading

from fake_server import FakeServer
from fetch import Client

THREADS = 8
PER_THREAD = 250


def fd_count():
    try:
        return len(os.listdir("/proc/self/fd"))
    except OSError:
        return -1


def main():
    server = FakeServer().start()
    client = Client("127.0.0.1", server.port, timeout=5.0)
    client.get("/warmup")
    base_fds = fd_count()

    mismatch = []
    lock = threading.Lock()

    def worker(tid):
        local_bad = 0
        for i in range(PER_THREAD):
            path = f"/t{tid}-{i}"
            try:
                body = client.get(path)
            except Exception as exc:  # noqa: BLE001
                local_bad += 1
                continue
            if body != path.encode():
                local_bad += 1
        if local_bad:
            with lock:
                mismatch.append((tid, local_bad))

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=120)
    client.close()
    server.stop()
    delta_fds = fd_count() - base_fds

    total = THREADS * PER_THREAD
    bad = sum(n for _, n in mismatch)
    if bad or delta_fds > 5:
        print(f"FAIL: {total} requests, {bad} mismatch, fds {delta_fds:+d}")
        raise SystemExit(1)
    print(f"OK: {total} requests, 0 mismatch, fds back to baseline")


if __name__ == "__main__":
    main()
