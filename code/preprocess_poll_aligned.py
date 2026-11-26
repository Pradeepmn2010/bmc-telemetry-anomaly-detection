#!/usr/bin/env python3

"""Validate and convert collector-v5 Redfish data into poll-aligned data."""

from pathlib import Path
import sys

import pandas as pd


SOURCE = Path("data/raw/healthy_baseline_3h_20261125.csv")
OUTPUT = Path("data/processed/healthy_baseline_3h_wide_20261125.csv")
METADATA_OUTPUT = Path("data/processed/healthy_baseline_3h_sensor_metadata_20261125.csv")


def main():
    for path in (SOURCE, OUTPUT, METADATA_OUTPUT):
        if not path.exists() and path != SOURCE:
            continue
        if path != SOURCE and path.exists():
            raise FileExistsError(f"Refusing to overwrite: {path}")

    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)

    df = pd.read_csv(SOURCE)

    required = {
        "poll_id", "poll_start_timestamp", "poll_duration_seconds",
        "poll_status", "request_status", "sensor_id", "reading",
        "sensor_name", "units", "reading_type",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if df[list(required)].isnull().any().any():
        raise ValueError("Null values found in required fields.")

    if df.duplicated(["poll_id", "sensor_id"]).any():
        raise ValueError("Duplicate poll_id/sensor_id records found.")

    if not (df["poll_status"] == "complete").all():
        raise ValueError("Incomplete polls found.")

    if not (df["request_status"] == "success").all():
        raise ValueError("Failed sensor requests found.")

    df["reading"] = pd.to_numeric(df["reading"], errors="raise")

    sensors = sorted(df["sensor_id"].unique())
    poll_counts = df.groupby("poll_id")["sensor_id"].nunique()

    if len(sensors) != 12:
        raise ValueError(f"Expected 12 sensors; found {len(sensors)}.")

    if not (poll_counts == len(sensors)).all():
        raise ValueError("Polls do not contain the same complete sensor set.")

    sensor_sets = df.groupby("poll_id")["sensor_id"].apply(set)
    expected = set(sensors)

    if not sensor_sets.map(lambda x: x == expected).all():
        raise ValueError("Sensor membership differs between polls.")

    poll_metadata = (
        df.groupby("poll_id", sort=False)
        .agg(
            timestamp=("poll_start_timestamp", "first"),
            poll_duration_seconds=("poll_duration_seconds", "first"),
        )
        .reset_index()
    )

    wide = df.pivot(
        index="poll_id",
        columns="sensor_id",
        values="reading",
    ).reset_index()

    wide.columns.name = None
    wide = poll_metadata.merge(wide, on="poll_id", validate="one_to_one")
    wide["timestamp"] = pd.to_datetime(wide["timestamp"], utc=True)
    wide = wide.sort_values("timestamp").reset_index(drop=True)

    if wide[sensors].isnull().any().any():
        raise ValueError("Missing values found after pivot.")

    metadata_columns = [
        "sensor_id", "sensor_name", "units", "reading_type",
        "reading_range_min", "reading_range_max",
        "lower_caution", "lower_critical",
        "upper_caution", "upper_critical",
    ]

    available = [c for c in metadata_columns if c in df.columns]

    metadata = (
        df.groupby("sensor_id", sort=True)[available[1:]]
        .first()
        .reset_index()
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wide.to_csv(OUTPUT, index=False)
    metadata.to_csv(METADATA_OUTPUT, index=False)

    print("PREPROCESSING SUCCESSFUL")
    print(f"Source records: {len(df)}")
    print(f"Polls: {len(wide)}")
    print(f"Sensors: {len(sensors)}")
    print(f"Wide dataset shape: {wide.shape}")
    print(f"Missing readings: {int(wide[sensors].isnull().sum().sum())}")
    print(f"Wide dataset: {OUTPUT}")
    print(f"Sensor metadata: {METADATA_OUTPUT}")
    print("\nSensor columns:")
    print("\n".join(sensors))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
