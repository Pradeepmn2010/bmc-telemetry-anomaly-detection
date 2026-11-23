# Redfish Collector v5 – Metadata Enhancement

## Objective
Extend the validated v4 Redfish collector to preserve additional
sensor metadata without modifying the original v4 implementation.

## Environment
- Platform: WSL2 Ubuntu 24.04.4 LTS
- Emulator: QEMU 8.2.2
- BMC firmware: OpenBMC v11.04
- Interface: Redfish HTTPS
- Endpoint: https://127.0.0.1:2445
- Sensor resources discovered: 12

## Implementation
Created code/collector_v5.py as a separate copy of collector_v4.py.

Four fields were added:
- reading_type
- reading_range_min
- reading_range_max
- speed_rpm

The original v4 polling, threading, persistent sessions,
authentication, timing, and error-handling behavior were retained.

## Smoke Test
Output:
data/raw/collector_v5_smoketest_20261123.csv

Configuration:
- Poll count: 3
- Workers: 4
- Target interval: 2 seconds
- Timeout: 15 seconds

Results:
- Sensor resources: 12
- Total records: 36
- Successful requests: 36
- Failed requests: 0
- Unique polls: 3
- CSV columns: 22
- Average poll duration: approximately 4.454 seconds

The configured 2-second polling interval was not achieved.

## Metadata Validation
- ReadingType: 36/36 populated
- ReadingRangeMin: 36/36 populated
- ReadingRangeMax: 36/36 populated
- SpeedRPM: 12/36 populated

SpeedRPM was populated for the four fan tachometer sensors.
All reported 0 RPM.

Observed ReadingType values:
Percent, Rotational, Temperature, Voltage.

## Fan Telemetry Limitation
All four fan tachometers reported 0 RPM and Critical health.
All four PWM sensors reported 100%.

These readings are retained as evidence of the current
QEMU emulation limitation. They are not treated as a validated
normal fan operating baseline or as a successful fan fault injection.

## Code Integrity
The v4 and v5 source comparison showed only the four intended
metadata additions and their corresponding CSV/fallback fields.

Original v4 SHA-256:
c13552beb14e9d9fa71f43595935d439b557995ddca70d53caade9d410c8f432

Python syntax compilation passed for v5.

## Limitations
This was a three-poll smoke test, not a sustained performance test.
No claim of improved polling speed or anomaly-detection accuracy is made.
The additional metadata does not establish natural sensor variability.

## Artifacts
- code/collector_v5.py
- data/raw/collector_v5_smoketest_20261123.csv
- evidence/phase_1/collector_v5/v5_metadata_enhancement_20261123.md

## Next Steps
1. Review the new metadata for feature suitability.
2. Continue normal telemetry characterization.
3. Investigate sources of natural variation.
4. Preserve v4 as the validated baseline.
5. Do not train ML models until the normal dataset is suitable.
