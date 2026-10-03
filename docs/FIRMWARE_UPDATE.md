# AeroMeter Desktop 固件升级 / Firmware Update

## 中文

AeroMeter Desktop 1.3 起支持通过 USB 安装官方签名的 `.amfw` 固件包。

### 升级前

1. 使用 USB 数据线连接 AeroMeter，并在 Desktop 中选择该 USB 设备。
2. 停止压力/流量测量。
3. 在 AeroMeter 设备信息页长按约 2 秒，开启维护授权。授权窗口约 2 分钟。
4. 点击 **Firmware Update…**，选择官方 `.amfw` 文件。

### Desktop 会检查

- 包内只能包含 `manifest.json` 与 `firmware.bin`；
- manifest 必需字段和版本格式；
- 文件大小；
- SHA-256；
- ESP32-S3 应用镜像头；
- 固件镜像内嵌的版本/build/hardware/layout/release counter metadata；
- 设备 product、hardware profile、partition layout；
- release counter 必须高于当前固件；
- OTA 平台、维护授权和设备状态必须允许升级。

PC 端完成的是**完整性和兼容性预检查**。真正的固件签名校验仍由 AeroMeter 内部的受信任公钥执行；签名私钥不会进入 Desktop 程序或公开仓库。

### 升级过程

Desktop 会断开正常测量连接并独占 USB，将镜像写入备用 OTA 分区。设备校验签名和 SHA-256 后切换启动分区并重启。Desktop 随后重新找到同一 UID 的设备，并核对：

- 固件版本/build/release counter；
- OTA slot 已切换；
- SN / UID / HW 不变；
- 生产日期和校准记录不变；
- 新固件完成启动健康确认，没有 rollback。

升级期间不要拔掉 USB。

## English

AeroMeter Desktop 1.3 can install an official signed `.amfw` package over USB.

Before updating, stop measurement, select the USB AeroMeter, open the device-information page and hold it for about two seconds to authorize maintenance, then choose **Firmware Update…**.

The Desktop app validates package structure, manifest fields, SHA-256, ESP32-S3 image metadata, hardware profile/layout and release counter. The AeroMeter device remains the trust boundary: it verifies the ECDSA signature with its embedded trusted public key before accepting the image.

The image is written to the inactive OTA slot. After reboot, Desktop confirms the new version/build/counter and slot, and verifies that UID, serial number, hardware revision, manufacture metadata and calibration metadata were preserved.

Do not unplug USB while the update is in progress.
