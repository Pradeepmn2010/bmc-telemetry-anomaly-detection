from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/final_experiments"
RESULTS = ROOT / "results/final_experiments"
RESULTS.mkdir(parents=True, exist_ok=True)

CONFIGS = {
    "voltage": {
        "features": [
            "voltage_ADC0_12V",
            "voltage_ADC8_12V",
            "temperature_Ambient_Temp",
        ],
        "train": "voltage_normal_train.csv",
        "validation": "voltage_normal_validation.csv",
        "holdout": "voltage_normal_normal_holdout.csv",
        "evaluation": "voltage_labeled_evaluation.csv",
        "label": "anomaly_label",
    },
    "thermal": {
    "features": ["temperature_Ambient_Temp"],
    "train": "thermal_normal_train_v3.csv",
    "validation": "thermal_normal_validation_v3.csv",
    "holdout": "thermal_normal_holdout_v3.csv",
    "evaluation": "thermal_labeled_evaluation.csv",
    "label": "anomaly_label",
},
}

RANDOM_STATE = 42
N_ESTIMATORS = 200
VALIDATION_QUANTILE = 0.01


def load_data(filename):
    path = DATA / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing dataset: {path}")
    return pd.read_csv(path)


def get_features(df, feature_names):
    missing = set(feature_names) - set(df.columns)
    if missing:
        raise ValueError(f"Missing features: {sorted(missing)}")

    values = df[feature_names].apply(
        pd.to_numeric, errors="raise"
    )

    if values.isna().any().any():
        raise ValueError("Missing values found in model features")

    if not np.isfinite(values.to_numpy()).all():
        raise ValueError("Non-finite values found in model features")

    return values.to_numpy(dtype=float)


def calculate_metrics(y_true, y_pred):
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )
    far = fp / (fp + tn) if fp + tn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0

    return {
        "samples": len(y_true),
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_alarm_rate": far,
        "specificity": specificity,
    }


def save_predictions(name, df, scores, threshold, predictions):
    output = df.copy()
    output["iforest_anomaly_score"] = scores
    output["iforest_threshold"] = threshold
    output["iforest_prediction"] = predictions
    output["detector"] = "IsolationForest"

    path = RESULTS / f"{name}_iforest_predictions.csv"
    output.to_csv(path, index=False)

    print(f"Saved predictions: {path}")


def run_experiment(experiment_name, config):
    print("\n" + "=" * 65)
    print(f"ISOLATION FOREST — {experiment_name.upper()}")
    print("=" * 65)

    train = load_data(config["train"])
    validation = load_data(config["validation"])
    holdout = load_data(config["holdout"])
    evaluation = load_data(config["evaluation"])

    features = config["features"]

    # Fit scaler using training data only.
    x_train = get_features(train, features)
    x_validation = get_features(validation, features)
    x_holdout = get_features(holdout, features)
    x_evaluation = get_features(evaluation, features)

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_validation_scaled = scaler.transform(x_validation)
    x_holdout_scaled = scaler.transform(x_holdout)
    x_evaluation_scaled = scaler.transform(x_evaluation)

    # Fit Isolation Forest using normal training samples only.
    model = IsolationForest(
        n_estimators=N_ESTIMATORS,
        contamination="auto",
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    model.fit(x_train_scaled)

    # score_samples: lower values indicate more anomalous samples.
    validation_scores = model.score_samples(x_validation_scaled)

    # Calibrate threshold on normal validation scores.
    threshold = float(
        np.quantile(validation_scores, VALIDATION_QUANTILE)
    )

    print(f"Training samples: {len(train)}")
    print(f"Validation samples: {len(validation)}")
    print(f"Training features: {features}")
    print(f"Validation quantile: {VALIDATION_QUANTILE}")
    print(f"Calibrated anomaly threshold: {threshold:.8f}")

    summary = []

    # Evaluate normal holdout.
    holdout_scores = model.score_samples(x_holdout_scaled)
    holdout_predictions = (
        holdout_scores < threshold
    ).astype(int)

    holdout["ground_truth"] = 0
    save_predictions(
        f"{experiment_name}_normal_holdout",
        holdout,
        holdout_scores,
        threshold,
        holdout_predictions,
    )

    holdout_metrics = calculate_metrics(
        holdout["ground_truth"].to_numpy(),
        holdout_predictions,
    )
    holdout_metrics["experiment"] = experiment_name
    holdout_metrics["dataset"] = "normal_holdout"
    summary.append(holdout_metrics)

    # Evaluate controlled labelled samples.
    if config["label"] not in evaluation.columns:
        raise ValueError(
            f"Missing evaluation label: {config['label']}"
        )

    y_true = pd.to_numeric(
        evaluation[config["label"]], errors="raise"
    ).to_numpy(dtype=int)

    if not np.isin(y_true, [0, 1]).all():
        raise ValueError("Evaluation labels must be binary")

    evaluation_scores = model.score_samples(x_evaluation_scaled)
    evaluation_predictions = (
        evaluation_scores < threshold
    ).astype(int)

    save_predictions(
        f"{experiment_name}_controlled_evaluation",
        evaluation,
        evaluation_scores,
        threshold,
        evaluation_predictions,
    )

    evaluation_metrics = calculate_metrics(
        y_true,
        evaluation_predictions,
    )
    evaluation_metrics["experiment"] = experiment_name
    evaluation_metrics["dataset"] = "controlled_evaluation"
    summary.append(evaluation_metrics)

    print("\nNormal holdout metrics:")
    print(pd.Series(holdout_metrics).to_string())

    print("\nControlled evaluation metrics:")
    print(pd.Series(evaluation_metrics).to_string())

    # Record useful model diagnostics.
    diagnostics = {
        "experiment": experiment_name,
        "training_samples": len(train),
        "validation_samples": len(validation),
        "validation_quantile": VALIDATION_QUANTILE,
        "threshold": threshold,
        "training_feature_count": len(features),
        "training_feature_names": ",".join(features),
    }

    return summary, diagnostics


def main():
    all_metrics = []
    all_diagnostics = []

    for experiment_name, config in CONFIGS.items():
        metrics, diagnostics = run_experiment(
            experiment_name, config
        )
        all_metrics.extend(metrics)
        all_diagnostics.append(diagnostics)

    metrics_df = pd.DataFrame(all_metrics)
    diagnostics_df = pd.DataFrame(all_diagnostics)

    metrics_path = RESULTS / "iforest_metrics.csv"
    diagnostics_path = RESULTS / "iforest_diagnostics.csv"

    metrics_df.to_csv(metrics_path, index=False)
    diagnostics_df.to_csv(diagnostics_path, index=False)

    print("\n" + "=" * 65)
    print("ISOLATION FOREST SUMMARY")
    print("=" * 65)
    print(metrics_df.to_string(index=False))
    print(f"\nMetrics saved: {metrics_path}")
    print(f"Diagnostics saved: {diagnostics_path}")


if __name__ == "__main__":
    main()
