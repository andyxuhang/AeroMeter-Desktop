from dataclasses import dataclass
import math
import struct

SERVICE_UUID = "8d530001-6c90-4a36-9c5f-5a07d0a11000"
DEVICE_INFO_UUID = "8d530002-6c90-4a36-9c5f-5a07d0a11000"
LIVE_DATA_UUID = "8d530003-6c90-4a36-9c5f-5a07d0a11000"
STATISTICS_UUID = "8d530004-6c90-4a36-9c5f-5a07d0a11000"
CONTROL_UUID = "8d530005-6c90-4a36-9c5f-5a07d0a11000"
RPC_REQUEST_UUID = "8d530006-6c90-4a36-9c5f-5a07d0a11000"
RPC_RESPONSE_UUID = "8d530007-6c90-4a36-9c5f-5a07d0a11000"
PROTOCOL_VERSION = 1
PACKET_TYPE_LIVE = 1
PACKET_TYPE_STATISTICS = 2
LIVE_PACKET_SIZE = 14
STATISTICS_PACKET_SIZE = 20
_LIVE = struct.Struct("<BBHIHHBB")
_STATISTICS = struct.Struct("<BBHIHHHHHH")
STABILITY_NAMES = {0: "IDLE", 1: "ACTIVE", 2: "STABLE"}


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class LiveData:
    sequence: int
    timestamp_ms: int
    pressure_kpa: float
    flow_l_min: float
    stability_state: int
    session_active: bool
    pressure_overrange: bool
    flow_overrange: bool

    @property
    def stability_name(self):
        return STABILITY_NAMES[self.stability_state]


@dataclass(frozen=True, slots=True)
class StatisticsData:
    sequence: int
    timestamp_ms: int
    pressure_mean_kpa: float
    pressure_sigma_kpa: float
    pressure_peak_to_peak_kpa: float
    flow_mean_l_min: float
    flow_sigma_l_min: float
    flow_peak_to_peak_l_min: float


def _header(version, packet_type, expected):
    if version != PROTOCOL_VERSION:
        raise ProtocolError(f"Unsupported protocol version {version}; expected {PROTOCOL_VERSION}")
    if packet_type != expected:
        raise ProtocolError(f"Unexpected packet type {packet_type}; expected {expected}")


def decode_live_packet(data):
    if len(data) != LIVE_PACKET_SIZE:
        raise ProtocolError(f"Invalid live packet length {len(data)}; expected {LIVE_PACKET_SIZE}")
    version, packet_type, sequence, timestamp, pressure, flow, state, flags = _LIVE.unpack(data)
    _header(version, packet_type, PACKET_TYPE_LIVE)
    if state not in STABILITY_NAMES:
        raise ProtocolError(f"Unknown stability state {state}")
    return LiveData(sequence, timestamp, pressure / 100, flow / 100, state,
                    bool(flags & 1), bool(flags & 2), bool(flags & 4))


def decode_statistics_packet(data):
    if len(data) != STATISTICS_PACKET_SIZE:
        raise ProtocolError(f"Invalid statistics packet length {len(data)}; expected {STATISTICS_PACKET_SIZE}")
    value = _STATISTICS.unpack(data)
    _header(value[0], value[1], PACKET_TYPE_STATISTICS)
    return StatisticsData(value[2], value[3], *(item / 100 for item in value[4:]))


def encode_unsigned_hundredths(value):
    if not math.isfinite(value) or value <= 0:
        return 0
    return min(65535, int(math.floor(value * 100 + 0.5)))


def encode_live_packet(sequence, timestamp_ms, pressure_kpa, flow_l_min,
                       stability_state, session_active=False,
                       pressure_overrange=False, flow_overrange=False):
    if stability_state not in STABILITY_NAMES:
        raise ProtocolError(f"Unknown stability state {stability_state}")
    flags = (int(bool(session_active)) | (int(bool(pressure_overrange)) << 1)
             | (int(bool(flow_overrange)) << 2))
    return _LIVE.pack(PROTOCOL_VERSION, PACKET_TYPE_LIVE, sequence & 0xffff,
                      timestamp_ms & 0xffffffff,
                      encode_unsigned_hundredths(pressure_kpa),
                      encode_unsigned_hundredths(flow_l_min), stability_state, flags)


def encode_statistics_packet(sequence, timestamp_ms, pressure_mean_kpa,
                             pressure_sigma_kpa, pressure_peak_to_peak_kpa,
                             flow_mean_l_min, flow_sigma_l_min,
                             flow_peak_to_peak_l_min):
    values = (pressure_mean_kpa, pressure_sigma_kpa, pressure_peak_to_peak_kpa,
              flow_mean_l_min, flow_sigma_l_min, flow_peak_to_peak_l_min)
    return _STATISTICS.pack(PROTOCOL_VERSION, PACKET_TYPE_STATISTICS,
                            sequence & 0xffff, timestamp_ms & 0xffffffff,
                            *(encode_unsigned_hundredths(value) for value in values))


def streaming_command(enabled):
    return bytes((1, int(bool(enabled))))


def rate_command(hertz):
    if hertz not in (5, 10, 20):
        raise ProtocolError(f"Unsupported rate {hertz}")
    return bytes((2, hertz))
