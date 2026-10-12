#!/usr/bin/env python
"""E18 -- gerbang perubahan masukan (POST HOC, deskriptif; tanpa pelatihan). E16 menunjukkan HANFIS merugi pada baris yang masukannya tidak berubah. Di sini aturan transparan 'bila x2 dan status KEV tidak berubah selama --lag minggu, pakai persistence;
selain itu pakai model' diterapkan pada prediksi yang sudah ada (HANFIS dan rumus) di tiga horizon (jendela perubahan = lag horizon: 4, 8, 12 minggu). Dilaporkan SS (CI95 bootstrap per image, resampel bersama) terhadap persistence dan terhadap rumus tanpa gerbang.
python scripts/e18_gate.py [--h30 GLOB --h58 GLOB --h86 GLOB --table CSV]"""
import argparse, glob, sys
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--h30", default="results_python/e11/e11_predictions_*.csv"); ap.add_argument("--h58", default="results_python/e14_h58_e11/e11_predictions_*.csv"); ap.add_argument("--h86", default="results_python/e14_h86_e11/e11_predictions_*.csv")
ap.add_argument("--table", default="data/processed/asset_weeks_v2_120assets_e4bis.csv"); ap.add_argument("--boot", type=int, default=2000); ap.add_argument("--seed", type=int, default=20261012); a = ap.parse_args()
T = pd.read_csv(a.table, usecols=["event_id", "week_start_utc", "exploitability", "threat_intelligence"]); T["asset"] = T["event_id"].str.rsplit("__", n=1).str[0]; T["w"] = pd.to_datetime(T["week_start_utc"], utc=True).dt.tz_localize(None).dt.normalize()
for k, g, lag in (("h30", a.h30, 4), ("h58", a.h58, 8), ("h86", a.h86, 12)):
    fs = sorted(glob.glob(g))
    if not fs: print(f"PERINGATAN: tidak ada berkas untuk {k}"); continue
    P = pd.read_csv(fs[-1]); prev = T[["asset", "w", "exploitability", "threat_intelligence"]].copy(); prev["w"] = prev["w"] + pd.Timedelta(lag * 7, unit="D"); prev = prev.rename(columns={"exploitability": "x2p", "threat_intelligence": "x7p"})
    D = P.merge(T[["event_id", "asset", "w", "exploitability", "threat_intelligence"]], on="event_id", how="left").merge(prev, on=["asset", "w"], how="left")
    known = D["x2p"].notna() & D["x7p"].notna(); chg = ((D["exploitability"] - D["x2p"]).abs() > 1e-12) | (D["threat_intelligence"] != D["x7p"]); D = D[known].copy(); chg = chg[known]
    for m, c in (("HANFIS", "y_full"), ("rumus", "y_maxform")): D["g_" + m] = np.where(chg, D[c], D["y_pers"])
    grp = D["image_id"].str.replace(r"-(on|off)$", "", regex=True).to_numpy(); gs = sorted(set(grp)); gi = {x: i for i, x in enumerate(gs)}; idx = np.array([gi[x] for x in grp]); G = len(gs)
    cnt = np.random.default_rng(a.seed).multinomial(G, np.full(G, 1.0 / G), size=a.boot); y = D["y_true"].to_numpy()
    def pi(c): v = np.zeros(G); np.add.at(v, idx, (D[c].to_numpy() - y) ** 2); return v
    S = {n: pi(c) for n, c in (("persistence", "y_pers"), ("rumus", "y_maxform"), ("HANFIS", "y_full"), ("HANFIS+gerbang", "g_HANFIS"), ("rumus+gerbang", "g_rumus"))}
    def ss(m1, m2): bs = 1 - (cnt @ S[m1]) / np.maximum(cnt @ S[m2], 1e-300); return 1 - S[m1].sum() / S[m2].sum(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
    n = len(D); print(f"\n== {k} (jendela perubahan {lag} minggu): {n} baris, {chg.mean():.0%} dengan perubahan masukan ==")
    print("   MSE: " + " | ".join(f"{m} {S[m].sum() / n:.3f}" for m in S))
    for lab, (m1, m2) in {"HANFIS vs persistence": ("HANFIS", "persistence"), "HANFIS+gerbang vs persistence": ("HANFIS+gerbang", "persistence"), "HANFIS+gerbang vs HANFIS": ("HANFIS+gerbang", "HANFIS"), "HANFIS+gerbang vs rumus": ("HANFIS+gerbang", "rumus"), "rumus+gerbang vs rumus": ("rumus+gerbang", "rumus")}.items():
        r = ss(m1, m2); print(f"   {lab:32} SS {r[0]:+.3f} [{r[1]:+.3f}, {r[2]:+.3f}]")
print("\nSTATUS=E18_DONE (deskriptif, post hoc)")
