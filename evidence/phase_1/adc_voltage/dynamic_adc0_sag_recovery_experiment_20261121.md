# Dynamic ADC0 Voltage Sag and Recovery Experiment

Date: 21 November 2026
Platform: QEMU AST2600 emulated BMC
QEMU version: 8.2.2
OpenBMC image: ASPEED AST2600, 64 MiB
Interface: Redfish telemetry
Experiment type: Controlled ADC0 CH0 register-level variation

## 1. Objective

Evaluate whether ADC0 voltage telemetry collected through Redfish
reflects controlled voltage sag and subsequent recovery in the
emulated AST2600 BMC.

## 2. Experimental method

Only ADC0 CH0 was modified through the guest MMIO register
0x1E6E9010.

ADC0 CH1 was preserved. Other ADC channels were not intentionally
modified.

Each phase collected 20 Redfish polling cycles at a 2-second
configured interval. Each poll contained 12 sensor records.

## 3. Phase results

| Phase | ADC0 raw | Register value | ADC0 voltage | Deviation |
|---|---:|---|---:|---:|
| Baseline | 243 | 0x001400F3 | 12.0000 V | 0.000% |
| Sag 2% | 228 | 0x001400E4 | 11.7624 V | 1.980% |
| Sag 4% | 213 | 0x001400D5 | 11.5182 V | 4.015% |
| Sag 6% | 198 | 0x001400C6 | 11.2739 V | 6.051% |
| Recovery 4% | 213 | 0x001400D5 | 11.5182 V | 4.015% |
| Recovery 2% | 228 | 0x001400E4 | 11.7624 V | 1.980% |
| Nominal recovery | 243 | 0x001400F3 | 12.0000 V | 0.000% |

## 4. Dataset inventory

| Phase | CSV file | Rows |
|---|---|---:|
| Baseline | dynamic_adc0_baseline_20261121.csv | 240 |
| Sag 2% | dynamic_adc0_sag2_20261121.csv | 240 |
| Sag 4% | dynamic_adc0_sag4_20261121.csv | 240 |
| Sag 6% | dynamic_adc0_sag6_20261121.csv | 240 |
| Recovery 4% | dynamic_adc0_recovery4_20261121.csv | 240 |
| Recovery 2% | dynamic_adc0_recovery2_20261121.csv | 240 |
| Nominal recovery | dynamic_adc0_recovery_nominal_20261121.csv | 240 |

Total records: 1,680
Total timestamps: 140
Records per timestamp: 12
Polls per phase: 20

## 5. Control observations

ADC8 12V remained at 12.0000 V in all seven phases.

Ambient temperature remained at 35.0 degrees C in all seven phases.

ADC0 health was reported as OK for all 140 ADC0 samples.

The experiment therefore demonstrates that the measured ADC0
voltage changed and recovered while the two monitored reference
signals remained constant.

## 6. Interpretation and limitations

This is a controlled emulation experiment using guest MMIO
register writes. It demonstrates telemetry response in the
emulated AST2600/OpenBMC environment. It is not a physical
power-supply or hardware validation.

The BMC reported Health OK throughout the tested voltage range.
This indicates that the configured health thresholds did not
classify these deviations as unhealthy.

The experiment does not independently establish PLDM telemetry
behavior, physical ADC accuracy, or real hardware fault response.

The seven phases are controlled experimental labels. They must
be retained separately and must not be treated as naturally
occurring hardware failures.

## 7. Conclusion

Seven controlled voltage phases were collected and validated.
All seven datasets contain 240 records, with 20 complete polling
timestamps and 12 sensor records per timestamp.

ADC0 voltage decreased from 12.0000 V to 11.2739 V and returned
to 12.0000 V during recovery. ADC8 and ambient temperature
remained constant.

The resulting datasets are preserved as separate phase-specific
CSV files for subsequent preprocessing and anomaly-detection
experiments.
