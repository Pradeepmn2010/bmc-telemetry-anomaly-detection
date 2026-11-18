# ADC to D-Bus and Redfish End-to-End Validation

Date: 2026-11-19
Platform: QEMU 8.2.2, ASPEED AST2600 EVB
Firmware: OpenBMC v11.04
Status: PASS

## Objective
Verify propagation of a controlled ADC channel change through:
QEMU ADC -> Linux hwmon -> OpenBMC D-Bus -> Redfish.

## Sensor mapping
ADC0 CH0 -> hwmon in1_input -> ADC0_12V D-Bus sensor
ADC0_12V Redfish resource:
 /redfish/v1/Chassis/AST2600_EVB/Sensors/voltage_ADC0_12V

## Experimental results

| Layer | Baseline | During injection | After rollback |
|---|---:|---:|---:|
| ADC0 CH0 raw | 10 | 100 | 10 |
| Linux hwmon (mV) | 1250 | 1469 | 1250 |
| D-Bus (V) | 8.2508 | 9.6964 | 8.2508 |
| Redfish (V) | 8.2508 | 9.6964 | 8.2508 |

ADC0 CH1 remained unchanged at raw 20 and 1274 mV.

## Injection
Original packed ADC register:
0x0014000A

Injected packed ADC register:
0x00140064

Register address:
0x1E6E9010

## Conversion
ADC0 CH0 offset = 502
ADC scale = 2.44140625
Entity Manager ScaleFactor = 0.1515

Injected hwmon voltage:
(100 + 502) * 2.44140625 = 1469.24 mV

Expected D-Bus voltage:
1.469 / 0.1515 = approximately 9.6964 V

Observed D-Bus and Redfish voltage:
9.6964 V

## Redfish health observation
The sensor reported Health = Critical during both baseline
and injected measurements. The injected value of 9.6964 V
remained below the configured lower-caution threshold of
10.8 V and lower-critical threshold of 10.2 V.

The numerical reading changed correctly; the health classification
was consistent with the configured thresholds.

## Rollback verification
The original register value 0x0014000A was restored.
The following values were observed after rollback:
- hwmon: 1250 mV
- D-Bus: 8.2508 V
- Redfish: 8.2508 V

## Conclusion
The controlled ADC register modification propagated through
Linux hwmon, OpenBMC D-Bus and Redfish.

The original register and sensor readings were successfully restored.

This validates the emulated telemetry propagation path for ADC0 CH0.

## Limitations
- This is an emulated sensor fault, not a physical hardware fault.
- The experiment is a point validation, not a time-series dataset.
- The tested voltage baseline is unhealthy according to configured
  Redfish thresholds and must not be labelled as healthy ML training data.
