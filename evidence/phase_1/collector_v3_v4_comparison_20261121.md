# Collector v3 vs v4 Performance Comparison

Date: 2026-11-21
Environment: QEMU-emulated ASPEED AST2600 OpenBMC
Redfish endpoint: HTTPS localhost:2445
Sensor count: 12
Workers: 4
Poll count: 10 per collector
Target interval: 2 seconds
Request timeout: 15 seconds

## Objective

Evaluate whether persistent thread-local HTTPS sessions in collector_v4.py
improve complete Redfish telemetry collection performance compared with
collector_v3.py.

## Results

| Metric | Collector v3 | Collector v4 |
|---|---:|---:|
| CSV records | 120 | 120 |
| Polls | 10 | 10 |
| Sensors | 12 | 12 |
| Successful requests | 120 | 120 |
| Failed requests | 0 | 0 |
| Duplicate poll/sensor pairs | 0 | 0 |
| Mean poll duration | 5.817 s | 4.556 s |
| Median poll duration | 5.568 s | 4.510 s |
| Minimum poll duration | 5.061 s | 3.882 s |
| Maximum poll duration | 8.054 s | 5.286 s |
| Mean start-to-start interval | 5.569 s | 4.476 s |
| Median start-to-start interval | 5.451 s | 4.407 s |

## Performance Improvement

Mean poll-duration reduction:
(5.817 - 4.556) / 5.817 * 100 = 21.68%

Median poll-duration reduction:
(5.568 - 4.510) / 5.568 * 100 = 19.00%

Mean start-to-start interval reduction:
(5.569 - 4.476) / 5.569 * 100 = 19.64%

## Interpretation

Collector v4 completed all 120 requests successfully and showed lower
mean and median polling durations than collector v3.

The result is consistent with the separate Redfish connection-reuse
benchmark. Persistent thread-local requests.Session objects are a
promising optimization for this emulated BMC environment.

## Limitations

- Only 10 polls were collected per implementation.
- Collector v3 was run before collector v4; run-order effects are possible.
- This is one QEMU/OpenBMC environment and one 12-sensor workload.
- The requested 2-second start-to-start interval was not achieved.
- The test does not isolate TLS handshake time.

## Decision

Use collector_v4.py as the candidate implementation for the next
healthy telemetry collection experiment.

Retain collector_v3.py unchanged as the baseline.

Before using v4 for a longer collection, perform sustained validation
of completeness, failures, polling intervals, and repeatability.
