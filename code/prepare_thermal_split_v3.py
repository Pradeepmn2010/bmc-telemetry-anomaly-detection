from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/final_experiments"


def main():
    baseline_train = pd.read_csv(DATA / "baseline_train.csv")
    baseline_validation = pd.read_csv(DATA / "baseline_validation.csv")

    historical = pd.read_csv(
        ROOT / "data/processed/thermal_temperature_labeled_20261122.csv"
    )

    # Select only healthy 25 C and 30 C captures.
    normal = historical[
        historical["training_role"] == "NORMAL_TRAINING_CANDIDATE"
    ].copy()

    normal["timestamp"] = pd.to_datetime(normal["timestamp"], utc=True)
    normal["temperature_Ambient_Temp"] = pd.to_numeric(
        normal["reading"], errors="raise"
    )

    # Keep 25 C and 30 C captures separate.
    train_parts = []
    validation_parts = []

    for temperature in [25, 30]:
        capture = normal[
            normal["operating_point_c"] == temperature
        ].sort_values("timestamp").copy()

        if len(capture) != 30:
            raise ValueError(
                f"Expected 30 samples at {temperature} C; found {len(capture)}"
            )

        capture["capture_id"] = capture["source_file"]
        capture["sequence_id"] = capture["source_file"]

        # First 20 samples for training; final 10 for validation.
        train_parts.append(capture.iloc[:20].copy())
        validation_parts.append(capture.iloc[20:].copy())

    # Select 40 evenly distributed samples from the healthy 35 C baseline.
    baseline_train = baseline_train.sort_values("timestamp").reset_index(drop=True)
    selected_indices = np.linspace(
        0, len(baseline_train) - 1, 40, dtype=int
    )

    baseline_selected = baseline_train.iloc[selected_indices].copy()
    baseline_selected["capture_id"] = "healthy_baseline_train"
    baseline_selected["sequence_id"] = "healthy_baseline_train"

    # Standardize the selected historical capture columns.
    selected_columns = [
        "timestamp",
        "temperature_Ambient_Temp",
        "capture_id",
        "sequence_id",
    ]

    historical_train = pd.concat(
        train_parts, ignore_index=True
    )[selected_columns]

    historical_validation = pd.concat(
        validation_parts, ignore_index=True
    )[selected_columns]

    baseline_selected = baseline_selected[selected_columns]

    # Construct balanced normal training data.
    train_v3 = pd.concat(
        [baseline_selected, historical_train],
        ignore_index=True,
    )

    # Validation includes the original 35 C baseline plus held-out
    # portions of the independent 25 C and 30 C historical captures.
    baseline_validation = baseline_validation.copy()
    baseline_validation["capture_id"] = "healthy_baseline_validation"
    baseline_validation["sequence_id"] = "healthy_baseline_validation"

    baseline_validation = baseline_validation[selected_columns]

    validation_v3 = pd.concat(
        [baseline_validation, historical_validation],
        ignore_index=True,
    )

    # Keep the untouched normal holdout.
    holdout_v3 = pd.read_csv(
        DATA / "thermal_normal_holdout.csv"
    )

    # Add explicit dataset roles.
    train_v3["dataset_role"] = "normal_training"
    validation_v3["dataset_role"] = "normal_validation"
    holdout_v3["dataset_role"] = "normal_holdout"

    # Validate values and missing data.
    for name, frame in [
        ("training", train_v3),
        ("validation", validation_v3),
        ("holdout", holdout_v3),
    ]:
        if frame["temperature_Ambient_Temp"].isna().any():
            raise ValueError(f"Missing temperature values in {name}")

        if not set(frame["temperature_Ambient_Temp"].unique()).issubset(
            {25.0, 30.0, 35.0}
        ):
            raise ValueError(f"Unexpected temperature in {name}")

    # Save as new versioned files.
    outputs = {
        "thermal_normal_train_v3.csv": train_v3,
        "thermal_normal_validation_v3.csv": validation_v3,
        "thermal_normal_holdout_v3.csv": holdout_v3,
    }

    for filename, frame in outputs.items():
        frame.to_csv(DATA / filename, index=False)
        print(f"Saved {filename}: {len(frame)} rows")

    print("\nTraining temperature distribution:")
    print(train_v3["temperature_Ambient_Temp"].value_counts().sort_index())

    print("\nValidation temperature distribution:")
    print(validation_v3["temperature_Ambient_Temp"].value_counts().sort_index())

    print("\nTraining capture distribution:")
    print(train_v3.groupby("capture_id").size())

    print("\nValidation capture distribution:")
    print(validation_v3.groupby("capture_id").size())

    print("\nThermal split v3 preparation completed.")
    print("Original datasets and previous results remain unchanged.")


if __name__ == "__main__":
    main()
