#!/usr/bin/env python3
"""
detect_threshold.py  -  Phase 4: Static-threshold baseline
Reproduces current out-of-band practice: per-sensor fixed limits. Flags any
timestamp where a sensor is out of bounds. Deliberately simple (no smoothing).

Limits are learned from the clean normal.csv (mean +/- k*std), which is a fair,
reproducible way to set them. You may instead hard-code the BMC's own
UpperCritical / LowerCritical values if you prefer a spec-based baseline.

Run:  python3 detect_threshold.py --normal data/normal.csv \
          --faulty data/faulty.csv --out results/verdict_threshold.csv
"""
import argparse
import os
import numpy as np
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normal", default="data/normal.csv")
    ap.add_argument("--faulty", default="data/faulty.csv")
    ap.add_argument("--out", default="results/verdict_threshold.csv")
    ap.add_argument("--k", type=float, default=4.0,
                    help="How many std-devs beyond normal counts as out-of-bounds")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    normal = pd.read_csv(args.normal)
    faulty = pd.read_csv(args.faulty)

    sensor_cols = [c for c in normal.columns
                   if c not in ("timestamp", "label")
                   and np.issubdtype(normal[c].dropna().dtype, np.number)]

    # derive per-sensor upper/lower limits from healthy data
    limits = {}
    for c in sensor_cols:
        mu, sd = normal[c].mean(), normal[c].std()
        limits[c] = (mu - args.k * sd, mu + args.k * sd)

    # flag any row where ANY sensor is outside its limits
    verdict = np.zeros(len(faulty), dtype=int)
    for c in sensor_cols:
        if c in faulty:
            lo, hi = limits[c]
            out = (faulty[c] < lo) | (faulty[c] > hi)
            verdict = verdict | out.fillna(False).astype(int).values

    out_df = faulty[["timestamp"]].copy()
    out_df["verdict"] = verdict
    out_df.to_csv(args.out, index=False)
    print(f"Threshold baseline: flagged {int(verdict.sum())}/{len(verdict)} rows")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
