# AeroMeter Desktop

AeroMeter 的公开桌面客户端。当前提供 Windows 版源码与预编译程序；macOS 使用同一套跨平台源码，但本次暂不发布安装包。

## 下载 Windows 版

普通用户请从 GitHub 的 **Releases** 页面下载最新的 `AeroMeter-Windows-x64-*.zip`。解压完整目录后运行 `AeroMeter.exe`，不要只复制单个 EXE。

下载后可用同一发布页中的 SHA256SUMS.txt 核对文件完整性。发布包采用目录式构建，不使用自解压单文件封装或可执行文件压缩，并在上传前使用 Windows Defender 扫描。

当前 EXE 尚未使用受信任的 Authenticode 证书签名，因此部分电脑仍可能显示“未知发布者”或 SmartScreen 提示。SHA-256 可以确认文件完整性，但不能替代数字签名。

## 公开范围

本仓库包含：

- PySide6 桌面界面
- USB 与 Bluetooth Low Energy 连接
- AeroMeter 测量协议的客户端必要子集
- 实时压力/流量、图表、统计、累计气量与 CSV 导出
- 测试及 Windows 构建工具

本仓库不包含设备固件、校准与生产算法、OTA/签名、设备序列号和量产工具，也不包含移动端应用。详见 [OPEN_SOURCE_SCOPE.md](OPEN_SOURCE_SCOPE.md)。

## 从源码运行

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

输出位于 `desktop_app/dist/windows/AeroMeter.dist/`。

## English

AeroMeter Desktop is the public desktop client for Galeon AeroMeter. Windows source code and prebuilt packages are currently available. The same source is designed to remain compatible with macOS, but no macOS package is published in this release.

The public repository includes the PySide6 UI, USB/BLE transports, the client-side measurement protocol subset, charts, statistics, accumulated volume, CSV export, tests, and Windows build tooling. Device firmware, calibration and production algorithms, OTA/signing, serial-number tooling, and mobile apps are excluded.

Download the Windows ZIP from **GitHub Releases**, extract the complete folder, and run AeroMeter.exe. Verify its SHA-256 value against SHA256SUMS.txt. The package uses an unpacked directory build without executable compression and is scanned with Windows Defender before upload.

The executable is currently unsigned, so Windows may still show an unknown-publisher or SmartScreen warning until a trusted Authenticode certificate is available.

## License

Project source is licensed under the Apache License 2.0. Third-party components remain under their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [LICENSES](LICENSES/).
