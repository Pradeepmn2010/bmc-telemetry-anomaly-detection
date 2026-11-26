from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/final_experiments"
RESULTS = ROOT / "results/final_experiments"
RESULTS.mkdir(parents=True, exist_ok=True)

# BMC-configured caution limits from the sensor metadata.
LIMITS = {
    "temperature_Ambient_Temp": {"lower": 5.0, "upper": 38.0},
    "voltage_ADC0_12V": {"lower": 10.8, "upper": 13.2},
    "voltage_ADC8_12V": {"lower": 10.8, "upper": 13.2},
}


def predict(df, features):
    """Return 1 if any selected sensor crosses its BMC caution limit."""
    predictions = pd.Series(0, index=df.index, dtype=int)

    for feature in features:
        if feature not in df.columns:
            raise ValueError(f"Missing required sensor feature: {feature}")

        values = pd.to_numeric(df[feature], errors="raise")
        lower = LIMITS[feature]["lower"]
        upper = LIMITS[feature]["upper"]

        predictions.loc[(values < lower) | (values > upper)] = 1

    return predictions


def evaluate(name, df, features, label_column=None):
    df = df.copy()

    if label_column is None:
        df["ground_truth"] = 0
    else:
        if label_column not in df.columns:
            raise ValueError(f"{name}: missing label column {label_column}")

        if df[label_column].isna().any():
            raise ValueError(f"{name}: missing ground-truth labels")

        df["ground_truth"] = pd.to_numeric(
            df[label_column], errors="raise"
        ).astype(int)

    if not df["ground_truth"].isin([0, 1]).all():
        raise ValueError(f"{name}: labels must be binary 0/1")

    df["prediction"] = predict(df, features)

    df["detector"] = "BMC_static_caution_threshold"
    df["experiment"] = name

    output = RESULTS / f"{name}_threshold_predictions.csv"
    df.to_csv(output, index=False)

    y = df["ground_truth"]
    p = df["prediction"]

    tp = int(((y == 1) & (p == 1)).sum())
    tn = int(((y == 0) & (p == 0)).sum())
    fp = int(((y == 0) & (p == 1)).sum())
    fn = int(((y == 1) & (p == 0)).sum())

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )
    far = fp / (fp + tn) if fp + tn else 0.0

    print(f"\n{name}")
    print("-" * 55)
    print(f"Samples:   {len(df)}")
    print(f"TP: {tp}  TN: {tn}  FP: {fp}  FN: {fn}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1-score:  {f1:.4f}")
    print(f"FAR:       {far:.4f}")
    print(f"Predictions saved: {output}")

    return {
        "experiment": name,
        "samples": len(df),
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_alarm_rate": far,
    }


def main():
    summaries = []

    # Voltage: 3-hour healthy normal holdout.
    voltage_normal = pd.read_csv(
        DATA / "voltage_normal_normal_holdout.csv"
    )
    summaries.append(
        evaluate(
           "voltage_normal_holdout",
voltage_normal,
[
    "voltage_ADC0_12V",
    "voltage_ADC8_12V",
    "temperature_Ambient_Temp",
],
None,
        )
    )

    # Voltage: controlled ADC0 sag and recovery experiment.
    voltage_fault = pd.read_csv(
        DATA / "voltage_labeled_evaluation.csv"
    )
    summaries.append(
        evaluate(
            "voltage_controlled_evaluation",
            voltage_fault,
            [
                "voltage_ADC0_12V",
                "voltage_ADC8_12V",
                "temperature_Ambient_Temp",
            ],
            "anomaly_label",
        )
    )

    # Thermal: 3-hour healthy normal holdout.
    thermal_normal = pd.read_csv(
        DATA / "thermal_normal_holdout.csv"
    )
    thermal_normal["ground_truth"] = 0
    summaries.append(
        evaluate(
            "thermal_normal_holdout",
            thermal_normal,
            ["temperature_Ambient_Temp"],
            "ground_truth",
        )
    )

    # Thermal: controlled 60 C fault and 25 C recovery.
    thermal_fault = pd.read_csv(
        DATA / "thermal_labeled_evaluation.csv"
    )
    summaries.append(
        evaluate(
            "thermal_controlled_evaluation",
            thermal_fault,
            ["temperature_Ambient_Temp"],
            "anomaly_label",
        )
    )

    summary = pd.DataFrame(summaries)
    summary_path = RESULTS / "threshold_metrics.csv"
    summary.to_csv(summary_path, index=False)

    print("\n" + "=" * 55)
    print("STATIC THRESHOLD SUMMARY")
    print("=" * 55)
    print(summary.to_string(index=False))
    print(f"\nSummary saved: {summary_path}")


if __name__ == "__main__":
    main()
