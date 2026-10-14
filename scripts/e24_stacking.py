#!/usr/bin/env python
"""E24 -- apakah HANFIS menambah informasi di atas rumus? (POST HOC, deskriptif; dijalankan SETELAH registrasi E7 publik; tanpa pelatihan jaringan; hanya data lama).
Pada prediksi out-of-fold E11 (horizon 4 minggu) dicocokkan kombinasi linear label = a + sum(b_k x prediksi_k), dengan a dan b dicocokkan pada baris dari lipatan LAIN lalu dipakai pada lipatan ini (silang):
   F_rc : rumus saja, direkalibrasi (pembanding yang adil)      FP : rumus + persistence
   FH   : rumus + HANFIS                                         FHP: rumus + HANFIS + persistence
Skill = 1 - MSE model / MSE referensi, gabungan semua baris, CI95 bootstrap per image (resampel bersama). Skill FH terhadap F_rc adalah nilai tambah HANFIS di atas rumus. Batas atas dalam-sampel (koefisien dari semua baris) juga dilaporkan. Rekalibrasi silang memakai lipatan yang lebih baru: diagnostik deskriptif, bukan prosedur prediktif.
Opsi --clean membatasi pada baris bersih dari pergantian model EPSS (+-28 hari dari 2026-06-15).   python scripts/e24_stacking.py [--clean]"""
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
y = D["y_true"].to_numpy(float); fold = D["fold"].to_numpy(); Fv, Hv, Pv = D["y_maxform"].to_numpy(float), D["y_full"].to_numpy(float), D["y_pers"].to_numpy(float)
grp = D["image_id"].str.replace(r"-(on|off)$", "", regex=True).to_numpy(); gs = sorted(set(grp)); gi = {x: i for i, x in enumerate(gs)}; idx = np.array([gi[x] for x in grp]); G = len(gs)
cnt = np.random.default_rng(a.seed).multinomial(G, np.full(G, 1.0 / G), size=a.boot).astype(float)
X1 = lambda cols: np.column_stack([np.ones(len(y))] + cols)


def fit(Xtr, ytr): return np.linalg.lstsq(Xtr, ytr, rcond=None)[0]


def cross(cols):
    X = X1(cols); out = np.empty(len(y)); coefs = []
    for f in np.unique(fold):
        te = fold == f; tr = ~te
        if tr.sum() < 20: sys.exit(f"ABORT: terlalu sedikit baris latih untuk lipatan {f}")
        b = fit(X[tr], y[tr]); out[te] = X[te] @ b; coefs.append(b)
    return out, np.array(coefs)


def insample(cols): X = X1(cols); return X @ fit(X, y)


SPEC = {"F_rc": [Fv], "FP": [Fv, Pv], "FH": [Fv, Hv], "FHP": [Fv, Hv, Pv]}
V = {"F_mentah": Fv}; C = {}
for k, cols in SPEC.items(): V[k], C[k] = cross(cols); V[k + "_dalam"] = insample(cols)
SE = {}
for k, x in V.items(): S = np.zeros(G); np.add.at(S, idx, (y - x) ** 2); SE[k] = S
pc = lambda v: np.nanpercentile(v, [2.5, 97.5])


def skill(m, r): pt = 1 - SE[m].sum() / SE[r].sum(); b = 1 - (cnt @ SE[m]) / (cnt @ SE[r]); return pt, pc(b)


print("\nMSE gabungan (skala label 0-100):")
for k in V: print(f"   {k:10s} {SE[k].sum() / len(y):.4f}")
print("\nKoefisien silang (rerata dan rentang antar lipatan; urutan: konstanta, rumus, HANFIS, persistence):")
for k, names in (("FH", ("a", "b_rumus", "b_HANFIS")), ("FHP", ("a", "b_rumus", "b_HANFIS", "b_pers"))):
    print(f"   {k}: " + " | ".join(f"{n} {C[k][:, j].mean():+.3f} [{C[k][:, j].min():+.3f}, {C[k][:, j].max():+.3f}]" for j, n in enumerate(names)))
print("\nSkill silang (CI95 per image) -- positif berarti model pertama lebih baik:")
for m, r, note in (("FH", "F_rc", "nilai tambah HANFIS di atas rumus"), ("FP", "F_rc", "nilai tambah persistence di atas rumus"), ("FH", "FP", "HANFIS dibanding persistence sebagai prediktor kedua"), ("FHP", "FP", "HANFIS ditambahkan ke rumus + persistence"), ("FH", "F_mentah", "rumus + HANFIS dibanding rumus mentah")):
    pt, ci = skill(m, r); print(f"   {m} vs {r:8s}: {pt:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]  ({note})")
pt, ci = skill("FH_dalam", "F_rc_dalam"); print(f"\nBatas atas dalam-sampel, FH vs F_rc: {pt:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]")
print("\nSTATUS=E24_DONE (deskriptif, post hoc)")
