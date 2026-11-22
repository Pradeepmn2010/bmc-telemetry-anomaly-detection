#!/usr/bin/env python3

import argparse
from pathlib import Path

import pandas as pd


PHASES = {
    "dynamic_adc0_baseline_20261121.csv": ("BASELINE", "NORMAL", 0),
    "dynamic_adc0_sag2_20261121.csv": ("SAG_2", "SAG_2", 1),
    "dynamic_adc0_sag4_20261121.csv": ("SAG_4", "SAG_4", 1),
    "dynamic_adc0_sag6_20261121.csv": ("SAG_6", "SAG_6", 1),
    "dynamic_adc0_recovery4_20261121.csv": ("RECOVERY_4", "RECOVERY_4", 1),
    "dynamic_adc0_recovery2_20261121.csv": ("RECOVERY_2", "RECOVERY_2", 1),
    "dynamic_adc0_recovery_nominal_20261121.csv": (
        "NORMAL_RECOVERY", "NORMAL_RECOVERY", 0
    ),
}

EXPECTED_SENSORS = 12
EXPECTED_SAMPLES_PER_PHASE = 20

REQUIRED_COLUMNS = {
    "timestamp",
    "sensor_id",
    "sensor_name",
    "reading",
    "units",
    "health",
}


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess the controlled ADC0 sag/recovery experiment"
    )
    parser.add_argument(
        "--input-dir",
        default="data/raw",
        help="Directory containing the seven raw experiment CSV files",
    )
    parser.add_argument(
        "--output",
        default="data/processed/dynamic_adc0_labeled_wide_20261121.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_path = Path(args.output)

    if output_path.exists():
        parser.error(f"Output already exists; refusing to overwrite: {output_path}")

    frames = []

    for filename, (phase, ground_truth, anomaly_label) in PHASES.items():
        path = input_dir / filename

        if not path.is_file():
            raise FileNotFoundError(f"Missing input file: {path}")

        df = pd.read_csv(path)

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"{filename}: missing columns {sorted(missing)}")

        if len(df) != EXPECTED_SENSORS * EXPECTED_SAMPLES_PER_PHASE:
            raise ValueError(
                f"{filename}: expected 240 records, found {len(df)}"
            )

        df["timestamp"] = pd.to_datetime(
            df["timestamp"], errors="coerce", utc=True
        )
        df["reading"] = pd.to_numeric(df["reading"], errors="coerce")

        if df["timestamp"].isna().any():
            raise ValueError(f"{filename}: invalid timestamps found")

        if df["reading"].isna().any():
            raise ValueError(f"{filename}: invalid numeric readings found")

        if df["sensor_id"].isna().any() or df["health"].isna().any():
            raise ValueError(f"{filename}: missing sensor ID or health value")

        if df.duplicated(["timestamp", "sensor_id"]).any():
            raise ValueError(f"{filename}: duplicate timestamp/sensor records")

        counts = df.groupby("timestamp")["sensor_id"].nunique()

        if len(counts) != EXPECTED_SAMPLES_PER_PHASE:
            raise ValueError(
                f"{filename}: expected 20 timestamps, found {len(counts)}"
            )

        if not (counts == EXPECTED_SENSORS).all():
            raise ValueError(
                f"{filename}: each timestamp must contain 12 unique sensors"
            )

        adc0 = df[df["sensor_id"] == "voltage_ADC0_12V"]

        if len(adc0) != EXPECTED_SAMPLES_PER_PHASE:
            raise ValueError(f"{filename}: expected 20 ADC0 samples")

        df["source_file"] = filename
        df["phase"] = phase
        df["ground_truth"] = ground_truth
        df["anomaly_label"] = anomaly_label

        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)

    # Convert sensor readings into wide-format columns.
    readings = combined.pivot(
        index="timestamp",
        columns="sensor_id",
        values="reading",
    )
    readings.columns.name = None

    # Preserve OpenBMC health independently from sensor readings.
    health = combined.pivot(
        index="timestamp",
        columns="sensor_id",
        values="health",
    )
    health.columns = [f"health_{column}" for column in health.columns]
    health.columns.name = None

    # Attach experiment metadata once per polling timestamp.
    metadata_columns = [
        "source_file",
        "phase",
        "ground_truth",
        "anomaly_label",
    ]

    metadata = combined[
        ["timestamp"] + metadata_columns
    ].drop_duplicates()

    if metadata["timestamp"].duplicated().any():
        raise ValueError("Conflicting experiment metadata for a timestamp")

    wide = (
        metadata.set_index("timestamp")
        .join(readings, how="inner")
        .join(health, how="inner")
        .reset_index()
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    if len(wide) != 140:
        raise ValueError(f"Expected 140 output rows, found {len(wide)}")

    if wide.isna().any().any():
        raise ValueError("Missing values found in the consolidated dataset")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wide.to_csv(output_path, index=False)

    print("PREPROCESSING SUCCESSFUL")
    print("Input files:", len(PHASES))
    print("Raw records:", len(combined))
    print("Output rows:", len(wide))
    print("Sensor reading columns:", EXPECTED_SENSORS)
    print("Health columns:", EXPECTED_SENSORS)
    print("Ground-truth distribution:")
    print(wide["ground_truth"].value_counts().to_string())
    print("Anomaly label distribution:")
    print(wide["anomaly_label"].value_counts().to_string())
    print("Output:", output_path)


if __name__ == "__main__":
    main()
