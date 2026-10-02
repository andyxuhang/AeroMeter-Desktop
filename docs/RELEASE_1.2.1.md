# AeroMeter Desktop 1.2.1 — Release and Acceptance Notes

Release date: 2026-10-03. Application build: 11. Framework: 1.1.0. Protocol: 1.

## 中文

本版由 Windows 桌面 beta9 转为正式版本号，通信与测量逻辑不变。发布包附中英文设备/PC说明书、公开USB/BLE开发接口指南、许可证及第三方声明。

使用前必须正常启动设备，确认没有红色传感器警告。Protocol 1没有传感器缺失/气压未归零的有效性标志；电脑出现数字不代表测量有效。设备气路必须干燥、无冷凝水；请详阅使用说明书。

桌面软件正式版本号不等同于设备固件正式验收。设备固件单独管理，本次没有烧录或进行已知压力/流量点的实机测量。随附说明书如列出候选固件，应由供应方先完成该固件的硬件验收再发货。

发货前检查：

- 登记 SN/HW/FW/BUILD；核对厂家传感器校准资料。
- 正常开机、气压归零、气流提醒、传感器错误/缺失和恢复。
- 已知压力/流量点、稳定/动态测试、超量程红色提示、统计清除。
- USB和BLE连接、断线重连；核对设备与PC读数及累计气量差异。
- 固件升级及断电恢复由专用工具按其流程验证，不属于公开测量接口。
- 在第三方目标Windows电脑完整解压试运行。EXE未签名，不保证没有SmartScreen或杀毒误报。

目前没有CSV导出，不提供macOS安装包。请勿把本说明中的检查清单当作检查已经通过的证明。

## English

This release promotes Windows desktop beta9 to version 1.2.1 without changing measurement or connection behavior. It includes Chinese/English device and PC manuals, public USB/BLE integration guides, licenses and third-party notices.

Require normal device startup without red sensor warnings. Protocol 1 has no sensor-missing or pressure-zero-incomplete validity flag; PC numbers do not prove valid measurement. Keep the gas path dry and condensation-free and read the manual before use.

A stable desktop version is not firmware/hardware acceptance. Firmware is managed separately; this release task does not flash a device or verify known pressure/flow points. Any candidate firmware listed in the manual requires supplier hardware acceptance before delivery.

Before delivery verify identity and calibration records, normal startup and fault recovery, known measurement points, stable/dynamic operation, overload and statistics reset, USB/BLE disconnect/reconnect, device/PC differences and operation on the user's Windows computer. Validate firmware updates separately using the dedicated tool. The executable is unsigned; no SmartScreen/antivirus false-positive guarantee is made.

CSV export and a macOS binary are not included. This checklist is not evidence that the listed hardware checks have already passed. See the accompanying verification report for checks actually performed.
