#!/usr/bin/env python
"""E15 -- utilidade de priorizacao (ranking) por minggu (POST HOC, deskriptif; tidak melatih apa pun). Skor risiko dipakai untuk memprioritaskan aset; yang penting adalah urutan dalam satu minggu, bukan MSE.
Untuk tiap minggu dengan >= --min-assets aset: korelasi Spearman antara skor dan label, dan presisi@k (k = --top dari aset; 'berisiko' = label >= kuantil 1-top minggu itu; ikatan skor dipecah acak berseed).
Metode: rumus bentuk-maks, HANFIS, persistence. Selisih berpasangan (rumus-persistence, HANFIS-persistence, rumus-HANFIS) pada rerata mingguan, CI95 dengan bootstrap per MINGGU (kluster minggu, lebih konservatif daripada per image).
Memakai berkas prediksi out-of-fold E11 (event_id, y_true, y_maxform, y_pers, y_full) untuk tiga horizon.  python scripts/e15_ranking.py"""
import argparse, glob, sys
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--h30", default="results_python/e11/e11_predictions_*.csv"); ap.add_argument("--h58", default="results_python/e14_h58_e11/e11_predictions_*.csv"); ap.add_argument("--h86", default="results_python/e14_h86_e11/e11_predictions_*.csv")
ap.add_argument("--min-assets", type=int, default=15); ap.add_argument("--top", type=float, default=0.20); ap.add_argument("--boot", type=int, default=2000); ap.add_argument("--seed", type=int, default=20261012)
ap.add_argument("--out-dir", default="results_python/e15"); a = ap.parse_args()
M = {"rumus": "y_maxform", "HANFIS": "y_full", "persistence": "y_pers"}; rng = np.random.default_rng(a.seed)


def spearman(x, y):
    if np.ptp(x) == 0 or np.ptp(y) == 0: return 0.0                     # skor konstan = tanpa informasi urutan
    rx, ry = pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy(); return float(np.corrcoef(rx, ry)[0, 1])


def prec(pred, y, top):
    n = len(y); k = max(1, int(np.ceil(top * n))); thr = np.quantile(y, 1 - top); hi = y >= thr
    order = np.argsort(-(pred + rng.normal(0, 1e-9, n)), kind="stable"); return float(hi[order[:k]].mean())


def analyse(df, name):
    df = df.copy(); df["week"] = df["event_id"].str.rsplit("__", n=1).str[1]; rows = []
    for w, g in df.groupby("week"):
        if len(g) < a.min_assets: continue
        y = g["y_true"].to_numpy(float); r = {"week": w, "n": len(g)}
        for m, c in M.items(): p = g[c].to_numpy(float); r[f"sp_{m}"] = spearman(p, y); r[f"pr_{m}"] = prec(p, y, a.top)
        rows.append(r)
    W = pd.DataFrame(rows)
    if W.empty: print(f"{name}: nenhuma semana com >= {a.min_assets} aset"); return None
    print(f"\n== {name}: {len(W)} minggu (>= {a.min_assets} aset), top {a.top:.0%} ==")
    print("   rerata mingguan | " + " | ".join(f"{m}: Spearman {W[f'sp_{m}'].mean():.3f}, presisi@{a.top:.0%} {W[f'pr_{m}'].mean():.3f}" for m in M))
    cnt = rng.integers(0, len(W), size=(a.boot, len(W)))
    for lab, (m1, m2) in {"rumus - persistence": ("rumus", "persistence"), "HANFIS - persistence": ("HANFIS", "persistence"), "rumus - HANFIS": ("rumus", "HANFIS")}.items():
        out = []
        for met, pre in (("Spearman", "sp"), ("presisi", "pr")):
            d = (W[f"{pre}_{m1}"] - W[f"{pre}_{m2}"]).to_numpy(); bs = d[cnt].mean(axis=1); out.append(f"{met} {d.mean():+.3f} [{np.percentile(bs, 2.5):+.3f}, {np.percentile(bs, 97.5):+.3f}]")
        print(f"   {lab:22} " + " | ".join(out))
    return W


from pathlib import Path
od = Path(a.out_dir); od.mkdir(parents=True, exist_ok=True)
for k, g in (("h30", a.h30), ("h58", a.h58), ("h86", a.h86)):
    fs = sorted(glob.glob(g))
    if not fs: print(f"PERINGATAN: tidak ada berkas untuk {k}: {g}"); continue
    W = analyse(pd.read_csv(fs[-1]), f"{k} ({fs[-1].split('/')[-1]})")
    if W is not None: W.to_csv(od / f"e15_weekly_{k}.csv", index=False)
print("\nSTATUS=E15_DONE (deskriptif, post hoc; CI per minggu)")
