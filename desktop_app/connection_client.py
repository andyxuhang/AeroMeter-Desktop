"""USB-first discovery with the same signals/data models as the existing BLE UI."""
from __future__ import annotations

import asyncio
import threading
import time

from ble_client import AeroMeterBleClient, DiscoveredDevice
from protocol import decode_live_packet, decode_statistics_packet

from usb_transport import SerialRPC, candidate_ports, identity_text


class AeroMeterConnectionClient(AeroMeterBleClient):
    def __init__(self):
        super().__init__()
        self.mode = "Auto"
        self.preferred_address = ""

    def scan(self, mode="Auto", preferred_address=""):
        if mode not in ("Auto", "USB", "BLE"):
            raise ValueError("Unknown connection mode")
        if not self.running:
            self.mode = mode
            self.preferred_address = preferred_address
            super().scan()

    def _scan_usb(self):
        found = []
        for port in candidate_ports():
            if self._stop_requested.is_set():
                break
            try:
                with SerialRPC(port, timeout=1.5) as connection:
                    info = connection.call("info").get("info", {})
                if info.get("product") == "AeroMeter":
                    name = "AeroMeter " + (info.get("sn") or info.get("uid", ""))
                    found.append(DiscoveredDevice(name, "usb:"+port, 0))
            except (OSError, RuntimeError, TimeoutError):
                continue  # Busy port, old firmware, or non-AeroMeter: no writes beyond info.
        return found

    async def _scan(self):
        if self.mode == "USB":
            self.signals.status_changed.emit("SCANNING", "Checking AeroMeter USB connections...")
            try:
                devices = await asyncio.to_thread(self._scan_usb)
            except ImportError:
                raise RuntimeError("USB support needs pyserial; run 'python desktop_app/manage.py setup'")
            self.signals.status_changed.emit("READY", f"Found {len(devices)} USB AeroMeter device(s)")
            return devices

        if self.mode == "BLE":
            return await super()._scan(self.preferred_address)

        self.signals.status_changed.emit("SCANNING", "Checking USB and BLE connections...")
        usb_task = asyncio.create_task(asyncio.to_thread(self._scan_usb))
        ble_task = asyncio.create_task(
            super()._scan(
                "" if self.preferred_address.startswith("usb:") else self.preferred_address
            )
        )
        usb_devices, ble_devices = await asyncio.gather(usb_task, ble_task)
        if self._stop_requested.is_set():
            return []

        # Auto presents both transports. Keep USB first so the preferred local
        # connection remains the default selection without hiding BLE devices.
        devices = usb_devices + ble_devices
        self.signals.status_changed.emit(
            "READY", f"Found {len(devices)} AeroMeter connection(s)"
        )
        return devices

    def connect(self, address, name, locate_timeout=10.0):
        if not address.startswith("usb:"):
            return super().connect(address, name, locate_timeout)
        if self.running:
            return
        self._target_address, self._target_name = address, name
        self._stop_requested.clear()
        self._thread = threading.Thread(target=self._usb_main, name="AeroMeter-USB", daemon=True)
        self._thread.start()

    def _event(self, event):
        if event.get("event") == "live":
            self.signals.live_data_received.emit(decode_live_packet(bytes.fromhex(event["hex"])))
            return True
        if event.get("event") == "statistics":
            self.signals.statistics_received.emit(decode_statistics_packet(bytes.fromhex(event["hex"])))
        return False

    def _usb_main(self):
        try:
            port = self._target_address[4:]
            self.signals.status_changed.emit("CONNECTING", f"USB {port}")
            with SerialRPC(port) as connection:
                info = connection.call("info")["info"]
                if info.get("product") != "AeroMeter":
                    raise RuntimeError("This USB device is not an AeroMeter")
                self.signals.device_info_received.emit(identity_text(info))
                connection.call("stream", enabled=True)
                self.signals.connection_changed.emit(True)
                self.signals.status_changed.emit("CONNECTED", f"USB {port} — {self._target_name}")
                last_ping = last_live = time.monotonic()
                try:
                    while not self._stop_requested.is_set():
                        events = connection.events + connection.poll()
                        connection.events.clear()
                        for event in events:
                            if self._event(event):
                                last_live = time.monotonic()
                        now = time.monotonic()
                        if now - last_ping > 1.5:
                            connection.call("ping")
                            last_ping = time.monotonic()
                        if now - last_live > 10:
                            raise RuntimeError("No measurement data for 10 seconds; check calibration/sensors or update status")
                finally:
                    try:
                        connection.call("stream", enabled=False)
                    except Exception:
                        pass
            self.signals.status_changed.emit("DISCONNECTED", "USB connection closed")
        except Exception as error:
            self.signals.status_changed.emit("ERROR", str(error))
        finally:
            self._thread = None
            self.signals.connection_changed.emit(False)
