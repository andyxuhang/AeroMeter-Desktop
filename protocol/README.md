# Public protocol subset

Third-party integration guide: [AeroMeter Protocol 1](AEROMETER_PROTOCOL_1.md)

This directory contains only the Python protocol modules required by AeroMeter Desktop:

- measurement payload parsing;
- request/response framing used by the public client.

It is vendored into this standalone repository so cloning and building do not require access to a private submodule. Firmware, OTA, provisioning, signing, calibration, and production protocol implementations are not included.

The public decoder tests use the transport-neutral examples in
[shared_protocol/vectors/measurement_v1.json](shared_protocol/vectors/measurement_v1.json).
