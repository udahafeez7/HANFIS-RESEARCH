#!/usr/bin/env python
"""E20 -- simulasi daya untuk P7e dan P7f (POST HOC, dilakukan SETELAH praregistrasi; bukan bagian protokol beku; tanpa pelatihan). Pertanyaan: bila rumus dan HANFIS berperilaku seperti pada baris out-of-fold yang BERSIH dari pergantian model EPSS,
berapa peluang studi forward enam minggu yang berisi 119 image mengonfirmasi P7e dan mendukung P7f menurut aturan protokol (SS >= 0,05 dan batas bawah CI95 > 0 serta Holm untuk P7e; batas atas CI95 < 0,05 serta Holm untuk P7f; keluarga kedua, alpha satu sisi 0,025)?
Studi simulasi: tiap dari 119 'slot' mengambil satu image dari kolam (dengan pengembalian) dan satu jendela 6 minggu berurutan dari baris bersih image itu; bootstrap per slot (resampel dalam). Kolam 'all' = baris bersih apa pun periodenya; 'new' = baris bersih era model baru (t >= 2026-07-13).
Keterbatasan: tiap image hanya diuji pada satu blok waktu pada data OOF; image dengan < 6 minggu bersih tidak masuk kolam.   python scripts/e20_power_sim.py [--pool all|new --sims 1000 --boot 500]"""
import argparse, glob, sys
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--pred", default="results_python/e11/e11_predictions_*.csv"); ap.add_argument("--table", default="data/processed/asset_weeks_v2_120assets_e4bis.csv")
ap.add_argument("--pool", choices=["all", "new"], default="all"); ap.add_argument("--sims", type=int, default=1000); ap.add_argument("--boot", type=int, default=500); ap.add_argument("--slots", type=int, default=119)
ap.add_argument("--weeks", type=int, default=6); ap.add_argument("--change", default="2026-06-15"); ap.add_argument("--seed", type=int, default=20261012); a = ap.parse_args()
fs = sorted(glob.glob(a.pred))
if not fs: sys.exit(f"ABORT: tidak ada berkas prediksi: {a.pred}")
T = pd.read_csv(a.table, usecols=["event_id", "week_start_utc"]); T["w"] = pd.to_datetime(T["week_start_utc"], utc=True).dt.tz_localize(None).dt.normalize()
D = pd.read_csv(fs[-1]).merge(T[["event_id", "w"]], on="event_id", how="left"); ch = pd.Timestamp(a.change); win = pd.Timedelta(28, unit="D")
D = D[~((D["w"] >= ch - win) & (D["w"] < ch + win))]                     # hanya baris bersih (horizon 4 minggu)
if a.pool == "new": D = D[D["w"] >= ch + win]
D = D.sort_values(["image_id", "w"]); pool = []
for img, g in D.groupby("image_id"):
    g = g.reset_index(drop=True); ok = [i for i in range(len(g) - a.weeks + 1) if (g.loc[i + a.weeks - 1, "w"] - g.loc[i, "w"]).days == 7 * (a.weeks - 1)]   # jendela berurutan
    if ok: pool.append((g, ok))
print(f"kolam '{a.pool}': {len(pool)} image dengan >= {a.weeks} minggu bersih berurutan ({sum(len(o) for _, o in pool)} jendela)")
if len(pool) < 10: sys.exit("ABORT: kolam terlalu kecil")
rng = np.random.default_rng(a.seed); res = []; M = ("y_pers", "y_maxform", "y_full")
for s in range(a.sims):
    S = np.zeros((a.slots, 3))
    for j in range(a.slots):
        g, ok = pool[rng.integers(len(pool))]; i = ok[rng.integers(len(ok))]; r = g.iloc[i:i + a.weeks]
        for k, c in enumerate(M): S[j, k] = ((r[c].to_numpy() - r["y_true"].to_numpy()) ** 2).sum()
    cnt = rng.multinomial(a.slots, np.full(a.slots, 1.0 / a.slots), size=a.boot); ss_e = 1 - S[:, 1].sum() / S[:, 0].sum(); ss_f = 1 - S[:, 2].sum() / S[:, 1].sum()
    be = 1 - (cnt @ S[:, 1]) / np.maximum(cnt @ S[:, 0], 1e-300); bf = 1 - (cnt @ S[:, 2]) / np.maximum(cnt @ S[:, 1], 1e-300)
    pv = {"e": (1 + (be <= 0).sum()) / (a.boot + 1), "f": (1 + (bf >= 0.05).sum()) / (a.boot + 1)}; ok_h, stop = {}, False
    for i2, (k, p) in enumerate(sorted(pv.items(), key=lambda t: t[1])): ok = (not stop) and p <= 0.025 / (2 - i2); ok_h[k] = ok; stop = stop or not ok
    lo_e, hi_e = np.percentile(be, [2.5, 97.5]); lo_f, hi_f = np.percentile(bf, [2.5, 97.5])
    res.append((ss_e, ss_f, ss_e >= 0.05 and lo_e > 0 and ok_h["e"], hi_e < 0, hi_f < 0.05 and ok_h["f"], ss_f >= 0.05 and lo_f > 0, hi_e - lo_e))
R = np.array(res, dtype=float)
print(f"{a.sims} studi simulasi ({a.slots} slot x {a.weeks} minggu, {a.boot} resampel dalam)")
print(f"  P7e TERKONFIRMASI:  {R[:, 2].mean():.1%} | LEBIH BURUK: {R[:, 3].mean():.1%} | tidak terkonfirmasi: {1 - R[:, 2].mean() - R[:, 3].mean():.1%}")
print(f"  P7f DIDUKUNG:       {R[:, 4].mean():.1%} | DIBANTAH: {R[:, 5].mean():.1%}")
print(f"  SS rumus vs persistence: median {np.median(R[:, 0]):+.3f} (IQR {np.percentile(R[:, 0], 25):+.3f} .. {np.percentile(R[:, 0], 75):+.3f}); lebar CI median {np.median(R[:, 6]):.3f}")
print(f"  SS HANFIS vs rumus:      median {np.median(R[:, 1]):+.3f} (IQR {np.percentile(R[:, 1], 25):+.3f} .. {np.percentile(R[:, 1], 75):+.3f})")
print("STATUS=E20_DONE (post hoc, deskriptif)")
