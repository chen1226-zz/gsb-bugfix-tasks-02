"""自定义二进制消息格式（服务端与客户端共用）。

编码格式：tag(<B) | length(<H) | value，依次排列。
v1 字段：1=name(utf-8), 2=age(uint16)
v2 新增：3=email(utf-8, 可选)

对外接口（不得更改签名）：
    encode(msg, version=2) -> bytes
    decode(data, version=1) -> Message
    Message(name, age, email="")
"""

import struct

TAG_NAME = 1
TAG_AGE = 2
TAG_EMAIL = 3

FIELDS = {TAG_NAME: "name", TAG_AGE: "age"}


class Message:
    def __init__(self, name, age, email=""):
        self.name = name
        self.age = age
        self.email = email

    def as_tuple(self):
        return (self.name, self.age, self.email)

    def __eq__(self, other):
        return isinstance(other, Message) and self.as_tuple() == other.as_tuple()


def _field(tag, raw):
    return struct.pack("<BH", tag, len(raw)) + raw


def encode(msg, version=2):
    out = _field(TAG_NAME, msg.name.encode())
    out += _field(TAG_AGE, struct.pack("<H", msg.age))
    if version >= 2 and msg.email:
        out += _field(TAG_EMAIL, msg.email.encode())
    return out


def decode(data, version=1):
    msg = Message("", 0, "")
    pos = 0
    while pos < len(data):
        tag, length = struct.unpack("<BH", data[pos : pos + 3])
        pos += 3
        raw = data[pos : pos + length]
        pos += length
        setattr(msg, FIELDS[tag], raw.decode() if tag != TAG_AGE else struct.unpack("<H", raw)[0])
    return msg
