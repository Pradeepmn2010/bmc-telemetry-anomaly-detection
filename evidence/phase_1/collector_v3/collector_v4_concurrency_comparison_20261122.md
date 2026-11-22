# Collector v4 Concurrency Comparison

**Date:** 22 November 2026
**Project:** ML-Based Anomaly Detection on Emulated BMC for Server Health Monitoring

## 1. Objective

Compare 4-worker and 8-worker configurations of the persistent-session Redfish collector (v4), evaluating collection duration and telemetry completeness.

## 2. Test configuration

- Platform: QEMU-emulated AST2600, OpenBMC v11.04
- Collector: `code/collector_v4.py`
- Discovered sensors: 12
- Target interval: 2 seconds
- HTTP timeout: 15 seconds
- Polls per run: 10
- Configurations: 4 workers and 8 workers

## 3. Experimental procedure

Two alternating comparison pairs were performed:

| Pair | First run | Second run |
|---|---|---|
| 1 | 4 workers | 8 workers |
| 2 | 8 workers | 4 workers |

Raw datasets:

- `data/raw/concurrency_pair1_workers4_20261122.csv`
- `data/raw/concurrency_pair1_workers8_20261122.csv`
- `data/raw/concurrency_pair2_workers8_20261122.csv`
- `data/raw/concurrency_pair2_workers4_20261122.csv`

## 4. Results

| Run | Mean duration (s) | Median (s) | P95 (s) | Maximum (s) |
|---|---:|---:|---:|---:|
| Pair 1 - 4 workers | 3.702 | 3.636 | 4.066 | 4.229 |
| Pair 1 - 8 workers | 3.372 | 3.171 | 4.134 | 4.445 |
| Pair 2 - 8 workers | 3.928 | 3.636 | 5.270 | 5.674 |
| Pair 2 - 4 workers | 3.451 | 3.413 | 3.891 | 3.949 |

### Paired comparison

| Pair | 4-worker mean | 8-worker mean | 8-worker change |
|---|---:|---:|---:|
| 1 | 3.702 s | 3.372 s | 8.92% faster |
| 2 | 3.451 s | 3.928 s | 13.82% slower |

Average of the two run means:

- 4 workers: 3.576 seconds
- 8 workers: 3.650 seconds
- 8 workers were approximately 2.05% slower overall.

### Collection completeness

All four runs achieved:
- 10/10 complete polls per run.
- 120/120 successful sensor requests per run.
- Zero failed requests.
- All 12 sensors represented in every poll.

Total: 40 polls and 480 successful requests.

## 5. Interpretation and limitations

The results do not demonstrate a consistent performance improvement from increasing concurrency to eight workers. The direction of the result reversed between the two pairs.

The comparison is preliminary:
- Only 10 polls were collected per run.
- Runs were sequential, not simultaneous.
- System and emulator load may have varied.
- All sensor readings remained constant.
- Neither configuration achieved the requested 2-second polling interval.

The results evaluate collection performance, not anomaly-detection accuracy.

## 6. Engineering decision

Retain **4 workers as the provisional v4 configuration**.

The 8-worker configuration did not show a repeatable advantage. The 4-worker configuration also has a successful 120-poll sustained validation history.

This is a provisional decision, not proof that four workers are universally optimal. Further investigation should examine endpoint response latency, BMC processing, request scheduling, and collector polling-cycle design.

The 2-second polling target remains unresolved.

## 7. Reproduction

Run from the project root, using new output filenames if repeating the experiment:

For reproduction, use `code/collector_v4.py` with:
- `--interval 2`
- `--count 10`
- `--timeout 15`
- `--workers 4` or `--workers 8`

Assign a different output CSV filename to every run. Preserve the four original datasets unchanged.
