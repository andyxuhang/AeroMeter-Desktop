"""Tests for public .amfw validation and device compatibility checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from firmware_update import inspect_package, validate_device_compatibility
from usb_transport import RpcError


def build_package(path: Path, *, counter: int = 120006, corrupt_hash: bool = False) -> dict:
    manifest = {
        "product": "AeroMeter",
        "hardware_profile": "S3-LCD147-R1",
        "layout": "am16-v1",
        "version": "1.2.0-beta.6",
        "build": "testbuild",
        "counter": counter,
        "size": 512,
        "sha256": "",
        "signature": "ab" * 64,
    }
    marker = (
        f"AMMETA1|{manifest['version']}|{manifest['build']}|"
        f"{manifest['hardware_profile']}|{manifest['layout']}|"
        f"{manifest['counter']}|END"
    ).encode("ascii")
    image = bytearray(512)
    image[0] = 0xE9
    image[12:14] = (9).to_bytes(2, "little")
    image[64 : 64 + len(marker)] = marker
    manifest["sha256"] = hashlib.sha256(image).hexdigest()
    if corrupt_hash:
        manifest["sha256"] = "0" * 64
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("firmware.bin", bytes(image))
    return manifest


class FirmwareUpdateTests(unittest.TestCase):
    def test_valid_package_checks_structure_hash_and_embedded_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "firmware.amfw"
            manifest = build_package(path)
            package = inspect_package(path)
            self.assertEqual(package.manifest["counter"], manifest["counter"])
            self.assertEqual(len(package.image), 512)

    def test_bad_hash_is_rejected_before_device_contact(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "firmware.amfw"
            build_package(path, corrupt_hash=True)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                inspect_package(path)

    def test_device_preflight_requires_matching_newer_authorized_ota(self):
        manifest = {
            "product": "AeroMeter",
            "hardware_profile": "S3-LCD147-R1",
            "layout": "am16-v1",
            "counter": 120006,
        }
        good = {
            **manifest,
            "counter": 120005,
            "ota_ready": True,
            "maintenance": True,
            "pending_boot": False,
            "updating": False,
        }
        validate_device_compatibility(good, manifest)

        for changed, expected in (
            ({"maintenance": False}, "Maintenance authorization"),
            ({"ota_ready": False}, "OTA platform"),
            ({"counter": 120006}, "not newer"),
            ({"layout": "legacy"}, "layout mismatch"),
        ):
            with self.subTest(changed=changed):
                info = {**good, **changed}
                with self.assertRaisesRegex(RpcError, expected):
                    validate_device_compatibility(info, manifest)


if __name__ == "__main__":
    unittest.main()
