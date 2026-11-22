#!/usr/bin/env python3

import argparse
from pathlib import Path

import pandas as pd


EXPERIMENTS = {
    "healthy_temp_25c_20261119.csv": {
        "phase": "NORMAL_25C",
        "ground_truth": "NORMAL",
        "anomaly_label": 0,
        "operating_point_c": 25,
        "training_role": "NORMAL_TRAINING_CANDIDATE",
    },
    "healthy_temp_30c_20261119.csv": {
        "phase": "NORMAL_30C",
        "ground_truth": "NORMAL",
        "anomaly_label": 0,
        "operating_point_c": 30,
        "training_role": "NORMAL_TRAINING_CANDIDATE",
    },
    "healthy_temp_35c_20261119.csv": {
        "phase": "NORMAL_35C",
        "ground_truth": "NORMAL",
        "anomaly_label": 0,
        "operating_point_c": 35,
        "training_role": "NORMAL_TRAINING_CANDIDATE",
    },
    "thermal_fault_60c_20261118.csv": {
        "phase": "THERMAL_FAULT",
        "ground_truth": "THERMAL_FAULT",
        "anomaly_label": 1,
        "operating_point_c": 60,
        "training_role": "FAULT_EVALUATION",
    },
    "thermal_recovery_25c_20261118.csv": {
        "phase": "RECOVERY",
        "ground_truth": "RECOVERY",
        "anomaly_label": 0,
        "operating_point_c": 25,
        "training_role": "RECOVERY_EVALUATION",
    },
}

TARGET_SENSOR = "temperature_Ambient_Temp"
EXPECTED_SAMPLES = 30

REQUIRED_COLUMNS = {
    "timestamp",
    "sensor_id",
    "sensor_name",
    "reading",
    "units",
    "health",
    "state",
}


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess controlled AST2600 thermal experiments"
    )
    parser.add_argument(
        "--input-dir",
        default="data/raw",
        help="Directory containing original thermal CSV files",
    )
    parser.add_argument(
        "--output",
        default="data/processed/thermal_temperature_labeled_20261122.csv",
        help="Processed dataset output path",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_path = Path(args.output)

    if output_path.exists():
        parser.error(
            f"Output already exists; refusing to overwrite: {output_path}"
        )

    frames = []

    for filename, metadata in EXPERIMENTS.items():
        path = input_dir / filename

        if not path.is_file():
            raise FileNotFoundError(f"Missing input file: {path}")

        df = pd.read_csv(path)

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(
                f"{filename}: missing columns {sorted(missing)}"
            )

        if len(df) != EXPECTED_SAMPLES * 12:
            raise ValueError(
                f"{filename}: expected 360 raw records, found {len(df)}"
            )

        df = df[df["sensor_id"] == TARGET_SENSOR].copy()

        if len(df) != EXPECTED_SAMPLES:
            raise ValueError(
                f"{filename}: expected 30 temperature samples, found {len(df)}"
            )

        df["timestamp"] = pd.to_datetime(
            df["timestamp"], errors="coerce", utc=True
        )
        df["reading"] = pd.to_numeric(df["reading"], errors="coerce")

        if df["timestamp"].isna().any():
            raise ValueError(f"{filename}: invalid timestamps")

        if df["reading"].isna().any():
            raise ValueError(f"{filename}: invalid temperature readings")

        if df["timestamp"].duplicated().any():
            raise ValueError(f"{filename}: duplicate timestamps")

        if set(df["units"].dropna()) != {"Cel"}:
            raise ValueError(f"{filename}: unexpected temperature units")

        expected_temperature = metadata["operating_point_c"]

        if not (df["reading"] == expected_temperature).all():
            raise ValueError(
                f"{filename}: readings do not match expected "
                f"{expected_temperature} C"
            )

        if df["health"].isna().any():
            raise ValueError(f"{filename}: missing sensor health")

        df["source_file"] = filename
        df["phase"] = metadata["phase"]
        df["ground_truth"] = metadata["ground_truth"]
        df["anomaly_label"] = metadata["anomaly_label"]
        df["operating_point_c"] = expected_temperature
        df["training_role"] = metadata["training_role"]

        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("timestamp").reset_index(drop=True)

    if len(combined) != 150:
        raise ValueError(
            f"Expected 150 processed samples, found {len(combined)}"
        )

    if combined["timestamp"].duplicated().any():
        raise ValueError("Duplicate timestamps across input datasets")

    if combined["source_file"].isna().any():
        raise ValueError("Missing source-file metadata")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_path, index=False)

    print("\nTHERMAL PREPROCESSING SUCCESSFUL")
    print("Input files:", len(EXPERIMENTS))
    print("Processed samples:", len(combined))
    print("Sensor:", TARGET_SENSOR)

    print("\nPhase distribution:")
    print(combined["phase"].value_counts().to_string())

    print("\nGround-truth distribution:")
    print(combined["ground_truth"].value_counts().to_string())

    print("\nAnomaly-label distribution:")
    print(combined["anomaly_label"].value_counts().to_string())

    print("\nTraining-role distribution:")
    print(combined["training_role"].value_counts().to_string())

    print("\nTemperature distribution:")
    print(combined.groupby("phase")["reading"].agg(
        ["count", "mean", "min", "max"]
    ).to_string())

    print("\nOutput:", output_path)


if __name__ == "__main__":
    main()
