# ML-Based Anomaly Detection on Emulated BMC
## Server Health Monitoring Using QEMU and OpenBMC

A proof-of-concept project for collecting Baseboard Management Controller (BMC) telemetry from a QEMU-emulated ASPEED AST2600 platform and evaluating anomaly-detection methods for server health monitoring.

## 1. Project Overview

The project integrates QEMU, OpenBMC, Redfish telemetry collection, controlled fault experiments, data preprocessing and anomaly detection.

The primary objective is to investigate whether BMC sensor telemetry can identify abnormal server conditions, particularly:

- ADC0 voltage sag and recovery.
- Elevated ambient temperature.
- Abnormal or unavailable sensor readings.

The project uses an emulated AST2600 environment. Results are controlled proof-of-concept findings and are not physical-server validation.

## 2. System Architecture

```mermaid
flowchart TD
    A["QEMU Emulator"] --> B["ASPEED AST2600 BMC"]
    B --> C["OpenBMC Firmware"]
    C --> D["Hwmon / D-Bus Sensors"]
    D --> E["Redfish Sensor API"]
    E --> F["Python Telemetry Collector"]
    F --> G["Raw Telemetry CSV"]
    G --> H["Preprocessing and Labels"]
    H --> I["Processed Datasets"]
    I --> J["Anomaly Detection"]
    J --> K["Threshold / Isolation Forest / LSTM Feasibility"]
    K --> L["Evaluation and Evidence"]



## 3. Experimental Environment

| Component | Configuration |
|---|---|
| Host environment | Windows with WSL2 |
| Linux distribution | Ubuntu 24.04.4 LTS |
| Emulator | QEMU 8.2.2 |
| Emulated platform | ASPEED AST2600 EVB |
| Firmware | OpenBMC v11.04 |
| Telemetry interface | Redfish over HTTPS |
| Programming language | Python 3.12 |
| ML libraries | NumPy, pandas, scikit-learn, PyTorch |

The experiments use a 64 MiB AST2600 firmware image in an isolated emulated environment.

## 4. Implementation

### Telemetry Collection
Python collectors retrieve BMC sensor readings and metadata through the Redfish API. Collector v5 includes persistent HTTP sessions, concurrent polling and sensor metadata.

### Controlled Experiments
- ADC0 voltage sag and recovery experiments.
- Ambient temperature experiments using controlled temperature operating points.
- Sensor discovery and telemetry-quality investigations.

### Anomaly Detection
- Rule-based threshold detection for ADC0 voltage.
- Redfish threshold-based temperature detection.
- Isolation Forest feasibility investigation.
- LSTM autoencoder feasibility investigation.

### Evaluation
Controlled experiment results are evaluated using confusion-matrix metrics, including accuracy, precision, recall, F1-score and false alarm rate.


## 5. Repository Structure

```text
bmc-anomaly-project/
├── code/
│   ├── collector.py
│   ├── collector_v2.py
│   ├── collector_v3.py
│   ├── collector_v4.py
│   ├── collector_v5.py
│   ├── detect_adc0_threshold.py
│   ├── detect_temperature_threshold.py
│   ├── detect_iforest.py
│   ├── detect_lstm.py
│   ├── evaluate.py
│   ├── evaluate_controlled_experiments.py
│   ├── inject_faults.py
│   ├── preprocess_dynamic_adc0.py
│   ├── preprocess_thermal_temperature.py
│   └── preprocess_redfish.py
├── config/
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   ├── dataset/
│   ├── source/
│   └── ...
├── evidence/
│   └── phase_1/
├── results/
├── testbed/
└── README.md




## 6. Experimental Results

### 6.1 ADC0 Voltage Anomaly Detection

A controlled ADC0 experiment captured 140 samples across nominal, voltage-sag and recovery operating points.

| Metric | Result |
|---|---:|
| Samples | 140 |
| True negatives | 40 |
| False positives | 0 |
| False negatives | 0 |
| True positives | 100 |
| Accuracy | 1.00 |
| Precision | 1.00 |
| Recall | 1.00 |
| F1-score | 1.00 |
| False alarm rate | 0.00 |

Important qualification: the normal samples used to estimate the threshold were also included in evaluation. The result is therefore a controlled experiment result, not an independent holdout evaluation.

### 6.2 Temperature Threshold Detection

A controlled thermal experiment captured 150 samples across 25 C, 30 C, 35 C, 60 C fault and 25 C recovery operating points.

| Metric | Result |
|---|---:|
| Samples | 150 |
| True negatives | 120 |
| False positives | 0 |
| False negatives | 0 |
| True positives | 30 |
| Accuracy | 1.00 |
| Precision | 1.00 |
| Recall | 1.00 |
| F1-score | 1.00 |
| False alarm rate | 0.00 |

The detector used the configured Redfish upper-critical temperature threshold. These results apply to the tested emulator operating points and are not evidence of generalization to unseen hardware.

### 6.3 Machine Learning Model Feasibility

- Isolation Forest: the current controlled datasets did not provide useful separation between normal and anomalous samples under the investigated setup.
- LSTM autoencoder: training and evaluation were not considered sufficiently supported because the captures contain short, repetitive operating-point sequences and limited temporal diversity.
- No LSTM performance metrics are claimed.

The threshold-based experiments currently provide the strongest validated proof-of-concept results in this project.

## 7. Limitations

- Experiments were performed on an emulated AST2600 platform, not physical server hardware.
- The available Redfish system resources did not expose usable CPU or memory telemetry in the tested environment.
- Fan tachometer readings and battery voltage behavior require further validation.
- The ADC0 experiment uses controlled labels and reuses normal threshold-fitting samples during evaluation.
- The thermal experiment covers a limited set of fixed operating points.
- Isolation Forest and LSTM results do not establish that these methods are unsuitable in general; the available dataset is insufficient for a strong comparison.
- The collector polling interval target of 2 seconds was not consistently achieved.
- Results should not be interpreted as production-ready anomaly detection.


## 8. Installation and Environment Setup

### Prerequisites

- Windows with WSL2.
- Ubuntu 24.04 or compatible Linux environment.
- Python 3.12.
- QEMU with ASPEED AST2600 machine support.
- An AST2600-compatible OpenBMC firmware image.
- Git.

### Python Environment

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Recorded package versions from the experimental environment:

| Package | Version |
|---|---|
| requests | 2.34.2 |
| pandas | 3.1.0 |
| NumPy | 2.5.4 |
| scikit-learn | 1.9.1 |
| matplotlib | 3.11.2 |
| PyTorch | 2.14.1+cu130 |

CUDA was unavailable in the recorded WSL environment.

### Lab Security Note

The current collector uses HTTPS with certificate verification disabled for the isolated local emulation environment. Do not reuse this TLS configuration for production systems.

### Running the Redfish Collector

With the AST2600 OpenBMC instance running and its HTTPS port forwarded to localhost, run:

```bash
python code/collector_v5.py --url https://127.0.0.1:2445 --username root --output data/raw/collector_v5_manual.csv --interval 2 --count 60 --workers 4 --timeout 15
```

The collector prompts for the BMC password. Do not place passwords directly in commands or commit credentials.

The example uses a separate output filename. The collector refuses to overwrite an existing output file. Confirm the destination does not already exist before running it.

The requested polling interval is 2 seconds; actual polling duration may be longer.

### Reproducing ADC0 Threshold Detection

Run the ADC0 threshold detector on the processed controlled experiment dataset:

```bash
python code/detect_adc0_threshold.py --input data/processed/dynamic_adc0_labeled_wide_20261121.csv --out results/adc0_threshold_verdict_reproduction.csv --k 4
```

The detector estimates its threshold from normal-labelled samples. In the existing experiment, these same normal samples were also included in evaluation; interpret the metrics accordingly.

The output filename is separate from the historical experiment result. Check that it does not already exist before execution.

### Reproducing Temperature Threshold Detection

Run the temperature detector using the five controlled thermal captures:

```bash
python code/detect_temperature_threshold.py --input data/raw/healthy_temp_25c_20261119.csv data/raw/healthy_temp_30c_20261119.csv data/raw/healthy_temp_35c_20261119.csv data/raw/thermal_fault_60c_20261118.csv data/raw/thermal_recovery_25c_20261118.csv --out results/temperature_threshold_verdict_reproduction_20261124.csv
```

This experiment evaluates the Ambient Temp sensor using configured Redfish threshold metadata. Ground-truth comparisons must be aligned using source-file identity, not CSV row position.

The output filename is separate from the historical verification result. Confirm that it does not already exist before execution.

## 9. Evaluation and Evidence

The controlled experiments are evaluated using the project evaluation scripts:

```bash
python code/evaluate_controlled_experiments.py
```

The evaluator aligns predictions and ground truth using source-file identity and produces separate ADC0 and thermal experiment summaries. Review the script output paths and existing-file protections before rerunning it; do not overwrite historical results.

### Key Evidence Reports

- `evidence/phase_1/adc_investigation/adc0_threshold_baseline_20261122.md` — ADC0 threshold experiment.
- `evidence/phase_1/thermal_fault/thermal_threshold_evaluation_20261123.md` — thermal threshold experiment.
- `evidence/phase_1/ml_experiments/thermal_evaluation_correction_20261124.md` — corrected thermal evaluation.
- `evidence/phase_1/ml_experiments/isolation_forest_feasibility_20261124.md` — Isolation Forest feasibility.
- `evidence/phase_1/ml_experiments/lstm_feasibility_20261124.md` — LSTM feasibility.
- `evidence/phase_1/ml_experiments/ml_experiment_summary_20261124.md` — consolidated ML experiment summary.

Preserve raw captures, processed datasets, generated verdicts, logs and reports. Record experiment commands, configuration, timestamps and limitations so that results can be reproduced and audited.

## 10. Dataset Availability and Reproducibility

The project distinguishes between source code, experiment documentation and locally generated experiment data.

- Raw telemetry captures are stored locally under `data/raw/`.
- Processed and labelled datasets are stored locally under `data/processed/`.
- Detection verdicts and evaluation outputs are stored locally under `results/`.
- Emulator firmware images and testbed resources are maintained under `testbed/`.
- Experiment procedures and supporting reports are maintained under `evidence/` and `docs/`.

Some data, result and emulator directories are excluded from Git tracking through `.gitignore`. Therefore, cloning the GitHub repository alone may not provide every dataset or generated result required to reproduce the experiments. Obtain the corresponding experiment captures and firmware separately from the project owner.

The file `docs/dataset/DATASET_STATUS.md` describes the current dataset status. In particular, `data/baseline_telemetry.csv` must not be treated as a validated healthy baseline without further sensor validation.

## 11. Project Status

This project is an experimental proof of concept. Controlled threshold-based ADC0 and temperature detection have been evaluated. Isolation Forest and LSTM feasibility have been investigated, but the current datasets do not support strong claims about their generalization performance.

Further work includes improving telemetry coverage, validating additional sensors, collecting longer and more diverse time series, and evaluating models on independent captures and physical hardware.
