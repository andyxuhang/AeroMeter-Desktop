# AeroMeter Protocol 1 — 客户端接入指南

本文说明第三方客户端读取 Galeon AeroMeter 测量数据所需的公开协议。它适用于 Windows、macOS、Linux、iOS 和 Android 客户端。

本程序和协议需要配合 AeroMeter 硬件使用。产品信息请访问 [Galeon 官网](https://www.galeonwhistles.com/)；网站可能暂未提供更详细的产品信息。

## 1. 公开范围

公开接口包括：

- BLE 设备发现、设备信息读取、实时数据和统计数据通知；
- BLE 数据流开关和刷新率设置；
- USB 设备识别、设备信息读取和测量数据流；
- 与公开 Python 解析器一致的数据格式和测试向量。

本文不定义固件升级、设备配置写入、校准、序列号写入、签名、生产或维护操作。客户端不应猜测或调用未在本文列出的特征、命令或字段。

## 2. 通用规则

- 协议版本：`1`。
- 多字节整数全部采用 little-endian（小端）字节序。
- 压力单位为 `kPa`，流量单位为 `L/min`。
- 压力和流量以无符号整数传输，实际值为整数值除以 `100`。
- 编码端将有限的正数四舍五入到 `0.01`；零、负数和非有限数编码为 `0`。
- 接收端必须检查数据包的精确长度、协议版本和数据包类型。
- `OVER` 状态必须以标志位为准，不要仅根据显示数值推断是否超量程。
- 未知的设备信息字段和未来新增的标志位应忽略，以保持向前兼容。

BLE 和 USB 传输使用相同的 14 字节实时数据包与 20 字节统计数据包。两种连接的序列号和时间戳分别维护，不能跨连接比较。

## 3. Bluetooth Low Energy

### 3.1 服务与特征

| 用途 | UUID | 访问方式 |
| --- | --- | --- |
| AeroMeter 服务 | `8d530001-6c90-4a36-9c5f-5a07d0a11000` | 广播发现 |
| 设备信息 | `8d530002-6c90-4a36-9c5f-5a07d0a11000` | Read |
| 实时数据 | `8d530003-6c90-4a36-9c5f-5a07d0a11000` | Notify |
| 统计数据 | `8d530004-6c90-4a36-9c5f-5a07d0a11000` | Notify |
| 数据流控制 | `8d530005-6c90-4a36-9c5f-5a07d0a11000` | Write |

发现设备时应匹配广播中的 AeroMeter 服务 UUID，不应只依赖设备名称。连接后订阅实时数据和统计数据通知，并读取设备信息。

### 3.2 设备信息

设备信息是 UTF-8 文本：

```text
AeroMeter|id=AM1-55|fw=1.2.0-beta.9|proto=1|sn=AM1-55|hw=R1
```

第一个字段是产品名，后续字段为 `key=value`，使用 `|` 分隔。已定义键包括：

| 键 | 含义 |
| --- | --- |
| `id` | 设备标识 |
| `fw` | 固件版本 |
| `proto` | 协议版本 |
| `sn` | 序列号 |
| `hw` | 硬件修订号 |

解析器应忽略未知键。BLE 名称不是唯一设备身份，持久化设备选择时应优先使用设备地址和设备信息。

### 3.3 实时数据包

实时数据包固定为 14 字节，Python `struct` 格式为 `<BBHIHHBB`。

| 偏移 | 类型 | 字段 | 含义 |
| ---: | --- | --- | --- |
| 0 | `u8` | version | 必须为 `1` |
| 1 | `u8` | type | 必须为 `1` |
| 2 | `u16` | sequence | 循环递增序列号 |
| 4 | `u32` | timestamp_ms | 设备启动后的毫秒数 |
| 8 | `u16` | pressure_x100 | 压力 × 100 |
| 10 | `u16` | flow_x100 | 流量 × 100 |
| 12 | `u8` | stability | `0` 空闲、`1` 活动、`2` 稳定 |
| 13 | `u8` | flags | 状态标志位 |

`flags` 已定义位：

| 位 | 掩码 | 含义 |
| ---: | ---: | --- |
| 0 | `0x01` | 测量会话正在进行 |
| 1 | `0x02` | 压力超量程 |
| 2 | `0x04` | 流量超量程 |

其余位保留，接收端应忽略。

示例数据包：

```text
01013412785634127b00d2040205
```

它表示序列号 `4660`、时间戳 `305419896 ms`、压力 `1.23 kPa`、流量 `12.34 L/min`、状态为稳定、会话有效且流量超量程。

### 3.4 统计数据包

统计数据包固定为 20 字节，Python `struct` 格式为 `<BBHIHHHHHH`。

| 偏移 | 类型 | 字段 | 含义 |
| ---: | --- | --- | --- |
| 0 | `u8` | version | 必须为 `1` |
| 1 | `u8` | type | 必须为 `2` |
| 2 | `u16` | sequence | 循环递增序列号 |
| 4 | `u32` | timestamp_ms | 设备启动后的毫秒数 |
| 8 | `u16` | pressure_mean_x100 | 压力平均值 × 100 |
| 10 | `u16` | pressure_sigma_x100 | 压力标准差 Σ × 100 |
| 12 | `u16` | pressure_pp_x100 | 压力峰峰值 × 100 |
| 14 | `u16` | flow_mean_x100 | 流量平均值 × 100 |
| 16 | `u16` | flow_sigma_x100 | 流量标准差 Σ × 100 |
| 18 | `u16` | flow_pp_x100 | 流量峰峰值 × 100 |

示例：

```text
0102010002000000640005000900d00714002800
```

对应压力平均值 `1.00 kPa`、压力 Σ `0.05 kPa`、压力峰峰值 `0.09 kPa`、流量平均值 `20.00 L/min`、流量 Σ `0.20 L/min`、流量峰峰值 `0.40 L/min`。

### 3.5 数据流控制

向数据流控制特征写入恰好 2 字节：

| 功能 | 数据 |
| --- | --- |
| 停止数据流 | `01 00` |
| 启动数据流 | `01 01` |
| 5 Hz | `02 05` |
| 10 Hz | `02 0A` |
| 20 Hz | `02 14` |

客户端应先订阅通知，再设置刷新率并启动数据流。断开前可停止数据流，但连接异常中断时也必须能够安全退出。

## 4. USB 串口

### 4.1 设备识别与串口设置

- USB VID：`0x303A`
- USB PID：`0x1001`
- 波特率：`115200`
- 每行以 LF（`\n`）结束。
- 打开串口时使用 `DTR=false`、`RTS=false`，避免无意复位设备。

VID/PID 只能筛选候选串口。连接后还必须发送 `info` 请求，并确认返回的 `product` 为 `AeroMeter`。

### 4.2 行协议

每个请求、响应或事件是一行带固定前缀的紧凑 ASCII JSON：

```text
@AM1 {"id":1,"op":"info"}\n
```

- 前缀必须为 `@AM1 `，包含末尾空格。
- 请求 `id` 范围为 `1` 到 `2147483647`，客户端负责匹配响应。
- 设备主动事件使用 `id:0`。
- 建议客户端拒绝超过 4096 字节的输入行；当前公开客户端发送的 JSON 不超过 1500 字节。
- 不带正确前缀的串口输出应忽略。

成功响应：

```json
{"id":1,"ok":true,"info":{"product":"AeroMeter","uid":"...","fw":"1.2.0-beta.9","sn":"AM1-55","hw":"R1"}}
```

失败响应：

```json
{"id":1,"ok":false,"error":"unsupported operation"}
```

### 4.3 公开请求

读取设备信息：

```text
@AM1 {"id":1,"op":"info"}\n
```

启动数据流：

```text
@AM1 {"id":2,"op":"stream","enabled":true}\n
```

停止数据流：

```text
@AM1 {"id":3,"op":"stream","enabled":false}\n
```

连接存活检查：

```text
@AM1 {"id":4,"op":"ping"}\n
```

本文只承诺以上 USB 请求。不要依赖未公开的操作。

### 4.4 测量事件

USB 实时数据固定为 20 Hz，统计数据固定为 1 Hz。事件的 `hex` 字段承载与 BLE 完全相同的二进制数据包：

```text
@AM1 {"id":0,"event":"live","hex":"01013412785634127b00d2040205"}\n
@AM1 {"id":0,"event":"statistics","hex":"0102010002000000640005000900d00714002800"}\n
```

客户端先将 `hex` 解码为字节，再按第 3.3 或 3.4 节解析。

## 5. Python 解码示例

```python
import struct


def decode_live(payload: bytes) -> dict:
    if len(payload) != 14:
        raise ValueError("invalid live packet length")

    version, packet_type, sequence, timestamp_ms, pressure, flow, stability, flags = (
        struct.unpack("<BBHIHHBB", payload)
    )
    if version != 1 or packet_type != 1 or stability not in (0, 1, 2):
        raise ValueError("unsupported or invalid live packet")

    return {
        "sequence": sequence,
        "timestamp_ms": timestamp_ms,
        "pressure_kpa": pressure / 100.0,
        "flow_lpm": flow / 100.0,
        "stability": stability,
        "session": bool(flags & 0x01),
        "pressure_overrange": bool(flags & 0x02),
        "flow_overrange": bool(flags & 0x04),
    }
```

生产代码还应处理序列号回绕、重复包、连接中断、无效十六进制和 JSON 解析失败。

## 6. 参考实现与兼容性

- Python 参考解析器：[`shared_protocol/python/galeon_protocol`](shared_protocol/python/galeon_protocol/)
- 自动测试：[`shared_protocol/python/tests`](shared_protocol/python/tests/)
- 测试向量：[`shared_protocol/vectors/measurement_v1.json`](shared_protocol/vectors/measurement_v1.json)

兼容 Protocol 1 的客户端应忽略未知设备信息键与未定义标志位，但必须拒绝未知协议版本、错误数据包类型和错误长度。未来如果出现不兼容的二进制布局，将使用新的协议版本号。

## 7. English summary

Protocol 1 exposes the client-facing AeroMeter measurement interface over BLE and USB. Both transports carry the same 14-byte live packet and 20-byte statistics packet. All multibyte fields are little-endian; pressure is in kPa × 100 and flow is in L/min × 100. Treat overload flag bits as authoritative, validate version/type/exact length, and ignore unknown metadata keys or reserved flag bits.

The public scope is read-only measurement integration plus stream control. Firmware update, provisioning, calibration, signing, serial-number programming, production, and maintenance operations are intentionally excluded.
