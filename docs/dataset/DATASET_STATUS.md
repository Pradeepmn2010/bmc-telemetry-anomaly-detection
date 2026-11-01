# Dataset Status and Initial Quality Assessment

## Dataset
File: data/baseline_telemetry.csv

## Collection summary
- Records: 720
- Unique sensors: 12
- Collection duration: approximately 4 minutes 52 seconds
- Missing values: 0
- Collection date: 2026-10-29

## Initial observations
- PWM sensors report constant 100%.
- Four fan tachometer sensors report constant 0 RPM and Critical health.
- Ambient temperature reports constant 0 Celsius and Critical health.
- Battery voltage reports constant 1.5415 V and Critical health.
- ADC0_12V ranges from 7.8152 V to 23.7822 V.
- ADC8_12V ranges from 7.8944 V to 23.8614 V.
- ADC channels show repeated transitions between OK, Warning and Critical.

## Classification
This dataset is an initial raw telemetry capture.
It is NOT yet verified as a healthy normal-operation baseline.

Do not use it as clean normal-only training data until sensor
validity and operating conditions have been established.

## Limitations
- Physical hardware behavior has not been independently verified.
- Several sensor readings may represent unavailable or simulated values.
- ADC scaling and input behavior require further investigation.
- Fan tachometer and ambient temperature sensor validity require investigation.

## Next steps
1. Investigate ADC input and scaling behavior.
2. Verify fan tachometer sensor availability.
3. Verify ambient temperature sensor availability.
4. Verify battery sensor configuration.
5. Collect a new telemetry dataset after establishing a documented
   healthy operating condition.
6. Keep raw captures separate from validated normal and fault datasets.
