"""Shared AeroMeter USB/BLE desktop application for Windows and macOS."""

from __future__ import annotations

from collections import deque
import math
import sys
import time

import pyqtgraph as pg
from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from connection_client import AeroMeterConnectionClient, DiscoveredDevice
from protocol import LiveData, StatisticsData, decode_live_packet
from app_version import APP_VERSION, FRAMEWORK_VERSION
from measurement_policy import VolumeIntegrator, coefficient


WINDOW_SECONDS = 10.0
MAX_HISTORY_POINTS = 400
STARTUP_DIRECT_TIMEOUT_SECONDS = 3.0


def display_value(value: float | None, decimals: int = 2) -> str:
    if value is None or not math.isfinite(value):
        return "---"
    return f"{value:.{decimals}f}"


def display_flow_value(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "---"
    return f"{value:.2f}"


def display_duration(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class MetricCard(QFrame):
    def __init__(
        self,
        title: str,
        unit: str = "",
        value: str = "---",
        accent: str = "#e9f0f7",
        large: bool = False,
    ) -> None:
        super().__init__()
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("metricTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("heroValue" if large else "metricValue")
        self.value_label.setStyleSheet(f"color: {accent};")
        self.unit_label = QLabel(unit)
        self.unit_label.setObjectName("metricUnit")

        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.value_label)
        if unit:
            layout.addWidget(self.unit_label)

    def set_value(self, value: float | None, decimals: int = 2) -> None:
        self.value_label.setText(display_value(value, decimals))


class HeroMeasurement(QFrame):
    def __init__(self, title: str, unit: str, accent: str) -> None:
        super().__init__()
        self.accent = accent
        self.setObjectName("heroPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(4)

        title_row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("heroTitle")
        unit_label = QLabel(unit)
        unit_label.setObjectName("heroUnit")
        title_row.addWidget(title_label)
        title_row.addStretch()
        title_row.addWidget(unit_label)

        self.value_label = QLabel("--.--")
        self.value_label.setObjectName("realtimeValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet(f"color: {accent};")

        stats = QGridLayout()
        stats.setHorizontalSpacing(20)
        self.sigma_value = QLabel("---")
        self.pp_value = QLabel("---")
        for column, (name, value_label) in enumerate(
            (("Σ", self.sigma_value), ("P-P", self.pp_value))
        ):
            key = QLabel(name)
            key.setObjectName("inlineMetricTitle")
            value_label.setObjectName("inlineMetricValue")
            stats.addWidget(key, 0, column)
            stats.addWidget(value_label, 1, column)

        layout.addLayout(title_row)
        layout.addWidget(self.value_label, 1)
        layout.addLayout(stats)

    def set_value(self, value: float | None, overrange: bool, *, flow: bool = False) -> None:
        if overrange:
            self.value_label.setText("OVER")
            self.value_label.setStyleSheet("color: #ff5c68;")
            return
        self.value_label.setText(display_flow_value(value) if flow else display_value(value))
        self.value_label.setStyleSheet(f"color: {self.accent};")


class AeroMeterWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"Galeon AeroMeter {APP_VERSION} — Framework {FRAMEWORK_VERSION} — USB / BLE")
        self.resize(1280, 820)
        self.setMinimumSize(980, 680)

        self.ble = AeroMeterConnectionClient()
        # Startup discovery uses a separate client so it can run while the
        # remembered address is being connected directly.
        self.startup_scanner = AeroMeterConnectionClient()
        self.settings = QSettings("Galeon", "AeroMeter")
        self.preferred_device_address = self.settings.value("lastDeviceAddress", "", str)
        self.preferred_device_name = self.settings.value("lastDeviceName", "AeroMeter", str)
        self.startup_scan_pending = True
        self.auto_connect_after_scan = False
        self.connected = False
        self.auto_connect_device: DiscoveredDevice | None = None
        self.fallback_connect_device: DiscoveredDevice | None = None
        self.startup_phase = "idle"
        self.startup_direct_attempts = 0
        self.startup_scan_complete = False
        self.startup_scan_devices: list[DiscoveredDevice] = []
        self.connected_device_address = ""
        self.connected_device_name = ""
        self.closing = False
        self.close_deadline = 0.0
        self.latest_live: LiveData | None = None
        self.latest_statistics: StatisticsData | None = None
        self.pressure_history: deque[tuple[float, float]] = deque(
            maxlen=MAX_HISTORY_POINTS
        )
        self.flow_history: deque[tuple[float, float]] = deque(
            maxlen=MAX_HISTORY_POINTS
        )

        self._volume_integrator = VolumeIntegrator()
        self._pretrigger = deque()
        self.local_session_active = False
        self.session_started_at: float | None = None
        self.session_duration_s = 0.0
        self.session_volume_l = 0.0
        self.session_volume_incomplete = False
        self.session_pressure_min: float | None = None
        self.session_pressure_max: float | None = None
        self.session_flow_min: float | None = None
        self.session_flow_max: float | None = None
        self.last_sample_time: float | None = None
        self.stable_pressure: float | None = None
        self.stable_flow: float | None = None
        self.capture_stable_on_next_statistics = False

        self._build_ui()
        self._connect_signals()

        self.chart_timer = QTimer(self)
        self.chart_timer.setInterval(50)
        self.chart_timer.timeout.connect(self._refresh_dynamic_display)
        self.chart_timer.start()
        # Start immediately once Qt's event loop is ready. Running discovery
        # inside the constructor can delay the first paint on slower systems.
        QTimer.singleShot(0, self._start_startup_connection)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 14, 18, 16)
        root.setSpacing(12)

        root.addLayout(self._build_header())
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._build_live_page(), "1  LIVE VIEW")
        self.tabs.addTab(self._build_statistics_page(), "2  STATISTICS")
        root.addWidget(self.tabs, 1)
        root.addLayout(self._build_device_info_bar())

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        product = QLabel(f"AeroMeter  {APP_VERSION}")
        product.setObjectName("productName")
        self.status_dot = QLabel("●")
        self.status_dot.setObjectName("statusDot")
        self.status_label = QLabel("DISCONNECTED")
        self.status_label.setObjectName("statusLabel")
        self.detail_label = QLabel("Ready")
        self.detail_label.setObjectName("detailLabel")
        self.detail_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.device_combo = QComboBox()
        self.transport_combo = QComboBox()
        self.transport_combo.addItems(["Auto", "USB", "BLE"])
        self.transport_combo.setToolTip("Auto: show USB and BLE, with USB listed first. Refresh after changing.")
        self.device_combo.setMinimumWidth(255)
        self.device_combo.setPlaceholderText("No AeroMeter selected")
        self.scan_button = QPushButton("Refresh")
        self.connect_button = QPushButton("Connect")
        self.connect_button.setObjectName("primaryButton")
        self.connect_button.setMinimumWidth(120)
        self.connect_button.setEnabled(False)

        header.addWidget(product)
        header.addSpacing(18)
        header.addWidget(self.status_dot)
        header.addWidget(self.status_label)
        header.addWidget(self.detail_label)
        header.addWidget(self.transport_combo)
        header.addWidget(self.device_combo)
        header.addWidget(self.scan_button)
        header.addWidget(self.connect_button)
        return header

    def _build_live_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 10, 4, 8)
        layout.setSpacing(10)

        state_row = QHBoxLayout()
        state_row.addWidget(QLabel("MEASUREMENT STATE"))
        self.overview_state = QLabel("---")
        self.overview_state.setObjectName("stateBadge")
        state_row.addWidget(self.overview_state)
        state_row.addStretch()
        state_row.addWidget(QLabel("SESSION"))
        self.overview_session = QLabel("---")
        self.overview_session.setObjectName("sessionBadge")
        state_row.addWidget(self.overview_session)
        layout.addLayout(state_row)

        measurements = QHBoxLayout()
        measurements.setSpacing(10)
        self.overview_pressure = HeroMeasurement("PRESSURE", "kPa", "#56c7ff")
        self.overview_flow = HeroMeasurement("FLOW", "L/min", "#69e6a6")
        derived = QVBoxLayout()
        derived.setSpacing(10)
        self.overview_pq = MetricCard("P/Q", "kPa per L/min", large=True)
        self.overview_power = MetricCard("POWER", "W", large=True)
        derived.addWidget(self.overview_pq)
        derived.addWidget(self.overview_power)
        measurements.addWidget(self.overview_pressure, 3)
        measurements.addWidget(self.overview_flow, 3)
        measurements.addLayout(derived, 2)
        layout.addLayout(measurements, 2)

        charts = QHBoxLayout()
        charts.setSpacing(10)

        pressure_section = QVBoxLayout()
        pressure_section.setSpacing(7)
        self.pressure_plot, self.pressure_curve = self._create_plot(
            "PRESSURE — LAST 10 SECONDS", "Pressure", "kPa", "#56c7ff"
        )
        pressure_section.addWidget(self.pressure_plot, 1)
        pressure_stats = QHBoxLayout()
        pressure_stats.setSpacing(7)
        self.pressure_10s_avg = MetricCard("10 s AVG", "kPa")
        self.pressure_10s_min = MetricCard("10 s MIN", "kPa")
        self.pressure_10s_max = MetricCard("10 s MAX", "kPa")
        pressure_stats.addWidget(self.pressure_10s_avg)
        pressure_stats.addWidget(self.pressure_10s_min)
        pressure_stats.addWidget(self.pressure_10s_max)
        pressure_section.addLayout(pressure_stats)

        flow_section = QVBoxLayout()
        flow_section.setSpacing(7)
        self.flow_plot, self.flow_curve = self._create_plot(
            "FLOW — LAST 10 SECONDS", "Flow", "L/min", "#69e6a6"
        )
        self.pressure_overrange_curve = self.pressure_plot.plot(
            pen=pg.mkPen("#ff5252", width=3), symbol="s", symbolSize=4,
            symbolPen=None, symbolBrush="#ff5252", connect="finite")
        self.flow_overrange_curve = self.flow_plot.plot(
            pen=pg.mkPen("#ff5252", width=3), symbol="s", symbolSize=4,
            symbolPen=None, symbolBrush="#ff5252", connect="finite")
        flow_section.addWidget(self.flow_plot, 1)
        flow_stats = QHBoxLayout()
        flow_stats.setSpacing(7)
        self.flow_10s_avg = MetricCard("10 s AVG", "L/min")
        self.flow_10s_min = MetricCard("10 s MIN", "L/min")
        self.flow_10s_max = MetricCard("10 s MAX", "L/min")
        flow_stats.addWidget(self.flow_10s_avg)
        flow_stats.addWidget(self.flow_10s_min)
        flow_stats.addWidget(self.flow_10s_max)
        flow_section.addLayout(flow_stats)

        charts.addLayout(pressure_section)
        charts.addLayout(flow_section)
        layout.addLayout(charts, 3)
        return page

    def _build_statistics_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 14, 4, 8)
        layout.setSpacing(12)

        columns = QHBoxLayout()
        columns.setSpacing(14)
        pressure_panel, self.pressure_stat_values = self._statistics_column(
            "PRESSURE", "kPa", "#56c7ff"
        )
        flow_panel, self.flow_stat_values = self._statistics_column(
            "FLOW", "L/min", "#69e6a6"
        )
        columns.addWidget(pressure_panel)
        columns.addWidget(flow_panel)
        layout.addLayout(columns, 3)

        stable_title = QLabel("STABLE & SESSION")
        stable_title.setObjectName("sectionTitle")
        layout.addWidget(stable_title)
        bottom = QGridLayout()
        bottom.setHorizontalSpacing(10)
        bottom.setVerticalSpacing(10)
        self.stable_pressure_card = MetricCard("STABLE P", "kPa")
        self.stable_flow_card = MetricCard("STABLE Q", "L/min")
        self.stable_pq_card = MetricCard("P/Q", "kPa per L/min")
        self.session_volume_card = MetricCard("VOLUME", "L")
        self.session_duration_card = MetricCard("DURATION")
        cards = (
            self.stable_pressure_card,
            self.stable_flow_card,
            self.stable_pq_card,
            self.session_volume_card,
            self.session_duration_card,
        )
        for column, card in enumerate(cards):
            bottom.addWidget(card, 0, column)
        layout.addLayout(bottom, 2)

        note = QLabel(
            "Session values are App estimates, not device totals. "
            "Volume ! = incomplete (OVER or data gap)."
        )
        note.setObjectName("footnote")
        footer = QHBoxLayout()
        footer.addWidget(note, 1)
        self.reset_statistics_button = QPushButton("RESET STATISTICS")
        self.reset_statistics_button.setObjectName("dangerButton")
        footer.addWidget(self.reset_statistics_button)
        layout.addLayout(footer)
        return page

    @staticmethod
    def _statistics_column(
        title: str, unit: str, accent: str
    ) -> tuple[QFrame, dict[str, QLabel]]:
        panel = QFrame()
        panel.setObjectName("statisticsPanel")
        layout = QGridLayout(panel)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(7)
        heading = QLabel(title)
        heading.setObjectName("statisticsTitle")
        heading.setStyleSheet(f"color: {accent};")
        unit_label = QLabel(unit)
        unit_label.setObjectName("metricUnit")
        unit_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(heading, 0, 0)
        layout.addWidget(unit_label, 0, 1)

        values: dict[str, QLabel] = {}
        for row, key in enumerate(("AVG", "MIN", "MAX", "P-P", "Σ", "CV"), 1):
            name = QLabel(key)
            name.setObjectName("statisticsKey")
            value = QLabel("---")
            value.setObjectName("statisticsValue")
            value.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(name, row, 0)
            layout.addWidget(value, row, 1)
            values[key] = value
        return panel, values

    def _build_device_info_bar(self) -> QHBoxLayout:
        controls = QHBoxLayout()
        controls.addStretch()
        controls.addWidget(QLabel("DEVICE INFO"))
        self.device_info = QLabel("---")
        self.device_info.setObjectName("deviceInfo")
        controls.addWidget(self.device_info)
        return controls

    @staticmethod
    def _create_plot(
        title: str, quantity: str, unit: str, color: str
    ) -> tuple[pg.PlotWidget, pg.PlotDataItem]:
        plot = pg.PlotWidget()
        plot.setBackground("#101820")
        plot.setTitle(title, color="#e9f0f7", size="13pt")
        plot.setLabel("left", quantity, units=unit)
        plot.setLabel("bottom", "Time", units="s")
        plot.setXRange(-WINDOW_SECONDS, 0, padding=0)
        plot.showGrid(x=True, y=True, alpha=0.2)
        plot.getAxis("left").setTextPen("#c3ced8")
        plot.getAxis("bottom").setTextPen("#c3ced8")
        plot.getAxis("left").setStyle(tickFont=QFont("Segoe UI", 11))
        plot.getAxis("bottom").setStyle(tickFont=QFont("Segoe UI", 11))
        curve = plot.plot(pen=pg.mkPen(QColor(color), width=2.5))
        return plot, curve

    def _connect_signals(self) -> None:
        self.connect_button.clicked.connect(self._toggle_connection)
        self.scan_button.clicked.connect(self._scan_devices)
        self.reset_statistics_button.clicked.connect(
            self._confirm_reset_statistics
        )
        self.device_combo.currentIndexChanged.connect(self._device_selection_changed)
        self.ble.signals.status_changed.connect(self._show_status)
        self.ble.signals.connection_changed.connect(self._connection_changed)
        self.ble.signals.scan_changed.connect(self._scan_changed)
        self.ble.signals.devices_discovered.connect(self._devices_discovered)
        self.ble.signals.device_info_received.connect(self.device_info.setText)
        self.ble.signals.live_data_received.connect(self._live_data_received)
        self.ble.signals.statistics_received.connect(self._statistics_received)
        self.startup_scanner.signals.scan_changed.connect(
            self._startup_scan_changed
        )
        self.startup_scanner.signals.devices_discovered.connect(
            self._startup_devices_discovered
        )

    def _start_startup_connection(self) -> None:
        if not self.startup_scan_pending:
            return
        if not self.preferred_device_address:
            self._scan_devices()
            return

        self.startup_scan_pending = False
        self.startup_phase = "direct_1"
        self.startup_direct_attempts = 1
        self.startup_scan_complete = False
        self.startup_scan_devices = []
        # Keep collecting validated USB/BLE candidates while the remembered
        # device is tried immediately, without waiting for scan completion.
        self.startup_scanner.scan(self.transport_combo.currentText(), "")
        self._connect_device(
            DiscoveredDevice(
                self.preferred_device_name,
                self.preferred_device_address,
                0,
            ),
            locate_timeout=STARTUP_DIRECT_TIMEOUT_SECONDS,
        )

    def _startup_scan_changed(self, scanning: bool) -> None:
        if scanning:
            return
        self.startup_scan_complete = True
        if self.startup_phase == "fallback_wait":
            QTimer.singleShot(0, self._connect_startup_fallback)

    def _startup_devices_discovered(
        self, devices: list[DiscoveredDevice]
    ) -> None:
        self.startup_scan_devices = devices
        self._devices_discovered(devices)
        if self.startup_phase == "fallback_wait" and devices:
            QTimer.singleShot(0, self._connect_startup_fallback)

    def _scan_devices(self) -> None:
        if not self.connected and not self.ble.running:
            self.auto_connect_after_scan = self.startup_scan_pending
            self.startup_scan_pending = False
            preferred = self.preferred_device_address if self.auto_connect_after_scan else ""
            self.ble.scan(self.transport_combo.currentText(), preferred)

    def _scan_changed(self, scanning: bool) -> None:
        self.transport_combo.setEnabled(not scanning and not self.connected)
        self.scan_button.setEnabled(not scanning and not self.connected)
        self.device_combo.setEnabled(not scanning and not self.connected)
        if scanning:
            self.connect_button.setEnabled(False)
        elif self.auto_connect_device is not None and not self.connected:
            device = self.auto_connect_device
            self.auto_connect_device = None
            self._connect_device(device)

    def _devices_discovered(self, devices: list[DiscoveredDevice]) -> None:
        previous = self.device_combo.currentData()
        previous_address = (
            previous.address if isinstance(previous, DiscoveredDevice) else ""
        )
        self.device_combo.clear()
        selected_index = -1
        for index, device in enumerate(devices):
            self.device_combo.addItem(
                f"{device.name}   ({device.address[4:]})" if device.address.startswith("usb:")
                else f"{device.name}   ({device.rssi} dBm)", device
            )
            if device.address == previous_address:
                selected_index = index
        if selected_index >= 0:
            self.device_combo.setCurrentIndex(selected_index)
        elif devices:
            self.device_combo.setCurrentIndex(0)
        self.connect_button.setEnabled(
            self.connected or (bool(devices) and not self.ble.running)
        )
        self.auto_connect_device = None
        self.fallback_connect_device = None
        if self.auto_connect_after_scan and devices:
            preferred = next(
                (item for item in devices if item.address == self.preferred_device_address),
                None,
            )
            self.auto_connect_device = preferred or devices[0]
            if preferred is not None:
                self.fallback_connect_device = next(
                    (item for item in devices if item.address != preferred.address), None
                )
        self.auto_connect_after_scan = False

    def _device_selection_changed(self, _index: int) -> None:
        self.connect_button.setEnabled(
            self.connected
            or isinstance(self.device_combo.currentData(), DiscoveredDevice)
        )

    def _toggle_connection(self) -> None:
        if self.connected or self.ble.running:
            self.connect_button.setEnabled(False)
            self._show_status("DISCONNECTING", "Closing connection...")
            self.ble.disconnect()
            return

        selected = self.device_combo.currentData()
        if not isinstance(selected, DiscoveredDevice):
            self._show_status("READY", "Select an AeroMeter first")
            return
        self._connect_device(selected)

    def _connect_device(
        self, device: DiscoveredDevice, locate_timeout: float = 10.0
    ) -> None:
        self.connected_device_address = device.address
        self.connected_device_name = device.name
        for index in range(self.device_combo.count()):
            item = self.device_combo.itemData(index)
            if isinstance(item, DiscoveredDevice) and item.address == device.address:
                self.device_combo.setCurrentIndex(index)
                break
        self._reset_measurement_view()
        self.connect_button.setEnabled(False)
        self._show_status("CONNECTING", f"Connecting to {device.name}...")
        self.ble.connect(device.address, device.name, locate_timeout)

    def _reset_measurement_view(self) -> None:
        self.latest_live = None
        self.latest_statistics = None
        self.pressure_history.clear()
        self.flow_history.clear()
        self.pressure_curve.clear()
        self.flow_curve.clear()
        self.pressure_overrange_curve.clear()
        self.flow_overrange_curve.clear()
        self._reset_local_session()
        self.stable_pressure = None
        self.stable_flow = None
        self.capture_stable_on_next_statistics = False
        self.last_sample_time = None
        self.device_info.setText("---")
        self._update_all_labels()

    def _reset_local_session(self, clear_pretrigger=True) -> None:
        self.local_session_active = False
        self.session_started_at = None
        self.session_duration_s = 0.0
        self.session_volume_l = 0.0
        self.session_volume_incomplete = False
        self.session_pressure_min = None
        self.session_pressure_max = None
        self.session_flow_min = None
        self.session_flow_max = None
        self._volume_integrator.reset()
        if clear_pretrigger:
            self._pretrigger.clear()

    def _confirm_reset_statistics(self) -> None:
        response = QMessageBox.question(
            self,
            "Reset Statistics",
            "Clear desktop session statistics and saved stable results?\n\n"
            "This does not reset data stored on the AeroMeter device.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if response != QMessageBox.StandardButton.Yes:
            return

        self._reset_pc_statistics()

    def _reset_pc_statistics(self) -> None:
        self._reset_local_session()
        self.stable_pressure = None
        self.stable_flow = None
        self.capture_stable_on_next_statistics = False
        self._update_all_labels()

    def _connection_changed(self, connected: bool) -> None:
        self.transport_combo.setEnabled(not connected)
        self.connected = connected
        if connected:
            self.startup_phase = "complete"
            self.startup_scanner.disconnect()
            self.fallback_connect_device = None
            saved_name = self.connected_device_name or self.preferred_device_name
            self.preferred_device_address = self.connected_device_address
            self.preferred_device_name = saved_name
            self.settings.setValue(
                "lastDeviceAddress", self.connected_device_address
            )
            self.settings.setValue("lastDeviceName", saved_name)
            self.settings.sync()
            for index in range(self.device_combo.count()):
                item = self.device_combo.itemData(index)
                if (
                    isinstance(item, DiscoveredDevice)
                    and item.address == self.connected_device_address
                ):
                    self.device_combo.setCurrentIndex(index)
                    break
        self.connect_button.setText("Disconnect" if connected else "Connect")
        self.scan_button.setEnabled(not connected)
        self.device_combo.setEnabled(not connected)
        self.connect_button.setEnabled(
            connected
            or (
                isinstance(self.device_combo.currentData(), DiscoveredDevice)
                and not self.ble.running
                and self.startup_phase
                not in ("direct_1", "direct_2", "fallback_wait", "fallback_connect")
            )
        )
        if not connected:
            self.local_session_active = False
            self.status_dot.setStyleSheet("color: #7f8b96;")

    def _show_status(self, status: str, detail: str) -> None:
        self.status_label.setText(status)
        self.detail_label.setText(detail)
        colors = {
            "CONNECTED": "#69e6a6",
            "ERROR": "#ff6b7a",
            "PACKET ERROR": "#ffb454",
            "SCANNING": "#56c7ff",
            "CONNECTING": "#56c7ff",
            "READY": "#69e6a6",
        }
        self.status_dot.setStyleSheet(f"color: {colors.get(status, '#7f8b96')};")
        if status == "ERROR" and self.startup_phase in ("direct_1", "direct_2"):
            QTimer.singleShot(100, self._advance_startup_after_error)
        elif status == "ERROR" and self.fallback_connect_device is not None:
            QTimer.singleShot(100, self._connect_fallback_device)

    def _advance_startup_after_error(self) -> None:
        if self.connected:
            return
        if self.ble.running:
            QTimer.singleShot(100, self._advance_startup_after_error)
            return
        if self.startup_direct_attempts < 2:
            self.startup_direct_attempts += 1
            self.startup_phase = "direct_2"
            self._show_status(
                "CONNECTING", "Direct connection failed; retrying once..."
            )
            self._connect_device(
                DiscoveredDevice(
                    self.preferred_device_name,
                    self.preferred_device_address,
                    0,
                ),
                locate_timeout=STARTUP_DIRECT_TIMEOUT_SECONDS,
            )
            return

        self.startup_phase = "fallback_wait"
        self._show_status(
            "SCANNING", "Direct connection failed twice; selecting a scanned device..."
        )
        self._connect_startup_fallback()

    def _connect_startup_fallback(self) -> None:
        if self.connected or self.startup_phase != "fallback_wait":
            return
        if self.ble.running:
            QTimer.singleShot(100, self._connect_startup_fallback)
            return
        if self.startup_scan_devices:
            device = self.startup_scan_devices[0]
            self.startup_phase = "fallback_connect"
            self._connect_device(device)
            return
        if not self.startup_scan_complete:
            return
        self.startup_phase = "complete"
        self._show_status(
            "ERROR", "Direct connection failed twice and no AeroMeter was found"
        )

    def _connect_fallback_device(self) -> None:
        if self.connected or self.fallback_connect_device is None:
            return
        if self.ble.running:
            QTimer.singleShot(100, self._connect_fallback_device)
            return
        device = self.fallback_connect_device
        self.fallback_connect_device = None
        self._connect_device(device)

    def _live_data_received(self, data: LiveData) -> None:
        received_at = time.monotonic()
        dt = 0.0 if self.last_sample_time is None else received_at - self.last_sample_time
        self.last_sample_time = received_at
        previous_stability_state = (
            self.latest_live.stability_state if self.latest_live is not None else None
        )
        self.latest_live = data
        # Keep chart time moving for both channels. Infinity is only an overload
        # marker; it must never enter statistics or volume calculations.
        self.pressure_history.append((received_at, math.inf if data.pressure_overrange else data.pressure_kpa))
        self.flow_history.append((received_at, math.inf if data.flow_overrange else data.flow_l_min))
        self._trim_history(received_at)

        if data.stability_state == 2 and previous_stability_state != 2:
            self.capture_stable_on_next_statistics = True

        self._update_local_session(data, received_at, dt)
        self._update_all_labels()

    def _statistics_received(self, data: StatisticsData) -> None:
        self.latest_statistics = data
        if self.capture_stable_on_next_statistics:
            self.stable_pressure = data.pressure_mean_kpa
            self.stable_flow = data.flow_mean_l_min
            self.capture_stable_on_next_statistics = False
        self._update_all_labels()

    def _update_local_session(
        self, data: LiveData, received_at: float, dt: float
    ) -> None:
        invalid = data.pressure_overrange or data.flow_overrange
        increment = self._volume_integrator.add(data.flow_l_min, dt, invalid)
        gap = dt >= 1.0
        if gap:
            self._pretrigger.clear()
        if not self.local_session_active:
            if invalid:
                self._pretrigger.clear()
            else:
                self._pretrigger.append((received_at, increment))
                while self._pretrigger and self._pretrigger[0][0] < received_at - 0.2:
                    self._pretrigger.popleft()
        if data.session_active and not self.local_session_active:
            buffered = sum(amount for _, amount in self._pretrigger)
            self._reset_local_session(clear_pretrigger=False)
            self.session_volume_l = buffered
            self.session_started_at = received_at
            self._volume_integrator.add(data.flow_l_min, 0.0, invalid)
            self._pretrigger.clear()
        elif data.session_active and not invalid:
            self.session_volume_l += increment
        if data.session_active:
            self.session_volume_incomplete |= invalid or gap
            if self.session_started_at is not None:
                self.session_duration_s = max(0.0, received_at - self.session_started_at)
            if not data.pressure_overrange:
                self.session_pressure_min = self._minimum(self.session_pressure_min, data.pressure_kpa)
                self.session_pressure_max = self._maximum(self.session_pressure_max, data.pressure_kpa)
            if not data.flow_overrange:
                self.session_flow_min = self._minimum(self.session_flow_min, data.flow_l_min)
                self.session_flow_max = self._maximum(self.session_flow_max, data.flow_l_min)
        self.local_session_active = data.session_active

    @staticmethod
    def _minimum(current: float | None, value: float) -> float:
        return value if current is None else min(current, value)

    @staticmethod
    def _maximum(current: float | None, value: float) -> float:
        return value if current is None else max(current, value)

    def _update_all_labels(self) -> None:
        live = self.latest_live
        stats = self.latest_statistics
        pressure = live.pressure_kpa if live else None
        flow = live.flow_l_min if live else None

        self.overview_pressure.set_value(
            pressure,
            bool(live and live.pressure_overrange),
        )
        self.overview_flow.set_value(
            flow,
            bool(live and live.flow_overrange),
            flow=True,
        )
        self.overview_state.setText(live.stability_name if live else "---")
        state_colors = {
            "IDLE": "#7f8b96",
            "ACTIVE": "#ffb454",
            "STABLE": "#69e6a6",
        }
        state_name = live.stability_name if live else "---"
        self.overview_state.setStyleSheet(
            f"color: {state_colors.get(state_name, '#edf4fa')};"
        )
        self.overview_session.setText(
            "ACTIVE" if live and live.session_active else "INACTIVE" if live else "---"
        )
        self.overview_session.setStyleSheet(
            "color: #69e6a6;" if live and live.session_active else "color: #9aa8b4;"
        )

        if stats:
            self.overview_pressure.sigma_value.setText(
                display_value(stats.pressure_sigma_kpa)
            )
            self.overview_pressure.pp_value.setText(
                display_value(stats.pressure_peak_to_peak_kpa)
            )
            self.overview_flow.sigma_value.setText(display_value(stats.flow_sigma_l_min))
            self.overview_flow.pp_value.setText(
                display_value(stats.flow_peak_to_peak_l_min)
            )
        else:
            for label in (
                self.overview_pressure.sigma_value,
                self.overview_pressure.pp_value,
                self.overview_flow.sigma_value,
                self.overview_flow.pp_value,
            ):
                label.setText("---")

        pq = None
        if stats and stats.flow_mean_l_min > 1.0:
            pq = stats.pressure_mean_kpa / stats.flow_mean_l_min
        power = stats.pressure_mean_kpa * stats.flow_mean_l_min / 60.0 if stats else None
        self.overview_pq.set_value(pq, 2)
        self.overview_power.set_value(power, 2)

        pressure_values = [value for _, value in self.pressure_history if math.isfinite(value)]
        flow_values = [value for _, value in self.flow_history if math.isfinite(value)]
        self._set_history_cards(
            pressure_values,
            self.pressure_10s_avg,
            self.pressure_10s_min,
            self.pressure_10s_max,
        )
        self._set_history_cards(
            flow_values,
            self.flow_10s_avg,
            self.flow_10s_min,
            self.flow_10s_max,
        )

        pressure_avg = stats.pressure_mean_kpa if stats else None
        flow_avg = stats.flow_mean_l_min if stats else None
        pressure_sigma = stats.pressure_sigma_kpa if stats else None
        flow_sigma = stats.flow_sigma_l_min if stats else None
        pressure_pp = stats.pressure_peak_to_peak_kpa if stats else None
        flow_pp = stats.flow_peak_to_peak_l_min if stats else None
        pressure_cv = coefficient(pressure_sigma, pressure_avg, 0.30)
        flow_cv = coefficient(flow_sigma, flow_avg, 1.00)
        self._set_statistics_column(
            self.pressure_stat_values,
            pressure_avg,
            self.session_pressure_min,
            self.session_pressure_max,
            pressure_pp,
            pressure_sigma,
            pressure_cv,
        )
        self._set_statistics_column(
            self.flow_stat_values,
            flow_avg,
            self.session_flow_min,
            self.session_flow_max,
            flow_pp,
            flow_sigma,
            flow_cv,
        )

        stable_pq = (
            self.stable_pressure / self.stable_flow
            if self.stable_pressure is not None
            and self.stable_flow is not None
            and self.stable_flow > 1.0
            else None
        )
        self.stable_pressure_card.set_value(self.stable_pressure)
        self.stable_flow_card.set_value(self.stable_flow)
        self.stable_pq_card.set_value(stable_pq, 3)
        self.session_volume_card.set_value(self.session_volume_l, 2)
        if self.session_volume_incomplete:
            self.session_volume_card.value_label.setText(
                f"{display_value(self.session_volume_l, 2)} !"
            )
            self.session_volume_card.value_label.setStyleSheet("color: #ff5c68;")
        else:
            self.session_volume_card.value_label.setStyleSheet("color: #e9f0f7;")
        self.session_duration_card.value_label.setText(
            display_duration(self.session_duration_s)
        )

    @staticmethod
    def _set_history_cards(
        values: list[float], avg: MetricCard, minimum: MetricCard, maximum: MetricCard
    ) -> None:
        if not values:
            avg.set_value(None)
            minimum.set_value(None)
            maximum.set_value(None)
            return
        avg.set_value(sum(values) / len(values))
        minimum.set_value(min(values))
        maximum.set_value(max(values))

    @staticmethod
    def _set_statistics_column(
        labels: dict[str, QLabel],
        average: float | None,
        minimum: float | None,
        maximum: float | None,
        peak_to_peak: float | None,
        sigma: float | None,
        cv: float | None,
    ) -> None:
        labels["AVG"].setText(display_value(average))
        labels["MIN"].setText(display_value(minimum))
        labels["MAX"].setText(display_value(maximum))
        labels["P-P"].setText(display_value(peak_to_peak))
        labels["Σ"].setText(display_value(sigma))
        labels["CV"].setText(
            f"{display_value(cv, 1)} %" if cv is not None else "---"
        )

    def _trim_history(self, newest_time: float) -> None:
        cutoff = newest_time - WINDOW_SECONDS
        for history in (self.pressure_history, self.flow_history):
            while history and history[0][0] < cutoff:
                history.popleft()

    def _refresh_dynamic_display(self) -> None:
        self._refresh_curve(self.pressure_curve, self.pressure_history, self.pressure_overrange_curve, 10.0)
        self._refresh_curve(self.flow_curve, self.flow_history, self.flow_overrange_curve, 50.0)
        self._update_chart_axis(
            self.pressure_plot,
            self.pressure_history,
            step=2.0,
            maximum=10.0,
        )
        self._update_chart_axis(
            self.flow_plot,
            self.flow_history,
            step=10.0,
            maximum=50.0,
        )
        if self.local_session_active and self.session_started_at is not None:
            self.session_duration_s = time.monotonic() - self.session_started_at
            self.session_duration_card.value_label.setText(
                display_duration(self.session_duration_s)
            )

    @staticmethod
    def _update_chart_axis(
        plot: pg.PlotWidget,
        history: deque[tuple[float, float]],
        step: float,
        maximum: float,
    ) -> None:
        peak = max((maximum if math.isinf(value) else value
                    for _, value in history if not math.isnan(value)), default=0.0)
        axis_max = max(step, math.ceil(peak / step) * step)
        axis_max = min(axis_max, maximum)
        plot.setYRange(0.0, axis_max, padding=0.0)

    @staticmethod
    def _refresh_curve(
        curve: pg.PlotDataItem, history: deque[tuple[float, float]],
        overrange_curve: pg.PlotDataItem, maximum: float,
    ) -> None:
        if not history:
            curve.clear()
            overrange_curve.clear()
            return
        latest = history[-1][0]
        timestamps = [timestamp - latest for timestamp, _ in history]
        curve.setData(
            timestamps,
            [value if math.isfinite(value) else math.nan for _, value in history],
            connect="finite",
        )
        if any(math.isinf(value) for _, value in history):
            overrange_curve.setData(
                timestamps,
                [maximum if math.isinf(value) else math.nan for _, value in history],
                connect="finite",
            )
        else:
            overrange_curve.clear()

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API name
        if (
            not self.connected
            and not self.ble.running
            and not self.startup_scanner.running
        ):
            event.accept()
            return

        if not self.closing:
            self.closing = True
            self.close_deadline = time.monotonic() + 2.0
            self._show_status("DISCONNECTING", "Closing device connection...")
            self.ble.disconnect()
            self.startup_scanner.disconnect()

        if time.monotonic() < self.close_deadline:
            event.ignore()
            QTimer.singleShot(100, self.close)
            return
        event.accept()


STYLE_SHEET = """
QWidget {
    background: #090e13;
    color: #edf4fa;
    font-family: "Segoe UI";
    font-size: 14px;
}
QLabel#productName { font-size: 26px; font-weight: 700; }
QLabel#statusDot { font-size: 20px; color: #7f8b96; }
QLabel#statusLabel { font-size: 14px; font-weight: 700; }
QLabel#detailLabel, QLabel#footnote, QLabel#deviceInfo { color: #94a3af; }
QLabel#deviceInfo { font-family: Consolas; }
QTabWidget::pane { border: 1px solid #26343f; border-radius: 8px; }
QTabBar::tab {
    background: #111820;
    color: #9baab6;
    border: 1px solid #26343f;
    padding: 11px 24px;
    min-width: 120px;
    font-weight: 700;
}
QTabBar::tab:selected { background: #176b8d; color: #ffffff; }
QFrame#heroPanel, QFrame#metricCard, QFrame#statisticsPanel {
    background: #111820;
    border: 1px solid #283844;
    border-radius: 9px;
}
QLabel#heroTitle, QLabel#pageTitle, QLabel#statisticsTitle {
    font-size: 20px;
    font-weight: 700;
}
QLabel#realtimeValue {
    font-size: 82px;
    font-weight: 700;
}
QLabel#heroUnit, QLabel#trendUnit { color: #a8b5c0; font-size: 17px; }
QLabel#inlineMetricTitle, QLabel#metricTitle, QLabel#statisticsKey {
    color: #92a2af;
    font-size: 14px;
    font-weight: 700;
}
QLabel#inlineMetricValue { font-size: 22px; font-weight: 700; }
QLabel#metricValue { font-size: 27px; font-weight: 700; }
QLabel#heroValue { font-size: 34px; font-weight: 700; }
QLabel#metricUnit { color: #91a0ad; font-size: 13px; }
QLabel#trendValue { color: #ffffff; font-size: 32px; font-weight: 700; }
QLabel#statisticsValue { font-size: 21px; font-weight: 700; }
QLabel#sectionTitle { color: #92a2af; font-size: 14px; font-weight: 700; }
QLabel#stateBadge, QLabel#sessionBadge {
    background: #16232d;
    border: 1px solid #304554;
    border-radius: 5px;
    padding: 6px 14px;
    font-size: 17px;
    font-weight: 700;
}
QPushButton {
    background: #18232d;
    border: 1px solid #30404e;
    border-radius: 6px;
    padding: 8px 14px;
}
QPushButton:hover { background: #21313e; }
QPushButton:pressed { background: #2a3d4c; }
QPushButton:checked { background: #176b8d; border-color: #56c7ff; }
QPushButton:disabled { color: #596671; background: #111820; }
QPushButton#primaryButton { background: #176b8d; border-color: #56c7ff; }
QPushButton#dangerButton { background: #4a2027; border-color: #c75b69; }
QPushButton#dangerButton:hover { background: #642a34; }
QComboBox {
    background: #111820;
    border: 1px solid #30404e;
    border-radius: 6px;
    padding: 7px 10px;
}
QComboBox:disabled { color: #596671; }
"""


def packaged_self_test() -> int:
    """Exercise packaged Qt and the canonical decoder without device access."""
    import struct

    sample = decode_live_packet(
        struct.pack("<BBHIHHBB", 1, 1, 1, 1000, 123, 234, 1, 0)
    )
    if sample.pressure_kpa != 1.23 or sample.flow_l_min != 2.34:
        raise RuntimeError("Protocol 1 packaged self-test failed")
    owns_application = QApplication.instance() is None
    application = QApplication.instance() or QApplication(["AeroMeter self-test"])
    label = QLabel(display_flow_value(sample.flow_l_min))
    if label.text() != "2.34":
        raise RuntimeError("Qt packaged self-test failed")
    application.processEvents()
    label.deleteLater()
    if owns_application:
        application.quit()
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return packaged_self_test()
    pg.setConfigOptions(antialias=True)
    app = QApplication(sys.argv)
    app.setApplicationName("Galeon AeroMeter")
    app.setStyleSheet(STYLE_SHEET)
    window = AeroMeterWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
