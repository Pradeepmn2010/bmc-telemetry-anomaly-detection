#!/usr/bin/env python3
import argparse
import os

import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="Convert raw Redfish telemetry to wide ML data")
    parser.add_argument("--input", default="data/raw/redfish_telemetry.csv")
    parser.add_argument("--output", default="data/processed/normal_v2.csv")
    args = parser.parse_args()

    if os.path.exists(args.output):
        parser.error(f"Output already exists; choose another path: {args.output}")

    df = pd.read_csv(args.input)

    required = {"timestamp", "sensor_id", "reading"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df["reading"] = pd.to_numeric(df["reading"], errors="coerce")
    df = df.dropna(subset=["timestamp", "sensor_id", "reading"])

    if df.empty:
        raise ValueError("No valid numeric telemetry readings found")

    duplicates = df.duplicated(subset=["timestamp", "sensor_id"]).sum()
    if duplicates:
        raise ValueError(
            f"Found {duplicates} duplicate timestamp/sensor records. "
            "Resolve these before preprocessing."
        )

    wide = df.pivot(index="timestamp", columns="sensor_id", values="reading")
    wide = wide.sort_index()
    wide.columns.name = None
    wide = wide.reset_index()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    wide.to_csv(args.output, index=False)

    print(f"Raw records: {len(df)}")
    print(f"Unique sensors: {df['sensor_id'].nunique()}")
    print(f"Time samples: {len(wide)}")
    print(f"Missing feature values: {int(wide.drop(columns='timestamp').isna().sum().sum())}")
    print(f"Output: {args.output}")
    print("\nFeature columns:")
    print(", ".join(wide.columns[1:]))

if __name__ == "__main__":
    main()
