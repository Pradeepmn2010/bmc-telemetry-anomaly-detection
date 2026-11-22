# AST2600 Battery ADC Stability and Polling Investigation

## 1. Experiment information

- Date: 2026-11-22
- Platform: QEMU-emulated ASPEED AST2600 EVB
- Firmware: OpenBMC v11.04
- Yocto release codename: styhead
- Target machine: ast2600-default
- Firmware BUILD_ID: 20261008090705
- ADC service: xyz.openbmc_project.adcsensor.service
- ADC executable: /usr/libexec/dbus-sensors/adcsensor

## 2. Objective

Investigate the discrepancy between the historical Battery voltage observed during ADC sensor service startup and the later stable Battery voltage.

Verify the current conversion path across:
- Linux IIO ADC raw data
- Linux hwmon voltage input
- Entity Manager ScaleFactor
- OpenBMC D-Bus sensor value

Also inspect the configured Battery PollRate and determine what can be established about ADC polling behavior from the installed firmware.

No service restart, BMC reboot, configuration modification, or ADC register modification was performed during this investigation.

## 3. Battery sensor configuration

Entity Manager configuration file:

`/usr/share/entity-manager/configurations/ast2600-evb.json`

Battery configuration:

| Property | Value |
|---|---:|
| Index | 7 |
| Name | Battery |
| ScaleFactor | 0.75188 |
| PollRate | 43200 |
| Upper critical | 3.30 V |
| Upper non-critical | 3.21 V |
| Lower non-critical | 2.79 V |
| Lower critical | 2.70 V |

The configuration associates Battery with ADC index 7.

## 4. ADC channel and conversion path

Previously established device-tree and IIO mapping identifies:
- ADC0 as `/sys/bus/iio/devices/iio:device0`
- ADC0 channel 7 as the Battery input
- IIO scale: 2.441406250
- IIO offset: 502
- Linux hwmon input: `/sys/class/hwmon/hwmon18/in8_input`

The IIO-to-hwmon conversion is:

`ADC voltage (mV) = (raw count + offset) * scale`

For the current raw count of 422:

`(422 + 502) * 2.441406250 = 2255.86 mV`

The hwmon interface reports 2255 mV.

The Entity Manager scaling is:

`Battery voltage = ADC voltage (mV) / (1000 * ScaleFactor)`

Using the reported hwmon value:

`2.255 / 0.75188 = approximately 2.9991 V`

This matches the D-Bus Battery value.

## 5. Historical startup observation

The ADC sensor service journal contains the following startup messages at 2026-11-17 17:41:37 UTC:

`Sensor name: Battery, low threshold: 2.790000, assert value: 1.629200, raw data: 1225.000000`

`Sensor name: Battery, low threshold: 2.700000, assert value: 1.629200, raw data: 1225.000000`

The same startup log reports ADC0_12V and ADC8_12V at 8.2508 V with raw data 1250 mV.

For Battery:

`1225 / 0.75188 = approximately 1.6292 V`

The startup raw data of 1225 mV is consistent with an IIO raw count near zero:

`(0 + 502) * 2.441406250 = 1225.59 mV`

However, the ADC raw count was not captured at the exact startup timestamp. Therefore, a zero-count initialization condition is a plausible explanation, not a proven root cause.

## 6. Current live measurements

On 2026-11-22, the following values were observed:

| Measurement layer | Value |
|---|---:|
| ADC0 channel 7 raw count | 422 |
| IIO scale | 2.441406250 |
| IIO offset | 502 |
| Calculated ADC voltage | 2255.86 mV |
| hwmon in8_input | 2255 mV |
| Entity Manager ScaleFactor | 0.75188 |
| Battery D-Bus Value | 2.9991 V |

D-Bus property queried:

`xyz.openbmc_project.Sensor.Value.Value`

D-Bus object:

`/xyz/openbmc_project/sensors/voltage/Battery`

The Battery object was also previously observed with Available=true and Functional=true.

## 7. Stability experiment

A read-only stability test collected ten observations of:
- ADC0 channel 7 raw count
- hwmon in8_input
- Battery D-Bus Value

Observation period: approximately 29 seconds, beginning at 2026-11-22 05:18:36 UTC.

| Metric | Observations |
|---|---:|
| Number of samples | 10 |
| ADC raw count | 422 in all samples |
| hwmon voltage | 2255 mV in all samples |
| D-Bus Battery value | 2.9991 V in all samples |

All three layers remained consistent throughout the observation.

Important limitation: repeated reads of a published hwmon/D-Bus value do not necessarily represent independent hardware ADC conversions. This test establishes stability of the observed interfaces, not the underlying conversion frequency.

## 8. ADC sensor service status and logs

Systemd unit:

`xyz.openbmc_project.adcsensor.service`

Observed status:
- Loaded and enabled
- Active (running)
- Main PID: 446
- Started: 2026-11-17 17:41:38 UTC
- No service restart was performed during the investigation.

The unit file executes:

`/usr/libexec/dbus-sensors/adcsensor`

The service unit itself does not specify a polling interval.

The startup journal contains an additional message:

`error getting SpecialMode status: 'No route to host'`

This message was observed during service startup. Its relationship, if any, to the Battery reading discrepancy has not been established.

## 9. PollRate and binary inspection

The installed Entity Manager configuration contains:

`"PollRate": 43200`

The ADC executable's embedded strings include:
- `PollRate`
- `ScaleFactor`
- `std::chrono::steady_clock`
- Boost.Asio timer-related symbols
- ADC source paths under `dbus-sensors/0.1+git/src/adc/`

These observations support the presence of configuration and timer-related functionality in the executable. They do not, by themselves, prove the exact unit conversion, scheduling semantics, or default interval in this firmware build.

The firmware image did not provide a usable package database in the locations checked. The following utilities were also unavailable on the BMC: opkg, readelf, objdump, and file.

Firmware version information:
- `/etc/os-release`: v11.04, styhead
- `BUILD_ID`: 20261008090705
- `/etc/version`: 20180309123456

The `/etc/version` value differs from the image BUILD_ID and is not treated as the firmware image build date.

ADC executable fingerprint:

- File size: 633468 bytes
- SHA-256: `765f06a76fc8eeffc8992e73be612f4c11475ba877362d100919f6dd73600a9b`

The exact dbus-sensors Git revision and exact PollRate implementation in this binary remain unverified.

## 10. Findings

1. The current Battery measurement path from ADC0 channel 7 through IIO, hwmon, Entity Manager scaling, and D-Bus is numerically consistent.
2. Ten observations over approximately 29 seconds showed stable values at all three measurement layers.
3. The historical startup value of 1.6292 V corresponds mathematically to 1225 mV before Entity Manager scaling.
4. The current value is 2.9991 V, corresponding to 2255 mV before Entity Manager scaling.
5. The startup discrepancy is real in the service journal, but its root cause is unresolved.
6. The Battery configuration contains PollRate=43200. Its precise interpretation in this firmware binary has not been independently verified.
7. The stability test does not establish the frequency of physical ADC conversions.

## 11. ML dataset decision

Battery is not currently approved as a validated healthy ML training feature.

Reasons:
- Historical startup discrepancy remains unresolved.
- The ten-sample stability test was conducted under one steady operating condition.
- Repeated interface reads do not prove independent ADC conversions.
- Healthy operating variation has not yet been characterized.

Preserve historical Battery telemetry in the raw datasets. Do not delete or rewrite previous records. Exclude Battery from the validated normal-training feature set until its behavior is sufficiently characterized.

## 12. Reproduction commands

Connect to the BMC:

`ssh -p 2225 root@127.0.0.1`

Inspect the configuration:

`grep -n -B 12 -A 25 '"Name": "Battery"' /usr/share/entity-manager/configurations/ast2600-evb.json`

Read the ADC channel:

`cat /sys/bus/iio/devices/iio:device0/in_voltage7_raw`

Read IIO scale and offset:

`cat /sys/bus/iio/devices/iio:device0/in_voltage_scale`

`cat /sys/bus/iio/devices/iio:device0/in_voltage_offset`

Read hwmon:

`cat /sys/class/hwmon/hwmon18/in8_input`

Read D-Bus:

`busctl get-property xyz.openbmc_project.ADCSensor /xyz/openbmc_project/sensors/voltage/Battery xyz.openbmc_project.Sensor.Value Value`

Inspect service status and logs:

`systemctl status xyz.openbmc_project.adcsensor.service --no-pager`

`journalctl -u xyz.openbmc_project.adcsensor.service --no-pager -n 100`

## 13. Follow-up work

- Preserve this report and its executable hash.
- Do not change Battery PollRate during the current investigation.
- If exact polling semantics become necessary, obtain the matching dbus-sensors source revision or build metadata.
- Continue healthy telemetry validation using the existing collector v4 workflow.
- Keep Battery excluded from validated normal ML training until its sampling behavior and historical discrepancy are resolved.
