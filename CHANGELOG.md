# Changelog

## 1.3.0-beta.1 — 2026-10-03

- Added user-facing signed `.amfw` package validation and USB OTA firmware installation.
- Validates package structure, manifest, SHA-256, ESP32-S3 image metadata, device hardware profile/layout and monotonic release counter before transfer.
- Keeps signing private keys and firmware signing/build workflows out of the public Desktop repository.
- Device-side ECDSA verification remains authoritative before the inactive OTA slot is written.
- Verifies the new firmware after reboot and checks that device identity plus factory/calibration metadata remain unchanged.

This prerelease requires real-hardware acceptance testing before promotion to stable.

## 1.2.1 — 2026-10-03

- Promoted desktop beta.9 to stable 1.2.1, build 11; Framework 1.1.0 and Protocol 1 remain unchanged.
- Added complete Chinese and English device/desktop user manuals and an English public integration guide.
- Documented moisture/condensation precautions, pressure-only startup zeroing, sensor-warning limitations, overloads, and desktop-versus-device volume differences.
- Corrected BLE naming, Auto connection behavior, negative-pressure handling, and unsupported CSV-export claims in documentation.
- No measurement, connection, firmware, or wire-protocol behavior changes in this desktop release.

Windows only. Executable remains unsigned. Automated checks do not replace acceptance testing with the shipping hardware.

## 1.2.0-beta.9 — 2026-09-10

- Added the official AeroMeter multi-resolution Windows application icon.
- Retained directory-based Nuitka packaging without a self-extracting one-file wrapper or executable compression.
- Added SHA-256 release verification and Windows Defender scan reporting to the release process.

The Windows executable is currently unsigned because no trusted code-signing certificate is installed. A valid Authenticode certificate is still required to establish publisher identity and reduce Microsoft SmartScreen warnings.

## 1.2.0-beta.8 — 2026-09-10

- Published the standalone AeroMeter Desktop source with a clean public history.
- Added USB and BLE Auto discovery with remembered-device direct connection, one automatic retry, and scan fallback.
- Unified USB and BLE measurement decoding through Protocol 1.
- Kept device BLE Stream and Live Rate controls out of the desktop interface.
- Added overload graph continuity, statistics thresholds, accumulated-volume status, and reset confirmation. (Corrected in 1.2.1: CSV export was not implemented.)
- Added Windows packaging and packaged self-test support.

This prerelease provides a Windows package. A macOS package is not included.
