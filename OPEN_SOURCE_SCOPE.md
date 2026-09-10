# Open-source scope

This repository is a clean, standalone public distribution of the AeroMeter desktop client. Its Git history does not inherit history from private AeroMeter repositories.

## Included

- Desktop user interface implemented with Python and PySide6
- USB serial and Bluetooth Low Energy discovery and transport
- Client-side Protocol 1 measurement decoding and RPC framing required by the desktop client
- Live pressure and flow display
- Charts, summary statistics, accumulated-volume calculation, overload presentation, and CSV export
- Desktop tests, sample test vectors, and Windows build tooling

## Excluded

- Device firmware and board-support code
- Sensor calibration, factory calibration, and production algorithms
- OTA implementation, signing keys, signing workflows, and secure-boot material
- Serial-number management, provisioning, manufacturing, and factory flashing tools
- Private release-management utilities
- Android, iOS, and other mobile application source
- Private specifications and internal development records

The protocol code in this repository is intentionally limited to the subset required by the public desktop client. It is vendored directly so the public project can be cloned without access to a private repository or submodule.

## Contribution boundary

Issues and pull requests should relate to the public desktop client. Requests that require private firmware, manufacturing, security-key, or calibration internals may be closed or transferred to private development.
