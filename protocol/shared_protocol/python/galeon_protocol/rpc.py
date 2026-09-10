import json


class ProtocolRpcError(RuntimeError):
    pass


def json_bytes(value, maximum=1500):
    data = json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    if len(data) > maximum:
        raise ProtocolRpcError("Request too large")
    return data


def checked_reply(reply):
    if reply.get("ok") is not True:
        raise ProtocolRpcError(str(reply.get("error", "Invalid device response")))
    return reply


class JsonLineDecoder:
    def __init__(self, prefix=b"", maximum=4096):
        self.prefix, self.maximum = prefix, maximum
        self.buffer = bytearray()
        self.overflow = False

    def feed(self, data):
        frames = []
        for value in data:
            if value == 10:
                if not self.overflow and self.buffer.startswith(self.prefix):
                    try:
                        frame = json.loads(self.buffer[len(self.prefix):])
                        if isinstance(frame, dict): frames.append(frame)
                    except (ValueError, UnicodeDecodeError, RecursionError):
                        pass
                self.buffer.clear(); self.overflow = False
            elif len(self.buffer) < self.maximum:
                self.buffer.append(value)
            else:
                self.overflow = True
        return frames
