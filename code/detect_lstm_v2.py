#!/usr/bin/env python3

from pathlib import Path
import random

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/final_experiments"
SOURCE = ROOT / "data/processed"
RESULTS = ROOT / "results/final_experiments/lstm_v2"
RESULTS.mkdir(parents=True, exist_ok=True)

SEED = 42
WINDOW = 10
EPOCHS = 40
BATCH_SIZE = 32
HIDDEN = 16
LEARNING_RATE = 0.001
VALIDATION_PERCENTILE = 99.0

DEVICE = torch.device("cpu")

CONFIGS = {
    "voltage": {
        "features": [
            "voltage_ADC0_12V",
            "voltage_ADC8_12V",
            "temperature_Ambient_Temp",
        ],
        "evaluation": "voltage_labeled_evaluation.csv",
        "holdout": "baseline_normal_holdout.csv",
    },
    "thermal": {
        "features": ["temperature_Ambient_Temp"],
        "evaluation": "thermal_labeled_evaluation.csv",
        "holdout": "thermal_normal_holdout_v3.csv",
    },
}


class BiLSTMAutoencoder(nn.Module):
    def __init__(self, n_features, hidden):
        super().__init__()

        self.encoder = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden,
            batch_first=True,
            bidirectional=True,
        )

        self.decoder = nn.LSTM(
            input_size=hidden * 2,
            hidden_size=hidden,
            batch_first=True,
            bidirectional=True,
        )

        self.output_layer = nn.Linear(hidden * 2, n_features)

    def forward(self, x):
        encoded, _ = self.encoder(x)
        decoded, _ = self.decoder(encoded)
        return self.output_layer(decoded)


def load_csv(filename, directory=DATA):
    path = directory / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")
    return pd.read_csv(path)


def prepare_frame(df, features, capture_column=None):
    df = df.copy()

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(
            df["timestamp"], utc=True, errors="coerce"
        )

    for feature in features:
        if feature not in df.columns:
            raise ValueError(f"Missing feature: {feature}")

        df[feature] = pd.to_numeric(
            df[feature], errors="raise"
        )

    if df[features].isna().any().any():
        raise ValueError("Missing values found in sensor features")

    if not np.isfinite(df[features].to_numpy(dtype=float)).all():
        raise ValueError("Non-finite sensor values found")

    if capture_column and capture_column in df.columns:
        df["capture_id"] = df[capture_column].astype(str)
    elif "capture_id" not in df.columns:
        df["capture_id"] = "single_capture"

    return df


def build_thermal_training_and_validation(features):
    baseline_train = load_csv("baseline_train.csv")
    baseline_validation = load_csv("baseline_validation.csv")

    historical = load_csv(
        "thermal_temperature_labeled_20261122.csv",
        SOURCE,
    )

    historical["timestamp"] = pd.to_datetime(
        historical["timestamp"], utc=True
    )
    historical["temperature_Ambient_Temp"] = pd.to_numeric(
        historical["reading"], errors="raise"
    )

    normal = historical[
        historical["training_role"] == "NORMAL_TRAINING_CANDIDATE"
    ].copy()

    train_parts = []
    validation_parts = []

    for temperature in [25, 30]:
        capture = normal[
            normal["operating_point_c"] == temperature
        ].sort_values("timestamp").copy()

        if len(capture) != 30:
            raise ValueError(
                f"Expected 30 normal samples at {temperature} C"
            )

        capture["capture_id"] = capture["source_file"].astype(str)

        # First 20 samples are training; last 10 are validation.
        train_parts.append(capture.iloc[:20].copy())
        validation_parts.append(capture.iloc[20:].copy())

    baseline_train = prepare_frame(baseline_train, features)
    baseline_train["capture_id"] = "healthy_baseline_train"

    baseline_validation = prepare_frame(
        baseline_validation, features
    )
    baseline_validation["capture_id"] = "healthy_baseline_validation"

    historical_train = pd.concat(train_parts, ignore_index=True)
    historical_validation = pd.concat(
        validation_parts, ignore_index=True
    )

    train = pd.concat(
        [
            baseline_train,
            historical_train[
                ["timestamp", "temperature_Ambient_Temp", "capture_id"]
            ],
        ],
        ignore_index=True,
    )

    validation = pd.concat(
        [
            baseline_validation,
            historical_validation[
                ["timestamp", "temperature_Ambient_Temp", "capture_id"]
            ],
        ],
        ignore_index=True,
    )

    return (
        prepare_frame(train, features),
        prepare_frame(validation, features),
    )


def build_voltage_training_and_validation(features):
    train = prepare_frame(
        load_csv("baseline_train.csv"), features
    )
    validation = prepare_frame(
        load_csv("baseline_validation.csv"), features
    )

    train["capture_id"] = "healthy_baseline_train"
    validation["capture_id"] = "healthy_baseline_validation"

    return train, validation


def make_windows_for_frame(df, features, scaler):
    """
    Create capture-aware sliding windows.
    Retain the original row index for every timestep in each window.
    """
    windows = []
    window_row_indices = []

    for _, group in df.groupby("capture_id", sort=False):
        if "timestamp" in group.columns:
            group = group.sort_values("timestamp")

        values = group[features].to_numpy(dtype=float)
        scaled = scaler.transform(values).astype(np.float32)
        indices = group.index.to_numpy()

        if len(scaled) < WINDOW:
            continue

        for end in range(WINDOW - 1, len(scaled)):
            start = end - WINDOW + 1
            windows.append(scaled[start:end + 1])
            window_row_indices.append(indices[start:end + 1])

    if not windows:
        return (
            np.empty((0, WINDOW, len(features)), dtype=np.float32),
            np.empty((0, WINDOW), dtype=int),
        )

    return (
        np.asarray(windows, dtype=np.float32),
        np.asarray(window_row_indices),
    )

def train_model(train, validation, features, experiment):
    # Fit scaler exclusively on normal training rows.
    scaler = MinMaxScaler()
    scaler.fit(train[features].to_numpy(dtype=float))

    train_windows, _ = make_windows_for_frame(
        train, features, scaler
    )
    validation_windows, validation_row_indices = make_windows_for_frame(
        validation, features, scaler
    )

    if len(train_windows) == 0 or len(validation_windows) == 0:
        raise ValueError("Insufficient data to create training/validation windows")

    print(f"\n{experiment.upper()} MODEL")
    print(f"Training rows: {len(train)}")
    print(f"Training windows: {len(train_windows)}")
    print(f"Validation rows: {len(validation)}")
    print(f"Validation windows: {len(validation_windows)}")
    print(f"Window length: {WINDOW}")
    print(f"Features: {features}")

    torch.manual_seed(SEED)
    np.random.seed(SEED)
    random.seed(SEED)

    model = BiLSTMAutoencoder(
        n_features=len(features),
        hidden=HIDDEN,
    ).to(DEVICE)

    optimizer = torch.optim.Adam(
        model.parameters(), lr=LEARNING_RATE
    )
    loss_function = nn.MSELoss()

    dataset = TensorDataset(torch.from_numpy(train_windows))
    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
    )

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0.0

        for (batch,) in loader:
            batch = batch.to(DEVICE)

            optimizer.zero_grad()
            reconstruction = model(batch)
            loss = loss_function(reconstruction, batch)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * len(batch)

        average_loss = total_loss / len(train_windows)

        if epoch == 0 or (epoch + 1) % 10 == 0:
            print(
                f"Epoch {epoch + 1:02d}/{EPOCHS} "
                f"loss={average_loss:.8f}"
            )

        # Calibrate using row-level errors from normal validation data.
    validation_errors = row_level_reconstruction_errors(
        model,
        validation_windows,
        validation_row_indices,
    )

    if not validation_errors:
        raise ValueError("No validation rows received reconstruction scores")

    threshold = float(
        np.percentile(
            list(validation_errors.values()),
            VALIDATION_PERCENTILE,
        )
    )

    print(
        f"Validation rows scored: {len(validation_errors)}/{len(validation)}"
    )
    print(f"Validation error threshold: {threshold:.10f}")

    return model, scaler, threshold


def row_level_reconstruction_errors(model, windows, window_row_indices):
    """
    Calculate reconstruction error for every row.
    If a row appears in multiple windows, average its errors.
    """
    model.eval()
    error_sums = {}
    error_counts = {}

    with torch.no_grad():
        for start in range(0, len(windows), BATCH_SIZE):
            batch_windows = windows[start:start + BATCH_SIZE]
            batch_indices = window_row_indices[start:start + BATCH_SIZE]

            batch = torch.from_numpy(batch_windows).to(DEVICE)
            reconstruction = model(batch)

            timestep_errors = torch.mean(
                (reconstruction - batch) ** 2,
                dim=2,
            ).cpu().numpy()

            for window_errors, row_indices in zip(
                timestep_errors, batch_indices
            ):
                for row_index, error in zip(row_indices, window_errors):
                    error_sums[row_index] = (
                        error_sums.get(row_index, 0.0) + float(error)
                    )
                    error_counts[row_index] = (
                        error_counts.get(row_index, 0) + 1
                    )

    return {
        row_index: error_sums[row_index] / error_counts[row_index]
        for row_index in error_sums
    }


def evaluate_dataset(
    experiment,
    dataset_name,
    df,
    features,
    scaler,
    model,
    threshold,
    label_column=None,
):
    df = prepare_frame(df, features)

    windows, window_row_indices = make_windows_for_frame(
        df, features, scaler
    )

    output = df.copy()
    output["lstm_reconstruction_error"] = np.nan
    output["lstm_prediction"] = -1
    output["scored"] = False

    if len(windows):
        row_errors = row_level_reconstruction_errors(
            model, windows, window_row_indices
        )

        row_indices = list(row_errors.keys())
        errors = np.array(
            [row_errors[index] for index in row_indices],
            dtype=float,
        )
        predictions = (errors > threshold).astype(int)

        output.loc[
            row_indices, "lstm_reconstruction_error"
        ] = errors

        output.loc[
            row_indices, "lstm_prediction"
        ] = predictions

        output.loc[row_indices, "scored"] = True

    if label_column is None:
        output["ground_truth"] = 0
    else:
        if label_column not in output.columns:
            raise ValueError(f"Missing label column: {label_column}")

        output["ground_truth"] = pd.to_numeric(
            output[label_column], errors="raise"
        ).astype(int)

    scored = output[output["scored"]].copy()

    if not scored.empty:
        y = scored["ground_truth"].to_numpy(dtype=int)
        pred = scored["lstm_prediction"].to_numpy(dtype=int)

        tp = int(((y == 1) & (pred == 1)).sum())
        tn = int(((y == 0) & (pred == 0)).sum())
        fp = int(((y == 0) & (pred == 1)).sum())
        fn = int(((y == 1) & (pred == 0)).sum())

        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall else 0.0
        )
        far = fp / (fp + tn) if fp + tn else 0.0
        specificity = tn / (tn + fp) if tn + fp else 0.0

    else:
        tp = tn = fp = fn = 0
        precision = recall = f1 = far = specificity = np.nan

    output["detector"] = "BiLSTM_Autoencoder"
    output["experiment"] = experiment
    output["dataset"] = dataset_name
    output["lstm_threshold"] = threshold

    filename = f"{experiment}_{dataset_name}_lstm_predictions.csv"
    output_path = RESULTS / filename
    output.to_csv(output_path, index=False)

    metrics = {
        "experiment": experiment,
        "dataset": dataset_name,
        "total_rows": len(output),
        "scored_rows": len(scored),
        "unscored_rows": len(output) - len(scored),
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_alarm_rate": far,
        "specificity": specificity,
        "threshold": threshold,
    }

    print(f"\n{dataset_name}:")
    print(pd.Series(metrics).to_string())
    print(f"Saved: {output_path}")

    return metrics


def run_experiment(experiment, config):
    features = config["features"]

    if experiment == "thermal":
        train, validation = build_thermal_training_and_validation(
            features
        )
    else:
        train, validation = build_voltage_training_and_validation(
            features
        )

    model, scaler, threshold = train_model(
        train, validation, features, experiment
    )

    holdout = load_csv(config["holdout"])
    holdout["capture_id"] = f"{experiment}_normal_holdout"

    evaluation = load_csv(config["evaluation"])

    if "source_file" in evaluation.columns:
        evaluation["capture_id"] = evaluation["source_file"].astype(str)
    else:
        evaluation["capture_id"] = f"{experiment}_evaluation"

    metrics = []

    metrics.append(
        evaluate_dataset(
            experiment,
            "normal_holdout",
            holdout,
            features,
            scaler,
            model,
            threshold,
        )
    )

    metrics.append(
        evaluate_dataset(
            experiment,
            "controlled_evaluation",
            evaluation,
            features,
            scaler,
            model,
            threshold,
            label_column="anomaly_label",
        )
    )

    return metrics


def main():
    all_metrics = []

    for experiment, config in CONFIGS.items():
        print("\n" + "=" * 65)
        print(f"STARTING {experiment.upper()} LSTM EXPERIMENT")
        print("=" * 65)

        metrics = run_experiment(experiment, config)
        all_metrics.extend(metrics)

    metrics_df = pd.DataFrame(all_metrics)
    output = RESULTS / "lstm_final_metrics.csv"
    metrics_df.to_csv(output, index=False)

    print("\n" + "=" * 65)
    print("FINAL Bi-LSTM AUTOENCODER RESULTS")
    print("=" * 65)
    print(metrics_df.to_string(index=False))
    print(f"\nMetrics saved: {output}")


if __name__ == "__main__":
    main()
