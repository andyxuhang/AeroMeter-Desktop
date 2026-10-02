# AeroMeter Desktop 1.2.1

[English](#english) | [中文](#中文)

## English

### Overview

AeroMeter Desktop is the public desktop client for Galeon AeroMeter. Windows source code and prebuilt packages are available. macOS uses the same cross-platform source, but no macOS package is published in this release.

> **Hardware required:** This application requires AeroMeter hardware. See the [Galeon website](https://www.galeonwhistles.com/) for product information; a more detailed product page may not yet be available.

### Download the Windows Application

Download `AeroMeter-Windows-x64-*.zip` from [GitHub Releases](https://github.com/andyxuhang/AeroMeter-Desktop/releases), extract the complete folder, and run `AeroMeter.exe`. Do not copy the EXE alone or remove its supporting files. The current stable release is [1.2.1](https://github.com/andyxuhang/AeroMeter-Desktop/releases/tag/v1.2.1).

Verify the download against `SHA256SUMS.txt` from the same release. Packages use a directory-based build, without a self-extracting single-file wrapper or executable compression, and are scanned with Windows Defender before upload. A clean local scan does not guarantee security or the absence of antivirus false positives on other computers.

The executable is not signed with a trusted Authenticode certificate. Windows may still show an unknown-publisher or SmartScreen warning. SHA-256 verifies file integrity but does not replace a digital signature; do not disable system security to bypass a warning.

### Before Use

Read the [English user manual](docs/AeroMeter_User_Manual_V1_EN.md), especially the moisture/condensation precautions, startup pressure zeroing, sensor warnings and volume limitations. The desktop version and device firmware are managed separately; a software update is not an instrument calibration or hardware acceptance test.

Protocol 1 has no sensor-missing or pressure-zero-incomplete validity flag. Numbers displayed on the PC do not prove valid measurement. Confirm normal device startup with no red sensor warnings before measuring. See the [release and acceptance notes](docs/RELEASE_1.2.1.md) and [verification report](docs/VERIFICATION_1.2.1.md) for delivery checks and what was actually tested.

### Public Scope

This repository includes:

- The PySide6 desktop interface
- USB and Bluetooth Low Energy connections
- The client-facing subset of the AeroMeter measurement protocol
- Live pressure/flow, charts, statistics and accumulated volume; CSV export is not implemented
- Tests and Windows build tooling

Device firmware, calibration and production algorithms, OTA/signing, serial-number and mass-production tools, and mobile apps are excluded. See [OPEN_SOURCE_SCOPE.md](OPEN_SOURCE_SCOPE.md).

### Third-Party Development

Third-party clients can read AeroMeter data through the public BLE or USB measurement interface. The [English Protocol 1 integration guide](protocol/AEROMETER_PROTOCOL_1_EN.md) documents service UUIDs, binary packets, USB line framing, stream controls, examples, limitations and compatibility rules. Firmware updates, calibration, signing, production and maintenance interfaces are not part of the public protocol.

### Run and Build from Source

Python 3.11 or later is required. From the repository root, run:

```powershell
python desktop_app/manage.py setup --development
python desktop_app/manage.py test
python desktop_app/manage.py run
```

Build the Windows release directory:

```powershell
python desktop_app/manage.py build
```

Output: `desktop_app/dist/windows/AeroMeter.dist/`. For additional development and packaging instructions, see [desktop_app/README.md](desktop_app/README.md).

### License

Project source is licensed under the Apache License 2.0; see [LICENSE](LICENSE). Third-party components remain under their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [LICENSES](LICENSES/).

## 中文

### 项目介绍

AeroMeter Desktop 是 Galeon AeroMeter 的公开桌面客户端。当前提供 Windows 版源码与预编译程序；macOS 使用同一套跨平台源码，但本次不发布 macOS 安装包。

> **硬件要求：** 本程序需要配合 AeroMeter 硬件才能使用。产品信息请访问 [Galeon 官网](https://www.galeonwhistles.com/)（网站可能暂未提供更详细的产品信息）。

### 下载 Windows 程序

从 [GitHub Releases](https://github.com/andyxuhang/AeroMeter-Desktop/releases) 下载 `AeroMeter-Windows-x64-*.zip`，完整解压后运行 `AeroMeter.exe`。不要只复制单个 EXE，也不要删除其依赖文件。当前正式版为 [1.2.1](https://github.com/andyxuhang/AeroMeter-Desktop/releases/tag/v1.2.1)。

下载后使用同一发布页的 `SHA256SUMS.txt` 核对文件完整性。发布包采用目录式构建，不使用自解压单文件封装或可执行文件压缩，并在上传前使用 Windows Defender 扫描。一次本地扫描无异常不能保证绝对安全，也不能保证其他电脑不出现杀毒误报。

当前 EXE 尚未使用受信任的 Authenticode 证书签名，因此 Windows 仍可能显示“未知发布者”或 SmartScreen 提示。SHA-256 可以核对文件完整性，但不能替代数字签名；不要为了跳过提示关闭系统安全保护。

### 使用前必读

请阅读[中文使用说明书](docs/AeroMeter_使用说明书_V1.md)，尤其是湿气/冷凝水防护、开机气压归零、传感器警告和累计气量限制。桌面程序与设备固件分别管理；软件升级不等同于整机校准或实机验收。

Protocol 1 没有传感器缺失或气压归零未完成的有效性标志。PC 出现数字不代表测量有效；测量前须确认设备正常启动、没有红色传感器警告。交付前检查事项及本次实际完成的测试见[发布与验收说明](docs/RELEASE_1.2.1.md)和[验证报告](docs/VERIFICATION_1.2.1.md)。

### 公开范围

本仓库包含：

- PySide6 桌面界面
- USB 与 Bluetooth Low Energy 连接
- AeroMeter 测量协议的客户端必要子集
- 实时压力/流量、图表、统计与累计气量；当前没有 CSV 导出功能
- 测试及 Windows 构建工具

本仓库不包含设备固件、校准与生产算法、OTA/签名、设备序列号和量产工具，也不包含移动端应用。详见 [OPEN_SOURCE_SCOPE.md](OPEN_SOURCE_SCOPE.md)。

### 二次开发

第三方程序可通过公开的 BLE 或 USB 测量接口读取 AeroMeter 数据。服务 UUID、二进制数据包、USB 行协议、数据流控制指令、示例、限制和兼容性规则见 [Protocol 1 中文接入指南](protocol/AEROMETER_PROTOCOL_1.md)。固件升级、校准、签名、生产和维护接口不属于公开协议。

### 从源码运行与构建

需要 Python 3.11 或更新版本。在仓库根目录执行：

```powershell
python desktop_app/manage.py setup --development
python desktop_app/manage.py test
python desktop_app/manage.py run
```

生成 Windows 发布目录：

```powershell
python desktop_app/manage.py build
```

输出位于 `desktop_app/dist/windows/AeroMeter.dist/`。其他开发与打包说明见 [desktop_app/README.md](desktop_app/README.md)。

### 许可证

项目源码采用 Apache License 2.0，见 [LICENSE](LICENSE)。第三方组件保留各自许可证，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 和 [LICENSES](LICENSES/)。
