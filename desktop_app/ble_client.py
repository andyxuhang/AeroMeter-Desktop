"""Background BLE transport for the AeroMeter desktop test tool."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import threading

from bleak import BleakClient, BleakScanner
from PySide6.QtCore import QObject, Signal

from protocol import (
    DEVICE_INFO_UUID,
    DEVICE_NAME_PREFIX,
    LIVE_DATA_UUID,
    SERVICE_UUID,
    STATISTICS_UUID,
    ProtocolError,
    decode_live_packet,
    decode_statistics_packet,
)

SCAN_TIMEOUT_SECONDS = 5.0
SCAN_SETTLE_SECONDS = 0.35
PREFERRED_DEVICE_TIMEOUT_SECONDS = 2.0
DEFAULT_LOCATE_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True, slots=True)
class DiscoveredDevice:
    name: str
    address: str
    rssi: int


class BleSignals(QObject):
    status_changed = Signal(str, str)
    connection_changed = Signal(bool)
    scan_changed = Signal(bool)
    devices_discovered = Signal(object)
    device_info_received = Signal(str)
    live_data_received = Signal(object)
    statistics_received = Signal(object)


class AeroMeterBleClient:
    """Owns Bleak and its asyncio loop on a background Python thread."""

    def __init__(self) -> None:
        self.signals = BleSignals()
        self._thread: threading.Thread | None = None
        self._stop_requested = threading.Event()
        self._target_address = ""
        self._target_name = DEVICE_NAME_PREFIX
        self._locate_timeout_seconds = DEFAULT_LOCATE_TIMEOUT_SECONDS
        self._ble_devices: dict[str, object] = {}

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def scan(self) -> None:
        if self.running:
            return
        self._stop_requested.clear()
        self._thread = threading.Thread(
            target=self._scan_thread_main,
            name="AeroMeter-Scan",
            daemon=True,
        )
        self._thread.start()

    def connect(
        self,
        address: str,
        name: str,
        locate_timeout: float = DEFAULT_LOCATE_TIMEOUT_SECONDS,
    ) -> None:
        if self.running:
            return
        self._target_address = address
        self._target_name = name
        self._locate_timeout_seconds = locate_timeout
        self._stop_requested.clear()
        self._thread = threading.Thread(
            target=self._thread_main,
            name="AeroMeter-BLE",
            daemon=True,
        )
        self._thread.start()

    def disconnect(self) -> None:
        self._stop_requested.set()

    def _thread_main(self) -> None:
        try:
            asyncio.run(self._run())
        except Exception as error:  # Keep BLE errors out of the Qt main thread.
            self.signals.status_changed.emit("ERROR", str(error))
        finally:
            self._thread = None
            self.signals.connection_changed.emit(False)

    def _scan_thread_main(self) -> None:
        self.signals.scan_changed.emit(True)
        try:
            devices = asyncio.run(self._scan())
            self.signals.devices_discovered.emit(devices)
        except Exception as error:
            self.signals.status_changed.emit("ERROR", str(error))
            self.signals.devices_discovered.emit([])
        finally:
            self._thread = None
            self.signals.scan_changed.emit(False)

    async def _scan(self, preferred_address: str = "") -> list[DiscoveredDevice]:
        self.signals.status_changed.emit(
            "SCANNING", "Searching for AeroMeter devices..."
        )
        service_uuid = SERVICE_UUID.casefold()
        matched: dict[str, DiscoveredDevice] = {}
        backend_devices: dict[str, object] = {}
        first_match = asyncio.Event()
        preferred_match = asyncio.Event()

        def detected(device: object, advertisement: object) -> None:
            advertised_services = {
                uuid.casefold() for uuid in (advertisement.service_uuids or [])
            }
            if service_uuid not in advertised_services:
                return
            name = advertisement.local_name or device.name or DEVICE_NAME_PREFIX
            matched[device.address] = DiscoveredDevice(
                name=name,
                address=device.address,
                rssi=advertisement.rssi,
            )
            backend_devices[device.address] = device
            first_match.set()
            if device.address.casefold() == preferred_address.casefold():
                preferred_match.set()

        async with BleakScanner(detected):
            if preferred_address:
                try:
                    await asyncio.wait_for(
                        preferred_match.wait(), PREFERRED_DEVICE_TIMEOUT_SECONDS
                    )
                except TimeoutError:
                    if not first_match.is_set():
                        try:
                            await asyncio.wait_for(
                                first_match.wait(),
                                SCAN_TIMEOUT_SECONDS - PREFERRED_DEVICE_TIMEOUT_SECONDS,
                            )
                        except TimeoutError:
                            pass
            else:
                try:
                    await asyncio.wait_for(first_match.wait(), SCAN_TIMEOUT_SECONDS)
                except TimeoutError:
                    pass
                else:
                    # Keep a short window for a second nearby AeroMeter without
                    # imposing the full scan timeout once the first match exists.
                    await asyncio.sleep(SCAN_SETTLE_SECONDS)

        self._ble_devices = backend_devices
        devices = list(matched.values())
        devices.sort(key=lambda item: (-item.rssi, item.name))
        count = len(devices)
        self.signals.status_changed.emit(
            "READY", f"Found {count} AeroMeter device{'s' if count != 1 else ''}"
        )
        return devices

    async def _run(self) -> None:
        device = await self._resolve_target_device()
        if device is None:
            raise RuntimeError(
                f"{self._target_name} is no longer available. Refresh the device "
                "list and try again."
            )
        if self._stop_requested.is_set():
            self.signals.status_changed.emit("DISCONNECTED", "Scan cancelled")
            return

        self.signals.status_changed.emit("CONNECTING", self._target_name)

        def disconnected_callback(_: BleakClient) -> None:
            self._stop_requested.set()

        async with BleakClient(
            device, disconnected_callback=disconnected_callback
        ) as client:
            # LIVE is the readiness boundary: report the connection as soon as
            # measurements can arrive. Statistics and descriptive information
            # must not delay the first visible sample.
            await client.start_notify(LIVE_DATA_UUID, self._on_live_notification)
            self.signals.connection_changed.emit(True)
            self.signals.status_changed.emit("CONNECTED", self._target_name)

            await client.start_notify(
                STATISTICS_UUID, self._on_statistics_notification
            )

            try:
                raw_info = await client.read_gatt_char(DEVICE_INFO_UUID)
                self.signals.device_info_received.emit(
                    bytes(raw_info).decode("utf-8", errors="replace")
                )
            except Exception as error:
                self.signals.status_changed.emit(
                    "CONNECTED", f"Device info unavailable: {error}"
                )

            while client.is_connected and not self._stop_requested.is_set():
                await asyncio.sleep(0.05)

            if client.is_connected:
                await client.stop_notify(LIVE_DATA_UUID)
                await client.stop_notify(STATISTICS_UUID)

        self.signals.status_changed.emit("DISCONNECTED", "Connection closed")

    async def _resolve_target_device(self) -> object | None:
        device = self._ble_devices.get(self._target_address)
        if device is None:
            self.signals.status_changed.emit(
                "CONNECTING", f"Locating {self._target_name}..."
            )
            device = await BleakScanner.find_device_by_address(
                self._target_address, timeout=self._locate_timeout_seconds
            )
            if device is not None:
                # A direct cold-start lookup must feed the same in-process cache
                # as a normal scan. Manual disconnect/reconnect can then reuse
                # the backend object instead of performing another discovery.
                self._ble_devices[self._target_address] = device
        return device

    def _on_live_notification(self, _characteristic: object, data: bytearray) -> None:
        try:
            self.signals.live_data_received.emit(decode_live_packet(data))
        except ProtocolError as error:
            self.signals.status_changed.emit("PACKET ERROR", str(error))

    def _on_statistics_notification(
        self, _characteristic: object, data: bytearray
    ) -> None:
        try:
            self.signals.statistics_received.emit(decode_statistics_packet(data))
        except ProtocolError as error:
            self.signals.status_changed.emit("PACKET ERROR", str(error))
