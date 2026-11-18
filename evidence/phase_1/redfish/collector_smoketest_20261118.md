# Redfish Collector Smoke Test

- Date: 2026-11-18
- Endpoint: https://127.0.0.1:2445
- Poll interval: 2 seconds
- Requested polls: 3
- Result: PASS

## Collection results
- Records: 36
- Unique sensors: 12
- Unique poll timestamps: 3
- Missing core-field values: 0
- Duplicate timestamp/sensor pairs: 0

## Sensor health

sensor_id
fanpwm_Pwm_0                      OK
fanpwm_Pwm_1                      OK
fanpwm_Pwm_2                      OK
fanpwm_Pwm_3                      OK
fantach_Fan_0               Critical
fantach_Fan_1               Critical
fantach_Fan_2               Critical
fantach_Fan_3               Critical
temperature_Ambient_Temp          OK
voltage_ADC0_12V            Critical
voltage_ADC8_12V            Critical
voltage_Battery             Critical

## Threshold extraction

                          lower_caution  lower_critical  upper_caution  upper_critical
sensor_id                                                                             
fanpwm_Pwm_0                        NaN             NaN            NaN             NaN
fanpwm_Pwm_1                        NaN             NaN            NaN             NaN
fanpwm_Pwm_2                        NaN             NaN            NaN             NaN
fanpwm_Pwm_3                        NaN             NaN            NaN             NaN
fantach_Fan_0                    480.00           360.0            NaN             NaN
fantach_Fan_1                    480.00           360.0            NaN             NaN
fantach_Fan_2                    480.00           360.0            NaN             NaN
fantach_Fan_3                    480.00           360.0            NaN             NaN
temperature_Ambient_Temp           5.00             0.0          38.00            40.0
voltage_ADC0_12V                  10.80            10.2          13.20            13.8
voltage_ADC8_12V                  10.80            10.2          13.20            13.8
voltage_Battery                    2.79             2.7           3.21             3.3

## Dataset integrity
- CSV: `data/raw/collector_smoketest_20261118.csv`
- SHA-256: `a51211081cae1a26aa3dbae4a0923a2f688d6b4bc4f9865c8b0c706a9ac38f68`

## Interpretation
- All 12 sensors were collected in each of 3 polls.
- Nested Redfish threshold extraction is working.
- Blank threshold fields indicate thresholds not exposed by that sensor.
- This smoke-test dataset is not approved as a healthy ML training baseline.
