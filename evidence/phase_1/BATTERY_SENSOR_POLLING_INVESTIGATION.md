# Battery Sensor Polling Investigation — QEMU AST2600

## 1. Objective

Investigate why the Battery ADC sensor's D-Bus value appeared stale
while its underlying sysfs ADC input continued changing.

The investigation was performed on the emulated AST2600 OpenBMC
environment running under QEMU.

## 2. Sensor configuration

Configuration file:

`/usr/share/entity-manager/configurations/ast2600-evb.json`

Battery sensor configuration:

| Parameter | Original value |
|---|---:|
| Name | Battery |
| ScaleFactor | 0.75188 |
| PollRate | 43200 seconds |
| Index | 7 |

The Battery ADC input was observed through:

`/sys/devices/platform/iio-hwmon/hwmon/hwmon18/in8_input`

The corresponding D-Bus object:

`/xyz/openbmc_project/sensors/voltage/Battery`

D-Bus interface:

`xyz.openbmc_project.Sensor.Value`

## 3. Controlled experiment

A temporary configuration change was made to the Battery sensor only:

- Original PollRate: 43200 seconds
- Temporary PollRate: 1 second

The original configuration was backed up before modification. The ADC sensor service was subsequently restarted while the temporary PollRate of 1 second was configured, so the experiment tested the modified configuration after service initialization.

Backup path:

`/tmp/ast2600-evb.json.before-battery-test`

The modified JSON was validated successfully.

Entity Manager's ReScan method was invoked. The ADC sensor service
remained running with its existing process ID during this stage.

### Observation after ReScan

Across eight samples over approximately 24 seconds:

- Battery sysfs input changed from 2680 to 2800.
- Battery D-Bus value remained at 1.5415 V.

ReScan did not produce an observable Battery D-Bus value update.

## 4. ADC service restart experiment

The ADC sensor service was restarted to test whether it would reload
the modified configuration.

Service:

`xyz.openbmc_project.adcsensor.service`

After restart:

- New ADC process ID: 8360
- Service state: active
- Restart count: 0
- Entity Manager process ID remained 425.

The Battery D-Bus value initially became 3.7466 V.

However, subsequent observations showed:

- Battery sysfs input continued changing.
- Battery D-Bus value remained at 3.7466 V.
- ADC8 and ADC0 D-Bus values continued updating.
- D-Bus monitoring captured PropertiesChanged signals for ADC8
  and ADC0, but no Battery signal during the capture interval. This establishes only that no Battery PropertiesChanged signal was observed during that capture; it does not prove that the ADC read callback was never executed.

This indicates that the Battery D-Bus value was stale during the
observation period. It does not establish the exact internal reason
for the missing updates.

## 5. Restoration of original configuration

The original configuration was restored from the backup.

Restored Battery PollRate:

`43200 seconds`

SHA-256 verification:

| File | SHA-256 |
|---|---|
| Backup | `81cd39fc88255e94fcf2ff24cca579a4a154604b7aa5c27ad954be276e2fff5a` |
| Restored configuration | `81cd39fc88255e94fcf2ff24cca579a4a154604b7aa5c27ad954be276e2fff5a` |

The matching hashes confirm that the restored configuration is
identical to the backup.

The ADC sensor service was restarted again to load the original
configuration.

Final service state:

| Component | State | Process ID | Restart count |
|---|---|---:|---:|
| ADC sensor service | Active | 8629 | 0 |
| Entity Manager | Active | 425 | 0 |

QEMU and Entity Manager were not restarted.

## 6. Final observation

After restoring the original configuration and restarting the ADC
sensor service, the Battery D-Bus value was:

`4.2241 V`

The ADC service startup log reported:

- Battery raw data: 3176
- Scale factor: 0.75188
- Calculated value: 4.2241 V
- High threshold assertions at 3.21 V and 3.30 V

This is a fresh startup reading after configuration restoration. It does
not validate the correctness of the restored 12-hour polling interval
over an extended runtime.

The startup log also contained:

`error getting SpecialMode status: 'No route to host'`

This message was observed during service startup. Its relationship,
if any, to the Battery polling issue has not been established.

## 7. Findings

1. Battery sysfs input changed while the Battery D-Bus value remained
   unchanged during the observed intervals.
2. Entity Manager ReScan did not produce an observable Battery
   D-Bus update.
3. Restarting the ADC sensor service produced a fresh Battery
   startup reading.
4. ADC8 and ADC0 continued updating while Battery appeared stale.
5. The original Battery configuration was restored and its checksum
   verified.
6. The final ADC service and Entity Manager states were active.

## 8. Conclusion and limitations

The investigation reproduced a discrepancy between the changing
Battery sysfs input and the Battery D-Bus value.

Restarting the ADC sensor service resulted in a fresh startup reading.
However, the exact root cause of the missing Battery runtime updates
has not been identified.

The investigation does not establish whether the cause is related
to the deployed ADC sensor implementation, asynchronous file
handling, polling behavior, or another runtime condition.

The source code examined during the investigation was an upstream
reference. Its exact correspondence to the deployed firmware binary
has not been established.

The Battery telemetry must therefore not be treated as validated
healthy baseline data.

## 9. Project status

**Status:** Investigation reproduced; root cause unresolved.

**Configuration:** Original configuration restored.

**Dataset:** Original telemetry dataset left unchanged.

**Next investigation:** Compare the deployed ADC sensor binary and
its runtime behavior with the exact firmware source revision, if
available. Investigate the Battery-specific read/reopen/polling
path before proposing a code-level fix.
