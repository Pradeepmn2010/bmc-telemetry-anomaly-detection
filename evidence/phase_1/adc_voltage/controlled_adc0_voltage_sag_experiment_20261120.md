# Controlled ADC0 Voltage Sag Experiment

**Date:** 20 November 2026
**Platform:** QEMU AST2600 EVB
**Firmware:** OpenBMC
**Experiment:** Controlled ADC0 CH0 voltage sag and recovery

## 1. Objective

Demonstrate controlled ADC voltage fault injection on the emulated
AST2600 BMC and validate propagation through Linux hwmon and Redfish.

## 2. Initial configuration

ADC0 CH0/CH1 register:
- Address: 0x1E6E9010
- Baseline register: 0x001400F3
- CH0 raw value: 243
- CH1 raw value: 20

Other ADC channels were preserved:
- ADC0 CH6/CH7: 0x01A60000
- ADC1 CH0/CH1: 0x000000E9

Initial hwmon readings:
- ADC0 CH0 (in1_input): 1818 mV
- ADC0 CH7 (in8_input): 2255 mV
- ADC1 CH0 (in9_input): 1818 mV

## 3. Experimental procedure

Three separate Redfish collections were performed using
code/collector_v2.py with a 2-second polling interval and 30 polls
per phase.

### Phase A: Baseline

ADC0 CH0 register: 0x001400F3

Dataset:
data/raw/adc0_sag_baseline_20261120.csv

Result:
- 360 records
- 30 unique timestamps
- 12 records per timestamp
- ADC0 12V: 12.0000 V
- ADC8 12V: 12.0000 V
- Ambient Temp: 35.0 Cel
- Selected healthy channels reported Health OK and State Enabled.

### Phase B: Controlled voltage sag

ADC0 CH0 was changed from raw 243 to raw 213.
CH1 was preserved at raw 20.

Register write:
devmem 0x1E6E9010 32 0x001400D5

Register readback:
0x001400D5

Linux hwmon in1_input:
1745 mV

Dataset:
data/raw/adc0_sag_fault_20261120.csv

Result:
- 360 records
- 30 unique timestamps
- 12 records per timestamp
- ADC0 12V: 11.5182 V
- ADC8 12V: 12.0000 V
- Ambient Temp: 35.0 Cel
- ADC0 reported Health OK and State Enabled.

Measured ADC0 reduction:
(12.0000 - 11.5182) / 12.0000 * 100
= 4.015%

The injected value remained above the configured ADC0
lower-caution threshold of 10.8 V.

### Phase C: Recovery

ADC0 CH0 was restored to raw 243.

Register write:
devmem 0x1E6E9010 32 0x001400F3

Register readback:
0x001400F3

Linux hwmon in1_input:
1818 mV

Dataset:
data/raw/adc0_sag_recovery_20261120.csv

Result:
- 360 records
- 30 unique timestamps
- 12 records per timestamp
- ADC0 12V: 12.0000 V
- ADC8 12V: 12.0000 V
- Ambient Temp: 35.0 Cel
- ADC0 reported Health OK and State Enabled.

Recovery error relative to baseline:
0.0000 V at the reported Redfish precision.

## 4. Summary

| Measurement | Baseline | Sag | Recovery |
|---|---:|---:|---:|
| ADC0 12V | 12.0000 V | 11.5182 V | 12.0000 V |
| ADC8 12V | 12.0000 V | 12.0000 V | 12.0000 V |
| Ambient Temp | 35.0 Cel | 35.0 Cel | 35.0 Cel |
| ADC0 Health | OK | OK | OK |
| ADC0 Samples | 30 | 30 | 30 |

## 5. Conclusion

The experiment demonstrated controlled ADC0 CH0 register modification,
corresponding Linux hwmon response, propagation to Redfish telemetry,
and restoration to the nominal reading. D-Bus values were not independently
captured during this specific sag experiment.

ADC8 and ambient temperature remained unchanged during the experiment.
The ADC0 health status remained OK because the injected voltage stayed
above the configured lower-caution threshold.

This experiment demonstrates controlled fault injection and telemetry
propagation in an emulated environment. It does not demonstrate physical
hardware behavior or ML anomaly-detection accuracy.

## 6. Limitations and data-quality notes

- Battery telemetry was excluded from healthy-channel interpretation
  because it consistently reported 1.6292 V and Critical health.
- Fan tach telemetry was excluded because of the known QEMU PWM/tach
  emulation limitation.
- The three phases are steady-state collections, not a dynamic
  multivariate ML training dataset.
- No ML model was trained or evaluated using this experiment.
- Redfish Health OK during the sag is not proof that the voltage
  deviation was absent; it reflects the configured threshold status.

## 7. Reproduction commands

Guest-side baseline verification:
devmem 0x1E6E9010 32

Guest-side sag injection:
devmem 0x1E6E9010 32 0x001400D5

Guest-side sag verification:
devmem 0x1E6E9010 32
cat /sys/class/hwmon/hwmon18/in1_input

Guest-side recovery:
devmem 0x1E6E9010 32 0x001400F3

Guest-side recovery verification:
devmem 0x1E6E9010 32
cat /sys/class/hwmon/hwmon18/in1_input

The three raw CSV datasets listed above contain the corresponding
Redfish collection records.
