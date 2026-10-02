# Galeon AeroMeter User Manual V1

**Applicable firmware: 1.2.1 development candidate (hardware acceptance pending)**
**Companion desktop application: Windows 1.2.1 stable (build 11)**
**Last updated: 2026-10-03**

> This manual covers the candidate firmware with pressure-only startup zeroing; flow zeroing remains disabled. The main interface has six pages.

This manual is for end users and includes public integration information for third-party developers. Desktop and firmware versions are managed separately: updating the desktop application does not update the device firmware. The supplier must complete startup, measurement, USB/BLE and update acceptance checks on the shipping hardware. Candidate firmware status does not mean hardware acceptance has passed.

First-use checklist: dry gas path and pressure port open to atmosphere → power on without blowing → confirm no red errors → connect tubing in the marked direction → increase flow gradually and reduce input immediately on `OVER`. Complete these checks before PC measurement too.

## 1. Intended Use

AeroMeter is a portable pressure and gas-flow meter designed primarily for measuring playing pressure and air consumption in wind instruments, reeds, air bags, and related pneumatic systems.

Main measurement specifications:

| Measurement | Range | Sensor accuracy |
|---|---:|---:|
| Pressure | 0–10 kPa | ±0.25% FS (full scale), equivalent to approximately ±0.025 kPa or ±25 Pa |
| Flow | 0–50 L/min | ±1.5% |

The device is operated through a touchscreen. An approximately 10 cm straight tube is already installed in the flow path; the user does not need to add another straight tube.

The accuracy values are manufacturer specifications for the individual sensors, not a calibration certificate for the assembled instrument or a guarantee under all temperatures, humidities, gases and tubing configurations. The definition and conditions of the flow sensor's ±1.5% specification must follow the supplied manufacturer's documentation/report; do not assume it is a percentage of full scale or of reading. Two displayed decimals aid observation but do not guarantee accuracy of the last digit. Volume, P/Q and Power are calculated quantities without a separately guaranteed instrument accuracy.

The device is intended for musical-instrument and general airflow observation, not medical diagnosis, ventilator control, life support, pressure safety protection or trade billing. Do not connect unverified gases, corrosive gases or flammable gases.

The displayed unit is L/min. Follow the supplied documentation for calibration gas, standard/reference temperature and pressure, and flow definition. Software does not automatically compensate for arbitrary gas mixtures or environmental temperature/pressure; accumulated volume is not automatically actual volume under arbitrary conditions.

## 2. Startup and Environment Checks

### 2.1 Conditions Before Power-On

Startup checks both sensors and applies zero-offset compensation to pressure only. The average of 32 pressure readings becomes the offset for this startup and is subtracted from subsequent pressure readings. For example, a startup offset of 0.03 kPa is subtracted from later pressure readings. Flow is not zeroed and no startup flow offset is subtracted; it is checked only for an airflow notice.

Factory conversions remain unchanged. The pressure offset is held only for the current power-on session and is recalculated at the next startup. It does not change the sensor or calibration report, or improve the specified accuracy.

- Keep the pressure port unloaded and open to atmospheric pressure. Do not start with pressure applied.
- Place the device on a stable surface, away from direct airflow from fans or air-conditioning outlets.
- Do not blow or squeeze the tubing during startup. This could incorrectly subtract real applied pressure or trigger a pressure-zero error or airflow notice.
- There is no need to block either port for flow zeroing. Do not seal the flow path and trap residual pressure.
- Keep the ports and internal flow path dry and free of obstructions.

### 2.2 Startup Progress Screen

The startup screen shows Galeon AeroMeter, the firmware version, and progress. `PRESSURE ZERO / FLOW ZERO OFF` indicates that pressure zeroing is enabled and flow zeroing is disabled.

| Display | Meaning |
|---|---|
| `CHECKING SENSORS` | Check that both sensors are connected and responding |
| `PRESSURE ZERO` | Sample and compensate the pressure zero while checking the flow magnitude |
| `READY` / 100% | Checks are complete; the first page opens |

Pressure zeroing and the airflow check share the same 32 samples. The sampling intervals total approximately 0.32 seconds, plus communication, screen updates, and other startup operations. There is no additional flow-zeroing phase.

### 2.3 Airflow Notice and Sensor Errors

After pressure zeroing succeeds, the airflow notice works as follows:

- Short-term average flow magnitude below `0.50 L/min`: the main interface opens automatically.
- At or above `0.50 L/min`: the screen shows `POSSIBLE AIRFLOW`, `AVG |FLOW|` (the average flow magnitude from this check, in L/min), and `TAP TO CONTINUE`. Check the environment and flow path, then tap once to continue. No repeated passing test is required.
- This is a notice, not a calibration failure or proof of wind or a faulty sensor. Actual airflow, zero-point bias, or other factors may trigger it.
- A missing sensor, failed read, or flow-data checksum error produces a red `SENSOR WARNING` with the specific reason. For normal measurement, check power and connections and restart. If access is needed only for serial-number provisioning or maintenance, hold the screen continuously for 3 seconds to bypass the warning.
- After bypassing, all six pages remain available. The pressure or flow page shows a red warning for the unavailable sensor. If the pressure sensor is connected but another sensor failure interrupted startup before pressure zeroing, the pressure page shows `PRESSURE ZERO NOT APPLIED`. This is a maintenance-only state, not a valid measurement or a passed product startup. Reconnect the sensors and restart before measurement.

The pressure-zero average must be within ±0.25 kPa and no positive pressure overrange may occur during sampling. Otherwise, `PRESSURE ZERO FAILED` shows the average and limit and cannot be skipped. Remove applied pressure, let the flow path equalize with the atmosphere, and restart. The ±0.25 kPa limit protects against incorrect zeroing; it is not the sensor accuracy specification.

Ordinary touch controls are paused during automatic checks and pressure zeroing. A single tap acknowledges the airflow notice; a continuous 3-second hold bypasses a sensor warning for maintenance access. Normal touch controls resume in the main interface. `PRESSURE ZERO FAILED` remains non-bypassable.

Flow is not zeroed, so small positive flow readings may remain at rest. Pressure may still have some noise or drift after compensation. Negative compensated pressure and negative flow readings are displayed as `0.00`; this lower-limit treatment does not improve sensor accuracy.

## 3. Basic Operation

- Swipe up or down to change pages.
- The dots on the right indicate the current page.
- The page indicators appear after an operation and hide automatically after approximately three seconds of inactivity.
- Double-tap the fourth page, `STATISTICS`, to open the data-clear confirmation dialog.
- Touching the screen restores normal backlight brightness.
- On the first three pages, the backlight dims to approximately 10% after the device remains `IDLE` for about five seconds.
- Pages four, five, and six remain at normal brightness.

Page order:

1. Overview
2. Pressure graph
3. Flow graph
4. Statistics
5. Bluetooth
6. Device information

## 4. Page 1: Measurement Overview

The first page shows real-time pressure, flow, short-term variation, stability status, and derived pneumatic values.

### 4.1 PRESSURE

The real-time pressure after this startup's zero-offset compensation and filtering, in `kPa`.

- The main display uses two decimal places, for example `1.82 kPa`.
- The pressure sensor range is 0–10 kPa.
- Pressure-sensor accuracy is ±0.25% FS. For a 10 kPa full-scale range, this corresponds to approximately ±25 Pa or ±0.025 kPa.
- Negative readings are displayed as `0.00 kPa`.
- A positive full-scale reading is shown as a red `OVER` warning. Negative readings are treated as zero, not `OVER`.

### 4.2 FLOW

The filtered real-time gas flow in `L/min`.

- The main display uses two decimal places.
- Negative readings and residual readings below `0.10 L/min` are displayed as zero.
- Flow-sensor accuracy is ±1.5%, and the measurement range is 0–50 L/min. A reading at the upper limit is shown as a red `OVER` warning.

### 4.3 Σ

`Σ` is the standard deviation of data collected during the most recent one-second window. It indicates short-term pressure or flow variation.

- A smaller value indicates steadier output.
- Pressure Σ is expressed in kPa.
- Flow Σ is expressed in L/min.

### 4.4 P-P

`P-P` is the peak-to-peak value during the most recent one-second window:

`P-P = Maximum − Minimum`

It represents the total range of variation during that one-second period. A smaller P-P value indicates steadier measurement.

### 4.5 Status Indicator

| Status | Color | Meaning |
|---|---|---|
| `IDLE` | Gray | Pressure is below 0.30 kPa and flow is below 1.0 L/min |
| `ACTIVE` | Orange | Pressure or flow is present, but the stability conditions have not yet been met |
| `STABLE` | Green | Both pressure and flow meet the stability conditions |

To enter `STABLE`, all of the following conditions must be met:

- A complete one-second sample window is available.
- Average pressure is greater than 0.30 kPa.
- Average flow is greater than 1.0 L/min.
- Pressure coefficient of variation is no greater than 1.5%.
- Flow coefficient of variation is no greater than 2.0%.
- These conditions remain satisfied continuously for approximately 0.8 seconds.

After stability is reached, the device exits `STABLE` if the pressure coefficient of variation exceeds 2.5% or the flow coefficient of variation exceeds 3.0% continuously for approximately 0.3 seconds.

### 4.6 P/Q

`P/Q` is the ratio of pressure to flow:

`P/Q = Pressure (kPa) ÷ Flow (L/min)`

It can be used to compare the effective pneumatic resistance of an airway, instrument, or reed system. A larger value means that more pressure is required for each unit of flow.

When the average flow during the most recent one-second window is no greater than 1.0 L/min, P/Q is shown as `---` to prevent an unreliable ratio near zero flow.

### 4.7 Power

`Power` is an estimate of pneumatic power:

`Power (W) = Pressure (kPa) × Flow (L/min) ÷ 60`

It represents the pneumatic power corresponding to the current pressure and flow. It is not the instrument's acoustic power or acoustic efficiency.

## 5. Page 2: Pressure Graph

The second page shows pressure changes during the most recent ten seconds.

| Parameter | Meaning |
|---|---|
| Value at the top | Current filtered pressure in kPa |
| Graph | Pressure history for the most recent ten seconds; the right edge is the current time |
| `AVG` | Average pressure within the most recent ten-second window |
| `MIN` | Minimum pressure within the most recent ten-second window |
| `MAX` | Maximum pressure within the most recent ten-second window |
| `-10 s / -5 s / 0 s` | Time positions on the graph |

The graph updates at 20 Hz. Its vertical scale automatically selects an upper limit of approximately 2, 4, 6, 8, or 10 kPa so that changes remain easy to see at different pressure levels.

## 6. Page 3: Flow Graph

The third page shows flow changes during the most recent ten seconds.

| Parameter | Meaning |
|---|---|
| Value at the top | Current filtered flow in L/min |
| Graph | Flow history for the most recent ten seconds; the right edge is the current time |
| `AVG` | Average flow within the most recent ten-second window |
| `MIN` | Minimum flow within the most recent ten-second window |
| `MAX` | Maximum flow within the most recent ten-second window |
| `-10 s / -5 s / 0 s` | Time positions on the graph |

The graph updates at 20 Hz. Its vertical scale automatically selects an upper limit of approximately 10, 20, 30, 40, or 50 L/min.

## 7. Page 4: Statistics

The statistics page contains separate columns for pressure and flow. Pressure is expressed in kPa and flow in L/min.

### 7.1 Statistics Rows

| Parameter | Time range | Meaning |
|---|---|---|
| `AVG` | Most recent 1 second | Average value |
| `MIN` | Current measurement session | Minimum value during the session |
| `MAX` | Current measurement session | Maximum value during the session |
| `P-P` | Most recent 1 second | Maximum minus minimum |
| `Σ` | Most recent 1 second | Standard deviation |
| `CV` | Most recent 1 second | Coefficient of variation: `Σ ÷ |Average| × 100%` |

CV is a dimensionless indicator of relative stability. A smaller CV means less variation relative to the average value.

Pressure CV is displayed only when a complete one-second data window is available and the average pressure has reached `0.30 kPa`; flow CV is displayed only when a complete one-second data window is available and the average flow has reached `1.00 L/min`. Below the corresponding threshold, it is shown as `---`. Near zero pressure or at low flow, small zero-point noise would otherwise be magnified by the near-zero average in the CV formula, making the result statistically meaningless.

### 7.2 Stable P, Stable Q, and P/Q

When the device enters `STABLE`, it stores one set of stable measurement results:

- `Stable P`: Average pressure during the most recent one-second window when stability was reached.
- `Stable Q`: Average flow during the most recent one-second window when stability was reached.
- `P/Q`: Ratio of the corresponding stable pressure to stable flow.

Until a stable result has been obtained, these fields show `---`.

### 7.3 Volume

`Volume` is the accumulated gas volume during the current measurement session, expressed in liters:

`Accumulated volume = Flow integrated over time`

Volume accumulation uses faster-response flow data and trapezoidal integration. It also includes up to approximately 0.2 seconds of valid flow immediately before the session is confirmed, reducing missed volume when flow changes quickly. Only flow above 0.5 L/min is accumulated, preventing long-term accumulation of zero-point noise.

If pressure or flow exceeds its range during a session, the `Volume` value turns red and is followed by `!`. This means that flow during the out-of-range period could not be accumulated accurately and the displayed result is incomplete. Do not use it as a complete accumulated-volume result.

### 7.4 Duration

`Duration` is the length of the current or most recent measurement session, displayed as:

`Hours:Minutes:Seconds`

### 7.5 Automatic Session Start and End

A measurement session starts automatically when:

- Pressure exceeds 0.20 kPa or flow exceeds 0.5 L/min.
- The condition continues for approximately 0.1 seconds.

A measurement session ends automatically when:

- Pressure is below 0.20 kPa and flow is below 0.5 L/min.
- Both conditions continue for approximately two seconds.

### 7.6 Clearing Statistics

Quickly double-tap the `STATISTICS` page to display the confirmation dialog:

- `Yes`: Clear the session data and stored stable result.
- `No`: Keep the data and close the dialog.

## 8. Page 5: Bluetooth

The Bluetooth page displays the connection state and controls real-time data transmission.

### 8.1 STATUS

| Status | Meaning |
|---|---|
| `STARTING` | Bluetooth is starting |
| `ADVERTISING` | The device is advertising and waiting for a client connection |
| `CONNECTED` | A Bluetooth client is connected |
| `UNAVAILABLE` | Bluetooth initialization failed or Bluetooth is unavailable |

### 8.2 DEVICE

The Bluetooth device name is displayed in a format similar to:

`AeroMeter-AM1-12AB34`

The final six characters are derived from the device hardware identifier and distinguish multiple AeroMeter units.

### 8.3 STREAM

Controls real-time data notifications:

- On: Sends real-time measurements to the connected client.
- Off: Maintains the Bluetooth connection but pauses real-time notifications.

STREAM is enabled by default.

### 8.4 RATE

Selects the real-time data transmission rate:

- `5 Hz`: Lower data volume.
- `10 Hz`: Moderate data rate.
- `20 Hz`: Default setting, with higher time resolution.

Bluetooth data includes filtered pressure and flow, the one-second average, standard deviation and peak-to-peak values, stability status, and session status. The client must support the current AeroMeter BLE protocol.

## 9. Page 6: Device Information

`DEVICE INFORMATION` shows the device identity and software version:

| Field | Meaning |
|---|---|
| SN | Factory serial number for service and calibration records; `UNREGISTERED` if not assigned |
| HW | Hardware revision; `UNSET` if not recorded |
| UID | Unique chip identifier for checking factory records |
| FW | Running firmware version |
| BUILD | Firmware build identifier |
| CAL | Defaults to `FACTORY (SENSORS)`: both sensors were factory calibrated by their respective manufacturers. A subsequent recorded calibration report is shown by its date. This is not proof of calibration of the assembled device. `RECORD ERROR` indicates a record-reading error. CAL shows only the calibration source/report, not the current pressure offset. Flow has no startup offset |
| SLOT | Running firmware slot and update-layout status |

When requested by the registration or update tool, hold this page without moving for about two seconds. This allows a write operation to start within the next two minutes. No authorization is required just to view information. During an update, `FIRMWARE UPDATE` is displayed and measurement is paused. Do not unplug the device or interrupt power. Resume measurement after the device restarts, completes its connection checks, and any airflow notice has been acknowledged.

The PC application can connect through a USB data cable or Bluetooth. `Auto` searches USB and BLE concurrently, listing USB first. A remembered device is attempted directly, retried once on failure, and then scan fallback is used. Click `Refresh` after changing the connection mode. Older firmware may support Bluetooth only. Disconnect the PC measurement application and mobile apps before using the update tool.

## 10. Data Processing

### 10.1 Update Rates

- Sensor sampling: 100 Hz.
- Main interface update: 10 Hz.
- Graph update: 20 Hz.
- Graph history: 10 seconds.

### 10.2 Filtering

Displayed and statistical pressure and flow values use a two-stage filter:

1. A three-point median filter suppresses isolated spikes.
2. An exponential moving average with a coefficient of 0.10 smooths the displayed and statistical data.

Accumulated volume uses the same isolated-spike suppression but a faster smoothing setting, reducing integration error when flow changes quickly. Filtering reduces noise but introduces a small response delay.

### 10.3 Out-of-Range Handling

- A pressure reading at the 10 kPa upper limit is shown as a red `OVER` warning.
- A flow reading at the 50 L/min upper limit is shown as a red `OVER` warning.
- Negative pressure and flow are displayed as zero, not as `OVER`; this does not make the device a negative-pressure or reverse-flow meter.
- Charts keep scrolling during overload, with a red line at the full-scale limit (10 kPa or 50 L/min). This is a warning marker, not a measured value. Invalid readings do not enter filtering, statistics, or accumulated volume; the other valid channel continues updating. Missing sensor reads produce gaps, not red overload markers. If a measurement session is active, accumulated volume is marked as incomplete with a red `!`.
- Normal white values and data processing resume automatically when the reading returns to the valid range.

`OVER` means that the current value is outside the guaranteed measurement range. Any converted value obtained while the warning is active must not be treated as a valid measurement.

If there are no valid samples in the last 10 seconds, the chart's AVG/MIN/MAX fields show `---`, not zero.

## 11. Recommended Measurement Procedure

1. Check that the built-in approximately 10 cm straight tube, connectors, and airflow path are intact and unobstructed. No additional straight tube is required.
2. Make sure the sensors and airflow path are dry and free of foreign matter.
3. Power on the device with no pressure or flow applied.
4. Wait for the startup checks to finish. If an airflow notice appears, check the environment and tap once to continue. If a sensor warning appears, correct the connection and restart; do not measure in the bypassed maintenance state.
5. Connect the instrument, mouthpiece, or pneumatic system in the correct flow direction.
6. Increase pressure and flow gradually to avoid suddenly exceeding the measurement range.
7. Observe the real-time values and stability status on the first page.
8. Use the second and third pages when dynamic analysis is required.
9. After stability is reached, read Stable P, Stable Q, and P/Q on the fourth page.
10. To begin a new measurement, double-tap the statistics page and select `Yes` to clear the previous result.

## 12. Safety and Use Notes

- The device uses a unidirectional flow sensor. Flow in the wrong direction may continuously display zero.
- Do not allow saliva, water droplets, oil mist, or dust to enter the flow sensor.
- A replaceable dry filter or saliva barrier is recommended where appropriate.
- Do not blow forcefully into the device simply to test the full range. Direct exhalation can easily exceed 50 L/min.
- The `OVER` warning is a protective indication and does not by itself mean that the sensor is damaged.
- Keep pressure unloaded and do not blow during startup pressure zeroing.
- Sealing both the inlet and outlet can produce pressure changes due to temperature, hand pressure, or tubing deformation.
- Two pressure decimal places do not mean accuracy to 0.01 kPa. For a 10 kPa sensor with ±0.25% FS accuracy, the theoretical error is approximately ±0.025 kPa.

### 12.1 Exhaled Air, Moisture and Contamination

Use clean, dry gas without condensation. Exhaled air is warm and humid and may contain saliva; even brief blowing cannot be assumed condensation-free. Do not place your mouth directly against a device port. Use a separate mouthpiece, tubing and a suitably sized saliva barrier/water trap. Evaluate filtering and drying for the application; ordinary filter cotton is not a dehumidifier. Particle filters do not remove water vapor, and water traps do not guarantee removal of all moisture.

Filters, tubing and traps add resistance and alter response, potentially changing the instrument's working conditions. Keep the test configuration consistent and check for moisture, blockages and leaks. Do not restrict the outlet with a small filter and blow forcefully. Each user should have a separate external mouthpiece or one cleaned according to the supplier's instructions; do not share parts that contact the mouth.

If droplets, condensation, persistent abnormal offset or changed response appear, stop the gas supply and power off immediately. Do not blow through the device to dry it, or flush internal sensors with compressed air, heat, alcohol or solvents. Contact the supplier. This manual makes no claim of a waterproof rating or washability. Disconnect power before cleaning the exterior and keep liquids out of gas and USB ports.

### 12.2 Tubing, Environment and Power

Follow the marked flow direction. Avoid kinked, blocked, loose tubing and sealing both ports; secure connections and increase flow gradually. `OVER` is not a pressure-relief mechanism and cannot guarantee protection from overpressure. Reduce input immediately. Do not connect an unregulated compressed-air source.

Avoid direct sunlight, high heat, abrupt temperature changes, condensation, vibration and direct fan airflow. Allow the device to settle in the measurement environment before starting. This manual does not provide an assembled-instrument-validated temperature/humidity range; ask the supplier before use in special environments. After persistent drift, a drop, liquid ingress or a flow-path change, arrange inspection/calibration instead of using startup zeroing to hide a fault.

Use power matching the device's rated requirements and an undamaged USB data cable. Power off before connecting external sensors; numbers appearing after hot-plugging are not proof of valid measurement. During firmware updates, do not remove power, unplug cables or close the update tool. Do not let measurement and flashing tools occupy USB simultaneously. Store powered off with dry, clean, protected gas ports.

## 13. Windows Desktop Application 1.2.1

### 13.1 Installation and Connection

Download the official Windows x64 ZIP, verify it against SHA256SUMS.txt from the same release, extract the entire folder and run `AeroMeter.exe`. Do not copy the EXE alone or delete its dependencies. The application is currently unsigned and Windows may warn of an unknown publisher. A checksum and a single antivirus scan do not replace a digital signature or guarantee no false positives. Do not disable system security; contact the supplier if the source or checksum is suspicious.

First confirm normal device startup with no red sensor warnings. USB needs a data cable, not a charge-only cable; BLE needs an enabled, functioning Bluetooth Low Energy adapter. Select `Auto`, `USB` or `BLE`, use `Refresh`, select the device and click `Connect`. A remembered device may be connected directly. Auto discovery runs USB and BLE searches concurrently with USB entries listed first; a remembered-device attempt is retried once before scan fallback. Do not connect a phone or another application to the same device simultaneously. `Disconnect` releases the connection; normal application exit also disconnects.

### 13.2 Pages and Controls

- `LIVE VIEW`: real-time pressure/flow, 10-second charts, AVG/MIN/MAX, Σ, P-P, state, P/Q and Power, using the device's units.
- `STATISTICS`: recent AVG/P-P/Σ/CV, session MIN/MAX, stable readings, volume and duration. CV is `---` at low pressure/flow; this is not a fault.
- `RESET STATISTICS`: requires confirmation and clears computer-side statistics only; it does not clear device-side statistics or change calibration/firmware.
- The PC UI has no BLE STREAM/LIVE RATE settings, no CSV export, and is not a firmware flashing or serial-number management tool.

### 13.3 Relationship to Device Readings and Limitations

Live and 1-second statistical readings are sent by the device using Protocol 1, with pressure and flow encoded to two decimals. Computer-side 10-second history, session extrema and volume are based on received data and need not match the device at every instant. Wireless rate, delay, missing packets and connection start time affect results.

Device volume uses faster-smoothed data in its 100 Hz sampling chain. PC volume integrates received 5/10/20 Hz live flow using computer timing. Differences can grow with rapidly changing flow; the sensor's ±1.5% specification is not a guaranteed accuracy for PC volume. Treat volume after overload or significant communication interruption as incomplete. A red `!` result is not a complete volume measurement.

**Important: Protocol 1 has no sensor-missing or pressure-zero-incomplete validity flag. The PC may display zero or a previous reading; displayed numbers do not prove sensor health. Check the device's startup and red warnings before measuring. Stop testing after sensor errors, sensor insertion/removal or abnormal readings; resolve the problem, restart the device and begin a new measurement.**

## 14. Third-Party Development Interface

Public Protocol 1 supports custom clients, analysis and educational integration. USB and BLE share the same measurement packet layouts. Public scope covers device identification, live/statistics reading and stream control; firmware updates, calibration, signing, production and serial provisioning are excluded. Do not guess undocumented commands.

| Item | Description |
|---|---|
| BLE service | `8d530001-6c90-4a36-9c5f-5a07d0a11000` |
| BLE characteristics | UUID prefix 8d530002: information Read; 8d530003: live Notify; 8d530004: statistics Notify; 8d530005: stream control Write; all share the service UUID suffix |
| Live packet | 14 bytes, little-endian; version/type, sequence, uptime ms, pressure, flow, state and flags |
| Statistics packet | 20 bytes, little-endian; 1-second pressure/flow means, Σ and P-P |
| Scaling | Divide integers by 100 for kPa and L/min; encoding granularity does not imply accuracy |
| Flags | 0x02 pressure overload, 0x04 flow overload; 0x01 means session active, not sensor healthy |
| USB | Candidate VID/PID 303A/1001; 115200, DTR/RTS off; JSON lines prefixed `@AM1 `, terminated by LF; verify product with info |
| Public USB requests | info, stream, ping; ping every 1.5 seconds is recommended |
| Rates | USB live 20 Hz; BLE live 5/10/20 Hz; statistics 1 Hz; these are not the internal 100 Hz sampling rate |

Full offsets, UUIDs, commands, examples, error handling and compatibility rules are in the [English integration guide](https://github.com/andyxuhang/AeroMeter-Desktop/blob/main/protocol/AEROMETER_PROTOCOL_1_EN.md) and [Chinese guide](https://github.com/andyxuhang/AeroMeter-Desktop/blob/main/protocol/AEROMETER_PROTOCOL_1.md), also included in the release ZIP. Reference code is in `protocol/shared_protocol/python/galeon_protocol` in the public repository. See the repository LICENSE and third-party notices.

Validate length, version and type; honor overload flags; handle counter rollover, missing packets, reconnection and no-data timeouts. Negative/non-finite readings may encode as zero; zero does not prove absence of actual flow and the interface cannot establish sensor health. Custom volume calculations must mark missing intervals incomplete, not fill gaps with valid zero flow. Do not alter or bypass device safety/maintenance permissions.

## 15. Troubleshooting and Delivery Checks

| Symptom | Action |
|---|---|
| SENSOR WARNING / red page message | Stop measurement; power off, check connections, power and gas path, then restart. Hold-to-bypass is maintenance only |
| PRESSURE ZERO FAILED | Remove pressure, open to atmosphere and restart; contact supplier if repeated |
| POSSIBLE AIRFLOW | Check environment/residual flow; tap to continue. This notice does not certify calibration |
| Small idle flow or drift | Flow is not startup-zeroed; check moisture, airflow, leaks and environment. This alone proves neither improved accuracy nor damage |
| OVER / red line | Reduce input; readings during overload are invalid. Reset and repeat a volume test |
| USB device missing | Check data cable, USB port and system recognition; close competing software, Refresh and retry |
| BLE missing / connection fails | Enable Bluetooth, close phone connections, move closer, check page 5 advertising, then Refresh; use USB to isolate the issue |
| PC numbers while device reports an error | Do not continue measuring; see 13.3, correct the fault and restart |

Before delivery, the supplier should record SN/HW and firmware/desktop versions and check startup, idle baseline, known pressure/flow points, overload, USB, BLE and recovery, supplying actual calibration/inspection records. On first use, complete normal startup and connection checks. For support, provide SN, FW, BUILD, desktop version, warning photos and reproduction steps; do not disassemble sensors yourself.
