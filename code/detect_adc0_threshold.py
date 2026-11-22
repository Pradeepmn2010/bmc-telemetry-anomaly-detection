#!/usr/bin/env python3
"""ADC0-only static threshold evaluation for controlled sag experiment."""

import argparse
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/processed/dynamic_adc0_labeled_wide_20261121.csv",
    )
    parser.add_argument(
        "--out",
        default="results/adc0_threshold_verdict_20261122.csv",
    )
    parser.add_argument("--k", type=float, default=4.0)
    args = parser.parse_args()

    source = Path(args.input)
    output = Path(args.out)

    if not source.is_file():
        raise FileNotFoundError(source)
    if output.exists():
        raise FileExistsError(f"Preserving existing output: {output}")
    if args.k < 0:
        parser.error("--k must be non-negative")

    df = pd.read_csv(source)

    required = {
        "timestamp", "source_file", "phase",
        "voltage_ADC0_12V", "anomaly_label",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    df["voltage_ADC0_12V"] = pd.to_numeric(
        df["voltage_ADC0_12V"], errors="coerce"
    )
    df["anomaly_label"] = pd.to_numeric(
        df["anomaly_label"], errors="coerce"
    )

    if df[["voltage_ADC0_12V", "anomaly_label"]].isna().any().any():
        raise ValueError("Invalid ADC0 readings or labels")
    if not df["anomaly_label"].isin([0, 1]).all():
        raise ValueError("Labels must be binary")

    normal = df[df["anomaly_label"] == 0]
    if normal.empty:
        raise ValueError("No normal samples")

    mean = normal["voltage_ADC0_12V"].mean()
    std = normal["voltage_ADC0_12V"].std()
    lower = mean - args.k * std
    upper = mean + args.k * std

    result = df[
        ["timestamp", "source_file", "phase",
         "anomaly_label", "voltage_ADC0_12V"]
    ].copy()

    result.rename(
        columns={
            "anomaly_label": "ground_truth",
            "voltage_ADC0_12V": "adc0_voltage",
        },
        inplace=True,
    )

    result["threshold_lower"] = lower
    result["threshold_upper"] = upper
    result["verdict"] = (
        (result["adc0_voltage"] < lower)
        | (result["adc0_voltage"] > upper)
    ).astype(int)

    truth = result["ground_truth"].to_numpy(dtype=int)
    verdict = result["verdict"].to_numpy(dtype=int)

    tp = int(((truth == 1) & (verdict == 1)).sum())
    fp = int(((truth == 0) & (verdict == 1)).sum())
    fn = int(((truth == 1) & (verdict == 0)).sum())
    tn = int(((truth == 0) & (verdict == 0)).sum())

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )
    far = fp / (fp + tn) if fp + tn else 0.0

    print("===== ADC0 STATIC THRESHOLD BASELINE =====")
    print(f"Input rows: {len(df)}")
    print(f"Normal fitting rows: {len(normal)}")
    print(f"Mean: {mean:.6f} V")
    print(f"Standard deviation: {std:.6f} V")
    print(f"k: {args.k}")
    print(f"Lower threshold: {lower:.6f} V")
    print(f"Upper threshold: {upper:.6f} V")

    print("\n===== CONFUSION COUNTS =====")
    print(f"TP={tp}, FP={fp}, FN={fn}, TN={tn}")

    print("\n===== METRICS =====")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1: {f1:.4f}")
    print(f"False-alarm rate: {far:.4f}")

    print("\n===== RESULTS BY PHASE =====")
    summary = result.groupby("phase", sort=False).agg(
        samples=("verdict", "size"),
        actual_anomalies=("ground_truth", "sum"),
        detected=("verdict", "sum"),
        adc0_mean_v=("adc0_voltage", "mean"),
    )
    print(summary.to_string())

    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    print(f"\nOutput written to: {output}")


if __name__ == "__main__":
    main()
