# AeroMeter Desktop development guide

Windows 和 macOS 共用的 Python/PySide6 桌面测量程序。当前公开发布 Windows 安装包；macOS 兼容源码保留，但本次不构建或发布 macOS 程序。

## 获取源码

协议客户端必要子集已直接包含在仓库中，不需要私有子模块：

```bash
git clone https://github.com/andyxuhang/AeroMeter-Desktop.git
cd AeroMeter-Desktop
```

## 安装、测试和运行

Windows PowerShell 或 macOS Terminal 都在项目根目录执行：

```bash
python desktop_app/manage.py setup --development
python desktop_app/manage.py test
python desktop_app/manage.py run
```

本地环境保存在 `desktop_app/.venv`，不会上传。

## 生成 Windows 发布包

在 Windows 本机运行：

```bash
python desktop_app/manage.py build
```

输出为 `desktop_app/dist/windows/AeroMeter.dist/`。发布时必须分发整个目录，启动文件为其中的 `AeroMeter.exe`。

Windows 包显式包含 Bleak 和 WinRT 蓝牙后端。验证打包后的 BLE 扫描时，可设置 `AEROMETER_SELF_TEST_REPORT` 为可写文件路径并运行 `AeroMeter.exe --ble-scan-test`；输出 JSON 会列出匹配的 AeroMeter 设备。

## 连接策略

- `Auto` 模式并行发现 USB 和 BLE，USB 排在前面。
- 有上次成功设备时，启动后立即尝试直连，同时在后台扫描；直连失败会自动重试一次，之后才回退到扫描到的首台合格设备。
- USB 只接受原生 ESP32-S3 VID `303A` / PID `1001`，并进一步读取设备身份。
- USB 与 BLE 测量负载进入同一个 Protocol 1 解码器。
- 桌面端不显示或修改设备 BLE Stream、Live Rate 设置。
- 压力 CV 低于 0.30 kPa、流量 CV 低于 1.00 L/min 时显示为无意义值。
- OVER 样本不进入数值统计，图表在量程顶端持续显示红线；累计气量标记为不完整。

程序只在连接真正成功后记住设备。关闭程序时会清理当前 USB/BLE 连接。

## macOS 状态

代码仍保留 macOS 平台适配和构建入口，以便之后在 Mac 上验证并打包。本版本没有生成或发布 macOS 安装包。
