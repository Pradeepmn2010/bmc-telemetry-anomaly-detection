#!/usr/bin/env python3
"""
Temperature-specific Redfish threshold detector.

Uses configured lower/upper caution and critical thresholds.
Redfish Health is retained only for independent comparison.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED = {
    "timestamp", "sensor_name", "reading", "units",
    "health", "state",
    "lower_caution", "lower_critical",
    "upper_caution", "upper_critical",
}


def classify(row):
    if row["state"] != "Enabled" or row["units"] != "Cel":
        return "INVALID"

    values = [
        row["reading"],
        row["lower_caution"],
        row["lower_critical"],
        row["upper_caution"],
        row["upper_critical"],
    ]

    if not all(pd.notna(v) and np.isfinite(v) for v in values):
        return "INVALID"

    lc = row["lower_critical"]
    lw = row["lower_caution"]
    uw = row["upper_caution"]
    uc = row["upper_critical"]
    reading = row["reading"]

    if not lc < lw < uw < uc:
        return "INVALID"

    if reading < lc or reading >= uc:
        return "CRITICAL"

    if reading < lw or reading >= uw:
        return "WARNING"

    return "NORMAL"


def main():
    parser = argparse.ArgumentParser(
        description="Classify ambient temperature using Redfish thresholds"
    )
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="One or more long-format Redfish CSV files",
    )
    parser.add_argument(
        "--out",
        default="results/temperature_threshold_verdict.csv",
    )
    args = parser.parse_args()

    output = Path(args.out)
    if output.exists():
        parser.error(f"Output already exists; preserving it: {output}")

    frames = []

    for filename in args.input:
        path = Path(filename)
        if not path.is_file():
            parser.error(f"Input file not found: {path}")

        df = pd.read_csv(path)

        missing = REQUIRED - set(df.columns)
        if missing:
            parser.error(
                f"{path}: missing required columns: {sorted(missing)}"
            )

        temp = df[df["sensor_name"] == "Ambient Temp"].copy()
        if temp.empty:
            parser.error(f"{path}: no Ambient Temp records found")

        numeric_cols = [
            "reading", "lower_caution", "lower_critical",
            "upper_caution", "upper_critical",
        ]

        for col in numeric_cols:
            temp[col] = pd.to_numeric(temp[col], errors="coerce")

        temp["source_file"] = path.name
        frames.append(temp)

    result = pd.concat(frames, ignore_index=True)

    result["detector_class"] = result.apply(classify, axis=1)
    result["anomaly_flag"] = result["detector_class"].map({
        "NORMAL": 0,
        "WARNING": 1,
        "CRITICAL": 1,
        "INVALID": -1,
    }).astype(int)

    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False, mode="x")

    print("Temperature threshold detection complete")
    print("Input files:", len(args.input))
    print("Temperature observations:", len(result))
    print("\nPredicted classes:")
    print(result["detector_class"].value_counts().to_string())

    print("\nDetector class vs Redfish Health:")
    print(pd.crosstab(
        result["detector_class"],
        result["health"],
        dropna=False,
    ).to_string())

    print("\nOutput:", output)


if __name__ == "__main__":
    main()
