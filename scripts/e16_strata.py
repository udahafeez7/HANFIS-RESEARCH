#!/usr/bin/env python
"""E16 -- anatomi galat (POST HOC, deskriptif; tidak melatih apa pun): DARI MANA keunggulan rumus dan HANFIS atas persistence berasal, dan seberapa besar galat terkonsentrasi pada sedikit baris.
Strata (semua dari berkas prediksi out-of-fold E11 + tabel aset-minggu): (1) ada atau tidak ada perubahan masukan selama 4 minggu (selisih x2 atau status KEV t vs t-4 minggu; definisi yang sama dengan strata deskriptif E7),
(2) periode model EPSS (awal >= 2026-06-15 = baru), (3) kuartil besar perubahan label |y - y_lag4| (strata hasil: hanya untuk menjelaskan, bukan untuk inferensi). Untuk tiap strata: MSE tiap metode dan SS (CI95 bootstrap per image, resampel bersama).
Konsentrasi: porsi SSE dari 1%, 5%, 10% baris terburuk dan dari 5 image terburuk.   python scripts/e16_strata.py [--pred GLOB --table CSV]"""
import argparse, glob, sys
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--pred", default="results_python/e11/e11_predictions_*.csv"); ap.add_argument("--table", default="data/processed/asset_weeks_v2_120assets_e4bis.csv")
ap.add_argument("--boot", type=int, default=2000); ap.add_argument("--seed", type=int, default=20261012); ap.add_argument("--epss-change", default="2026-06-15"); a = ap.parse_args()
fs = sorted(glob.glob(a.pred))
if not fs: sys.exit(f"ABORT: tidak ada berkas prediksi: {a.pred}")
P = pd.read_csv(fs[-1]); T = pd.read_csv(a.table, usecols=["event_id", "week_start_utc", "exploitability", "threat_intelligence"]); print(f"prediksi: {fs[-1]} | {len(P)} baris")
T["asset"] = T["event_id"].str.rsplit("__", n=1).str[0]; T["w"] = pd.to_datetime(T["week_start_utc"], utc=True).dt.tz_localize(None).dt.normalize()
prev = T[["asset", "w", "exploitability", "threat_intelligence"]].copy(); prev["w"] = prev["w"] + pd.Timedelta(28, unit="D"); prev = prev.rename(columns={"exploitability": "x2p", "threat_intelligence": "x7p"})
D = P.merge(T[["event_id", "asset", "w", "exploitability", "threat_intelligence"]], on="event_id", how="left").merge(prev, on=["asset", "w"], how="left")
D["mud"] = np.where(D["x2p"].isna() | D["x7p"].isna(), "tidak diketahui", np.where((D["exploitability"] - D["x2p"]).abs().gt(1e-12) | D["threat_intelligence"].ne(D["x7p"]), "ada perubahan masukan", "tanpa perubahan masukan"))
D["era"] = np.where(D["w"] >= pd.Timestamp(a.epss_change), "model EPSS baru", "model EPSS lama"); mv = (D["y_true"] - D["y_pers"]).abs()
D["mov"] = pd.qcut(mv.rank(method="first"), 4, labels=["Q1 (label hampir tetap)", "Q2", "Q3", "Q4 (label berubah paling besar)"]).astype(str)
grp = D["image_id"].str.replace(r"-(on|off)$", "", regex=True).to_numpy(); groups = sorted(set(grp)); gi = {g: i for i, g in enumerate(groups)}; idx = np.array([gi[g] for g in grp]); G = len(groups)
cnt = np.random.default_rng(a.seed).multinomial(G, np.full(G, 1.0 / G), size=a.boot); M = {"persistence": "y_pers", "rumus": "y_maxform", "HANFIS": "y_full"}
E = {m: (D[c] - D["y_true"]).to_numpy() ** 2 for m, c in M.items()}


def per_image(v, mask): out = np.zeros(G); np.add.at(out, idx[mask], v[mask]); return out


def ss(mask, m1, m2):
    s1, s2 = per_image(E[m1], mask), per_image(E[m2], mask)
    if s2.sum() == 0: return float("nan"), float("nan"), float("nan")
    bs = 1 - (cnt @ s1) / np.maximum(cnt @ s2, 1e-300); return 1 - s1.sum() / s2.sum(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def block(title, col):
    print(f"\n== {title} ==\n{'strata':36} {'n':>5} {'MSE pers':>9} {'MSE rumus':>10} {'MSE HANFIS':>11} | {'SS rumus vs pers':>26} | {'SS HANFIS vs pers':>26}")
    for k in sorted(D[col].unique()):
        mk = (D[col] == k).to_numpy()
        if mk.sum() < 20: print(f"{k:36} {int(mk.sum()):5d}  (terlalu sedikit)"); continue
        a1, a2 = ss(mk, "rumus", "persistence"), ss(mk, "HANFIS", "persistence")
        print(f"{k:36} {int(mk.sum()):5d} {E['persistence'][mk].mean():9.3f} {E['rumus'][mk].mean():10.3f} {E['HANFIS'][mk].mean():11.3f} | {a1[0]:+8.3f} [{a1[1]:+.3f},{a1[2]:+.3f}] | {a2[0]:+8.3f} [{a2[1]:+.3f},{a2[2]:+.3f}]")


block("(1) perubahan masukan selama 4 minggu", "mud"); block("(2) periode model EPSS", "era"); block("(3) besar perubahan label (strata hasil; deskriptif)", "mov")
if "fold" in D.columns:
    print("\n== (4) per fold (blok waktu; baris periode baru biasanya hanya dari fold terakhir, jadi 'periode' dan 'image' tercampur) ==")
    print(f"{'fold':>5} {'n':>5} {'minggu':>23} {'MSE pers':>9} {'MSE rumus':>10} {'MSE HANFIS':>11} | {'SS rumus vs pers':>26} | porsi pengurangan SSE (rumus vs pers)")
    red = {f: per_image(E["persistence"], (D["fold"] == f).to_numpy()).sum() - per_image(E["rumus"], (D["fold"] == f).to_numpy()).sum() for f in sorted(D["fold"].unique())}; tot = sum(red.values())
    for f in sorted(D["fold"].unique()):
        mk = (D["fold"] == f).to_numpy(); a1 = ss(mk, "rumus", "persistence"); ws = D.loc[mk, "w"]
        print(f"{int(f):5d} {int(mk.sum()):5d} {str(ws.min())[:10]} .. {str(ws.max())[:10]} {E['persistence'][mk].mean():9.3f} {E['rumus'][mk].mean():10.3f} {E['HANFIS'][mk].mean():11.3f} | {a1[0]:+8.3f} [{a1[1]:+.3f},{a1[2]:+.3f}] | {red[f] / tot:6.1%}")
    print("\n== (5) tanpa satu fold (leave-one-fold-out): apakah keunggulan bergantung pada satu blok? ==")
    for f in sorted(D["fold"].unique()):
        mk = (D["fold"] != f).to_numpy(); a1, a2, a3 = ss(mk, "rumus", "persistence"), ss(mk, "HANFIS", "persistence"), ss(mk, "HANFIS", "rumus")
        print(f"  tanpa fold {int(f)}: rumus vs pers {a1[0]:+.3f} [{a1[1]:+.3f},{a1[2]:+.3f}] | HANFIS vs pers {a2[0]:+.3f} [{a2[1]:+.3f},{a2[2]:+.3f}] | HANFIS vs rumus {a3[0]:+.3f} [{a3[1]:+.3f},{a3[2]:+.3f}]")
print("\n== konsentrasi galat kuadrat ==")
for m in M:
    e = np.sort(E[m])[::-1]; tot = e.sum(); n = len(e); per = np.sort(per_image(E[m], np.ones(len(D), bool)))[::-1]
    print(f"  {m:12} baris terburuk 1%: {e[:max(1, n // 100)].sum() / tot:5.1%} | 5%: {e[:max(1, n // 20)].sum() / tot:5.1%} | 10%: {e[:max(1, n // 10)].sum() / tot:5.1%} | 5 image terburuk: {per[:5].sum() / tot:5.1%}")
print("\nSTATUS=E16_DONE (deskriptif, post hoc)")
