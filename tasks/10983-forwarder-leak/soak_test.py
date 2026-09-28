"""复现脚本：反复走失败/超时路径，检查句柄是否回落。"""

import os
import socket
import threading

from forwarder import Forwarder

REQUESTS = 2000


def fd_count():
    try:
        return len(os.listdir("/proc/self/fd"))
    except OSError:
        return -1


class FakeUpstream(threading.Thread):
    """一半直接断连，一半收下就不回。"""

    def __init__(self):
        super().__init__(daemon=True)
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(64)
        self.port = self.sock.getsockname()[1]
        self.stopped = False
        self.held = []

    def run(self):
        n = 0
        while not self.stopped:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            n += 1
            if n % 2:
                conn.close()
            else:
                self.held.append(conn)

    def stop(self):
        self.stopped = True
        self.sock.close()
        for conn in self.held:
            try:
                conn.close()
            except OSError:
                pass


def main():
    upstream = FakeUpstream()
    upstream.start()
    fwd = Forwarder("127.0.0.1", upstream.port, attempts=1, timeout=0.05)
    try:
        fwd.forward(b"warmup")
    except OSError:
        pass
    base_fds = fd_count()
    base_threads = threading.active_count()

    for i in range(REQUESTS):
        try:
            fwd.forward(b"payload-%d" % i)
        except OSError:
            pass

    fwd.shutdown()
    upstream.stop()
    upstream.join(timeout=5)

    now_fds = fd_count()
    now_threads = threading.active_count()
    stats = fwd.stats()
    delta_fds = now_fds - base_fds
    delta_threads = now_threads - base_threads

    if delta_fds > 5 or delta_threads > 1:
        print(f"FAIL: threads {delta_threads:+d}, fds {delta_fds:+d}")
        print(f"  inflight={stats['inflight']} ok={stats['ok']} failed={stats['failed']}")
        raise SystemExit(1)
    print(f"OK: {REQUESTS} requests, threads {delta_threads:+d}, fds {delta_fds:+d}")


if __name__ == "__main__":
    main()
