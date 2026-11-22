# Redfish Polling Latency Investigation

Date: 22 November 2026
Environment: QEMU 8.2.2, AST2600 EVB, OpenBMC v11.04, Ubuntu 24.04 WSL2.

## 1. Objective

Investigate why collector v4 does not meet its configured 2-second polling interval while collecting 12 Redfish sensor resources. The investigation was performed without restarting the active QEMU process or modifying BMC configuration, services, or ADC registers.

## 2. Sustained collector validation

Dataset: healthy_nominal_v4_20261122.csv

- Workers: 4
- Configured interval: 2 seconds
- Polls: 120
- Sensor resources: 12
- Records: 1,440
- Successful requests: 1,440/1,440
- Mean poll duration: 3.475 seconds
- Median: 3.404 seconds
- P95: 4.569 seconds
- Minimum: 2.620 seconds
- Maximum: 4.986 seconds

The configured 2-second interval was not achieved. The collector starts the next poll without sleeping when the preceding poll exceeds the target interval.

## 3. HTTP latency investigation

Individual endpoint measurements used four persistent worker sessions, one warm-up, and five measured rounds.

Mean request durations:
- PWM3: 1.818 seconds
- Fan2 tachometer: 1.664 seconds
- PWM2: 1.582 seconds
- PWM1: 1.452 seconds
- Fan0 tachometer: 1.398 seconds
- Fan3 tachometer: 1.366 seconds
- Fan1 tachometer: 1.326 seconds
- Ambient temperature: 1.207 seconds
- PWM0: 1.190 seconds
- ADC0: 1.041 seconds
- ADC8: 0.646 seconds
- Battery: 0.589 seconds

These durations include request/response and JSON decoding. They are not pure server execution times.

Five concurrent four-worker batches took 3.991, 3.658, 3.478, 3.325, and 3.114 seconds. Requests began in approximately three waves of four, consistent with the executor queue.

## 4. Worker-count comparison

A controlled alternating-order test compared persistent sessions with 1, 4, and 12 workers, using three batches per setting.

| Workers | Mean batch duration | Median |
|---|---:|---:|
| 1 | 4.133 s | 3.953 s |
| 4 | 3.820 s | 3.698 s |
| 12 | 3.946 s | 3.989 s |

All 108 requests succeeded. Four workers were fastest in this small test. The sample size is limited, so this is preliminary evidence, not a definitive optimization result. Retain four workers provisionally.

## 5. HTTP response timing breakdown

A streaming-response diagnostic measured five batches with four workers:
- Mean response-header waiting: approximately 0.971 seconds.
- Median: approximately 0.964 seconds.
- Maximum: approximately 1.703 seconds.
- Mean body transfer: approximately 0.0001 seconds.
- JSON parsing: negligible.

Header waiting includes connection-pool waiting, request transmission, TLS/network overhead, and server-side waiting. It is not a direct measurement of server execution. Response-header waiting dominated the measured request duration.

## 6. BMC observations

During an overlapping collector experiment:
- bmcweb PID: 406.
- Service active.
- Process thread count: 1.
- Observed wait channel: do_epoll_wait.
- BMC load and memory observations did not indicate obvious resource exhaustion.
- Scheduler counters showed approximately 10 seconds of bmcweb CPU runtime over approximately 42 seconds of polling.

This does not account for all elapsed request time. D-Bus or other waiting is a possible hypothesis, not a confirmed cause. A single bmcweb thread is consistent with an event-loop architecture and does not prove strictly serial request processing.

## 7. QEMU host CPU observations

Running QEMU PID: 9633.

During an overlapping ten-poll collector experiment:
- Collector poll durations summed to approximately 35.9 seconds.
- QEMU accumulated approximately 39 CPU seconds during the corresponding active interval.
- QEMU CPU consumption increased during polling and returned toward its earlier idle level afterward.
- Per-thread sampling showed substantial additional user CPU time in QEMU threads 9635 and 9636 during polling.

The thread names were generic qemu-system-arm. Their exact internal roles were not identified.

These observations establish a strong temporal correlation between Redfish polling and QEMU host CPU activity. They do not prove which QEMU subsystem or guest activity accounts for that CPU use.

## 8. TCG accelerator and threading mode

The QEMU binary reports version 8.2.2 and lists only TCG as an available accelerator. The running process command line uses AST2600 EVB and does not specify an explicit accelerator or TCG threading property. It also does not include -icount.

Source inspection found:
- accel/tcg/tcg-all.c contains the default MTTCG selection logic.
- configs/targets/arm-softmmu.mak defines TARGET_SUPPORTS_MTTCG=y.
- target/arm/cpu.h defines TCG_GUEST_DEFAULT_MO.
- build/arm-softmmu-config-target.h confirms TARGET_SUPPORTS_MTTCG 1.

The source enables MTTCG by default when supported, unless instruction counting or an oversized guest disables it. The emulated guest is 32-bit ARM on an x86-64 host, and the running command does not specify -icount.

Therefore, based on the inspected source and generated build configuration, the running QEMU process uses the default multi-threaded TCG configuration (thread=multi).

Both thread=single and thread=multi were accepted by version-only option checks. No guest was booted with either alternative, and no controlled single-versus-multi performance comparison was conducted.

## 9. Conclusions

1. All 12 sensor resources were collected successfully, but the 2-second poll target was not met.
2. Response-header waiting dominated HTTP request time; body transfer and JSON parsing were negligible.
3. Twelve workers did not outperform four workers in the small controlled comparison.
4. bmcweb CPU time did not explain all observed elapsed time.
5. QEMU CPU usage increased strongly during Redfish polling, with two threads accounting for most of the observed additional thread CPU activity.
6. The inspected build configuration indicates that the running ARM guest uses multi-threaded TCG by default.

The precise latency bottleneck remains unresolved. The evidence does not prove that TCG, bmcweb, D-Bus, virtual networking, or any single subsystem is solely responsible.

## 10. Limitations and operational decision

- Several diagnostics used small sample counts.
- Some measurements changed across successive batches, potentially due to warm-up, caching, or host load.
- Response-header waiting is not pure server processing time.
- QEMU thread roles were not independently identified.
- No controlled single-versus-multi TCG benchmark was performed.
- No BMC configuration or active QEMU setting was changed.

Retain collector v4 and four workers provisionally. Report actual poll duration and do not claim the 2-second target has been met. Do not change the active emulator as part of this investigation.

## 11. Reproduction notes

From the QEMU source checkout:

    cd ~/bmc-anomaly-project/qemu-ast2600-adc-experiment
    ./build/qemu-system-arm --version
    ./build/qemu-system-arm -accel help
    grep -n -C 8 -E 'thread|mttcg|TCG' accel/tcg/tcg-all.c
    grep -R -n -E 'TARGET_SUPPORTS_MTTCG|TCG_GUEST_DEFAULT_MO' target/arm configs
    grep -n 'TARGET_SUPPORTS_MTTCG' build/arm-softmmu-config-target.h

For collector timing reproduction, use code/collector_v4.py and a new output filename. Record worker count, interval, poll count, timeout, and start time. Do not overwrite earlier datasets.

## 12. Next project direction

Return priority to telemetry quality validation. Distinguish stable but non-informative sensors, sensors affected by QEMU model limitations, sensors with validated normal variation, and sensors with controlled fault/recovery evidence.

Do not use constant nominal readings as a representative multivariate normal ML training dataset. Begin model training only after telemetry quality and label validation criteria are satisfied.
