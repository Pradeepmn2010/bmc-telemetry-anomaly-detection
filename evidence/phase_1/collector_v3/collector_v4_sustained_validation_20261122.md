# Collector v4 Sustained Validation

Date: 2026-11-22
Platform: QEMU AST2600, OpenBMC v11.04
Collector: code/collector_v4.py
Dataset: data/raw/healthy_nominal_v4_20261122.csv

## 1. Redfish discovery

Live Redfish discovery returned one chassis and one Sensors collection.

- Declared sensor count: 12
- Returned sensor members: 12
- @odata.nextLink: absent
- Missing sensor URLs: 0

The current AST2600 environment returned all sensor members in one page.
Pagination support remains a future generalization requirement.

## 2. Dataset completeness

- Total records: 1440
- Polls: 120
- Unique sensors: 12
- Expected sensor IDs missing: 0
- Unexpected sensor IDs: 0
- Unique sensor URLs: 12
- Polls containing 12 unique sensors: 120
- Successful requests: 1440
- Failed requests: 0
- Complete poll records: 1440
- Duplicate poll/sensor pairs: 0

## 3. Poll structural integrity

- Polls with exactly 12 rows: 120
- Polls with 12 unique sensors: 120
- Polls with one timestamp: 120
- Polls with one start timestamp: 120
- Polls with one duration value: 120
- Invalid durations: 0
- Non-positive durations: 0
- Missing poll IDs: 0
- Missing timestamps: 0

## 4. Timing results

Configured target interval: 2 seconds.

Poll duration:
- Mean: 3.474754 seconds
- Standard deviation: 0.507221 seconds
- Minimum: 2.619500 seconds
- Median: 3.403795 seconds
- 95th percentile: 4.569213 seconds
- Maximum: 4.985903 seconds

Start-to-start interval:
- Mean: 3.474949 seconds
- Standard deviation: 0.509392 seconds
- Minimum: 2.619755 seconds
- Median: 3.402897 seconds
- 95th percentile: 4.569620 seconds
- Maximum: 4.986271 seconds

All 119 measured start-to-start intervals exceeded the configured
2-second target.

The collector sleeps only for the remaining interval after each poll.
When a collection cycle exceeds the target interval, it starts the next
poll without additional sleep. Therefore, the observed cadence is
limited by collection-cycle duration.

## 5. Collection window

First poll: 2026-11-22 05:36:29.688865 UTC
Last poll: 2026-11-22 05:43:23.207789 UTC
Elapsed between first and last poll starts: 413.518924 seconds.

## 6. Decision

The sustained run passed sensor completeness, request success, and
poll structural-integrity checks.

Collector v4 is retained as the experimental candidate for further
telemetry collection in this AST2600 environment.

The configured 2-second target was not achieved. Do not claim
2-second sampling performance.

The results are specific to this QEMU/OpenBMC environment and
120-poll experiment. Further repeatability testing is required.

## 7. Reproduction

From the project root:

    python code/collector_v4.py \
      --output data/raw/healthy_nominal_v4_20261122.csv \
      --interval 2 \
      --count 120 \
      --workers 4 \
      --timeout 15

The existing output must not be overwritten. Use a new output filename
for any repeated experiment.
