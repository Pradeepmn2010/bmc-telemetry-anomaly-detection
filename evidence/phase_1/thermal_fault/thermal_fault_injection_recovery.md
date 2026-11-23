# AST2600 QEMU Thermal Fault Injection and Recovery

## Experiment metadata
- Date/time recorded: 2026-11-17
- Environment: QEMU 8.2.2, AST2600 EVB
- Firmware: ASPEED OpenBMC image
- Sensor: Ambient_Temp
- Emulated sensor: TMP105 on I2C bus 8, address 0x4d
- QEMU QOM device path: /machine/unattached/device[20]
- Injection mechanism: QEMU monitor QOM temperature property
- Temperature unit: degrees Celsius

## Objective
Verify that a controlled temperature change propagates through the
emulated hardware and OpenBMC telemetry stack, activates the critical
threshold alarm, and clears the alarm after recovery.

## Injection sequence

### 1. Normal condition
QEMU monitor:
  qom-set /machine/unattached/device[20] temperature 25000

Expected and previously observed:
  D-Bus Sensor.Value = 25
  CriticalAlarmHigh = false

### 2. Thermal fault
QEMU monitor:
  qom-set /machine/unattached/device[20] temperature 60000

Observed:
  Linux hwmon temp1_input = 60000
  D-Bus Sensor.Value = 60
  D-Bus CriticalAlarmHigh = true

Redfish:
  URI: /redfish/v1/Chassis/AST2600_EVB/Sensors/temperature_Ambient_Temp
  Reading = 60.0 Cel
  UpperCaution = 38.0 Cel
  UpperCritical = 40.0 Cel
  Status.Health = Critical
  Status.State = Enabled

### 3. Recovery
QEMU monitor:
  qom-set /machine/unattached/device[20] temperature 25000

Observed:
  D-Bus Sensor.Value = 25
  D-Bus CriticalAlarmHigh = false

## Verified telemetry path
QEMU TMP105
  -> I2C
  -> Linux LM75-compatible driver
  -> Linux hwmon
  -> OpenBMC HwmonTempSensor D-Bus
  -> Redfish Sensor resource

## Result
PASS: Temperature injection to 60 C propagated through D-Bus and
Redfish. The critical-high alarm asserted above the configured
40 C threshold. Returning the emulated temperature to 25 C cleared
the critical-high alarm.

## Scope and limitations
- This is an emulator-level sensor fault injection experiment.
- It does not represent a physical thermal fault or real hardware
  temperature measurement.
- Redfish recovery at 25 C has not yet been recorded; only the D-Bus
  recovery value and alarm-clear transition were verified.
- This experiment validates the thermal sensor path, not the complete
  multi-sensor telemetry collection or anomaly-detection pipeline.

## Evidence source
Results were captured interactively during the 2026-11-17 experiment.
The recorded command outputs are in the project conversation and should
be retained alongside this report if terminal logs or screenshots are
collected later.

## Additional recovery verification — Redfish

After restoring the emulated temperature to 25 C, the Redfish
sensor resource was queried again.

Observed:
  Reading = 25.0 Cel
  Status.Health = OK
  Status.State = Enabled

Recovery verification: PASS.

The Redfish API therefore confirmed both the critical fault state
at 60 C and the healthy recovery state at 25 C.
