# Changelog

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
- Added overload graph continuity, statistics thresholds, accumulated-volume status, CSV export, and reset confirmation.
- Added Windows packaging and packaged self-test support.

This prerelease provides a Windows package. A macOS package is not included.
