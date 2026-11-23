# Thermal Temperature Threshold Evaluation

Date: 2026-11-23
Platform: QEMU 8.2.2, AST2600 EVB
Firmware: OpenBMC v11.04
Detector: Redfish-configured temperature threshold detector

## 1. Objective

Evaluate the temperature threshold detector using the previously collected
controlled thermal experiment data. Distinguish normal operating phases,
the 60 C thermal fault phase, and recovery.

This is a controlled threshold-pipeline validation. It is not evidence of
generalizable machine-learning performance.

## 2. Input data

Evaluation input:
- results/temperature_threshold_verification_20261122.csv

Source captures:
- data/raw/healthy_temp_25c_20261119.csv
- data/raw/healthy_temp_30c_20261119.csv
- data/raw/healthy_temp_35c_20261119.csv
- data/raw/thermal_fault_60c_20261118.csv
- data/raw/thermal_recovery_25c_20261118.csv

The evaluation contains 150 Ambient_Temp observations: 30 from each
source capture.

## 3. Ground-truth definition

Controlled phase labels were used:
- 25 C healthy phase: NORMAL (0)
- 30 C healthy phase: NORMAL (0)
- 35 C healthy phase: NORMAL (0)
- 60 C injected thermal fault: ANOMALY (1)
- 25 C recovery phase: NORMAL (0), retained as a separate recovery phase

The recovery observations are not treated as normal-only training data.

## 4. Detector configuration

The detector uses the configured Redfish temperature thresholds:

| Threshold | Value |
|---|---:|
| Lower caution | 5 C |
| Lower critical | 0 C |
| Upper caution | 38 C |
| Upper critical | 40 C |

A reading at or above the upper critical threshold is classified CRITICAL.
The detector also handles lower and caution thresholds as implemented in
code/detect_temperature_threshold.py.

This is a configured threshold baseline, not a learned ML detector.

## 5. Evaluation results

Total observations: 150

| Phase | Samples | Mean temperature | Detector result |
|---|---:|---:|---|
| NORMAL_25C | 30 | 25 C | NORMAL |
| NORMAL_30C | 30 | 30 C | NORMAL |
| NORMAL_35C | 30 | 35 C | NORMAL |
| THERMAL_FAULT_60C | 30 | 60 C | CRITICAL |
| RECOVERY_25C | 30 | 25 C | NORMAL |

Confusion matrix, with rows as actual [NORMAL, ANOMALY] and columns as
predicted [NORMAL, ANOMALY]:

    [[120, 0],
     [  0, 30]]

| Metric | Result |
|---|---:|
| True negatives | 120 |
| False positives | 0 |
| False negatives | 0 |
| True positives | 30 |
| Accuracy | 1.00 |
| NORMAL precision | 1.00 |
| NORMAL recall | 1.00 |
| ANOMALY precision | 1.00 |
| ANOMALY recall | 1.00 |
| ANOMALY F1-score | 1.00 |

The detector agreed with all 150 controlled phase labels in this dataset.

## 6. Interpretation and limitations

- The result applies only to these five controlled capture phases.
- There are 30 observations per phase and zero within-phase temperature
  variance in the inspected dataset.
- The fault class contains only one injected operating point: 60 C.
- The detector uses configured Redfish thresholds; these results do not
  demonstrate ML training or generalization.
- The controlled phase labels are the evaluation reference. Redfish
  Health is useful corroborating telemetry, but is not an independent
  ground-truth source.
- The recovery phase is evaluated separately and must not be mixed into
  normal-only model training.
- The dataset contains only Ambient_Temp.
- The captures are from separate experiment sessions. Do not infer
  continuous wall-clock detection latency from their row order.
- The injection report records November 17, while source CSV filenames
  indicate November 18. The available evidence does not establish that
  these are the same capture; this discrepancy remains unresolved.

Therefore, the 1.00 metrics describe this controlled threshold check only.
They must not be presented as expected real-world accuracy.

## 7. Reproduction

From the project root with the project virtual environment activated:

    python -m py_compile code/detect_temperature_threshold.py

The existing result file can be independently checked with:

    python - <<'PY'
    import pandas as pd
    from sklearn.metrics import confusion_matrix, classification_report

    df = pd.read_csv(
        "results/temperature_threshold_verification_20261122.csv"
    )
    df["ground_truth"] = (
        df["source_file"] == "thermal_fault_60c_20261118.csv"
    ).astype(int)
    df["prediction"] = df["anomaly_flag"].eq(1).astype(int)

    print(confusion_matrix(
        df["ground_truth"], df["prediction"], labels=[0, 1]
    ))
    print(classification_report(
        df["ground_truth"], df["prediction"],
        labels=[0, 1],
        target_names=["NORMAL", "ANOMALY"],
        zero_division=0
    ))
    PY

## 8. Evidence artifacts

- Detector: code/detect_temperature_threshold.py
- Preprocessing script: code/preprocess_thermal_temperature.py
- Processed dataset: data/processed/thermal_temperature_labeled_20261122.csv
- Threshold verification output: results/temperature_threshold_verification_20261122.csv
- Preprocessing report: evidence/phase_1/thermal_fault/thermal_temperature_dataset_preprocessing_20261122.md
- Injection and recovery report: evidence/phase_1/thermal_fault/thermal_fault_injection_recovery.md

## 9. Status

PASS: All 150 observations in this controlled evaluation were classified
in agreement with their phase labels.

The threshold baseline evaluation is documented. Further work must
establish a broader normal telemetry baseline and evaluate ML detectors
on appropriately separated data.
