# Thermal Threshold Evaluation Correction

Date: 2026-11-24

## 1. Issue identified

The historical thermal threshold result files contained predictions in an
order different from the processed ground-truth dataset.

An initial positional comparison produced an incorrect confusion matrix:
TN=90, FP=30, FN=30, TP=0.

This evaluation was invalid because predictions and labels were not aligned
by source file.

## 2. Detector verification

The existing code/detect_temperature_threshold.py implementation was
inspected.

It classifies readings at or above upper_critical as CRITICAL.
The configured upper-critical threshold is 40 C.

The saved verification result contains:
- 25 C normal: NORMAL
- 30 C normal: NORMAL
- 35 C normal: NORMAL
- 60 C thermal fault: CRITICAL
- 25 C recovery: NORMAL

## 3. Corrected alignment method

Ground truth and predictions were grouped by source_file.

Checks performed:
- Every source file exists in both datasets.
- One ground-truth label per source file.
- One prediction per source file.
- Matching sample counts per source file.

All checks passed.

## 4. Corrected metrics

Dataset: 150 observations.

- True negatives: 120
- False positives: 0
- False negatives: 0
- True positives: 30
- Accuracy: 1.00
- Precision: 1.00
- Recall: 1.00
- F1: 1.00
- False alarm rate: 0.00

Metrics saved in:
results/temperature_threshold_metrics_corrected_20261124.csv

## 5. Limitations

The result represents a controlled emulator experiment with fixed
temperature operating points. It does not establish generalization to
unseen hardware, natural workloads, or arbitrary thermal faults.

## 6. Preservation

Historical result files were not overwritten:
- results/temperature_threshold_verdict_20261119.csv
- results/temperature_threshold_verification_20261122.csv

The corrected metrics were saved under a new filename.
