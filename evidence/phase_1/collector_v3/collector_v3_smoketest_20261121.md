# Collector v3 – Redfish Concurrent Collection Smoke Test

**Date:** 21 November 2026
**Platform:** QEMU AST2600 EVB
**OpenBMC:** v11.04
**Collector:** code/collector_v3.py
**Test type:** 10-poll smoke test

## 1. Objective

Validate the new concurrent Redfish telemetry collector before conducting
longer healthy-telemetry collection.

## 2. Configuration

- Redfish endpoint: https://127.0.0.1:2445
- Username: root
- Target polling interval: 2 seconds
- Number of polls: 10
- Concurrent workers: 12
- Request timeout: 15 seconds
- Output: data/raw/collector_v3_smoketest_20261121.csv

## 3. Collection Results

- Sensors discovered: 12
- Total records: 120
- Polls completed: 10/10
- Successful sensor requests: 120
- Failed sensor requests: 0
- Records per poll: 12
- Duplicate (poll_id, sensor_id) records: 0
- Missing core telemetry fields: 0
- Polls reported complete: 10/10

## 4. Performance Measurements

| Metric | Result |
|---|---:|
| Mean poll duration | 4.533589 s |
| Standard deviation | 0.622361 s |
| Minimum poll duration | 3.721194 s |
| Maximum poll duration | 6.045949 s |
| Mean start-to-start interval | 4.573801 s |
| Minimum start-to-start interval | 4.025069 s |
| Maximum start-to-start interval | 6.046308 s |

## 5. Sensor Coverage

Each of the following sensors produced 10 records:

- fanpwm_Pwm_0
- fanpwm_Pwm_1
- fanpwm_Pwm_2
- fanpwm_Pwm_3
- fantach_Fan_0
- fantach_Fan_1
- fantach_Fan_2
- fantach_Fan_3
- temperature_Ambient_Temp
- voltage_ADC0_12V
- voltage_ADC8_12V
- voltage_Battery

## 6. CSV Schema

The CSV contains the original telemetry fields:

timestamp, sensor_id, sensor_name, reading, units, health, state,
lower_caution, lower_critical, upper_caution, upper_critical

Additional collection metadata:

poll_id, poll_start_timestamp, poll_duration_seconds, poll_status,
request_status, sensor_url, error

## 7. Interpretation

The smoke test validates successful discovery and collection of all
12 Redfish sensors using concurrent requests.

All 10 polling cycles were complete, with no failed requests, duplicate
sensor records, or missing core telemetry fields.

The requested polling interval was 2 seconds. However, the measured
mean start-to-start interval was approximately 4.57 seconds.

Therefore, the 2-second target was not achieved in this test. Further
performance investigation is required before selecting a final
collection interval.

## 8. Limitations

This experiment validates collection integrity, not anomaly detector
performance or ML training suitability.

The smoke-test dataset is not a representative normal training dataset.
Longer collection and sensor-variation analysis are still required.

## 9. Reproduction Command

From the WSL project root:

    python code/collector_v3.py \
      --url https://127.0.0.1:2445 \
      --username root \
      --interval 2 \
      --count 10 \
      --workers 12 \
      --timeout 15 \
      --output data/raw/collector_v3_smoketest_20261121.csv

## 10. Evidence Files

- Raw data: data/raw/collector_v3_smoketest_20261121.csv
- Collector source: code/collector_v3.py
- This report: evidence/phase_1/collector_v3/collector_v3_smoketest_20261121.md

## 11. Next Steps

1. Investigate Redfish request latency and polling cadence.
2. Validate collector behavior under longer collection runs.
3. Examine telemetry variation and sensor health.
4. Identify suitable healthy telemetry for normal-only model training.
5. Preserve subsequent experiments and their results separately.
