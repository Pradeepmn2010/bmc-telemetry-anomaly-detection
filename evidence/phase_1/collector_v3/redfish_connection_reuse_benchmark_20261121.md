# Redfish Connection Reuse Benchmark

Date: 2026-11-21
Environment: QEMU-emulated AST2600 OpenBMC
Endpoint: HTTPS Redfish on 127.0.0.1:2445
Sensor endpoints: 12
Concurrency: 4 workers

## Objective

Compare per-request fresh requests.Session objects against persistent
thread-local requests.Session objects for concurrent Redfish sensor reads.

## Method

- Same 12 Redfish sensor endpoints in both modes.
- Four concurrent workers.
- One warm-up batch per mode, excluded from measured results.
- Six measured batches per mode.
- Modes alternated within each pair to reduce test-order bias.
- Each batch requested all 12 sensor resources.
- HTTP status and JSON parsing were checked.
- No project source files or BMC configuration were modified.

## Results

| Metric | Fresh sessions | Persistent sessions |
|---|---:|---:|
| Successful measured requests | 72/72 | 72/72 |
| Mean batch time | 5.248 s | 4.150 s |
| Median batch time | 5.121 s | 4.125 s |
| Minimum batch time | 4.633 s | 3.631 s |
| Maximum batch time | 6.316 s | 4.648 s |

Mean batch-time reduction:
(5.248 - 4.150) / 5.248 * 100 = 20.9%

Mean of six paired percentage improvements reported by the benchmark:
20.5%.

All six paired comparisons favored persistent sessions.

## Individual Paired Measurements

| Pair | Fresh (s) | Persistent (s) |
|---|---:|---:|
| 1 | 6.316 | 4.648 |
| 2 | 5.486 | 4.558 |
| 3 | 5.613 | 4.207 |
| 4 | 4.633 | 4.044 |
| 5 | 4.756 | 3.631 |
| 6 | 4.682 | 3.814 |

## Interpretation

Persistent thread-local sessions were consistently faster in this test.
The result supports investigating session reuse in a separate collector
prototype while retaining collector_v3.py as the baseline.

This benchmark measures end-to-end request and batch latency. It does not
isolate TLS handshake time, and therefore does not prove that TLS overhead
alone explains the improvement.

The result is specific to this QEMU/OpenBMC environment and test workload.
Further validation is required under sustained collection.

## Next Step

Develop collector_v4.py as a separate experimental implementation with
persistent thread-local sessions. Do not overwrite collector_v3.py.

Validate:
- Sensor completeness per poll.
- Duplicate and missing sensor records.
- Request failures and timeout handling.
- Poll duration and start-to-start interval.
- Comparison against collector_v3.py under equivalent conditions.
