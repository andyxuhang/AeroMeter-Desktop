"""Shared Windows/macOS USB transport; no dependency on release tooling."""
from __future__ import annotations

import secrets
import time

from galeon_protocol.rpc import (
    JsonLineDecoder,
    ProtocolRpcError,
    checked_reply,
    json_bytes,
)

PREFIX = b"@AM1 "
RpcError = ProtocolRpcError


class FrameDecoder(JsonLineDecoder):
    def __init__(self):
        super().__init__(PREFIX)


def identity_text(info: dict) -> str:
    return "AeroMeter|" + "|".join(f"{key}={info.get(source, '')}" for key, source in
        (("id", "uid"), ("fw", "fw"), ("sn", "sn"), ("hw", "hw"))) + "|proto=1"


def candidate_ports() -> list[str]:
    """Do not probe arbitrary serial equipment; native ESP32-S3 USB only."""
    from serial.tools import list_ports
    return sorted(p.device for p in list_ports.comports() if (p.vid, p.pid) == (0x303A, 0x1001))


class SerialRPC:
    def __init__(self, port: str, timeout: float = 5.0, serial_factory=None):
        if serial_factory is None:
            import serial
            serial_factory = serial.Serial
        self.serial = serial_factory(port=None, baudrate=115200, timeout=0.05, write_timeout=1.0)
        # Set control-line states before opening. Never use 1200-baud touch/reset.
        self.serial.dtr = False
        self.serial.rts = False
        self.serial.port = port
        self.serial.open()
        self.timeout = timeout
        self.decoder = FrameDecoder()
        self.sequence = secrets.randbelow(2000000000) + 1
        self.events: list[dict] = []

    def poll(self) -> list[dict]:
        data = self.serial.read(min(max(self.serial.in_waiting, 1), 4096))
        return self.decoder.feed(data)

    def call(self, op: str, **fields) -> dict:
        self.sequence = self.sequence % 2147483646 + 1
        request = {**fields, "id": self.sequence, "op": op}
        packet = PREFIX + json_bytes(request) + b"\n"
        if self.serial.write(packet) != len(packet):
            raise RpcError("Incomplete USB write")
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            matching = None
            for reply in self.poll():
                if reply.get("id") == self.sequence:
                    matching = reply
                elif reply.get("id") == 0 and "event" in reply:
                    self.events.append(reply)
                    self.events = self.events[-100:]
            if matching is not None:
                return checked_reply(matching)
        raise TimeoutError(f"USB {op}: device did not reply")

    def close(self):
        self.serial.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
