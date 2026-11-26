# Comparative Evaluation of Three Anomaly Detection Approaches

**Date:** 26 November 2026  
**Project:** ML-Based Anomaly Detection on Emulated BMC for Server Health Monitoring  
**Evaluation scope:** ADC0 voltage-sag and thermal-fault experiments

---

## 1. Objective

This experiment compares three approaches for detecting anomalies in BMC telemetry:

1. BMC static caution-threshold detector
2. Isolation Forest
3. Bidirectional LSTM Autoencoder (Bi-LSTM v2)

The objective is to evaluate their detection performance on the available emulated voltage and thermal datasets using a common set of classification metrics.

The comparison uses previously generated prediction files. It does not retrain the models or modify the original datasets and predictions.

## 2. Experimental methodology

### 2.1 Evaluation scenarios

Two telemetry scenarios were evaluated independently.

**Voltage scenario**
- Normal holdout: 324 samples from the healthy baseline.
- Controlled evaluation: 140 samples.
- Controlled evaluation contains 40 normal samples and 100 anomaly-labelled samples across baseline, voltage-sag and recovery captures.

**Thermal scenario**
- Normal holdout: 324 samples from the healthy baseline.
- Controlled evaluation: 60 samples.
- Controlled evaluation contains 30 thermal-fault samples at 60°C and 30 recovery samples at 25°C.

The controlled captures are independent captures, not one continuous time series.

### 2.2 Detector configurations

**Static Threshold**

The BMC static caution limits used in the project were:
- Temperature: 5°C to 38°C.
- ADC0 and ADC8 voltage: 10.8V to 13.2V.

**Isolation Forest**

The comparison uses:
- Existing voltage Isolation Forest predictions.
- Thermal Isolation Forest v3 predictions.

The thermal v3 model was trained using selected normal-temperature training samples and calibrated using its normal validation data. Earlier thermal Isolation Forest versions are retained separately and are not included in this comparison.

**Bi-LSTM Autoencoder v2**

The comparison uses the v2 prediction files, not the earlier v1 files.

The v2 method averages reconstruction errors across all windows containing each original row. This provides row-level scores for all evaluated samples in the selected datasets.

### 2.3 Ground-truth handling

The common numeric convention is:

- `0`: Normal
- `1`: Anomaly

For controlled Isolation Forest evaluations, the numeric `anomaly_label` column is used. Its text `ground_truth` column contains descriptive capture labels such as `SAG_2`, `RECOVERY`, and `THERMAL_FAULT`, not the common binary encoding.

For the other prediction files, the numeric `ground_truth` column is used.

Bi-LSTM v2 predictions are included only when `scored=True`. All selected v2 datasets had complete scoring coverage.

### 2.4 Metrics

The following metrics are calculated:

- True Positive (TP)
- True Negative (TN)
- False Positive (FP)
- False Negative (FN)
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
- F1-score = harmonic mean of precision and recall
- False Alarm Rate (FAR) = FP / (FP + TN)
- Specificity = TN / (TN + FP)
- Scoring coverage = scored samples / total samples

For normal-only holdout datasets, precision, recall and F1 are undefined because there are no anomaly-positive ground-truth samples. FAR and specificity are the meaningful classification metrics for these datasets.

## 3. Voltage experiment results

### 3.1 Normal holdout

Dataset size: 324 normal samples.

| Metric | Static Threshold | Isolation Forest | Bi-LSTM v2 |
|---|---:|---:|---:|
| Samples | 324 | 324 | 324 |
| Scored samples | 324 | 324 | 324 |
| Coverage | 100% | 100% | 100% |
| TP | 0 | 0 | 0 |
| TN | 324 | 324 | 320 |
| FP | 0 | 0 | 4 |
| FN | 0 | 0 | 0 |
| FAR | 0% | 0% | 1.2346% |
| Specificity | 100% | 100% | 98.7654% |

Bi-LSTM v2 produced four false alarms on the voltage normal holdout. Static Threshold and Isolation Forest produced no false alarms on this dataset.

### 3.2 Controlled voltage evaluation

Dataset size: 140 samples, comprising 40 normal samples and 100 anomaly-labelled samples.

| Metric | Static Threshold | Isolation Forest | Bi-LSTM v2 |
|---|---:|---:|---:|
| TP | 0 | 0 | 100 |
| TN | 40 | 40 | 32 |
| FP | 0 | 0 | 8 |
| FN | 100 | 100 | 0 |
| Precision | N/A | N/A | 92.5926% |
| Recall | 0% | 0% | 100% |
| F1-score | N/A | N/A | 96.1538% |
| FAR | 0% | 0% | 20% |
| Specificity | 100% | 100% | 80% |
| Coverage | 100% | 100% | 100% |

Static Threshold and Isolation Forest classified every controlled voltage sample as normal. Both therefore missed all 100 anomaly-labelled samples.

Bi-LSTM v2 detected all 100 anomaly-labelled samples but also classified eight normal samples as anomalous.

The voltage-sag values remained above the configured BMC lower caution limit of 10.8V. This explains why the static caution-threshold detector did not flag these controlled sag samples. The result demonstrates a limitation of the tested static threshold for this particular injection range; it does not establish that static thresholds are generally ineffective.

## 4. Thermal experiment results

### 4.1 Normal holdout

Dataset size: 324 normal samples.

| Metric | Static Threshold | Isolation Forest v3 | Bi-LSTM v2 |
|---|---:|---:|---:|
| TN | 324 | 324 | 324 |
| FP | 0 | 0 | 0 |
| FAR | 0% | 0% | 0% |
| Specificity | 100% | 100% | 100% |
| Coverage | 100% | 100% | 100% |

All three detectors correctly classified the thermal normal holdout samples.

### 4.2 Controlled thermal evaluation

Dataset size: 60 samples: 30 thermal faults at 60°C and 30 recovery samples at 25°C.

| Metric | Static Threshold | Isolation Forest v3 | Bi-LSTM v2 |
|---|---:|---:|---:|
| TP | 30 | 0 | 30 |
| TN | 30 | 30 | 28 |
| FP | 0 | 0 | 2 |
| FN | 0 | 30 | 0 |
| Precision | 100% | N/A | 93.75% |
| Recall | 100% | 0% | 100% |
| F1-score | 100% | N/A | 96.7742% |
| FAR | 0% | 0% | 6.6667% |
| Specificity | 100% | 100% | 93.3333% |
| Coverage | 100% | 100% | 100% |

Static Threshold detected all 30 thermal faults and correctly classified all 30 recovery samples.

Bi-LSTM v2 detected all 30 thermal faults, with two false alarms during recovery.

Isolation Forest v3 classified all 60 samples as normal and missed all 30 thermal faults.

## 5. Consolidated findings

### 5.1 Voltage detection

Bi-LSTM v2 achieved 100% recall and 96.1538% F1-score on the controlled voltage evaluation. Static Threshold and Isolation Forest achieved zero recall on this dataset.

The Bi-LSTM result comes with a 20% false-alarm rate on the 40 normal controlled samples. Its normal holdout FAR was 1.2346%.

### 5.2 Thermal detection

Static Threshold achieved 100% precision, recall and F1-score on the controlled thermal dataset.

Bi-LSTM v2 also achieved 100% recall, with 93.75% precision and a 6.6667% FAR.

Isolation Forest v3 did not detect the controlled thermal faults in this experiment.

### 5.3 Interpretation

The experiments show that detector performance depends on the telemetry feature, fault magnitude, training distribution and selected threshold.

Static thresholds are effective for the tested 60°C thermal fault because it exceeds the configured temperature caution limit. The tested voltage-sag samples did not cross the configured lower voltage caution limit.

Bi-LSTM v2 detected the controlled voltage and thermal anomalies, but its false alarms show that high recall alone is not sufficient to establish operational suitability.

Isolation Forest did not distinguish the tested controlled anomalies from normal data in these experiments. Its zero FAR must not be interpreted as successful fault detection: it predicted every controlled sample as normal.

No single detector can be declared universally best from these two controlled experiments.

## 6. Limitations

1. **Limited healthy baseline diversity:** The three-hour healthy baseline was largely constant. It does not represent the full range of normal server workloads, operating conditions or telemetry variation.

2. **Limited fault coverage:** Evaluation used the available emulated ADC0 voltage-sag and thermal fault captures. Results do not establish detection performance for every possible server fault.

3. **Emulator constraints:** QEMU AST2600 did not provide functional fan tachometer behaviour. Fan tachometer readings were zero because of the emulation limitation and were excluded as anomaly features.

4. **Synthetic and emulated environment:** Fault injection and telemetry collection were performed in the emulated environment. No physical server hardware validation was completed.

5. **Model generalization:** Results apply to the tested datasets, feature sets, splits and detector configurations. Broader generalization requires additional workloads, fault magnitudes and independent test captures.

6. **Detection latency:** End-to-end detection latency and response time were not measured in this comparison.

7. **False alarms:** Bi-LSTM v2 produced false positives in the controlled voltage and thermal evaluations. Further validation is required before considering operational deployment.

## 7. Reproducibility

### 7.1 Environment

Run the following commands from the project root in the configured Python virtual environment:

```bash
cd ~/bmc-anomaly-project
source .venv/bin/activate
```

### 7.2 Regenerate the comparison

The comparison script reads existing detector prediction files and calculates common evaluation metrics. It does not retrain the models.

```bash
python code/compare_detectors_final.py
```

### 7.3 Output and source files

The consolidated metrics are written to:

`results/final_comparison/detector_comparison_metrics.csv`

The comparison uses existing predictions from:

- Static Threshold: `results/final_experiments/`
- Isolation Forest: `results/final_experiments/`
- Bi-LSTM v2: `results/final_experiments/lstm_v2/`

The four evaluation groups are voltage normal holdout, controlled voltage evaluation, thermal normal holdout and controlled thermal evaluation.

Retain the source datasets, prediction CSV files, detector scripts, configuration values and generated comparison CSV with this report for reproducibility.

## 8. Conclusion

The comparison evaluated Static Threshold, Isolation Forest and Bi-LSTM v2 using four common evaluation groups covering normal and controlled voltage and thermal telemetry.

Bi-LSTM v2 detected all anomaly-labelled samples in both controlled evaluations, but produced false alarms. Static Threshold performed best on the tested thermal evaluation and missed the tested voltage sag because the sag values remained above its configured lower caution limit. Isolation Forest did not detect the controlled faults in the selected evaluations.

These findings demonstrate the feasibility of evaluating multiple anomaly-detection approaches on an emulated AST2600 BMC telemetry testbed. However, the limited baseline diversity, fault coverage and emulator constraints mean that further validation is required before drawing conclusions about real-world server deployment.

