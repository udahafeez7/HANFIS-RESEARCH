#!/usr/bin/env python3
"""Cek apakah batas fold GroupTimeSplit memotong pergantian model EPSS (2026-06-15).
Hanya membaca; tidak menulis apa pun. Jalankan dari akar repo.
Penentu: tanggal label y(t) memakai EPSS pada t+7..t+28 hari, jadi minggu t 'terpengaruh'
bila [t+7, t+28] memuat/melewati tanggal pergantian."""
import argparse, sys
from pathlib import Path
import pandas as pd
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "python_hanfis"))
from splits import GroupTimeSplit  # noqa: E402
ap = argparse.ArgumentParser()
ap.add_argument("--table", default="data/processed/asset_weeks_v2_120assets_e4bis.csv")
ap.add_argument("--n-splits", type=int, default=5)
ap.add_argument("--embargo-days", type=int, default=30)
ap.add_argument("--min-train-weeks", type=int, default=4)
ap.add_argument("--boundary", default="2026-06-15")
a = ap.parse_args()
B = pd.Timestamp(a.boundary, tz="UTC")
df = pd.read_csv(a.table)
df["week_start_utc"] = pd.to_datetime(df["week_start_utc"], utc=True)
sup = df.dropna(subset=["y"]).reset_index(drop=True)
n_groups = min(a.n_splits, sup["image_id"].nunique())
sp = GroupTimeSplit(n_splits=n_groups, embargo_days=a.embargo_days, min_train_weeks=a.min_train_weeks)
folds = sp.split(sup); sp.assert_no_leakage(sup, folds)
D = lambda t: pd.Timestamp(t).tz_convert("UTC").date() if pd.Timestamp(t).tzinfo else pd.Timestamp(t).tz_localize("UTC").date()
print(f"batas model EPSS: {B.date()} | n_splits={n_groups} embargo={a.embargo_days} min_train_weeks={a.min_train_weeks}\n")
print(f"{'fold':>4} {'train_max_wk':>12} {'cutoff':>11} {'test_start':>11} {'test_end':>11}  status")
for f in folds:
    tr = sup.iloc[f.train_index]; te = sup.iloc[f.test_index]
    tr_last = tr["week_start_utc"].max(); te_first = te["week_start_utc"].min(); te_last = te["week_start_utc"].max()
    tr_label_end = tr_last + pd.Timedelta(28, unit="D")
    te_label_start, te_label_end = te_first + pd.Timedelta(7, unit="D"), te_last + pd.Timedelta(28, unit="D")
    if te_label_end < B: st = "semua label SEBELUM pergantian"
    elif te_label_start >= B and tr_label_end < B: st = "LATIH pra-pergantian, UJI pasca-pergantian (pergeseran distribusi)"
    elif te_label_start < B <= te_label_end: st = "blok UJI MELINTASI pergantian"
    elif tr_label_end >= B and tr["week_start_utc"].min() + pd.Timedelta(7, unit="D") < B: st = "latih memuat kedua model EPSS"
    else: st = "latih dan uji semua PASCA-pergantian"
    print(f"{f.index:>4} {D(tr_last)!s:>12} {D(f.cutoff)!s:>11} {D(f.test_start)!s:>11} {D(f.test_end)!s:>11}  {st}")
