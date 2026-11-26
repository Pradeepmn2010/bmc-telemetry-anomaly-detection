# Bi-LSTM Autoencoder v2 — Experiment Report

**Date:** 2026-11-26  
**Project:** ML-Based Anomaly Detection on Emulated BMC for Server Health Monitoring  
**Environment:** QEMU AST2600 / OpenBMC v11.04  
**Experiment version:** Bi-LSTM Autoencoder v2

---

## 1. Objective

The objective of this experiment was to improve the temporal reconstruction-error scoring method used in the initial Bi-LSTM autoencoder experiment.

In v1, each sliding-window reconstruction error was assigned only to the final row of that window. With a window length of 10, the first nine samples of every capture remained unscored.

The v2 experiment introduces row-level reconstruction-error aggregation so that every sample covered by at least one valid window receives an anomaly score.

The original v1 implementation and results are preserved.

## 2. Experimental methodology

### 2.1 Model architecture

A Bidirectional LSTM Autoencoder was used.

The architecture consists of:

- Bidirectional LSTM encoder.
- Bidirectional LSTM decoder.
- Linear output layer for sensor reconstruction.
- Mean Squared Error (MSE) reconstruction loss.

### 2.2 Hyperparameters

| Parameter | Configuration |
|---|---:|
| Model | Bi-LSTM Autoencoder |
| Window length | 10 |
| Epochs | 40 |
| Batch size | 32 |
| Hidden size | 16 |
| Learning rate | 0.001 |
| Optimizer | Adam |
| Loss function | MSE |
| Random seed | 42 |
| Device | CPU |
| Threshold percentile | 99th percentile |
| Scaler | MinMaxScaler |

The scaler was fitted exclusively on normal training data.

### 2.3 Voltage experiment features

The following features were used:

1. voltage_ADC0_12V
2. voltage_ADC8_12V
3. temperature_Ambient_Temp

### 2.4 Thermal experiment features

The thermal experiment used:

1. temperature_Ambient_Temp

## 3. Dataset preparation

### 3.1 Voltage experiment

| Dataset | Samples |
|---|---:|
| Normal training | 1,512 |
| Normal validation | 324 |
| Normal holdout | 324 |
| Controlled evaluation | 140 |

Training and validation windows:

- Training windows: 1,503
- Validation windows: 315

The controlled evaluation dataset contains nominal voltage captures, voltage-sag captures and recovery captures.

### 3.2 Thermal experiment

| Dataset | Samples |
|---|---:|
| Normal training | 1,552 |
| Normal validation | 344 |
| Normal holdout | 324 |
| Controlled evaluation | 60 |

Training and validation windows:

- Training windows: 1,525
- Validation windows: 317

Thermal training includes the healthy baseline and normal 25°C and 30°C operating-point samples.

The controlled evaluation consists of:

- 60°C thermal fault: 30 samples.
- 25°C recovery: 30 samples.

### 3.3 Dataset limitations

The controlled captures contain constant sensor values within individual captures.

The available data therefore represents controlled operating points rather than realistic, continuously varying server workloads.

The baseline training and validation datasets are chronological portions of the same baseline recording. The 25°C and 30°C thermal samples are divided into training and validation portions from their respective captures.

Consequently, these splits are sample-disjoint but do not establish fully independent capture-level generalization.

## 4. Revised reconstruction-error calculation

### 4.1 Previous method

In v1, each window reconstruction error was assigned to its final timestep.

For a window length of 10, the first nine rows in each capture did not receive predictions.

### 4.2 v2 method

In v2, reconstruction error is calculated separately for every timestep in every sliding window.

For each original sample, errors from all windows containing that sample are accumulated and averaged.

The row-level reconstruction error is:

\[
E_i =
\frac{1}{N_i}
\sum_{j \in W_i} E_{ij}
\]

Where:

- \(E_i\): averaged reconstruction error for sample \(i\).
- \(W_i\): set of windows containing sample \(i\).
- \(N_i\): number of windows containing sample \(i\).
- \(E_{ij}\): reconstruction error for sample \(i\) in window \(j\).

The same row-level scoring method is applied to normal validation data and evaluation data.

### 4.3 Threshold calibration

The anomaly threshold is calculated using the 99th percentile of normal validation row-level reconstruction errors.

A sample is classified as anomalous when:

\[
E_i > T
\]

Where \(T\) is the validation-derived threshold.

No controlled fault labels are used to calibrate the threshold.

## 5. Training results

### 5.1 Voltage model

| Epoch | Training loss |
|---|---:|
| 1 | 0.00627683 |
| 10 | 0.00000170 |
| 20 | 0.00000024 |
| 30 | 0.00000013 |
| 40 | 0.00000008 |

Validation threshold:

\[
T_{\text{voltage}} = 9.120028 \times 10^{-8}
\]

Validation scoring coverage: 324/324 rows.

### 5.2 Thermal model

| Epoch | Training loss |
|---|---:|
| 1 | 0.34265536 |
| 10 | 0.00074242 |
| 20 | 0.00001436 |
| 30 | 0.00000197 |
| 40 | 0.00000116 |

Validation threshold:

\[
T_{\text{thermal}} = 1.058200 \times 10^{-4}
\]

Validation scoring coverage: 344/344 rows.

A decreasing training loss indicates improved reconstruction of the training sequences. It does not, by itself, establish anomaly-detection performance.

## 6. Evaluation results

### 6.1 Voltage controlled evaluation

| Metric | Result |
|---|---:|
| Total samples | 140 |
| Scored samples | 140 |
| Unscored samples | 0 |
| True positives | 100 |
| True negatives | 32 |
| False positives | 8 |
| False negatives | 0 |
| Precision | 92.59% |
| Recall | 100% |
| F1-score | 96.15% |
| False-alarm rate | 20.00% |
| Specificity | 80.00% |

All 100 labelled anomaly samples were detected.

Eight normal samples were incorrectly classified as anomalous.

### 6.2 Thermal controlled evaluation

| Metric | Result |
|---|---:|
| Total samples | 60 |
| Scored samples | 60 |
| Unscored samples | 0 |
| True positives | 30 |
| True negatives | 28 |
| False positives | 2 |
| False negatives | 0 |
| Precision | 93.75% |
| Recall | 100% |
| F1-score | 96.77% |
| False-alarm rate | 6.67% |
| Specificity | 93.33% |

All 30 samples belonging to the 60°C thermal fault capture were detected.

Two normal recovery samples were incorrectly classified as anomalous.

### 6.3 Normal holdout results

| Metric | Voltage | Thermal |
|---|---:|---:|
| Total samples | 324 | 324 |
| Scored samples | 324 | 324 |
| Unscored samples | 0 | 0 |
| True negatives | 320 | 324 |
| False positives | 4 | 0 |
| False-alarm rate | 1.23% | 0.00% |
| Specificity | 98.77% | 100.00% |

The normal holdout datasets contain no positive examples. Therefore, precision, recall and F1-score are not meaningful for these datasets. False-alarm rate and specificity are reported instead.

## 7. False-positive investigation

### 7.1 Voltage false positives

The eight false positives were distributed as follows:

- Four samples in the nominal baseline capture.
- Four samples in the nominal recovery capture.

All occurred at capture positions 2–5.

Both nominal captures showed identical reconstruction-error profiles.

The corresponding sensor readings remained:

- ADC0: 12 V.
- ADC8: 12 V.
- Ambient temperature: 35°C.

The normal holdout also showed four false positives at rows 2–5.

This repeated positional pattern suggests a sequence-position-dependent reconstruction effect.

The precise cause has not yet been established.

### 7.2 Thermal false positives

Two false positives occurred in the 25°C recovery capture:

- Capture row 1.
- Capture row 30.

The remaining 28 samples were classified correctly.

This observation is consistent with a possible sequence-boundary effect.

### 7.3 Interpretation

The v2 row-level aggregation method achieved full scoring coverage but did not eliminate all false alarms.

The false-positive investigation indicates that sequence position and reconstruction behaviour should be considered when evaluating the detector.

The current results should not be interpreted as proof of generalization to arbitrary server workloads.

## 8. Comparison with v1

The v1 experiment assigned one window error to the final row of each window.

The v2 experiment averages timestep reconstruction errors across every window containing each sample.

| Observation | v1 | v2 |
|---|---|---|
| Voltage evaluation coverage | 77/140 | 140/140 |
| Thermal evaluation coverage | 42/60 | 60/60 |
| Voltage controlled F1 | 100% on scored subset | 96.15% |
| Thermal controlled F1 | 66.67% on scored subset | 96.77% |
| Thermal recovery false positives | 21 | 2 |
| Separate result directory | No | Yes |

The v1 metrics were calculated only on scored subsets and must not be directly compared with v2 as if both had identical evaluation coverage.

The v2 results provide complete row-level evaluation and are therefore more suitable for the final comparison.

## 9. Limitations

1. The dataset contains a limited number of independent captures.
2. Sensor readings are constant within individual controlled captures.
3. The normal training data does not represent the full range of natural server workloads.
4. The baseline training and validation portions originate from the same recording.
5. Thermal training and validation samples from the 25°C and 30°C captures are sample-disjoint but not capture-independent.
6. Voltage controlled evaluation contains only a small number of nominal captures.
7. The observed sequence-position-dependent false alarms require further investigation.
8. The results are based on a QEMU-emulated AST2600 OpenBMC environment.
9. Physical server hardware validation has not been performed.

These limitations restrict the generalization claims that can be made from this experiment.

## 10. Reproducibility

### Environment

- Ubuntu 24.04.4 LTS under WSL2.
- Python virtual environment.
- PyTorch CPU execution.
- QEMU 8.2.2.
- ASPEED AST2600 emulation.
- OpenBMC v11.04.

### Script

`code/detect_lstm_v2.py`

### Input datasets

`data/processed/final_experiments/`

- baseline_train.csv
- baseline_validation.csv
- baseline_normal_holdout.csv
- voltage_labeled_evaluation.csv
- thermal_normal_holdout_v3.csv
- thermal_labeled_evaluation.csv

The thermal training and validation builder also reads:

`data/processed/thermal_temperature_labeled_20261122.csv`

### Execution commands

Activate the project virtual environment:

```bash
source .venv/bin/activate
```

Compile-check the script:

```bash
python -m py_compile code/detect_lstm_v2.py
```

Execute the experiment:

```bash
python code/detect_lstm_v2.py
```

### Output directory

`results/final_experiments/lstm_v2/`

Generated files:

- voltage_normal_holdout_lstm_predictions.csv
- voltage_controlled_evaluation_lstm_predictions.csv
- thermal_normal_holdout_lstm_predictions.csv
- thermal_controlled_evaluation_lstm_predictions.csv
- lstm_final_metrics.csv

The v2 experiment script and outputs are kept separate from the original v1 experiment.

## 11. Conclusion

The Bi-LSTM Autoencoder v2 experiment successfully introduced row-level reconstruction-error aggregation and achieved 100% scoring coverage across validation, normal holdout and controlled evaluation datasets.

The controlled voltage experiment achieved 96.15% F1-score, while the controlled thermal experiment achieved 96.77% F1-score.

The thermal experiment showed substantially fewer false positives than the previous v1 scoring approach.

However, voltage false alarms and sequence-boundary-related reconstruction behaviour remain important limitations.

The experiment demonstrates the feasibility of applying a Bi-LSTM autoencoder to controlled BMC telemetry anomaly-detection scenarios in an emulated environment.

Further evaluation with diverse, independently captured and time-varying telemetry is necessary before claiming generalization to real-world server health monitoring.

---

**Evidence status:** Bi-LSTM v2 experiment executed successfully. Original v1 files, source datasets and historical experiment results preserved.
