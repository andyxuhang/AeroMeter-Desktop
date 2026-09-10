"""Off-screen desktop smoke tests: no serial ports or BLE scans are opened."""
import os
import math
from collections import deque
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from connection_client import AeroMeterConnectionClient, DiscoveredDevice
from main import AeroMeterWindow, display_flow_value, packaged_self_test
from protocol import SERVICE_UUID, decode_live_packet


class DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_flow_display_matches_device_hundredths(self):
        self.assertEqual(display_flow_value(1.23),"1.23")
        self.assertEqual(display_flow_value(None),"---")

    def test_packaged_self_test_has_no_device_access(self):
        self.assertEqual(packaged_self_test(), 0)

    def test_usb_discovery_render_and_protocol(self):
        with patch.object(AeroMeterWindow,"_start_startup_connection"),patch.object(AeroMeterConnectionClient,"connect"):
            window=AeroMeterWindow()
            window._devices_discovered([DiscoveredDevice("AeroMeter test","usb:COM5",0)])
            self.assertIn("COM5",window.device_combo.itemText(0))
            self.assertNotIn("dBm",window.device_combo.itemText(0))
            live=decode_live_packet(struct.pack("<BBHIHHBB",1,1,1,1000,123,234,1,7))
            window._live_data_received(live)
            self.assertTrue(live.pressure_overrange and live.flow_overrange)
            self.assertEqual(window.transport_combo.currentText(),"Auto")
            window._scan_changed(True)
            self.assertFalse(window.transport_combo.isEnabled())
            window.close()

    def test_auto_lists_usb_first_without_hiding_ble(self):
        import asyncio
        client=AeroMeterConnectionClient()
        usb=DiscoveredDevice("AeroMeter USB","usb:COM5",0)
        ble=DiscoveredDevice("AeroMeter BLE","28:84:85:55:35:6D",-43)
        with patch.object(client,"_scan_usb",return_value=[usb]),patch(
            "connection_client.AeroMeterBleClient._scan",
            new=AsyncMock(return_value=[ble]),
        ) as ble_scan:
            self.assertEqual(asyncio.run(client._scan()),[usb,ble])
            ble_scan.assert_awaited_once()

    def test_ble_scan_returns_early_and_caches_backend_device(self):
        import asyncio

        backend = SimpleNamespace(address="28:84:85:55:35:6D", name="AeroMeter-AM1-55")
        advertisement = SimpleNamespace(
            service_uuids=[SERVICE_UUID], local_name="AeroMeter-AM1-55", rssi=-42
        )

        class Scanner:
            def __init__(self, callback):
                self.callback = callback

            async def __aenter__(self):
                self.callback(backend, advertisement)
                return self

            async def __aexit__(self, *_args):
                return False

        client = AeroMeterConnectionClient()
        client.mode = "BLE"
        with patch("ble_client.BleakScanner", Scanner), patch(
            "ble_client.asyncio.sleep", new=AsyncMock()
        ) as settle:
            devices = asyncio.run(client._scan())
        self.assertEqual(devices, [DiscoveredDevice("AeroMeter-AM1-55", backend.address, -42)])
        self.assertIs(client._ble_devices[backend.address], backend)
        settle.assert_awaited_once()

    def test_direct_lookup_is_cached_for_manual_reconnect(self):
        import asyncio

        backend = SimpleNamespace(
            address="28:84:85:55:35:6D", name="AeroMeter-AM1-55"
        )
        client = AeroMeterConnectionClient()
        client._target_address = backend.address
        client._target_name = backend.name
        with patch(
            "ble_client.BleakScanner.find_device_by_address",
            new=AsyncMock(return_value=backend),
        ) as lookup:
            self.assertIs(asyncio.run(client._resolve_target_device()), backend)
            self.assertIs(asyncio.run(client._resolve_target_device()), backend)
        lookup.assert_awaited_once()

    def test_startup_direct_retries_once_then_uses_first_scanned_device(self):
        preferred = DiscoveredDevice("Remembered", "28:84:85:55:35:6D", -55)
        fallback = DiscoveredDevice("Nearby", "28:84:85:55:35:70", -40)
        with patch.object(AeroMeterWindow, "_start_startup_connection"):
            window = AeroMeterWindow()
        window.preferred_device_address = preferred.address
        window.preferred_device_name = preferred.name
        window.startup_scan_pending = True
        with patch.object(window.startup_scanner, "scan") as scan, patch.object(
            window.ble, "connect"
        ) as connect:
            AeroMeterWindow._start_startup_connection(window)
            scan.assert_called_once_with("Auto", "")
            connect.assert_called_once_with(preferred.address, preferred.name, 3.0)

            window.startup_scan_devices = [fallback, preferred]
            window.startup_scan_complete = True
            window._advance_startup_after_error()
            self.assertEqual(connect.call_count, 2)
            connect.assert_called_with(preferred.address, preferred.name, 3.0)

            window._advance_startup_after_error()
            self.assertEqual(connect.call_count, 3)
            connect.assert_called_with(fallback.address, fallback.name, 10.0)
            self.assertEqual(window.startup_phase, "fallback_connect")
        window.close()

    def test_overrange_chart_scrolls_caps_and_recovers_without_fake_statistics(self):
        with patch.object(AeroMeterWindow, "_start_startup_connection"), patch("main.time.monotonic", side_effect=[0.0, 0.1, 0.2, 0.3]):
            window = AeroMeterWindow()
            for seq, flags in enumerate([1, 5, 5, 1]):
                data = decode_live_packet(struct.pack("<BBHIHHBB", 1, 1, seq, seq * 100, 123, 234, 1, flags))
                window._live_data_received(data)
            self.assertEqual(len(window.flow_history), 4)
            self.assertEqual(len(window.pressure_history), 4)
            self.assertTrue(math.isinf(window.flow_history[1][1]))
            self.assertTrue(window.session_volume_incomplete)
            self.assertEqual(window.flow_10s_max.value_label.text(), "2.34")
            # Avoid the session duration timer, which also reads monotonic().
            window.local_session_active = False
            window._refresh_dynamic_display()
            x, red = window.flow_overrange_curve.getData()
            self.assertEqual(list(red[1:3]), [50.0, 50.0])
            self.assertTrue(math.isnan(red[0]) and math.isnan(red[3]))
            self.assertEqual(x[-1], 0.0)
            self.assertAlmostEqual(window.flow_curve.getData()[1][-1], 2.34)
            self.assertEqual(window.flow_plot.viewRange()[1], [0.0, 50.0])
            window._trim_history(11.0)
            window._refresh_dynamic_display()
            self.assertEqual(len(window.flow_history), 0)
            self.assertIsNone(window.flow_overrange_curve.getData()[0])
            window.close()

    def test_missing_read_is_a_gap_not_a_red_cap(self):
        with patch.object(AeroMeterWindow, "_start_startup_connection"):
            window = AeroMeterWindow()
            history = deque([(1.0, 2.0), (2.0, math.nan), (3.0, 3.0)])
            window._refresh_curve(window.flow_curve, history, window.flow_overrange_curve, 50.0)
            self.assertIsNone(window.flow_overrange_curve.getData()[1])
            self.assertTrue(math.isnan(window.flow_curve.getData()[1][1]))
            window.close()

    def test_entire_window_overrange_has_caps_but_no_numeric_statistics(self):
        with patch.object(AeroMeterWindow, "_start_startup_connection"), patch("main.time.monotonic", return_value=1.0):
            window = AeroMeterWindow()
            data = decode_live_packet(struct.pack("<BBHIHHBB", 1, 1, 0, 1000, 123, 234, 0, 6))
            window._live_data_received(data)
            window._refresh_dynamic_display()
            self.assertEqual(window.pressure_10s_avg.value_label.text(), "---")
            self.assertEqual(window.flow_10s_max.value_label.text(), "---")
            self.assertEqual(window.pressure_overrange_curve.getData()[1][0], 10.0)
            self.assertEqual(window.flow_overrange_curve.getData()[1][0], 50.0)
            window.close()



    def test_session_contract_pretrigger_gap_and_valid_other_channel(self):
        with patch.object(AeroMeterWindow, "_start_startup_connection"):
            window = AeroMeterWindow()
            def sample(t, active, pressure_over=False, flow_over=False, flow=6.0):
                data = decode_live_packet(struct.pack("<BBHIHHBB", 1, 1, 0, int(t*1000),
                    123, round(flow*100), 1, int(active) | (2 if pressure_over else 0) | (4 if flow_over else 0)))
                window._update_local_session(data, t, 0.1 if t < 1 else 1.0)
            sample(0.0, False)
            sample(0.1, False)
            sample(0.2, True)
            self.assertAlmostEqual(window.session_volume_l, 0.02)
            sample(0.3, True, pressure_over=True, flow=8.0)
            self.assertTrue(window.session_volume_incomplete)
            self.assertEqual(window.session_flow_max, 8.0)
            sample(0.4, False, flow_over=True)
            self.assertFalse(window.local_session_active)
            window._reset_pc_statistics()
            self.assertEqual(window.session_volume_l, 0)
            sample(0.5, True)
            self.assertEqual(window.session_volume_l, 0)
            sample(1.5, True)
            self.assertTrue(window.session_volume_incomplete)
            self.assertEqual(window.session_volume_l, 0)
            window.close()

if __name__=="__main__":unittest.main()
