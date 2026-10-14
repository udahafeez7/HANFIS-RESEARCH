#!/usr/bin/env python
"""E21 -- kalibrasi prediksi (POST HOC, deskriptif; dijalankan SETELAH registrasi OSF; tanpa pelatihan). Untuk persistence, rumus bentuk-maks, dan HANFIS pada prediksi out-of-fold E11 (horizon 4 minggu):
bias rata-rata ME = rerata(prediksi - label), regresi kalibrasi label = alfa + beta x prediksi (beta = 1 dan alfa = 0 berarti terkalibrasi), CI95 bootstrap per image (resampel bersama), dan tabel keandalan per desil prediksi.
Opsi --clean membatasi pada baris yang bersih dari pergantian model EPSS (label dan label persistence tidak melintasi 2026-06-15; +-28 hari).   python scripts/e21_calibration.py [--clean]"""
import argparse, glob, sys
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--pred", default="results_python/e11/e11_predictions_*.csv"); ap.add_argument("--table", default="data/processed/asset_weeks_v2_120assets_e4bis.csv")
ap.add_argument("--clean", action="store_true"); ap.add_argument("--change", default="2026-06-15"); ap.add_argument("--boot", type=int, default=2000); ap.add_argument("--seed", type=int, default=20261012); a = ap.parse_args()
fs = sorted(glob.glob(a.pred))
if not fs: sys.exit(f"ABORT: tidak ada berkas prediksi: {a.pred}")
T = pd.read_csv(a.table, usecols=["event_id", "week_start_utc"]); T["w"] = pd.to_datetime(T["week_start_utc"], utc=True).dt.tz_localize(None).dt.normalize()
D = pd.read_csv(fs[-1]).merge(T[["event_id", "w"]], on="event_id", how="left"); ch = pd.Timestamp(a.change); win = pd.Timedelta(28, unit="D")
if a.clean: D = D[~((D["w"] >= ch - win) & (D["w"] < ch + win))]
print(f"prediksi: {fs[-1]} | {len(D)} baris" + (" (hanya baris bersih dari pergantian model)" if a.clean else ""))
grp = D["image_id"].str.replace(r"-(on|off)$", "", regex=True).to_numpy(); gs = sorted(set(grp)); gi = {x: i for i, x in enumerate(gs)}; idx = np.array([gi[x] for x in grp]); G = len(gs)
cnt = np.random.default_rng(a.seed).multinomial(G, np.full(G, 1.0 / G), size=a.boot).astype(float); y = D["y_true"].to_numpy(float); M = {"persistence": "y_pers", "rumus": "y_maxform", "HANFIS": "y_full"}


def sums(x):
    out = np.zeros((G, 6)); np.add.at(out, idx, np.c_[np.ones(len(x)), x, y, x * x, x * y, x - y]); return out


def fit(Sg, w=None):
    t = Sg.sum(0) if w is None else w @ Sg                       # n, sx, sy, sxx, sxy, sme
    n, sx, sy, sxx, sxy = t[..., 0], t[..., 1], t[..., 2], t[..., 3], t[..., 4]; den = n * sxx - sx ** 2; beta = np.where(den > 0, (n * sxy - sx * sy) / np.where(den > 0, den, 1), np.nan)
    return (sy - beta * sx) / n, beta, t[..., 5] / n


for m, c in M.items():
    x = D[c].to_numpy(float); Sg = sums(x); al, be, me = fit(Sg); bal, bbe, bme = fit(Sg, cnt); pc = lambda v: np.nanpercentile(v, [2.5, 97.5])
    print(f"\n== {m} ==\n   ME (prediksi - label): {me:+.3f} [{pc(bme)[0]:+.3f}, {pc(bme)[1]:+.3f}] | kemiringan kalibrasi beta: {be:.3f} [{pc(bbe)[0]:.3f}, {pc(bbe)[1]:.3f}] | intersep alfa: {al:+.3f} [{pc(bal)[0]:+.3f}, {pc(bal)[1]:+.3f}]")
    q = pd.qcut(pd.Series(x).rank(method="first"), 10, labels=False); R = pd.DataFrame({"q": q, "x": x, "y": y}).groupby("q").agg(n=("x", "size"), pred=("x", "mean"), obs=("y", "mean"))
    print("   desil prediksi (rerata prediksi -> rerata label): " + " | ".join(f"{r.pred:.1f}->{r.obs:.1f}" for r in R.itertuples()))
print("\nSTATUS=E21_DONE (deskriptif, post hoc)")
