#!/usr/bin/env python
"""E22 -- sensitivitas E21: bootstrap berkelompok per MINGGU (POST HOC, deskriptif; dijalankan SETELAH registrasi E7 publik; tanpa pelatihan; hanya data lama).
Sama dengan E21 (prediksi out-of-fold E11, horizon 4 minggu; ME = rerata(prediksi - label); regresi label = alfa + beta x prediksi), tetapi resampel bootstrap per minggu (guncangan mingguan bersama semua image ikut berubah), atau per image dengan --by image (menghasilkan ulang E21).
Tambahan: selisih penyimpangan dari ideal (|ME|, |beta - 1|, |alfa|) antara HANFIS dan rumus serta persistence; positif berarti HANFIS menyimpang lebih jauh. Opsi --clean membatasi pada baris bersih dari pergantian model EPSS (+-28 hari dari 2026-06-15).
   python scripts/e22_calibration_weekboot.py [--clean] [--by week|image]"""
import argparse, glob, sys
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--pred", default="results_python/e11/e11_predictions_*.csv"); ap.add_argument("--table", default="data/processed/asset_weeks_v2_120assets_e4bis.csv")
ap.add_argument("--clean", action="store_true"); ap.add_argument("--change", default="2026-06-15"); ap.add_argument("--boot", type=int, default=2000); ap.add_argument("--seed", type=int, default=20261012)
ap.add_argument("--by", choices=["week", "image"], default="week"); a = ap.parse_args()
fs = sorted(glob.glob(a.pred))
if not fs: sys.exit(f"ABORT: tidak ada berkas prediksi: {a.pred}")
T = pd.read_csv(a.table, usecols=["event_id", "week_start_utc"]); T["w"] = pd.to_datetime(T["week_start_utc"], utc=True).dt.tz_localize(None).dt.normalize()
D = pd.read_csv(fs[-1]).merge(T[["event_id", "w"]], on="event_id", how="left"); ch = pd.Timestamp(a.change); win = pd.Timedelta(28, unit="D")
if D["w"].isna().any(): sys.exit("ABORT: ada baris prediksi tanpa minggu pada tabel aset-minggu")
if a.clean: D = D[~((D["w"] >= ch - win) & (D["w"] < ch + win))]
print(f"prediksi: {fs[-1]} | {len(D)} baris" + (" (hanya baris bersih dari pergantian model)" if a.clean else "") + f" | bootstrap per {a.by}")
grp = D["w"].dt.strftime("%Y-%m-%d").to_numpy() if a.by == "week" else D["image_id"].str.replace(r"-(on|off)$", "", regex=True).to_numpy()
gs = sorted(set(grp)); gi = {x: i for i, x in enumerate(gs)}; idx = np.array([gi[x] for x in grp]); G = len(gs); print(f"jumlah kelompok ({a.by}): {G}")
cnt = np.random.default_rng(a.seed).multinomial(G, np.full(G, 1.0 / G), size=a.boot).astype(float); y = D["y_true"].to_numpy(float); M = {"persistence": "y_pers", "rumus": "y_maxform", "HANFIS": "y_full"}


def sums(x):
    out = np.zeros((G, 6)); np.add.at(out, idx, np.c_[np.ones(len(x)), x, y, x * x, x * y, x - y]); return out


def fit(Sg, w=None):
    t = Sg.sum(0) if w is None else w @ Sg                       # n, sx, sy, sxx, sxy, sme
    n, sx, sy, sxx, sxy = t[..., 0], t[..., 1], t[..., 2], t[..., 3], t[..., 4]; den = n * sxx - sx ** 2; beta = np.where(den > 0, (n * sxy - sx * sy) / np.where(den > 0, den, 1), np.nan)
    return (sy - beta * sx) / n, beta, t[..., 5] / n


pc = lambda v: np.nanpercentile(v, [2.5, 97.5]); R = {}
for m, c in M.items():
    x = D[c].to_numpy(float); Sg = sums(x); al, be, me = fit(Sg); bal, bbe, bme = fit(Sg, cnt); R[m] = (al, be, me, bal, bbe, bme)
    print(f"\n== {m} ==\n   ME (prediksi - label): {me:+.3f} [{pc(bme)[0]:+.3f}, {pc(bme)[1]:+.3f}] | kemiringan kalibrasi beta: {be:.3f} [{pc(bbe)[0]:.3f}, {pc(bbe)[1]:.3f}] | intersep alfa: {al:+.3f} [{pc(bal)[0]:+.3f}, {pc(bal)[1]:+.3f}]")
IDEAL = (0.0, 1.0, 0.0); NAMES = ("alfa", "beta", "ME")
for other in ("rumus", "persistence"):
    print(f"\n== penyimpangan dari ideal: HANFIS minus {other} (positif = HANFIS menyimpang lebih jauh) ==")
    for k in (2, 1, 0):
        d = abs(R["HANFIS"][k] - IDEAL[k]) - abs(R[other][k] - IDEAL[k]); bd = np.abs(R["HANFIS"][3 + k] - IDEAL[k]) - np.abs(R[other][3 + k] - IDEAL[k])
        print(f"   |{NAMES[k]}{' - 1' if k == 1 else ''}|: {d:+.3f} [{pc(bd)[0]:+.3f}, {pc(bd)[1]:+.3f}]")
print("\nSTATUS=E22_DONE (deskriptif, post hoc)")
