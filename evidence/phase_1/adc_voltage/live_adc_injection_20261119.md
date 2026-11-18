# Live ADC Fault Injection Experiment

Date: 2026-11-19
Platform: QEMU 8.2.2, ASPEED AST2600 EVB
Firmware: OpenBMC v11.04
Status: PASS — injection and rollback verified

## Objective
Verify whether a controlled ADC channel value can be changed at runtime
and observed through the OpenBMC guest Linux hwmon interface.

## Test configuration
ADC controller base: 0x1E6E9000
ADC0 engine base: 0x1E6E9000
ADC0 CH0/CH1 data register: 0x1E6E9010

Original register value: 0x0014000A
Injected register value: 0x00140064

## Results

| Measurement | Baseline | During injection | After rollback |
|---|---:|---:|---:|
| ADC0 CH0 raw | 10 | 100 | 10 |
| ADC0 CH1 raw | 20 | 20 | 20 |
| hwmon in1_input (mV) | 1250 | 1469 | 1250 |
| hwmon in2_input (mV) | 1274 | 1274 | 1274 |

## Conversion check

ADC0 uses offset 502 and scale 2.44140625.

Injected CH0:
(100 + 502) * 2.44140625 = 1469.24 mV

Observed value: 1469 mV.

## Procedure
1. Read the original ADC register using devmem.
2. Record baseline hwmon readings.
3. Write 0x00140064 to register 0x1E6E9010.
4. Read back the register and hwmon values.
5. Restore 0x0014000A.
6. Verify the original register and hwmon readings.

## Conclusion
The guest-side MMIO write changed ADC0 CH0 from raw 10 to raw 100.
Linux hwmon reflected the change from 1250 mV to 1469 mV.
ADC0 CH1 remained unchanged.
The original register value and both hwmon readings were successfully restored.

This demonstrates reversible fault injection in the emulated ADC and
propagation to Linux hwmon.

## Limitations
- This is an emulated fault, not a physical hardware fault.
- The write was performed using guest devmem against a driver-owned register.
- D-Bus and Redfish propagation during this particular injection have not
  yet been verified.
- This experiment is a controlled point test, not a time-series dataset.
