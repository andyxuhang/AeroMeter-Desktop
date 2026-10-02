# AeroMeter Desktop 1.2.1 Verification

Date: 2026-10-03. Application 1.2.1, build 11; Windows file/product version 1.2.1.11.

Checks actually performed:

- Desktop unit/offscreen-UI suite: 19 tests passed.
- Shared Protocol 1 suite: 3 tests passed.
- Windows x64 Nuitka directory build: succeeded.
- Packaged EXE `--self-test`: exit 0; exercised Qt and reference decoding without device access.
- Binary metadata and included version.json: 1.2.1/build 11 verified.
- Chinese/English manual chapter numbering: 15 corresponding chapters.
- Firmware/Desktop copies of both manuals: identical hashes at packaging time.
- Complete application directory Windows Defender scan: no threats reported; engine 1.1.26080.3, signature 1.459.518.0.

Not verified in this task: actual sensor accuracy, shipping-hardware startup/fault behavior, live USB/BLE measurements, firmware update/recovery, another user's Windows computer or macOS. Existing candidate firmware remains subject to hardware acceptance. No firmware was flashed. Executable is unsigned; a clean local scan does not guarantee safety or absence of false positives on other computers.

本轮已验证22项自动测试、Windows编译、打包后Qt/协议自检、版本元数据及中英文文档一致性；完整程序目录扫描未发现威胁。尚未进行实机测量/准确度/USB-BLE连接验收或第三方电脑验证，未烧录设备固件。请结合 RELEASE_1.2.1.md 完成发货前检查。
