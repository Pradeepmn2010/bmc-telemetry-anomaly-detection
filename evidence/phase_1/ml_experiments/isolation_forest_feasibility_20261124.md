# Isolation Forest Feasibility Assessment

Date: 2026-11-24
Project: ML-Based Anomaly Detection on Emulated BMC for Server Health Monitoring

## 1. Objective

Assess whether the available controlled ADC0 voltage and thermal telemetry
datasets support useful Isolation Forest anomaly detection.

This was a diagnostic experiment. No existing project scripts, datasets,
or result files were modified.

## 2. Feature selection

ADC0 experiment:
- Feature: voltage_ADC0_12V
- Excluded: labels, phase, timestamps, metadata, and unrelated constant sensors.

Thermal experiment:
- Feature: reading
- Excluded: labels, phase, timestamps, operating-point metadata, and
  configured threshold fields.

## 3. Experimental splits

### ADC0 voltage

Training:
- dynamic_adc0_baseline_20261121.csv
- 20 rows, all 12.0 V.

Normal validation:
- dynamic_adc0_recovery_nominal_20261121.csv
- 20 rows, all 12.0 V.

Fault evaluation:
- SAG_2, SAG_4, SAG_6
- RECOVERY_2, RECOVERY_4
- 100 rows total.

### Thermal temperature

Training:
- healthy_temp_25c_20261119.csv
- healthy_temp_30c_20261119.csv
- 60 rows total, with two distinct values: 25 C and 30 C.

Normal validation:
- healthy_temp_35c_20261119.csv
- 30 rows, all 35 C.

Evaluation:
- thermal_fault_60c_20261118.csv: 30 fault rows.
- thermal_recovery_25c_20261118.csv: 30 normal recovery rows.

## 4. Model configuration

- Algorithm: scikit-learn IsolationForest
- Estimators: 200
- Contamination: auto
- Random seed: 42
- Anomaly score: negative decision_function output
- Threshold: 95th percentile of normal validation scores
- Prediction rule: anomaly score strictly greater than threshold.

Fault labels were not used for model fitting or threshold selection.

## 5. Observed results

### ADC0

- Training rows: 20.
- Training unique values: 1 (12.0 V).
- Validation rows: 20.
- Validation unique values: 1 (12.0 V).
- Validation score: approximately 9.992007221626409e-16.
- Validation threshold: approximately 9.992007221626409e-16.
- All 100 evaluation rows received the same score.
- Predicted anomalies: 0/100.

### Thermal

- Training rows: 60.
- Training unique values: 2 (25.0 C and 30.0 C).
- Validation rows: 30.
- Validation unique values: 1 (35.0 C).
- Validation score: 0.018611038897276555.
- Validation threshold: 0.018611038897276555.
- The 60 C fault and 25 C recovery rows received the same score.
- Predicted anomalies: 0/60.

## 6. Interpretation

The current Isolation Forest configuration did not distinguish the
controlled fault observations from the normal validation observations.

ADC0 training data contains only one distinct normal operating value.
Thermal training data contains only two distinct normal operating values.
The observed score equality means the validation-derived threshold did not
separate the evaluated observations.

The strict greater-than comparison also means observations equal to the
threshold are classified as normal.

These results indicate that the current datasets and configuration do not
provide a useful Isolation Forest detector.

## 7. Limitations

- Telemetry values are constant within individual experiment phases.
- Repeated rows from a capture do not represent independent operating
  conditions.
- The number of distinct normal operating points is very small.
- These are controlled emulator experiments, not a representative
  distribution of real server telemetry.
- This diagnostic is not evidence that Isolation Forest is generally
  ineffective for BMC telemetry.
- No generalization claim should be made from these observations.

## 8. Conclusion

Isolation Forest feasibility was assessed separately for ADC0 voltage and
thermal temperature. Under the documented splits and configuration, neither
experiment detected the evaluated anomalies.

The existing controlled threshold-detector experiments remain separate
baselines. Further ML claims require more diverse normal telemetry and
independent operating conditions.
