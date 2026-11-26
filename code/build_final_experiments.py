from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

BASELINE_FILE = ROOT / "data/processed/healthy_baseline_3h_wide_20261125.csv"
ADC_FILE = ROOT / "data/processed/dynamic_adc0_labeled_wide_20261121.csv"
THERMAL_FILE = ROOT / "data/processed/thermal_temperature_labeled_20261122.csv"

OUT = ROOT / "data/processed/final_experiments"
OUT.mkdir(parents=True, exist_ok=True)


def load_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    return pd.read_csv(path)


def chronological_split(df):
    """Split one chronologically ordered healthy baseline: 70/15/15."""
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp").reset_index(drop=True)

    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    train = df.iloc[:train_end].copy()
    validation = df.iloc[train_end:val_end].copy()
    holdout = df.iloc[val_end:].copy()

    return train, validation, holdout


def save(df, filename):
    path = OUT / filename
    df.to_csv(path, index=False)
    print(f"Saved {filename}: {len(df)} rows")


def prepare_baseline():
    df = load_csv(BASELINE_FILE)

    required = {
        "poll_id",
        "timestamp",
        "temperature_Ambient_Temp",
        "voltage_ADC0_12V",
        "voltage_ADC8_12V",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Baseline is missing columns: {sorted(missing)}")

    if df["poll_id"].duplicated().any():
        raise ValueError("Duplicate poll_id values in healthy baseline")

    if df[list(required - {"poll_id", "timestamp"})].isna().any().any():
        raise ValueError("Missing values in baseline ML sensor features")

    train, validation, holdout = chronological_split(df)

    for part, name in [
        (train, "train"),
        (validation, "validation"),
        (holdout, "normal_holdout"),
    ]:
        part["capture_id"] = f"healthy_baseline_{name}"
        part["dataset_role"] = name

    save(train, "baseline_train.csv")
    save(validation, "baseline_validation.csv")
    save(holdout, "baseline_normal_holdout.csv")

    print("\nHealthy baseline split:")
    print(f"  Training:   {len(train)} polls")
    print(f"  Validation: {len(validation)} polls")
    print(f"  Holdout:    {len(holdout)} polls")

    return train, validation, holdout


def prepare_voltage(train, validation, holdout):
    df = load_csv(ADC_FILE)

    required = {
        "timestamp",
        "source_file",
        "phase",
        "ground_truth",
        "anomaly_label",
        "voltage_ADC0_12V",
        "voltage_ADC8_12V",
        "temperature_Ambient_Temp",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"ADC dataset is missing columns: {sorted(missing)}")

    if df["anomaly_label"].isna().any():
        raise ValueError("ADC dataset contains missing anomaly labels")

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["capture_id"] = df["source_file"]
    df["dataset_role"] = "controlled_evaluation"

    # Preserve all original labelled ADC0 samples and their source identity.
    save(df, "voltage_labeled_evaluation.csv")

    features = [
        "poll_id",
        "timestamp",
        "capture_id",
        "dataset_role",
        "voltage_ADC0_12V",
        "voltage_ADC8_12V",
        "temperature_Ambient_Temp",
    ]

    for name, part in [
        ("train", train),
        ("validation", validation),
        ("normal_holdout", holdout),
    ]:
        save(part[features], f"voltage_normal_{name}.csv")

    print("\nADC0 controlled evaluation labels:")
    print(df["anomaly_label"].value_counts(dropna=False).sort_index())


def prepare_thermal(train, validation, holdout):
    df = load_csv(THERMAL_FILE)

    required = {
        "timestamp",
        "source_file",
        "reading",
        "ground_truth",
        "anomaly_label",
        "training_role",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Thermal dataset is missing columns: {sorted(missing)}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    # Historical healthy 25/30/35 C captures are training sequences.
    normal = df[
    (df["training_role"] == "NORMAL_TRAINING_CANDIDATE")
    & (df["ground_truth"] == "NORMAL")
].copy()

    normal["capture_id"] = normal["source_file"]
    normal["sequence_id"] = normal["source_file"]
    normal["temperature_Ambient_Temp"] = pd.to_numeric(
        normal["reading"], errors="raise"
    )
    normal["dataset_role"] = "normal_training_capture"

    # The 60 C fault and 25 C recovery captures are held for evaluation.
    evaluation = df[
        df["training_role"].isin(
            ["FAULT_EVALUATION", "RECOVERY_EVALUATION"]
        )
    ].copy()

    evaluation["capture_id"] = evaluation["source_file"]
    evaluation["sequence_id"] = evaluation["source_file"]
    evaluation["temperature_Ambient_Temp"] = pd.to_numeric(
        evaluation["reading"], errors="raise"
    )
    evaluation["dataset_role"] = "controlled_evaluation"

    if normal.empty or evaluation.empty:
        raise ValueError("Thermal training or evaluation selection is empty")

    thermal_train = train[
        ["timestamp", "temperature_Ambient_Temp"]
    ].copy()
    thermal_train["capture_id"] = "healthy_baseline_train"
    thermal_train["sequence_id"] = "healthy_baseline_train"
    thermal_train["dataset_role"] = "baseline_training"

    thermal_train = pd.concat(
        [
            thermal_train,
            normal[
                [
                    "timestamp",
                    "temperature_Ambient_Temp",
                    "capture_id",
                    "sequence_id",
                    "dataset_role",
                ]
            ],
        ],
        ignore_index=True,
    )

    thermal_validation = validation[
        ["poll_id", "timestamp", "temperature_Ambient_Temp"]
    ].copy()
    thermal_holdout = holdout[
        ["poll_id", "timestamp", "temperature_Ambient_Temp"]
    ].copy()

    thermal_validation["capture_id"] = "healthy_baseline_validation"
    thermal_validation["sequence_id"] = "healthy_baseline_validation"
    thermal_holdout["capture_id"] = "healthy_baseline_holdout"
    thermal_holdout["sequence_id"] = "healthy_baseline_holdout"

    thermal_validation["dataset_role"] = "normal_validation"
    thermal_holdout["dataset_role"] = "normal_holdout"

    evaluation_columns = [
        "timestamp",
        "capture_id",
        "sequence_id",
        "dataset_role",
        "temperature_Ambient_Temp",
        "ground_truth",
        "anomaly_label",
        "phase",
        "training_role",
        "source_file",
    ]

    save(thermal_train, "thermal_normal_train.csv")
    save(thermal_validation, "thermal_normal_validation.csv")
    save(thermal_holdout, "thermal_normal_holdout.csv")
    save(evaluation[evaluation_columns], "thermal_labeled_evaluation.csv")

    print("\nThermal evaluation labels:")
    print(evaluation["anomaly_label"].value_counts(dropna=False).sort_index())
    print("\nThermal evaluation captures:")
    print(evaluation.groupby(["source_file", "training_role"]).size())


def main():
    print("Preparing final anomaly-detection experiment datasets")
    print(f"Output directory: {OUT}")

    train, validation, holdout = prepare_baseline()

    prepare_voltage(train, validation, holdout)
    prepare_thermal(train, validation, holdout)

    print("\nDataset preparation completed.")
    print("Original source CSV files were not modified.")


if __name__ == "__main__":
    main()
