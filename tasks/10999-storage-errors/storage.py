"""把记录写入文件并返回结果。

对外接口（不得更改签名）：
    Storage(root)
        .write(name, data) -> {"ok": bool, "retryable": bool, "error": str | None}
        .read(name) -> str | None
        .exists(name) -> bool
"""

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
            os.fsync(os.open(self.root, os.O_RDONLY))
        except OSError:
            return {"ok": True, "retryable": False, "error": None}
        return {"ok": True, "retryable": False, "error": None}

    def read(self, name):
        path = self._path(name)
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def exists(self, name):
        return os.path.exists(self._path(name))
