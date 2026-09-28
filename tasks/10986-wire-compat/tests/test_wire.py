import unittest

import wire
from wire import Message


class TestWire(unittest.TestCase):
    def test_v1_roundtrip(self):
        """既有断言：v1 编解码往返。"""
        msg = Message("a", 7, "")
        self.assertEqual(wire.decode(wire.encode(msg, 1), 1).as_tuple(), ("a", 7, ""))

    def test_v2_roundtrip(self):
        """既有断言：v2 编解码往返（含 email）。"""
        msg = Message("b", 8, "b@example.com")
        self.assertEqual(wire.decode(wire.encode(msg, 2), 2).as_tuple(), ("b", 8, "b@example.com"))

    def test_unicode_name(self):
        """既有断言：非 ASCII 名字可往返。"""
        msg = Message("名字", 9, "")
        self.assertEqual(wire.decode(wire.encode(msg, 1), 1).as_tuple()[0], "名字")


if __name__ == "__main__":
    unittest.main()
