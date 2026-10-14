#!/usr/bin/env python
"""E23 -- apakah rekalibrasi linear menutup celah HANFIS terhadap rumus? (POST HOC, deskriptif; dijalankan SETELAH registrasi E7 publik; tanpa pelatihan jaringan; hanya data lama).
Untuk persistence, rumus bentuk-maks dan HANFIS (prediksi out-of-fold E11, horizon 4 minggu) dibandingkan tiga versi: mentah; direkalibrasi silang (label = a + b x prediksi, a dan b dicocokkan pada baris dari lipatan LAIN lalu dipakai pada lipatan ini); direkalibrasi dalam-sampel (a dan b dari semua baris; batas atas yang optimistis).
Skill = 1 - MSE model / MSE referensi, gabungan semua baris, CI95 bootstrap per image (resampel bersama). Rekalibrasi silang memakai baris dari lipatan yang lebih baru: diagnostik deskriptif, bukan prosedur prediktif.
Opsi --clean membatasi pada baris bersih dari pergantian model EPSS (+-28 hari dari 2026-06-15).   python scripts/e23_recalibration.py [--clean]"""
import argparse, glob, sys
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--pred", default="results_python/e11/e11_predictions_*.csv"); ap.add_argument("--table", default="data/processed/asset_weeks_v2_120assets_e4bis.csv")
ap.add_argument("--clean", action="store_true"); ap.add_argument("--change", default="2026-06-15"); ap.add_argument("--boot", type=int, default=2000); ap.add_argument("--seed", type=int, default=20261012); a = ap.parse_args()
fs = sorted(glob.glob(a.pred))
if not fs: sys.exit(f"ABORT: tidak ada berkas prediksi: {a.pred}")
T = pd.read_csv(a.table, usecols=["event_id", "week_start_utc"]); T["w"] = pd.to_datetime(T["week_start_utc"], utc=True).dt.tz_localize(None).dt.normalize()
D = pd.read_csv(fs[-1]).merge(T[["event_id", "w"]], on="event_id", how="left"); ch = pd.Timestamp(a.change); win = pd.Timedelta(28, unit="D")
for c in ("fold", "y_true", "y_pers", "y_maxform", "y_full", "image_id"):
    if c not in D.columns: sys.exit(f"ABORT: kolom '{c}' tidak ada pada {fs[-1]}")
if a.clean: D = D[~((D["w"] >= ch - win) & (D["w"] < ch + win))].reset_index(drop=True)
print(f"prediksi: {fs[-1]} | {len(D)} baris" + (" (hanya baris bersih dari pergantian model)" if a.clean else "") + f" | lipatan: {sorted(D['fold'].unique().tolist())}")
y = D["y_true"].to_numpy(float); fold = D["fold"].to_numpy()
grp = D["image_id"].str.replace(r"-(on|off)$", "", regex=True).to_numpy(); gs = sorted(set(grp)); gi = {x: i for i, x in enumerate(gs)}; idx = np.array([gi[x] for x in grp]); G = len(gs)
cnt = np.random.default_rng(a.seed).multinomial(G, np.full(G, 1.0 / G), size=a.boot).astype(float)


def ols(x, t):
    vx = x.var()
    if vx <= 0: return float(t.mean()), 0.0
    b = float(np.cov(x, t, bias=True)[0, 1] / vx); return float(t.mean() - b * x.mean()), b


def recal_cross(x):
    out = np.empty_like(x)
    for f in np.unique(fold):
        te = fold == f; tr = ~te
        if tr.sum() < 10: sys.exit(f"ABORT: terlalu sedikit baris latih untuk lipatan {f}")
        al, be = ols(x[tr], y[tr]); out[te] = al + be * x[te]
    return out


def recal_in(x): al, be = ols(x, y); return al + be * x


BASE = {"persistence": D["y_pers"].to_numpy(float), "rumus": D["y_maxform"].to_numpy(float), "HANFIS": D["y_full"].to_numpy(float)}
V = {}
for k, x in BASE.items():
    V[(k, "mentah")] = x; V[(k, "silang")] = recal_cross(x); V[(k, "dalam-sampel")] = recal_in(x)
SE = {}
for key, x in V.items():
    se = (y - x) ** 2; S = np.zeros((G, 1)); np.add.at(S, idx, se[:, None]); SE[key] = S[:, 0]
pc = lambda v: np.nanpercentile(v, [2.5, 97.5])


def skill(km, kr):
    pt = 1 - SE[km].sum() / SE[kr].sum(); b = 1 - (cnt @ SE[km]) / (cnt @ SE[kr]); return pt, pc(b)


print("\nMSE gabungan (skala label 0-100):")
for lvl in ("mentah", "silang", "dalam-sampel"):
    print(f"   {lvl:13s} " + " | ".join(f"{k}: {SE[(k, lvl)].sum() / len(y):.4f}" for k in BASE))
print("\nSkill (CI95 per image) -- positif berarti model pertama lebih baik:")
for lvl in ("mentah", "silang", "dalam-sampel"):
    for m, r in (("HANFIS", "rumus"), ("HANFIS", "persistence"), ("rumus", "persistence")):
        pt, ci = skill((m, lvl), (r, lvl)); print(f"   [{lvl:12s}] {m} vs {r}: {pt:+.3f} [{ci[0]:+.3f}, {ci[1]:+.3f}]")
print("\nPerubahan skill HANFIS vs rumus akibat rekalibrasi (silang minus mentah):")
d = (1 - SE[("HANFIS", "silang")].sum() / SE[("rumus", "silang")].sum()) - (1 - SE[("HANFIS", "mentah")].sum() / SE[("rumus", "mentah")].sum())
bd = (1 - (cnt @ SE[("HANFIS", "silang")]) / (cnt @ SE[("rumus", "silang")])) - (1 - (cnt @ SE[("HANFIS", "mentah")]) / (cnt @ SE[("rumus", "mentah")]))
print(f"   {d:+.3f} [{pc(bd)[0]:+.3f}, {pc(bd)[1]:+.3f}]")
print("\nSTATUS=E23_DONE (deskriptif, post hoc)")
