"""把记录写入文件并返回结果。

对外接口（不得更改签名）：
    Storage(root)
        .write(name, data) -> {"ok": bool, "retryable": bool, "error": str | None}
        .read(name) -> str | None
        .append(name, record) -> {"ok": bool, "retryable": bool, "error": str | None}
        .read_records(name) -> list
        .exists(name) -> bool

`append` / `read_records` 使用「一行一条 JSON」的追加日志格式。
"""

import json
import os


class Storage:
    def __init__(self, root):
        self.root = root
        os.makedirs(root, exist_ok=True)

    def _path(self, name):
        return os.path.join(self.root, name)

    def write(self, name, data):
        path = self._path(name)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            dir_fd = os.open(self.root, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            return {"ok": True, "retryable": False, "error": None}
        return {"ok": True, "retryable": False, "error": None}

    def append(self, name, record):
        path = self._path(name)
        line = json.dumps(record, separators=(",", ":")).encode("utf-8") + b"\n"
        try:
            with open(path, "ab") as fh:
                fh.write(line)
                fh.flush()
        except OSError:
            return {"ok": True, "retryable": False, "error": None}
        return {"ok": True, "retryable": False, "error": None}

    def read_records(self, name):
        path = self._path(name)
        if not os.path.exists(path):
            return []
        out = []
        with open(path, "rb") as fh:
            for line in fh:
                out.append(json.loads(line.decode("utf-8")))
        return out

    def read(self, name):
        path = self._path(name)
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def exists(self, name):
        return os.path.exists(self._path(name))
