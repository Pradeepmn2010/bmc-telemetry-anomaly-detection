# ADC0 Static Threshold Baseline — 2026-11-22

## 1. Objective

Evaluate a static, normal-data-derived threshold detector against the controlled ADC0 voltage sag and recovery experiment on the QEMU-emulated AST2600 BMC.

This is a controlled experiment result, not a claim of general server anomaly-detection accuracy.

## 2. Environment and input

- Platform: QEMU-emulated ASPEED AST2600 BMC
- QEMU: 8.2.2
- OpenBMC image: v11.04
- Host: WSL2 Ubuntu 24.04.4 LTS
- Input: `data/processed/dynamic_adc0_labeled_wide_20261121.csv`
- Samples: 140 timestamp rows
- Telemetry channels: 12
- Detector feature: `voltage_ADC0_12V` only
- Stable control channel: `voltage_ADC8_12V`

## 3. Experimental phases

Each phase contains 20 samples.

| Phase | ADC0 voltage | Ground truth |
|---|---:|---|
| BASELINE | 12.0000 V | Normal |
| SAG_2 | 11.7624 V | Anomaly |
| SAG_4 | 11.5182 V | Anomaly |
| SAG_6 | 11.2739 V | Anomaly |
| RECOVERY_4 | 11.5182 V | Anomaly |
| RECOVERY_2 | 11.7624 V | Anomaly |
| NORMAL_RECOVERY | 12.0000 V | Normal |

The recovery phases remain anomaly-labelled until nominal voltage is restored. The phases were collected in separate sessions, not as one uninterrupted time series.

## 4. Detector methodology

Implementation: `code/detect_adc0_threshold.py`

The detector uses only normal-labelled ADC0 samples to calculate:

- Normal samples: 40
- Baseline samples: 20
- Normal-recovery samples: 20
- Threshold multiplier: k = 4

The limits are:

- Lower = mean - k × standard deviation
- Upper = mean + k × standard deviation

A sample is flagged when ADC0 is below the lower limit or above the upper limit. Other telemetry channels cannot trigger this detector.

## 5. Learned threshold

| Quantity | Result |
|---|---:|
| Normal ADC0 mean | 12.000000 V |
| Normal ADC0 standard deviation | 0.000000 V |
| k | 4.0 |
| Lower threshold | 12.000000 V |
| Upper threshold | 12.000000 V |

The zero standard deviation means all normal ADC0 observations were identical. Therefore, the learned limits reduce to an exact 12.0 V comparison.

## 6. Results

### Confusion counts

| Measure | Count |
|---|---:|
| True positives | 100 |
| False positives | 0 |
| False negatives | 0 |
| True negatives | 40 |
| Total | 140 |

### Evaluation metrics

| Metric | Result |
|---|---:|
| Precision | 1.0000 |
| Recall | 1.0000 |
| F1-score | 1.0000 |
| False-alarm rate | 0.0000 |

### Phase-wise detections

| Phase | Samples | Actual anomalies | Detected |
|---|---:|---:|---:|
| BASELINE | 20 | 0 | 0 |
| SAG_2 | 20 | 20 | 20 |
| SAG_4 | 20 | 20 | 20 |
| SAG_6 | 20 | 20 | 20 |
| RECOVERY_4 | 20 | 20 | 20 |
| RECOVERY_2 | 20 | 20 | 20 |
| NORMAL_RECOVERY | 20 | 0 | 0 |

## 7. Interpretation and limitations

The detector matched all 140 experimental labels in this controlled ADC0 experiment.

These results must not be interpreted as independent test performance or 100% real-world detection accuracy.

1. The normal samples used to fit the threshold were also used to calculate the normal-sample false-alarm rate. There is no independent normal test set.
2. Normal ADC0 standard deviation is zero. The resulting threshold is an exact-value comparison, not a realistic operating tolerance.
3. Labels were assigned from controlled experiment phases. They are experimental ground truth, not independently diagnosed production faults.
4. Partial-recovery phases remain anomaly-labelled until nominal voltage is restored.
5. The phases were collected in separate sessions. Row-based results do not establish wall-clock detection latency during continuous operation.
6. This validates only the ADC0 voltage-sag experiment, not thermal, fan, battery or stuck-sensor detection.
7. The zero false-alarm rate is specific to the 40 normal fitting samples and is not an independent estimate of operational false-alarm performance.

## 8. Output artifact

Detector verdict CSV:

`results/adc0_threshold_verdict_20261122.csv`

The output contains 140 rows with timestamp, source file, phase, ground truth, ADC0 voltage, lower and upper thresholds, and detector verdict.

Validation confirmed:
- 140 rows
- 40 normal and 100 anomaly-labelled samples
- No missing values
- No invalid verdicts
- Correct phase-wise detections
- Both threshold limits equal to 12.0 V

## 9. Reproduction

Run these commands from the project root with the virtual environment active:

- Compile check: `python -m py_compile code/detect_adc0_threshold.py`
- Run detector: `python code/detect_adc0_threshold.py`

The script refuses to overwrite an existing output file. To reproduce with a separate output filename, run:

`python code/detect_adc0_threshold.py --input data/processed/dynamic_adc0_labeled_wide_20261121.csv --out results/adc0_threshold_verdict_reproduction.csv --k 4`

## 10. Next steps

- Preserve this result as the controlled ADC0 static-threshold baseline.
- Investigate normal telemetry with meaningful natural variation before interpreting thresholds operationally.
- Evaluate Isolation Forest and LSTM only after suitable normal-only training data and leakage-safe evaluation are established.
- Keep controlled ADC0 experiment labels separate from Redfish Health status.
- Do not attribute unrelated fan or battery readings to the ADC0 voltage-sag experiment.
