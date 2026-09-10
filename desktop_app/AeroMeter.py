"""Stable package entry point whose filename controls the release artifact name."""
import asyncio
import json
import os
from pathlib import Path
import traceback


def write_self_test_report(text: str) -> None:
    path = os.environ.get("AEROMETER_SELF_TEST_REPORT")
    if path:
        Path(path).write_text(text, encoding="utf-8")


def run_ble_scan_test() -> int:
    """Exercise the packaged Windows BLE backend and save machine-readable results."""
    from ble_client import AeroMeterBleClient

    client = AeroMeterBleClient()
    devices = asyncio.run(client._scan())
    write_self_test_report(
        json.dumps(
            {
                "count": len(devices),
                "devices": [
                    {"name": item.name, "address": item.address, "rssi": item.rssi}
                    for item in devices
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    return 0 if devices else 2


if __name__ == "__main__":
    try:
        if "--ble-scan-test" in __import__("sys").argv:
            raise SystemExit(run_ble_scan_test())
        from main import main

        exit_code = main()
        write_self_test_report(f"exit_code={exit_code}\n")
        raise SystemExit(exit_code)
    except SystemExit:
        raise
    except BaseException:
        write_self_test_report(traceback.format_exc())
        raise
