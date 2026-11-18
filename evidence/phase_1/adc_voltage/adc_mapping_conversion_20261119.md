# AST2600 ADC Mapping and Voltage Conversion Investigation

Date: 2026-11-19
Platform: QEMU AST2600 EVB
OpenBMC image: ASPEED OpenBMC v11.04
QEMU: 8.2.2

## 1. Objective

Trace the ADC telemetry path from the AST2600 emulated ADC through
Linux IIO, hwmon, Entity Manager, ADCSensor D-Bus and Redfish.

## 2. Device-tree findings

The device tree identifies two ADC controllers:

| Controller | Device-tree address | IIO name | Phandle |
|---|---|---|---|
| ADC0 | 0x1e6e9000 | ast2600-adc0-0 | 0x8e |
| ADC1 | 0x1e6e9100 | ast2600-adc1-1 | 0x8f |

Both controllers report:
- compatible: aspeed,ast2600-adc0 / aspeed,ast2600-adc1
- #io-channel-cells: 1
- status: okay
- internal reference voltage: 0x002625a0 microvolts

The iio-hwmon device-tree io-channels property contains eight channels
from ADC0 followed by eight channels from ADC1.

## 3. Verified sensor channel mapping

| Entity Manager index | Controller | Channel | hwmon input | Sensor |
|---:|---|---:|---|---|
| 0 | ADC0 | 0 | in1_input | ADC0_12V |
| 7 | ADC0 | 7 | in8_input | Battery |
| 8 | ADC1 | 0 | in9_input | ADC8_12V |

## 4. Linux IIO measurements

ADC0:
- Offset: 502
- Scale: 2.441406250
- Channel 0 raw: 10
- Channel 1 raw: 20
- Channels 2 through 7 raw: 0

ADC1:
- Offset: 512
- Scale: 2.441406250
- Channels 0 through 7 raw: 0

The observed Linux hwmon values are consistent with:

mV = (raw + offset) * IIO scale

Examples:
- ADC0 channel 0: (10 + 502) * 2.44140625 = 1250 mV
- ADC0 channel 1: (20 + 502) * 2.44140625 = 1274.41 mV
- ADC0 channel 7: (0 + 502) * 2.44140625 = 1225 mV
- ADC1 channel 0: (0 + 512) * 2.44140625 = 1250 mV

## 5. Entity Manager configuration

Configuration file:
 /usr/share/entity-manager/configurations/ast2600-evb.json

| Sensor | Index | ScaleFactor |
|---|---:|---:|
| ADC0_12V | 0 | 0.1515 |
| Battery | 7 | 0.75188 |
| ADC8_12V | 8 | 0.1515 |

The final sensor voltage is consistent with:

V_sensor = (hwmon_mV / 1000) / ScaleFactor

Calculated and observed D-Bus values:

| Sensor | hwmon | ScaleFactor | Calculated voltage | D-Bus voltage |
|---|---:|---:|---:|---:|
| ADC0_12V | 1250 mV | 0.1515 | 8.2508 V | 8.2508 V |
| Battery | 1225 mV | 0.75188 | 1.6292 V | 1.6292 V |
| ADC8_12V | 1250 mV | 0.1515 | 8.2508 V | 8.2508 V |

## 6. Interpretation and limitations

The IIO-to-hwmon and hwmon-to-D-Bus conversion stages are numerically
consistent with the observed values.

The current emulated readings are below the configured lower voltage
thresholds for the two 12 V sensors and Battery. These readings must
not be interpreted as measurements of a real physical power supply.

The current results establish the telemetry mapping and conversion
baseline. They do not yet establish successful voltage fault injection,
recovery, or ML detection.

## 7. Next experiment

Perform controlled ADC raw-value changes, one channel at a time.
For every experiment, record:
- QEMU configuration and injected value
- IIO raw value
- hwmon value
- D-Bus sensor value and alarm state
- Redfish reading and health
- Recovery to the original value

Do not modify the running QEMU instance during this evidence checkpoint.
