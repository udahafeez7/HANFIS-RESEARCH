#!/usr/bin/env python
"""E19 -- kontrol pengacau pergantian model EPSS (POST HOC, deskriptif; tanpa pelatihan). E17 menunjukkan galat terbesar jatuh pada minggu 2026-W21..W24, yaitu minggu yang jendela labelnya melintasi 2026-06-15: x2 pada t memakai model lama sedangkan label (dan label persistence) memakai
skor model baru. Baris 'tercemar' = minggu t dalam +-jendela hari dari tanggal pergantian (jendela label 28, 56, 84 hari untuk horizon 4, 8, 12 minggu; label t melintasi, atau label persistence t-lag melintasi). Dilaporkan: porsi SSE dari baris tercemar dan SS gabungan
pada SEMUA baris dibanding hanya baris BERSIH (CI95 bootstrap per image). Minggu forward E7 (t >= 2026-08-31) bersih.  python scripts/e19_straddle.py [--change 2026-06-15 --table CSV]"""
import argparse, glob, sys
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--h30", default="results_python/e11/e11_predictions_*.csv"); ap.add_argument("--h58", default="results_python/e14_h58_e11/e11_predictions_*.csv"); ap.add_argument("--h86", default="results_python/e14_h86_e11/e11_predictions_*.csv")
ap.add_argument("--table", default="data/processed/asset_weeks_v2_120assets_e4bis.csv"); ap.add_argument("--change", default="2026-06-15"); ap.add_argument("--boot", type=int, default=2000); ap.add_argument("--seed", type=int, default=20261012); a = ap.parse_args()
ch = pd.Timestamp(a.change); T = pd.read_csv(a.table, usecols=["event_id", "week_start_utc"]); T["w"] = pd.to_datetime(T["week_start_utc"], utc=True).dt.tz_localize(None).dt.normalize()
for k, g, win in (("h30", a.h30, 28), ("h58", a.h58, 56), ("h86", a.h86, 84)):
    fs = sorted(glob.glob(g))
    if not fs: print(f"PERINGATAN: tidak ada berkas untuk {k}"); continue
    D = pd.read_csv(fs[-1]).merge(T[["event_id", "w"]], on="event_id", how="left"); dirty = ((D["w"] >= ch - pd.Timedelta(win, unit="D")) & (D["w"] < ch + pd.Timedelta(win, unit="D"))).to_numpy()
    grp = D["image_id"].str.replace(r"-(on|off)$", "", regex=True).to_numpy(); gs = sorted(set(grp)); gi = {x: i for i, x in enumerate(gs)}; idx = np.array([gi[x] for x in grp]); G = len(gs)
    cnt = np.random.default_rng(a.seed).multinomial(G, np.full(G, 1.0 / G), size=a.boot); y = D["y_true"].to_numpy(); M = {"persistence": "y_pers", "rumus": "y_maxform", "HANFIS": "y_full"}; E = {m: (D[c].to_numpy() - y) ** 2 for m, c in M.items()}
    def pi(v, mk): o = np.zeros(G); np.add.at(o, idx[mk], v[mk]); return o
    def ss(m1, m2, mk): s1, s2 = pi(E[m1], mk), pi(E[m2], mk); bs = 1 - (cnt @ s1) / np.maximum(cnt @ s2, 1e-300); return 1 - s1.sum() / s2.sum(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
    allm, clean = np.ones(len(D), bool), ~dirty; wk = D.loc[dirty, "w"]
    print(f"\n== {k} (jendela label {win} hari): {len(D)} baris; tercemar {int(dirty.sum())} ({dirty.mean():.0%})" + (f", minggu {str(wk.min())[:10]} .. {str(wk.max())[:10]}" if dirty.any() else "") + f"; bersih {int(clean.sum())} ==")
    print("   porsi SSE dari baris tercemar: " + " | ".join(f"{m} {E[m][dirty].sum() / E[m].sum():.1%}" for m in M))
    for lab, (m1, m2) in {"rumus vs persistence": ("rumus", "persistence"), "HANFIS vs persistence": ("HANFIS", "persistence"), "HANFIS vs rumus": ("HANFIS", "rumus")}.items():
        r1 = ss(m1, m2, allm); r2 = ss(m1, m2, clean) if clean.sum() >= 50 else (float("nan"),) * 3
        print(f"   {lab:24} semua {r1[0]:+.3f} [{r1[1]:+.3f}, {r1[2]:+.3f}] | bersih {r2[0]:+.3f} [{r2[1]:+.3f}, {r2[2]:+.3f}]")
print("\nSTATUS=E19_DONE (deskriptif, post hoc)")
