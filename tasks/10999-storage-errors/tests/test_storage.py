import tempfile
import unittest

from storage import Storage


def fresh():
    return Storage(tempfile.mkdtemp())


class TestStorage(unittest.TestCase):
    def test_write_then_read(self):
        """既有断言：正常写入后能读回。"""
        storage = fresh()
        storage.write("a.txt", "hello")
        self.assertEqual(storage.read("a.txt"), "hello")

    def test_write_returns_ok_on_success(self):
        """既有断言：成功时 ok 为 True。"""
        self.assertTrue(fresh().write("a.txt", "x")["ok"])

    def test_read_missing_returns_none(self):
        """既有断言：文件不存在返回 None。"""
        self.assertIsNone(fresh().read("nope.txt"))

    def test_exists(self):
        """既有断言：exists 反映文件状态。"""
        storage = fresh()
        self.assertFalse(storage.exists("a.txt"))
        storage.write("a.txt", "x")
        self.assertTrue(storage.exists("a.txt"))


if __name__ == "__main__":
    unittest.main()
