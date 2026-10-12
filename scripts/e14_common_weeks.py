#!/usr/bin/env python
"""E14c -- kontrol pengacau 'horizon x periode' (POST HOC, deskriptif; tidak melatih apa pun). Horizon yang lebih panjang hanya memiliki baris berlabel pada minggu yang lebih lama (h30 sampai 2026-08-24, h58 sampai 07-27, h86 sampai 06-29),
sehingga tren SS terhadap horizon bercampur dengan periode (model EPSS berganti 2026-06-15). Skrip ini memakai HANYA baris aset-minggu yang ada pada ketiga berkas prediksi E11 (irisan event_id), lalu menghitung ulang SS per horizon dan selisihnya
(h86 dikurangi h30) dengan bootstrap per image yang sama (sampel resampel bersama, jadi selisih berpasangan).  python scripts/e14_common_weeks.py [--h30 GLOB --h58 GLOB --h86 GLOB]"""
import argparse, datetime as dt, glob, sys
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--h30", default="results_python/e11/e11_predictions_*.csv"); ap.add_argument("--h58", default="results_python/e14_h58_e11/e11_predictions_*.csv"); ap.add_argument("--h86", default="results_python/e14_h86_e11/e11_predictions_*.csv")
ap.add_argument("--boot", type=int, default=2000); ap.add_argument("--seed", type=int, default=20261012); ap.add_argument("--before", default=None, help="hanya minggu < tanggal ini (YYYY-MM-DD)"); a = ap.parse_args()
D = {}
for k, g in (("h30", a.h30), ("h58", a.h58), ("h86", a.h86)):
    fs = sorted(glob.glob(g))
    if not fs: sys.exit(f"ABORT: tidak ada berkas untuk {k}: {g}")
    D[k] = pd.read_csv(fs[-1])
    if a.before:                                                         # opsi: hanya baris dengan minggu < --before (mis. 2026-03-23 = bersih dari pergantian model EPSS pada ketiga horizon)
        wk = D[k]["event_id"].str.rsplit("__", n=1).str[1]; dts = wk.apply(lambda w: dt.date.fromisocalendar(int(w[:4]), int(w.split("W")[1]), 1)); D[k] = D[k][dts < dt.date.fromisoformat(a.before)]
    print(f"{k}: {fs[-1]} | {len(D[k])} baris" + (f" (minggu < {a.before})" if a.before else ""))
common = set.intersection(*[set(d["event_id"]) for d in D.values()]); print(f"irisan event_id: {len(common)} baris aset-minggu pada ketiga horizon")
if len(common) < 100: sys.exit("ABORT: irisan terlalu kecil")
order = sorted(common); S = {}
for k, d in D.items(): S[k] = d[d["event_id"].isin(common)].drop_duplicates("event_id").set_index("event_id").loc[order]
grp = S["h30"]["image_id"].str.replace(r"-(on|off)$", "", regex=True).to_numpy(); groups = sorted(set(grp)); gi = {g: i for i, g in enumerate(groups)}; idx = np.array([gi[g] for g in grp]); G = len(groups)
cnt = np.random.default_rng(a.seed).multinomial(G, np.full(G, 1.0 / G), size=a.boot)
def sse(k, col): v = np.zeros(G); np.add.at(v, idx, (S[k][col].to_numpy() - S[k]["y_true"].to_numpy()) ** 2); return v
pairs = {"rumus vs persistence": ("y_maxform", "y_pers"), "HANFIS vs persistence": ("y_full", "y_pers"), "HANFIS vs rumus": ("y_full", "y_maxform")}
res, boots = {}, {}
for k in S:
    for name, (m, b) in pairs.items():
        am, ab = sse(k, m), sse(k, b); bs = 1 - (cnt @ am) / (cnt @ ab); res[(k, name)] = (1 - am.sum() / ab.sum(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)); boots[(k, name)] = bs
print(f"\n== SS pada {len(common)} baris yang SAMA (CI95 bootstrap per image, {G} kelompok) ==")
print(f"{'perbandingan':26} {'h30 (4 mgg)':>26} {'h58 (8 mgg)':>26} {'h86 (12 mgg)':>26}")
for name in pairs: print(f"{name:26}" + "".join(f" {res[(k, name)][0]:+8.3f} [{res[(k, name)][1]:+.3f},{res[(k, name)][2]:+.3f}]" for k in ("h30", "h58", "h86")))
print("\nMSE pada baris yang sama (skala tiap label berbeda; jangan dibandingkan antar horizon):")
for k in S: print(f"  {k}: persistence {np.mean((S[k]['y_pers'] - S[k]['y_true']) ** 2):.3f} | rumus {np.mean((S[k]['y_maxform'] - S[k]['y_true']) ** 2):.3f} | HANFIS {np.mean((S[k]['y_full'] - S[k]['y_true']) ** 2):.3f}")
print("\n== selisih berpasangan h86 - h30 (resampel bersama) ==")
for name in pairs:
    d = boots[("h86", name)] - boots[("h30", name)]; pt = res[("h86", name)][0] - res[("h30", name)][0]; print(f"  {name:26} dSS = {pt:+.3f} [{np.percentile(d, 2.5):+.3f}, {np.percentile(d, 97.5):+.3f}]")
print("\nSTATUS=E14C_DONE (deskriptif, post hoc)")
