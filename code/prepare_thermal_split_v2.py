from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/final_experiments"


def main():
    train_path = DATA / "thermal_normal_train.csv"
    validation_path = DATA / "thermal_normal_validation.csv"
    holdout_path = DATA / "thermal_normal_holdout.csv"

    train = pd.read_csv(train_path)
    validation = pd.read_csv(validation_path)
    holdout = pd.read_csv(holdout_path)

    required = {
        "timestamp",
        "temperature_Ambient_Temp",
        "capture_id",
        "sequence_id",
    }

    for name, df in [
        ("training", train),
        ("validation", validation),
        ("holdout", holdout),
    ]:
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"{name} dataset missing: {sorted(missing)}")

    # Move the independent 25 C and 30 C normal captures
    # from training into validation.
    validation_captures = {
        "healthy_temp_25c_20261119.csv",
        "healthy_temp_30c_20261119.csv",
    }

    moved = train[train["capture_id"].isin(validation_captures)].copy()
    corrected_train = train[
        ~train["capture_id"].isin(validation_captures)
    ].copy()

    if len(moved) != 60:
        raise ValueError(
            f"Expected 60 samples from 25 C and 30 C captures; found {len(moved)}"
        )

    if set(moved["capture_id"].unique()) != validation_captures:
        raise ValueError("Expected 25 C and 30 C validation captures not found")

    # Keep the original 35 C baseline validation sequence,
    # and add the two independent normal operating-point captures.
    corrected_validation = pd.concat(
        [validation, moved],
        ignore_index=True,
    )

    # Preserve the original untouched normal holdout.
    corrected_holdout = holdout.copy()

    # Verify that no capture appears in both training and validation.
    train_captures = set(corrected_train["capture_id"].unique())
    val_captures = set(corrected_validation["capture_id"].unique())

    overlap = train_captures.intersection(val_captures)
    if overlap:
        raise ValueError(f"Capture leakage detected: {sorted(overlap)}")

    outputs = {
        "thermal_normal_train_v2.csv": corrected_train,
        "thermal_normal_validation_v2.csv": corrected_validation,
        "thermal_normal_holdout_v2.csv": corrected_holdout,
    }

    for filename, df in outputs.items():
        df.to_csv(DATA / filename, index=False)
        print(f"Saved {filename}: {len(df)} rows")

    print("\nCorrected thermal split:")
    print("Training captures:")
    print(corrected_train.groupby("capture_id").size().to_string())

    print("\nValidation captures:")
    print(corrected_validation.groupby("capture_id").size().to_string())

    print("\nHoldout captures:")
    print(corrected_holdout.groupby("capture_id").size().to_string())

    print(f"\nTraining-validation capture overlap: {len(overlap)}")
    print("\nOriginal datasets remain unchanged.")


if __name__ == "__main__":
    main()
