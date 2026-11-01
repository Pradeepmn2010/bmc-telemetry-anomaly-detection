#!/usr/bin/env python3
"""
inject_faults.py  -  Phase 3: Fault injection
Reads data/normal.csv, paints the four fault types onto chosen time windows,
and writes data/faulty.csv plus data/labels.csv (the ground-truth answer key).

Option B approach: faults are injected at the telemetry (data) layer, not inside
the emulator. Each injected episode is logged to labels.csv in the same step.

Run:  python3 inject_faults.py --in data/normal.csv \
          --out data/faulty.csv --labels data/labels.csv
"""
import argparse
import numpy as np
import pandas as pd


# ---- CONFIGURE THESE to match YOUR sensor column names in normal.csv ----
# Open data/normal.csv, look at the header, and set the names below.
TEMP_COL    = "Total_Power"     # e.g. a temperature column -> will ramp up
FAN_COL     = "fan0"            # a fan RPM column           -> will drop
VOLTAGE_COL = "p12v"           # a voltage rail column      -> will sag
STUCK_COL   = "fan1"            # any column                 -> will freeze
# -------------------------------------------------------------------------


def pick_windows(n, k, length, rng, gap):
    """Choose k non-overlapping [start,end) windows of `length` rows within n rows."""
    windows, cursor = [], gap
    step = (n - 2 * gap) // max(k, 1)
    for i in range(k):
        start = cursor + i * step + rng.integers(0, max(step - length - gap, 1))
        end = min(start + length, n - gap)
        if end - start >= length // 2:
            windows.append((int(start), int(end)))
    return windows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/normal.csv")
    ap.add_argument("--out", default="data/faulty.csv")
    ap.add_argument("--labels", default="data/labels.csv")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    df = pd.read_csv(args.inp)
    n = len(df)
    if n < 200:
        print("Warning: very short normal.csv; capture more data for meaningful results.")

    # start with an all-normal label column
    df["label"] = 0          # 0 = normal, 1 = anomaly
    labels = []              # episode-level ground truth

    def log(fault, col, s, e):
        df.loc[s:e-1, "label"] = 1
        labels.append({
            "fault_type": fault, "sensor": col,
            "start_row": s, "end_row": e,
            "start_time": df.iloc[s]["timestamp"],
            "end_time": df.iloc[e-1]["timestamp"],
        })

    L = max(20, n // 40)     # episode length ~ a few % of the series

    # 1) THERMAL RUNAWAY - steady upward ramp on a temperature column
    for (s, e) in pick_windows(n, 2, L, rng, gap=L):
        if TEMP_COL in df:
            ramp = np.linspace(0, df[TEMP_COL].std() * 4 + 5, e - s)
            df.loc[s:e-1, TEMP_COL] = df.loc[s:e-1, TEMP_COL].values + ramp
            log("thermal_runaway", TEMP_COL, s, e)

    # 2) FAN FAILURE - RPM collapses toward zero
    for (s, e) in pick_windows(n, 2, L, rng, gap=L):
        if FAN_COL in df:
            df.loc[s:e-1, FAN_COL] = df.loc[s:e-1, FAN_COL].values * \
                np.linspace(1.0, 0.02, e - s)
            log("fan_failure", FAN_COL, s, e)

    # 3) VOLTAGE SAG - small dip that stays within 'legal' limits (subtle)
    for (s, e) in pick_windows(n, 2, L, rng, gap=L):
        if VOLTAGE_COL in df:
            df.loc[s:e-1, VOLTAGE_COL] = df.loc[s:e-1, VOLTAGE_COL].values * 0.96
            log("voltage_sag", VOLTAGE_COL, s, e)

    # 4) STUCK SENSOR - frozen at a plausible constant while others move
    for (s, e) in pick_windows(n, 2, L, rng, gap=L):
        if STUCK_COL in df:
            frozen = df.iloc[s][STUCK_COL]
            df.loc[s:e-1, STUCK_COL] = frozen
            log("stuck_sensor", STUCK_COL, s, e)

    df.to_csv(args.out, index=False)
    pd.DataFrame(labels).to_csv(args.labels, index=False)
    anom = int(df["label"].sum())
    print(f"Wrote {args.out}  ({n} rows, {anom} anomalous = {100*anom/n:.1f}%)")
    print(f"Wrote {args.labels}  ({len(labels)} fault episodes)")


if __name__ == "__main__":
    main()
