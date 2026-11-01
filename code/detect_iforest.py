#!/usr/bin/env python3
"""
detect_iforest.py  -  Phase 5a: Isolation Forest detector
Trains an Isolation Forest on normal.csv ONLY, then scores every row of
faulty.csv. Each row is judged independently (no time context) - this is the
lightweight, CPU-friendly ML baseline.

Run:  python3 detect_iforest.py --normal data/normal.csv \
          --faulty data/faulty.csv --out results/verdict_iforest.csv
"""
import argparse
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def numeric_cols(df):
    return [c for c in df.columns
            if c not in ("timestamp", "label")
            and np.issubdtype(df[c].dropna().dtype, np.number)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normal", default="data/normal.csv")
    ap.add_argument("--faulty", default="data/faulty.csv")
    ap.add_argument("--out", default="results/verdict_iforest.csv")
    ap.add_argument("--contamination", type=float, default=0.02,
                    help="Expected fraction of anomalies (keep small)")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    normal = pd.read_csv(args.normal)
    faulty = pd.read_csv(args.faulty)
    cols = [c for c in numeric_cols(normal) if c in faulty.columns]

    # scale using ONLY normal-data statistics
    scaler = StandardScaler().fit(normal[cols].ffill().fillna(0))
    Xn = scaler.transform(normal[cols].ffill().fillna(0))
    Xf = scaler.transform(faulty[cols].ffill().fillna(0))

    model = IsolationForest(
        n_estimators=200,
        contamination=args.contamination,
        random_state=42,
    ).fit(Xn)                         # train on normal only

    pred = model.predict(Xf)          # -1 = anomaly, +1 = normal
    verdict = (pred == -1).astype(int)

    out_df = faulty[["timestamp"]].copy()
    out_df["verdict"] = verdict
    out_df.to_csv(args.out, index=False)
    print(f"Isolation Forest: flagged {int(verdict.sum())}/{len(verdict)} rows")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
