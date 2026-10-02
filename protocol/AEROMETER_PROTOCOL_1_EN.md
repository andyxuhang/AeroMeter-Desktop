# AeroMeter Protocol 1 — Public Client Integration Guide

Last updated: 2026-10-03. Companion desktop: 1.2.1. Wire protocol: 1 (unchanged).

This guide describes public measurement integration for Windows, macOS, Linux, iOS and Android clients. AeroMeter hardware is required; see the [Galeon website](https://www.galeonwhistles.com/). It does not expose firmware updates, calibration, signing, provisioning, serial programming or production/maintenance operations. Do not guess undocumented commands or characteristics.

## 1. Common Rules

- Multibyte integers are little-endian. Pressure is kPa; flow is L/min.
- Pressure/flow integers are divided by 100. Finite positive values are rounded to hundredths; zero, negative and non-finite values encode as zero. This encoding does not guarantee accuracy to 0.01.
- Validate exact packet length, version and type. For live packets validate state as 0, 1 or 2.
- Use overload flags, not displayed numbers, to determine out-of-range readings. Ignore unknown metadata keys and reserved flag bits, but reject unsupported protocol versions/layouts.
- USB and BLE share the 14-byte live and 20-byte statistics layouts. Do not compare counters across transports or packet types.

## 2. BLE Discovery and Characteristics

Match the advertised service UUID rather than relying on names. A typical name is `AeroMeter-AM1-12AB34`, but it is not a unique identity. Read device information and subscribe to live and statistics notifications before enabling streaming.

| Function | UUID | Access |
|---|---|---|
| Service | `8d530001-6c90-4a36-9c5f-5a07d0a11000` | Advertised |
| Device information | `8d530002-6c90-4a36-9c5f-5a07d0a11000` | Read |
| Live measurement | `8d530003-6c90-4a36-9c5f-5a07d0a11000` | Notify |
| Statistics | `8d530004-6c90-4a36-9c5f-5a07d0a11000` | Notify |
| Stream control | `8d530005-6c90-4a36-9c5f-5a07d0a11000` | Write |

Device information is UTF-8 text with a product token followed by pipe-separated key=value entries:

```text
AeroMeter|id=28848555356D|fw=1.2.1|proto=1|sn=AM1-2610-000001|hw=R1
```

`id` identifies the device, `fw` is its firmware version (not the PC version), `proto` its protocol, `sn` its serial and `hw` its hardware revision. Example identifiers are illustrative, not fixed matching values. Ignore unknown keys. Retain address and returned identity when remembering a device.

## 3. Live Packet

Exactly 14 bytes; Python struct format `<BBHIHHBB`.

| Offset | Type | Field | Meaning |
|---:|---|---|---|
| 0 | u8 | version | 1 |
| 1 | u8 | type | 1 |
| 2 | u16 | sequence | Rolling counter |
| 4 | u32 | timestamp_ms | Device uptime in ms |
| 8 | u16 | pressure_x100 | kPa × 100 |
| 10 | u16 | flow_x100 | L/min × 100 |
| 12 | u8 | stability | 0 IDLE, 1 ACTIVE, 2 STABLE |
| 13 | u8 | flags | Bitmask below |

| Mask | Meaning |
|---|---|
| 0x01 | Measurement session active; NOT sensor healthy |
| 0x02 | Pressure overload |
| 0x04 | Flow overload |

Other bits are reserved. Example:

```text
01013412785634127b00d2040205
```

Sequence 4660, uptime 305419896 ms, pressure 1.23 kPa, encoded flow 12.34 L/min, STABLE, session active and flow overload. The overload flag overrides the encoded value and state: 12.34 is not a valid flow reading in this example.

## 4. Statistics Packet

Exactly 20 bytes; Python struct format `<BBHIHHHHHH`. Statistics describe the device's recent 1-second window, not a client-side session summary.

| Offset | Type | Field |
|---:|---|---|
| 0 | u8 | version = 1 |
| 1 | u8 | type = 2 |
| 2 | u16 | sequence |
| 4 | u32 | timestamp_ms |
| 8 | u16 | pressure mean × 100 |
| 10 | u16 | pressure standard deviation Σ × 100 |
| 12 | u16 | pressure peak-to-peak × 100 |
| 14 | u16 | flow mean × 100 |
| 16 | u16 | flow standard deviation Σ × 100 |
| 18 | u16 | flow peak-to-peak × 100 |

```text
0102010002000000640005000900d00714002800
```

Sequence 1, uptime 2 ms; pressure mean 1.00 kPa, Σ 0.05 kPa, P-P 0.09 kPa; flow mean 20.00 L/min, Σ 0.20 L/min, P-P 0.40 L/min.

## 5. BLE Stream Control

Write exactly two bytes to the stream-control characteristic:

| Operation | Bytes (hex) |
|---|---|
| Stop streaming | 01 00 |
| Start streaming | 01 01 |
| Live 5 Hz | 02 05 |
| Live 10 Hz | 02 0A |
| Live 20 Hz | 02 14 |

Subscribe first, select rate, then enable. Statistics are sent at 1 Hz. Stop before disconnecting if possible, but handle abrupt link loss safely. These controls are public developer interfaces; the desktop UI intentionally has no STREAM/RATE controls.

## 6. USB Transport

Candidate VID 0x303A, PID 0x1001; 115200 baud; DTR=false, RTS=false to avoid unintended resets. VID/PID alone does not identify an AeroMeter: send info and verify `product` is `AeroMeter`.

Requests, responses and events are compact ASCII JSON lines prefixed with `@AM1 ` (including the space), ending with LF. The literal `\n` below means one actual LF byte, not two characters. Ignore other debug lines. Request IDs are 1..2147483647 and must be matched with responses; unsolicited events use id=0. Reject oversized input lines (recommended maximum 4096 bytes); keep outgoing JSON within 1500 bytes.

Public requests:

```text
@AM1 {"id":1,"op":"info"}\n
@AM1 {"id":2,"op":"stream","enabled":true}\n
@AM1 {"id":3,"op":"stream","enabled":false}\n
@AM1 {"id":4,"op":"ping"}\n
```

Send ping about every 1.5 seconds, detect failed responses and no-data timeouts. Only these requests are publicly supported. Example response JSON (also prefixed and LF-terminated on the wire):

```json
{"id":1,"ok":true,"info":{"product":"AeroMeter","uid":"28848555356D","fw":"1.2.1","sn":"AM1-2610-000001","hw":"R1"}}
```

```json
{"id":1,"ok":false,"error":"unsupported operation"}
```

USB live rate is 20 Hz; statistics are 1 Hz. Convert hex to bytes, then apply the same decoders as BLE:

```text
@AM1 {"id":0,"event":"live","hex":"01013412785634127b00d2040205"}\n
@AM1 {"id":0,"event":"statistics","hex":"0102010002000000640005000900d00714002800"}\n
```

## 7. Python Decoder Example

```python
import struct

def decode_live(payload: bytes) -> dict:
    if len(payload) != 14:
        raise ValueError("invalid live packet length")
    version, kind, sequence, uptime, pressure, flow, state, flags = struct.unpack(
        "<BBHIHHBB", payload
    )
    if version != 1 or kind != 1 or state not in (0, 1, 2):
        raise ValueError("unsupported or invalid live packet")
    return dict(sequence=sequence, timestamp_ms=uptime,
                pressure_kpa=pressure / 100.0, flow_lpm=flow / 100.0,
                stability=state, session=bool(flags & 1),
                pressure_overrange=bool(flags & 2),
                flow_overrange=bool(flags & 4))
```

Reference parser: [shared_protocol/python/galeon_protocol](shared_protocol/python/galeon_protocol/); [tests](shared_protocol/python/tests/) and [vectors](shared_protocol/vectors/measurement_v1.json). See repository licensing and third-party notices.

## 8. Validity and Compatibility Requirements

**Protocol 1 has no sensor-missing or pressure-zero-incomplete flag.** Missing sensors can result in zero or retained filtered values. Receiving packets, zero values, session-active or STABLE state does not prove measurement validity. Use requires normal startup with no device red warnings. Bypassing startup sensor warnings is maintenance only; inserting sensors afterwards requires a restart and pressure zeroing. Do not claim this interface automatically detects all sensor faults.

Live values are filtered, not raw 100 Hz samples. Quantized Σ may be zero without the underlying signal being noiseless. Flow is not startup-zeroed. Negative readings are clipped. Ranges are pressure 0–10 kPa and flow 0–50 L/min; use overload flags to exclude invalid data, not chart-limit markers or retained numbers.

Handle u16 sequence rollover modulo 65536 and u32 uptime rollover after about 49.7 days. Re-establish timing after reboot/reconnection. Record missing/duplicate packets, gaps and disconnects; distinguish no data from zero flow. Ignore unknown metadata/flag bits for forward compatibility, but reject unknown packet versions, lengths and types. An incompatible binary layout requires a new protocol version.

Client-side volume may differ from device 100 Hz integration. Document rate, clock and missing-data policy; mark results incomplete after overload or communication gaps instead of treating missing readings as valid zero. Sensor specifications are not guaranteed accuracies for derived statistics/volume.

Avoid competing clients on one device and close measurement links before updates. Use only documented interfaces. Validate against reference vectors, then test startup, USB/BLE, overload, interruption, reconnection and reset with actual hardware. Software tests do not replace hardware acceptance.
