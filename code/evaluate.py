#!/usr/bin/env python3
"""
evaluate.py  -  Phase 6: Evaluation & comparison
Compares all three detector verdicts against the ground-truth labels and
computes Precision, Recall, F1, detection latency and false-alarm rate.
Also draws the key figures.

Run:  python3 evaluate.py --faulty data/faulty.csv --labels data/labels.csv \
          --threshold results/verdict_threshold.csv \
          --iforest   results/verdict_iforest.csv \
          --lstm      results/verdict_lstm.csv \
          --outdir results
"""
import argparse
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def metrics(truth, verdict):
    tp = int(((verdict == 1) & (truth == 1)).sum())
    fp = int(((verdict == 1) & (truth == 0)).sum())
    fn = int(((verdict == 0) & (truth == 1)).sum())
    tn = int(((verdict == 0) & (truth == 0)).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    far = fp / (fp + tn) if (fp + tn) else 0.0
    return dict(TP=tp, FP=fp, FN=fn, TN=tn,
                Precision=round(precision, 3), Recall=round(recall, 3),
                F1=round(f1, 3), FalseAlarmRate=round(far, 3))


def latencies(labels, verdict):
    """Average detection latency (rows) from each fault's start to first alert."""
    lats = []
    for _, ep in labels.iterrows():
        s, e = int(ep["start_row"]), int(ep["end_row"])
        fired = np.where(verdict[s:e] == 1)[0]
        lats.append(int(fired[0]) if len(fired) else (e - s))  # miss = full length
    return round(float(np.mean(lats)), 2) if lats else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--faulty", default="data/faulty.csv")
    ap.add_argument("--labels", default="data/labels.csv")
    ap.add_argument("--threshold", default="results/verdict_threshold.csv")
    ap.add_argument("--iforest", default="results/verdict_iforest.csv")
    ap.add_argument("--lstm", default="results/verdict_lstm.csv")
    ap.add_argument("--outdir", default="results")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    faulty = pd.read_csv(args.faulty)
    labels = pd.read_csv(args.labels)
    truth = faulty["label"].values

    detectors = {
        "Threshold": pd.read_csv(args.threshold)["verdict"].values,
        "IsolationForest": pd.read_csv(args.iforest)["verdict"].values,
        "LSTM_AE": pd.read_csv(args.lstm)["verdict"].values,
    }

    rows = []
    for name, v in detectors.items():
        m = metrics(truth, v)
        m["Detector"] = name
        m["AvgLatency_rows"] = latencies(labels, v)
        rows.append(m)

    table = pd.DataFrame(rows).set_index("Detector")[
        ["Precision", "Recall", "F1", "FalseAlarmRate", "AvgLatency_rows",
         "TP", "FP", "FN", "TN"]]
    table.to_csv(os.path.join(args.outdir, "comparison.csv"))
    print("\n=== Detector comparison ===")
    print(table.to_string())

    # ---- Figure 1: F1 bar chart ----
    plt.figure(figsize=(6, 4))
    table["F1"].plot(kind="bar", color=["#8899aa", "#3d78b0", "#0b6e99"])
    plt.ylabel("F1-score"); plt.title("Detector F1 comparison")
    plt.ylim(0, 1); plt.xticks(rotation=0); plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "fig_f1.png"), dpi=120)
    plt.close()

    # ---- Figure 2: timeline with fault windows shaded ----
    num = [c for c in faulty.columns if c not in ("timestamp", "label")]
    show = num[:3]  # first few sensors
    fig, ax = plt.subplots(figsize=(10, 4))
    for c in show:
        ax.plot(faulty[c].values, label=c, linewidth=0.8)
    for _, ep in labels.iterrows():
        ax.axvspan(int(ep["start_row"]), int(ep["end_row"]),
                   color="red", alpha=0.12)
    ax.set_title("Telemetry with injected fault windows (shaded)")
    ax.set_xlabel("row"); ax.legend(loc="upper right", fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "fig_timeline.png"), dpi=120)
    plt.close()

    print(f"\nWrote comparison.csv, fig_f1.png, fig_timeline.png to {args.outdir}/")


if __name__ == "__main__":
    main()
