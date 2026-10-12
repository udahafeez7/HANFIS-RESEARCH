#!/usr/bin/env python
"""E12 -- campuran rumus bentuk-maks dengan persistence atau HANFIS (POST HOC, deskriptif; tidak masuk keluarga keputusan E7). Hanya numpy dan pandas; tidak melatih apa pun.
Memakai prediksi out-of-fold E11 (kolom y_true, y_maxform, y_pers, y_full, image_id, fold). Bobot lambda tiap fold dipasang pada fold LAIN (leave-one-fold-out, tanpa optimisme):
  y = lambda * y_a + (1 - lambda) * y_b,  lambda* = sum((a-b)(y-b)) / sum((a-b)^2), dibatasi [0, 1].  CI95 bootstrap per image (mengabaikan ketidakpastian lambda).
  python scripts/e12_blend_analysis.py [--pred results_python/e11/e11_predictions_*.csv]"""
import argparse, glob, sys
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("--pred", default="results_python/e11/e11_predictions_*.csv"); ap.add_argument("--boot", type=int, default=2000)
ap.add_argument("--seed", type=int, default=20261012); a = ap.parse_args()
fs = sorted(glob.glob(a.pred))
if not fs: sys.exit(f"ABORT: tidak ada berkas {a.pred}")
M = pd.read_csv(fs[-1]); print(f"berkas: {fs[-1]} | baris {len(M)} | image {M.image_id.nunique()} | fold {sorted(M.fold.unique())}")
for c in ("y_true", "y_maxform", "y_pers", "y_full", "image_id", "fold"):
    if c not in M: sys.exit(f"ABORT: kolom {c} tidak ada")


def lam(a_, b_, y_):
    d = a_ - b_; den = float((d * d).sum()); return 0.5 if den == 0 else float(np.clip((d * (y_ - b_)).sum() / den, 0.0, 1.0))


groups = sorted(M.image_id.unique()); gi = {g: i for i, g in enumerate(groups)}; idx = M.image_id.map(gi).to_numpy(); G = len(groups); cnt = np.random.default_rng(a.seed).multinomial(G, np.full(G, 1.0 / G), size=a.boot)
def sse_by_group(pred): v = np.zeros(G); np.add.at(v, idx, (pred - M.y_true.to_numpy()) ** 2); return v
res = {"formula": M.y_maxform.to_numpy(), "persistence": M.y_pers.to_numpy(), "HANFIS": M.y_full.to_numpy()}
for name, (ca, cb) in {"campuran rumus+persistence": ("y_maxform", "y_pers"), "campuran rumus+HANFIS": ("y_maxform", "y_full")}.items():
    out = np.zeros(len(M)); ls = {}
    for f in sorted(M.fold.unique()):
        te = (M.fold == f).to_numpy(); tr = ~te; l = lam(M.loc[tr, ca].to_numpy(), M.loc[tr, cb].to_numpy(), M.loc[tr, "y_true"].to_numpy()); ls[int(f)] = round(l, 3)
        out[te] = l * M.loc[te, ca].to_numpy() + (1 - l) * M.loc[te, cb].to_numpy()
    res[name] = out; print(f"lambda per fold (dipasang pada fold lain), {name}: {ls}")
S = {k: sse_by_group(v) for k, v in res.items()}; n = len(M)
print("\n== MSE terkumpul (skala 0-100) =="); [print(f"  {k:28} {S[k].sum() / n:8.3f}") for k in sorted(S, key=lambda k: S[k].sum())]
print("\n== SS (1 - MSE_model / MSE_acuan), CI95 bootstrap per image; SS > 0 = model lebih baik ==")
for m, b in (("campuran rumus+persistence", "formula"), ("campuran rumus+persistence", "persistence"), ("campuran rumus+HANFIS", "formula"), ("campuran rumus+HANFIS", "HANFIS"), ("formula", "persistence")):
    bs = 1 - (cnt @ S[m]) / (cnt @ S[b]); print(f"  {m:28} vs {b:12} SS = {1 - S[m].sum() / S[b].sum():+.3f} [{np.percentile(bs, 2.5):+.3f}, {np.percentile(bs, 97.5):+.3f}]")
print("\nSTATUS=E12_DONE (deskriptif, post hoc)")
