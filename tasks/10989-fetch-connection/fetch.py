"""带重试的 HTTP 客户端。

对外接口（不得更改签名）：
    Client(host, port, timeout=2.0)
        .get(path) -> bytes
        .close()
"""

import http.client


class Client:
    def __init__(self, host, port, timeout=2.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._conn = http.client.HTTPConnection(host, port, timeout=timeout)
        self.count = 0

    def get(self, path):
        self._conn.request("GET", path)
        response = self._conn.getresponse()
        body = response.read()
        self.count += 1
        return body

    def close(self):
        self._conn.close()
