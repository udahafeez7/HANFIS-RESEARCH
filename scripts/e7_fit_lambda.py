#!/usr/bin/env python3
"""E7 -- menetapkan SATU parameter hibrida lambda dari prediksi out-of-fold E4 (label <= 2026-08-24). Tidak menyentuh data forward.
  y_hat = lambda * y_hat_HANFIS + (1 - lambda) * y_persistence ;  lambda = argmin MSE, dijepit ke [0,1] (bentuk tertutup).
Keluaran: protocols/E7_lambda_<tanggal>.json (lambda, CI bootstrap berkelompok per image, hash masukan) + ringkasan. Jalankan dari akar repo:
  python scripts/e7_fit_lambda.py [--pred <csv>] [--date YYYY-MM-DD]"""
import argparse, hashlib, json, sys, time
from pathlib import Path
import numpy as np, pandas as pd

PRED = "results_python/e4bis_120_models/predictions_20261005T083407Z.csv"


def fit(h, p, y):
    d, r = h - p, y - p
    den = float((d * d).sum())
    return float(np.clip((d * r).sum() / den, 0.0, 1.0)) if den > 0 else 0.0


def mse(a, y):
    return float(np.mean((a - y) ** 2))


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--pred", default=PRED); ap.add_argument("--date", default=time.strftime("%Y-%m-%d", time.gmtime()))
    ap.add_argument("--boot", type=int, default=2000); ap.add_argument("--seed", type=int, default=20261008); ap.add_argument("--out-dir", default="protocols"); a = ap.parse_args(argv)
    path = Path(a.pred); raw = path.read_bytes(); df = pd.read_csv(path)
    need = {"event_id", "fold", "y_true", "y_hanfis", "y_persistence"}
    if not need <= set(df.columns): sys.exit(f"ABORT: kolom kurang: {sorted(need - set(df.columns))}")
    n0 = len(df); df = df.dropna(subset=list(need - {"event_id"})).copy()
    df["grup"] = df["event_id"].str.rsplit("__", n=1).str[0].str.replace(r"-(on|off)$", "", regex=True)
    h, p, y = (df[c].to_numpy(float) for c in ("y_hanfis", "y_persistence", "y_true"))
    lam = fit(h, p, y)
    rng = np.random.default_rng(a.seed); groups = df["grup"].unique(); idx = {g: np.where(df["grup"].to_numpy() == g)[0] for g in groups}
    boots = []
    for _ in range(a.boot):
        pick = rng.choice(len(groups), len(groups), replace=True); ii = np.concatenate([idx[groups[k]] for k in pick]); boots.append(fit(h[ii], p[ii], y[ii]))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    per_fold = {int(f): fit(g["y_hanfis"].to_numpy(float), g["y_persistence"].to_numpy(float), g["y_true"].to_numpy(float)) for f, g in df.groupby("fold")}
    ly = np.log1p(np.clip(y, 0, None) / 100.0); lam_log = fit(np.log1p(np.clip(h, 0, None) / 100.0), np.log1p(np.clip(p, 0, None) / 100.0), ly)
    m = {"mse_hanfis": mse(h, y), "mse_persistence": mse(p, y), "mse_hibrida": mse(lam * h + (1 - lam) * p, y)}
    out = {"tanggal": a.date, "lambda": lam, "ci95_bootstrap_kelompok": [float(lo), float(hi)], "lambda_per_fold": per_fold, "lambda_log1p_sensitivitas": lam_log,
           "mse_oof_dalam_sampel_OPTIMIS": m, "ss_hibrida_vs_persistence_dalam_sampel_OPTIMIS": 1 - m["mse_hibrida"] / m["mse_persistence"],
           "baris": int(len(df)), "baris_dibuang_NaN": int(n0 - len(df)), "kelompok_image": int(len(groups)), "bootstrap": a.boot, "seed": a.seed,
           "masukan": str(path), "masukan_sha256": hashlib.sha256(raw).hexdigest(), "skrip_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "catatan": "lambda dipasang pada prediksi out-of-fold yang sama yang dilaporkan di E4; SS dalam sampel bersifat optimis dan BUKAN hasil E7."}
    od = Path(a.out_dir); od.mkdir(parents=True, exist_ok=True); fp = od / f"E7_lambda_{a.date}.json"
    if fp.exists(): sys.exit(f"ABORT: {fp} sudah ada (lambda dibekukan sekali)")
    fp.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"lambda = {lam:.4f}  CI95 bootstrap [{lo:.4f}, {hi:.4f}]  ({len(groups)} kelompok image, {len(df)} baris)")
    print("per fold:", {k: round(v, 3) for k, v in per_fold.items()}, "| sensitivitas log1p:", round(lam_log, 4))
    print(f"MSE OOF: HANFIS={m['mse_hanfis']:.4f} persistence={m['mse_persistence']:.4f} hibrida={m['mse_hibrida']:.4f} (dalam sampel, optimis)")
    print(f"ditulis: {fp}\nSTATUS=E7_LAMBDA_FIT_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
