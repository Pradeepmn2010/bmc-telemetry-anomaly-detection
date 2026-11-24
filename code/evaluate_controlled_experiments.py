#!/usr/bin/env python3
"""Leakage-aware, source-file-aligned evaluation of controlled experiments."""

from pathlib import Path
import pandas as pd


EXPERIMENTS = [
    {
        "name": "ADC0 controlled voltage sag",
        "processed": "data/processed/dynamic_adc0_labeled_wide_20261121.csv",
        "verdict": "results/adc0_threshold_verdict_20261122.csv",
        "truth_col": "anomaly_label",
        "prediction_col": "verdict",
        "phase_col": "phase",
        "independent_test": "NO - normal fitting samples are included",
        "limitation": (
            "Zero normal standard deviation; exact 12 V comparison. "
            "Normal fitting samples are reused in evaluation."
        ),
    },
    {
        "name": "Thermal controlled fault",
        "processed": "data/processed/thermal_temperature_labeled_20261122.csv",
        "verdict": "results/temperature_threshold_verification_20261122.csv",
        "truth_col": "anomaly_label",
        "prediction_col": "anomaly_flag",
        "phase_col": "phase",
        "independent_test": "CONTROLLED SOURCE-FILE EVALUATION",
        "limitation": (
            "Fixed emulator operating points; does not establish "
            "generalization to unseen hardware or natural workloads."
        ),
    },
]

METRICS_OUT = Path("results/controlled_experiment_metrics_20261124.csv")
PHASE_OUT = Path("results/controlled_experiment_phase_summary_20261124.csv")


def load_and_validate(config):
    processed = pd.read_csv(config["processed"])
    verdict = pd.read_csv(config["verdict"])

    required_p = {"source_file", config["truth_col"], config["phase_col"]}
    required_v = {"source_file", config["prediction_col"]}

    if not required_p.issubset(processed.columns):
        raise ValueError(f"Processed columns missing: {required_p - set(processed.columns)}")
    if not required_v.issubset(verdict.columns):
        raise ValueError(f"Verdict columns missing: {required_v - set(verdict.columns)}")

    if processed.empty or verdict.empty:
        raise ValueError("Empty input dataset")

    if processed["source_file"].isna().any() or verdict["source_file"].isna().any():
        raise ValueError("Missing source_file values")

    p_counts = processed.groupby("source_file").size().sort_index()
    v_counts = verdict.groupby("source_file").size().sort_index()

    if not p_counts.equals(v_counts):
        raise ValueError("Source-file sample counts do not match")

    if set(processed["source_file"]) != set(verdict["source_file"]):
        raise ValueError("Source-file sets do not match")

    truth = pd.to_numeric(processed[config["truth_col"]], errors="coerce")
    pred = pd.to_numeric(verdict[config["prediction_col"]], errors="coerce")

    if truth.isna().any() or pred.isna().any():
        raise ValueError("Missing or non-numeric labels")
    if not truth.isin([0, 1]).all() or not pred.isin([0, 1]).all():
        raise ValueError("Labels must be binary 0/1")

    processed = processed.copy()
    verdict = verdict.copy()
    processed["_truth"] = truth.astype(int)
    verdict["_prediction"] = pred.astype(int)

    phase_rows = []

    for source in sorted(p_counts.index):
        p_group = processed[processed["source_file"] == source]
        v_group = verdict[verdict["source_file"] == source]

        if p_group["_truth"].nunique() != 1:
            raise ValueError(f"Mixed ground truth in {source}")
        if v_group["_prediction"].nunique() != 1:
            raise ValueError(f"Mixed predictions in {source}")

        actual = int(p_group["_truth"].iloc[0])
        predicted = int(v_group["_prediction"].iloc[0])

        phases = p_group[config["phase_col"]].dropna().unique()
        phase = str(phases[0]) if len(phases) == 1 else str(source)

        phase_rows.append({
            "experiment": config["name"],
            "source_file": source,
            "phase": phase,
            "samples": len(p_group),
            "actual_label": actual,
            "predicted_label": predicted,
            "correct_samples": len(p_group) if actual == predicted else 0,
            "incorrect_samples": 0 if actual == predicted else len(p_group),
        })

    phase_df = pd.DataFrame(phase_rows)

    # Calculate sample-level counts from validated source-file groups.
    tn = int(((phase_df.actual_label == 0) &
              (phase_df.predicted_label == 0)) @ phase_df.samples)
    fp = int(((phase_df.actual_label == 0) &
              (phase_df.predicted_label == 1)) @ phase_df.samples)
    fn = int(((phase_df.actual_label == 1) &
              (phase_df.predicted_label == 0)) @ phase_df.samples)
    tp = int(((phase_df.actual_label == 1) &
              (phase_df.predicted_label == 1)) @ phase_df.samples)

    total = tn + fp + fn + tp
    accuracy = (tn + tp) / total
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )
    far = fp / (fp + tn) if fp + tn else 0.0

    metrics = {
        "experiment": config["name"],
        "samples": total,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "TP": tp,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "F1": f1,
        "false_alarm_rate": far,
        "independent_test_status": config["independent_test"],
        "limitations": config["limitation"],
    }

    return metrics, phase_df


def main():
    for path in (METRICS_OUT, PHASE_OUT):
        if path.exists():
            raise FileExistsError(f"Preserving existing output: {path}")

    metrics_rows = []
    phase_frames = []

    for config in EXPERIMENTS:
        metrics, phases = load_and_validate(config)
        metrics_rows.append(metrics)
        phase_frames.append(phases)

    metrics_df = pd.DataFrame(metrics_rows)
    phase_df = pd.concat(phase_frames, ignore_index=True)

    METRICS_OUT.parent.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(METRICS_OUT, index=False)
    phase_df.to_csv(PHASE_OUT, index=False)

    print("===== CONTROLLED EXPERIMENT METRICS =====")
    print(metrics_df[
        ["experiment", "samples", "TN", "FP", "FN", "TP",
         "accuracy", "precision", "recall", "F1", "false_alarm_rate"]
    ].to_string(index=False))

    print("\n===== SOURCE-FILE RESULTS =====")
    print(phase_df.to_string(index=False))

    print(f"\nSaved: {METRICS_OUT}")
    print(f"Saved: {PHASE_OUT}")
    print("\nExperiments evaluated separately; no pooled metric calculated.")


if __name__ == "__main__":
    main()
