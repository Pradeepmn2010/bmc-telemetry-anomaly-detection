#!/usr/bin/env python3
"""
detect_lstm.py  -  Phase 5b: LSTM / Bi-LSTM reconstruction autoencoder
Trains a small LSTM autoencoder to RECONSTRUCT normal telemetry windows.
Trained on normal.csv ONLY. On faulty.csv, windows it reconstructs badly
(high error) are flagged. The error threshold is taken from a high percentile
of reconstruction error on NORMAL data - never from the fault labels.

Keep the network small: CPU-only, modest data.

Run:  python3 detect_lstm.py --normal data/normal.csv \
          --faulty data/faulty.csv --out results/verdict_lstm.csv
"""
import argparse
import os
import numpy as np
import pandas as pd

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

WINDOW = 30          # readings per window
EPOCHS = 20
BATCH = 64
HIDDEN = 32
LR = 1e-3


def numeric_cols(df):
    return [c for c in df.columns
            if c not in ("timestamp", "label")
            and np.issubdtype(df[c].dropna().dtype, np.number)]


def make_windows(X, w):
    """Turn a (rows, features) array into (num_windows, w, features)."""
    return np.stack([X[i:i + w] for i in range(len(X) - w + 1)])


class LSTMAutoencoder(nn.Module):
    def __init__(self, n_features, hidden, bidirectional=True):
        super().__init__()
        self.encoder = nn.LSTM(n_features, hidden, batch_first=True,
                               bidirectional=bidirectional)
        enc_out = hidden * (2 if bidirectional else 1)
        self.decoder = nn.LSTM(enc_out, hidden, batch_first=True,
                               bidirectional=bidirectional)
        self.out = nn.Linear(hidden * (2 if bidirectional else 1), n_features)

    def forward(self, x):
        z, _ = self.encoder(x)
        d, _ = self.decoder(z)
        return self.out(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normal", default="data/normal.csv")
    ap.add_argument("--faulty", default="data/faulty.csv")
    ap.add_argument("--out", default="results/verdict_lstm.csv")
    ap.add_argument("--percentile", type=float, default=99.0,
                    help="Error percentile on NORMAL data used as the threshold")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    torch.manual_seed(42)
    np.random.seed(42)

    normal = pd.read_csv(args.normal)
    faulty = pd.read_csv(args.faulty)
    cols = [c for c in numeric_cols(normal) if c in faulty.columns]

    # normalize using normal-data min/max
    nmin = normal[cols].min()
    nrng = (normal[cols].max() - nmin).replace(0, 1.0)
    Xn = ((normal[cols] - nmin) / nrng).fillna(0).values.astype(np.float32)
    Xf = ((faulty[cols] - nmin) / nrng).fillna(0).values.astype(np.float32)

    Wn = make_windows(Xn, WINDOW)
    Wf = make_windows(Xf, WINDOW)

    model = LSTMAutoencoder(len(cols), HIDDEN)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loss_fn = nn.MSELoss()

    loader = DataLoader(TensorDataset(torch.from_numpy(Wn)),
                        batch_size=BATCH, shuffle=True)

    model.train()
    for ep in range(EPOCHS):
        total = 0.0
        for (batch,) in loader:
            opt.zero_grad()
            recon = model(batch)
            loss = loss_fn(recon, batch)
            loss.backward()
            opt.step()
            total += loss.item() * len(batch)
        print(f"  epoch {ep+1:2d}/{EPOCHS}  loss={total/len(Wn):.5f}")

    # per-window reconstruction error
    model.eval()
    with torch.no_grad():
        err_n = ((model(torch.from_numpy(Wn)) - torch.from_numpy(Wn)) ** 2
                 ).mean(dim=(1, 2)).numpy()
        err_f = ((model(torch.from_numpy(Wf)) - torch.from_numpy(Wf)) ** 2
                 ).mean(dim=(1, 2)).numpy()

    threshold = np.percentile(err_n, args.percentile)   # from NORMAL only

    # map each window verdict back to its last row; pad the first WINDOW-1 rows
    win_verdict = (err_f > threshold).astype(int)
    verdict = np.zeros(len(faulty), dtype=int)
    verdict[WINDOW - 1:] = win_verdict

    out_df = faulty[["timestamp"]].copy()
    out_df["verdict"] = verdict
    out_df.to_csv(args.out, index=False)
    print(f"LSTM AE: threshold={threshold:.5f}, "
          f"flagged {int(verdict.sum())}/{len(verdict)} rows")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
