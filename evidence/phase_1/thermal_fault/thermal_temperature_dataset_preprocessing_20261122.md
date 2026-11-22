# Thermal Temperature Dataset: Preprocessing and Validation

Date: 2026-11-22
Platform: QEMU AST2600, OpenBMC v11.04

## 1. Objective

Prepare a temperature-only dataset from existing controlled thermal
experiments. Preserve raw data and distinguish normal, fault, and recovery
phases. This dataset supports controlled threshold-pipeline validation;
it does not establish generalizable ML performance.

## 2. Input files

All inputs are in data/raw/.

| File | Phase | Label | Temperature | Role |
|---|---|---:|---:|---|
| healthy_temp_25c_20261119.csv | NORMAL_25C | 0 | 25 C | NORMAL_TRAINING_CANDIDATE |
| healthy_temp_30c_20261119.csv | NORMAL_30C | 0 | 30 C | NORMAL_TRAINING_CANDIDATE |
| healthy_temp_35c_20261119.csv | NORMAL_35C | 0 | 35 C | NORMAL_TRAINING_CANDIDATE |
| thermal_fault_60c_20261118.csv | THERMAL_FAULT | 1 | 60 C | FAULT_EVALUATION |
| thermal_recovery_25c_20261118.csv | RECOVERY | 0 | 25 C | RECOVERY_EVALUATION |

Each raw file contains 360 records across 12 sensors. The preprocessing
script selects 30 records for temperature_Ambient_Temp from each file.

## 3. Reproduction

From the project root with .venv activated:

    python -m py_compile code/preprocess_thermal_temperature.py

    python code/preprocess_thermal_temperature.py \
      --input-dir data/raw \
      --output data/processed/thermal_temperature_labeled_20261122.csv

The script refuses to overwrite an existing output.

## 4. Preprocessing checks

The script checks input existence, required columns, 360 records per source,
30 target-sensor records per source, valid UTC timestamps, numeric readings,
unique timestamps, Cel units, expected operating-point readings, present
health values, 150 combined samples, and source-file metadata.

The output retains source telemetry fields and adds source_file, phase,
ground_truth, anomaly_label, operating_point_c, and training_role.

## 5. Independent validation

Processed output: data/processed/thermal_temperature_labeled_20261122.csv

- 150 rows and 17 columns.
- All required metadata columns present.
- Zero missing values in required fields.
- Zero invalid timestamps and duplicate timestamps.
- Zero incorrect fault, normal, or recovery labels.
- One sensor: temperature_Ambient_Temp.
- Units: Cel.
- Health values: 120 OK and 30 Critical.

| Phase | Samples | Mean | Min | Max | Std |
|---|---:|---:|---:|---:|---:|
| NORMAL_25C | 30 | 25 | 25 | 25 | 0 |
| NORMAL_30C | 30 | 30 | 30 | 30 | 0 |
| NORMAL_35C | 30 | 35 | 35 | 35 | 0 |
| THERMAL_FAULT | 30 | 60 | 60 | 60 | 0 |
| RECOVERY | 30 | 25 | 25 | 25 | 0 |

All temperature values above are in degrees Celsius.

Recovery has binary label 0 because temperature returned to 25 C, but
remains a separate RECOVERY / RECOVERY_EVALUATION phase. Do not use
recovery samples for normal-only model training.

## 6. Limitations and interpretation

- This is a single-feature dataset.
- Each phase has zero within-phase temperature variance.
- The fault class contains one controlled operating point, 60 C.
- Normal operating points are training candidates, not proof of a
  comprehensive healthy baseline.
- Recovery is a separate evaluation slice, not normal training data.
- Other sensor features are excluded because previous investigations
  identified unresolved or unsuitable telemetry channels.
- The thermal injection report is dated November 17, while the CSV
  filenames indicate November 18. The evidence does not establish that
  these are the same capture. This discrepancy remains unresolved.
- This dataset supports controlled threshold-pipeline validation, not
  claims of robust ML generalization.

## 7. Checksums

SHA-256 recorded after generation and validation:

Preprocessing script:
622246cb312ed5143ac50838f67a8eeff24ce827249344e832f7437615d263d8

Processed dataset:
7dc9108c0ac5d85416b308a9d4f8301c24305b1957325cb9d6d4ae3746d780d1

Recheck using:

    sha256sum code/preprocess_thermal_temperature.py \
      data/processed/thermal_temperature_labeled_20261122.csv

## 8. Status

The preprocessing script compiled successfully. The processed dataset
passed the independent validation above. Raw source files were preserved.
Keep phase and training_role metadata during detector development. Use
normal-only training data for fitting and evaluate fault and recovery
separately.
