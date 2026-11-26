from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results" / "final_experiments"
OUTPUT = ROOT / "results" / "final_comparison"
OUTPUT.mkdir(parents=True, exist_ok=True)

EXPERIMENTS = [
    {
        "scenario": "Voltage",
        "dataset": "Normal holdout",
        "detector": "Static Threshold",
        "file": "voltage_normal_holdout_threshold_predictions.csv",
        "truth": "ground_truth",
        "prediction": "prediction",
    },
    {
        "scenario": "Voltage",
        "dataset": "Normal holdout",
        "detector": "Isolation Forest",
        "file": "voltage_normal_holdout_iforest_predictions.csv",
        "truth": "ground_truth",
        "prediction": "iforest_prediction",
    },
    {
        "scenario": "Voltage",
        "dataset": "Normal holdout",
        "detector": "Bi-LSTM v2",
        "file": "lstm_v2/voltage_normal_holdout_lstm_predictions.csv",
        "truth": "ground_truth",
        "prediction": "lstm_prediction",
    },
    {
        "scenario": "Voltage",
        "dataset": "Controlled evaluation",
        "detector": "Static Threshold",
        "file": "voltage_controlled_evaluation_threshold_predictions.csv",
        "truth": "ground_truth",
        "prediction": "prediction",
    },
    {
        "scenario": "Voltage",
        "dataset": "Controlled evaluation",
        "detector": "Isolation Forest",
        "file": "voltage_controlled_evaluation_iforest_predictions.csv",
        "truth": "anomaly_label",
        "prediction": "iforest_prediction",
    },
    {
        "scenario": "Voltage",
        "dataset": "Controlled evaluation",
        "detector": "Bi-LSTM v2",
        "file": "lstm_v2/voltage_controlled_evaluation_lstm_predictions.csv",
        "truth": "ground_truth",
        "prediction": "lstm_prediction",
    },
    {
        "scenario": "Thermal",
        "dataset": "Normal holdout",
        "detector": "Static Threshold",
        "file": "thermal_normal_holdout_threshold_predictions.csv",
        "truth": "ground_truth",
        "prediction": "prediction",
    },
    {
        "scenario": "Thermal",
        "dataset": "Normal holdout",
        "detector": "Isolation Forest",
        "file": "thermal_v3_normal_holdout_iforest_predictions.csv",
        "truth": "ground_truth",
        "prediction": "iforest_prediction",
    },
    {
        "scenario": "Thermal",
        "dataset": "Normal holdout",
        "detector": "Bi-LSTM v2",
        "file": "lstm_v2/thermal_normal_holdout_lstm_predictions.csv",
        "truth": "ground_truth",
        "prediction": "lstm_prediction",
    },
    {
        "scenario": "Thermal",
        "dataset": "Controlled evaluation",
        "detector": "Static Threshold",
        "file": "thermal_controlled_evaluation_threshold_predictions.csv",
        "truth": "ground_truth",
        "prediction": "prediction",
    },
    {
        "scenario": "Thermal",
        "dataset": "Controlled evaluation",
        "detector": "Isolation Forest",
        "file": "thermal_v3_controlled_evaluation_iforest_predictions.csv",
        "truth": "anomaly_label",
        "prediction": "iforest_prediction",
    },
    {
        "scenario": "Thermal",
        "dataset": "Controlled evaluation",
        "detector": "Bi-LSTM v2",
        "file": "lstm_v2/thermal_controlled_evaluation_lstm_predictions.csv",
        "truth": "ground_truth",
        "prediction": "lstm_prediction",
    },
]


def calculate_metrics(y_true, y_pred, coverage):
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)

    if not np.isin(y_true, [0, 1]).all():
        raise ValueError("Ground truth must contain only 0 and 1.")
    if not np.isin(y_pred, [0, 1]).all():
        raise ValueError("Predictions must contain only 0 and 1.")

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    precision = tp / (tp + fp) if tp + fp else np.nan
    recall = tp / (tp + fn) if tp + fn else np.nan
    f1 = (
        2 * precision * recall / (precision + recall)
        if np.isfinite(precision) and np.isfinite(recall)
        and precision + recall > 0
        else (0.0 if np.isfinite(precision) and np.isfinite(recall) else np.nan)
    )

    normal_count = tn + fp
    far = fp / normal_count if normal_count else np.nan
    specificity = tn / normal_count if normal_count else np.nan

    return {
        "samples": len(y_true),
        "scored_samples": int(coverage),
        "unscored_samples": len(y_true) - int(coverage),
        "coverage_percent": 100 * coverage / len(y_true) if len(y_true) else np.nan,
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "precision": precision,
        "recall": recall,
        "F1": f1,
        "false_alarm_rate": far,
        "specificity": specificity,
    }


results = []

for exp in EXPERIMENTS:
    path = INPUT / exp["file"]
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")

    df = pd.read_csv(path)

    required = [exp["truth"], exp["prediction"]]
    for column in required:
        if column not in df.columns:
            raise ValueError(f"{path.name} is missing column {column}")

    if "scored" in df.columns:
        scored_mask = df["scored"].fillna(False).astype(bool)
    else:
        scored_mask = pd.Series(True, index=df.index)

    scored_df = df.loc[scored_mask].copy()

    if scored_df.empty:
        raise ValueError(f"No scored samples in {path.name}")

    if scored_df[required].isna().any().any():
        raise ValueError(f"Missing labels or predictions in {path.name}")

    metrics = calculate_metrics(
        scored_df[exp["truth"]],
        scored_df[exp["prediction"]],
        len(scored_df),
    )

    results.append({
        "scenario": exp["scenario"],
        "dataset": exp["dataset"],
        "detector": exp["detector"],
        "source_file": exp["file"],
        **metrics,
    })

comparison = pd.DataFrame(results)

output_file = OUTPUT / "detector_comparison_metrics.csv"
comparison.to_csv(output_file, index=False)

print("\nCOMPARATIVE DETECTOR EVALUATION")
print("=" * 100)
print(comparison.to_string(index=False))
print("\nSaved:", output_file.relative_to(ROOT))
print("\nInput prediction files were not modified.")
