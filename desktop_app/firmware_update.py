"""User-facing AeroMeter USB firmware package validation and OTA update.

The public desktop client never contains signing private keys. Local validation checks
package structure, image metadata and SHA-256. The AeroMeter device performs the
authoritative ECDSA signature verification with its embedded trusted public key before
accepting ota_begin.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import threading
import time
import zipfile

from PySide6.QtCore import QObject, Signal

from usb_transport import SerialRPC, RpcError, candidate_ports

MAX_IMAGE_SIZE = 0x300000
MANIFEST_FIELDS = (
    "product",
    "hardware_profile",
    "layout",
    "version",
    "build",
    "counter",
    "size",
    "sha256",
)
VERSION_RE = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-(?:[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*))?\Z"
)


@dataclass(frozen=True, slots=True)
class FirmwarePackage:
    path: str
    manifest: dict
    image: bytes


def _validate_manifest(manifest: object) -> dict:
    if not isinstance(manifest, dict):
        raise ValueError("Firmware manifest is not an object")
    if any(field not in manifest for field in MANIFEST_FIELDS):
        raise ValueError("Firmware manifest is incomplete")
    if manifest.get("product") != "AeroMeter":
        raise ValueError("This firmware package is not for AeroMeter")
    for key in ("hardware_profile", "layout"):
        value = manifest.get(key)
        if not isinstance(value, str) or not 1 <= len(value) <= 40:
            raise ValueError(f"Invalid {key}")
    version = manifest.get("version")
    if not isinstance(version, str) or len(version) > 31 or not VERSION_RE.fullmatch(version):
        raise ValueError("Invalid firmware version")
    build = manifest.get("build")
    if not isinstance(build, str) or not re.fullmatch(r"[A-Za-z0-9.-]{1,24}", build):
        raise ValueError("Invalid firmware build ID")
    counter = manifest.get("counter")
    size = manifest.get("size")
    if type(counter) is not int or not 1 <= counter <= 2147483647:
        raise ValueError("Invalid firmware release counter")
    if type(size) is not int or not 288 <= size <= MAX_IMAGE_SIZE:
        raise ValueError("Invalid firmware image size")
    sha256 = manifest.get("sha256")
    if not isinstance(sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise ValueError("Invalid firmware SHA-256")
    signature = manifest.get("signature")
    if not isinstance(signature, str) or not re.fullmatch(r"[0-9a-fA-F]{128,160}", signature):
        raise ValueError("Firmware package has no valid signature encoding")
    return manifest


def _validate_image(image: bytes, manifest: dict) -> None:
    if len(image) != manifest["size"]:
        raise ValueError("Firmware image size does not match the manifest")
    if hashlib.sha256(image).hexdigest() != manifest["sha256"]:
        raise ValueError("Firmware SHA-256 does not match the manifest")
    if len(image) < 14 or image[0] != 0xE9 or int.from_bytes(image[12:14], "little") != 9:
        raise ValueError("Firmware is not an ESP32-S3 application image")
    marker = (
        f"AMMETA1|{manifest['version']}|{manifest['build']}|"
        f"{manifest['hardware_profile']}|{manifest['layout']}|"
        f"{manifest['counter']}|END"
    ).encode("ascii")
    if marker not in image:
        raise ValueError("Firmware image metadata does not match the manifest")


def inspect_package(path: str | Path) -> FirmwarePackage:
    package_path = Path(path)
    if not package_path.is_file():
        raise FileNotFoundError("Firmware package does not exist")
    try:
        with zipfile.ZipFile(package_path) as archive:
            names = archive.namelist()
            if sorted(names) != ["firmware.bin", "manifest.json"] or len(names) != 2:
                raise ValueError("Firmware package contains unexpected or duplicate files")
            if archive.getinfo("manifest.json").file_size > 8192:
                raise ValueError("Firmware manifest is too large")
            if archive.getinfo("firmware.bin").file_size > MAX_IMAGE_SIZE:
                raise ValueError("Firmware image is too large")
            manifest = _validate_manifest(json.loads(archive.read("manifest.json")))
            image = archive.read("firmware.bin")
    except zipfile.BadZipFile as error:
        raise ValueError("Firmware package is not a valid .amfw archive") from error
    _validate_image(image, manifest)
    return FirmwarePackage(str(package_path), manifest, image)


def validate_device_compatibility(info: dict, manifest: dict) -> None:
    for key in ("product", "hardware_profile", "layout"):
        if info.get(key) != manifest.get(key):
            raise RpcError(f"Device/package {key} mismatch")
    current_counter = info.get("counter")
    if type(current_counter) is not int:
        raise RpcError("Device did not report a valid firmware counter")
    if manifest["counter"] <= current_counter:
        raise RpcError("Firmware package is not newer than the running firmware")
    if info.get("updating"):
        raise RpcError("Another firmware update is already running")
    if info.get("pending_boot"):
        raise RpcError("Device is still validating a previous firmware update")
    if not info.get("ota_ready"):
        raise RpcError("Device OTA platform is not ready")
    if not info.get("maintenance"):
        raise RpcError(
            "Maintenance authorization is required. Hold the device information "
            "screen for two seconds, then retry within two minutes."
        )


def _read_identity(port: str) -> tuple[dict, dict]:
    with SerialRPC(port, timeout=5.0) as connection:
        info = connection.call("info")["info"]
        details = connection.call("details")["details"]
    return info, details


def _find_same_device(uid: str, preferred_port: str) -> tuple[str, dict, dict] | None:
    ports = candidate_ports()
    ordered = ([preferred_port] if preferred_port in ports else []) + [
        port for port in ports if port != preferred_port
    ]
    for port in ordered:
        try:
            info, details = _read_identity(port)
        except Exception:
            continue
        if info.get("uid") == uid:
            return port, info, details
    return None


def upgrade_usb(
    port: str,
    package_path: str | Path,
    *,
    progress=None,
    status=None,
) -> dict:
    package = inspect_package(package_path)
    manifest, image = package.manifest, package.image
    status = status or (lambda _message: None)
    progress = progress or (lambda _percent: None)

    status("Reading AeroMeter and checking compatibility…")
    before, before_details = _read_identity(port)
    validate_device_compatibility(before, manifest)
    uid = before.get("uid")
    if not uid:
        raise RpcError("Device did not report a UID")

    owned = False
    status("Device is verifying the signed firmware manifest…")
    with SerialRPC(port, timeout=6.0) as connection:
        try:
            connection.call("ota_begin", **manifest)
            owned = True
            status("Writing firmware to the inactive OTA slot…")
            for offset in range(0, len(image), 512):
                chunk = image[offset : offset + 512]
                reply = None
                for attempt in range(3):
                    try:
                        reply = connection.call(
                            "ota_write", offset=offset, hex=chunk.hex()
                        )
                        break
                    except TimeoutError:
                        if attempt == 2:
                            raise
                if reply is None or reply.get("received") != offset + len(chunk):
                    raise RpcError("Device acknowledgement offset mismatch")
                progress((offset + len(chunk)) * 100 // len(image))
            connection.call("ota_end")
            owned = False
        except BaseException:
            if owned:
                try:
                    connection.call("ota_abort")
                except Exception:
                    pass
            raise

    status("Transfer verified. Waiting for reboot and device self-test…")
    time.sleep(4)
    deadline = time.monotonic() + 100
    last_error = "Device did not reappear after the update"
    while time.monotonic() < deadline:
        found = _find_same_device(uid, port)
        if found is None:
            time.sleep(2)
            continue
        new_port, after, after_details = found
        if any(after.get(key) != before.get(key) for key in ("uid", "sn", "hw")):
            raise RpcError("Device identity changed after firmware update")
        if any(
            after_details.get(key) != before_details.get(key)
            for key in ("manufactured", "calibration_id", "calibration_date")
        ):
            raise RpcError("Factory or calibration metadata changed after firmware update")
        if (
            after.get("counter") == manifest["counter"]
            and after.get("fw") == manifest["version"]
            and after.get("build") == manifest["build"]
            and not after.get("pending_boot")
        ):
            if after.get("slot") == before.get("slot"):
                raise RpcError("Firmware update did not switch OTA slots")
            if not after_details.get("storage_ok"):
                raise RpcError("Factory/calibration storage is not healthy after update")
            progress(100)
            return {
                "port": new_port,
                "before": before,
                "after": after,
                "manifest": manifest,
            }
        last_error = (
            "New firmware has not completed boot validation yet; "
            "startup calibration may still be running or rollback may have occurred"
        )
        time.sleep(2)
    raise RpcError(last_error)


class FirmwareUpdateRunner(QObject):
    progress_changed = Signal(int)
    status_changed = Signal(str)
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, port: str, package_path: str) -> None:
        super().__init__()
        self.port = port
        self.package_path = package_path
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._thread = threading.Thread(
            target=self._run, name="AeroMeter-Firmware-Update", daemon=True
        )
        self._thread.start()

    def _run(self) -> None:
        try:
            result = upgrade_usb(
                self.port,
                self.package_path,
                progress=self.progress_changed.emit,
                status=self.status_changed.emit,
            )
            self.succeeded.emit(result)
        except BaseException as error:
            self.failed.emit(str(error))
        finally:
            self._thread = None
