#!/usr/bin/env python
"""E10 -- pembanding informasi-minimal (POST HOC, eksploratori): apakah HANFIS mengalahkan fungsi paling sederhana dari x2 (EPSS x rho) dan x7 (KEV)?
Lipatan, pembagian latih/validasi, dan pembanding E4 IDENTIK dengan scripts/e4_run.py (diimpor dari sana; lipatan diperiksa sama dengan prediksi E4-bis). Tidak ada pelatihan ulang HANFIS:
yang dibandingkan adalah y_hanfis (rata-rata 5 seed) dari berkas prediksi E4-bis. Cepat (menit).
Pembanding baru: plugin (100 x x2), ridge-2 (x2, x7), gbm-2 (x2, x7), gbm-7 (semua masukan), ridge-lag (y_lag4, x2, x7), gbm-lag (y_lag4 + 7 masukan). GBM = HistGradientBoostingRegressor (sklearn), bila tersedia.
  python scripts/e10_minimal_baselines.py"""
from __future__ import annotations
import argparse, datetime as dt, json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "data" / "processed" / "asset_weeks_v2_120assets_e4bis.csv"
E4PRED = ROOT / "results_python" / "e4bis_120_models" / "predictions_20261005T083407Z.csv"


def boot_ss(M, pairs, B, seed):
    groups = sorted(M["image_id"].unique()); gi = {g: i for i, g in enumerate(groups)}; idx = M["image_id"].map(gi).to_numpy(); G = len(groups); sse = {}
    for c in {c for p in pairs for c in p[:2]}:
        a = np.zeros(G); np.add.at(a, idx, (M[f"y_{c}"].to_numpy() - M["y_true"].to_numpy()) ** 2); sse[c] = a
    counts = np.random.default_rng(seed).multinomial(G, np.full(G, 1.0 / G), size=B); out = []
    for a, b in pairs:
        bs = 1.0 - (counts @ sse[a]) / (counts @ sse[b])
        out.append({"a": a, "b": b, "ss": float(1.0 - sse[a].sum() / sse[b].sum()), "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], "mse_a": float(sse[a].sum() / len(M)), "mse_b": float(sse[b].sum() / len(M))})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", default=str(TABLE)); ap.add_argument("--e4-pred", default=str(E4PRED)); ap.add_argument("--out-dir", default=str(ROOT / "results_python" / "e10"))
    ap.add_argument("--n-splits", type=int, default=5); ap.add_argument("--embargo-days", type=int, default=30); ap.add_argument("--min-train-weeks", type=int, default=4); ap.add_argument("--lag-weeks", type=int, default=4)
    ap.add_argument("--boot", type=int, default=2000); ap.add_argument("--boot-seed", type=int, default=20261009); a = ap.parse_args(argv)
    sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "python_hanfis"))
    import e4_run as E  # noqa: E402
    try:
        from sklearn.ensemble import HistGradientBoostingRegressor as GBR
    except Exception as ex:
        GBR = None; print(f"PERINGATAN: scikit-learn tidak dapat diimpor ({type(ex).__name__}: {str(ex)[:80]}); pembanding gbm dilewati")
    i2, i7 = E.INPUTS.index("exploitability"), E.INPUTS.index("threat_intelligence")
    df = pd.read_csv(a.table); df["week_start_utc"] = pd.to_datetime(df["week_start_utc"], utc=True); df["asset_id"] = df["event_id"].str.rsplit("__", n=1).str[0]
    df = df.sort_values(["asset_id", "week_start_utc"]).reset_index(drop=True); df["y_lag"] = df.groupby("asset_id")["y"].shift(a.lag_weeks); sup = df.dropna(subset=["y"]).reset_index(drop=True)
    X = E.normalise(sup); y = sup["y"].to_numpy(dtype=np.float64)
    sp = E.GroupTimeSplit(n_splits=min(a.n_splits, sup["image_id"].nunique()), embargo_days=a.embargo_days, min_train_weeks=a.min_train_weeks); folds = sp.split(sup); sp.assert_no_leakage(sup, folds)
    p4 = pd.read_csv(a.e4_pred)
    for f in folds:
        if set(sup.iloc[f.test_index]["event_id"]) != set(p4.loc[p4["fold"] == f.index, "event_id"]):
            print(f"ABORT: lipatan {f.index} berbeda dari prediksi E4-bis"); return 2
    print(f"lipatan identik dengan prediksi E4-bis ({len(folds)} fold); GBM: {'ya' if GBR else 'tidak'}")
    rows = []
    for f in folds:
        tr_all, te = f.train_index, f.test_index; nv = max(1, int(0.15 * len(tr_all))); rng = np.random.default_rng(20260928 + f.index)
        va = rng.choice(tr_all, size=nv, replace=False); tr = np.setdiff1d(tr_all, va); clim = float(y[tr].mean())
        lag = np.where(np.isnan(sup["y_lag"].to_numpy()), clim, sup["y_lag"].to_numpy())
        r = {"plugin": np.clip(100.0 * X[te][:, i2], 0.0, 100.0), "pers": lag[te]}
        r["ridge2"] = E.ridge_predict(E.ridge_fit(X[tr][:, [i2, i7]], y[tr]), X[te][:, [i2, i7]])
        Xl = np.c_[lag, X[:, i2], X[:, i7]]; r["ridgelag"] = E.ridge_predict(E.ridge_fit(Xl[tr], y[tr]), Xl[te])
        if GBR:
            Xg = np.c_[lag, X]
            for name, cols, src in (("gbm2", [i2, i7], X), ("gbm7", list(range(X.shape[1])), X), ("gbmlag", list(range(Xg.shape[1])), Xg)):
                m = GBR(max_iter=200, learning_rate=0.1, random_state=20261009).fit(src[tr][:, cols], y[tr]); r[name] = m.predict(src[te][:, cols])
        for i, ri in enumerate(te): rows.append({"event_id": sup.iloc[ri]["event_id"], "image_id": sup.iloc[ri]["image_id"], "fold": f.index, "y_true": y[ri], **{f"y_{k}": v[i] for k, v in r.items()}})
    M = pd.DataFrame(rows).merge(p4[["event_id", "y_hanfis", "y_cvss_only", "y_persistence"]].rename(columns={"y_hanfis": "y_full", "y_cvss_only": "y_cvss"}), on="event_id", how="left", validate="one_to_one")
    chk = float((M["y_pers"] - M["y_persistence"]).abs().max()); print(f"pencocokan persistence dengan E4-bis: selisih maks {chk:.1e}")
    base = [c[2:] for c in M.columns if c.startswith("y_") and c not in ("y_true", "y_full", "y_cvss", "y_persistence", "y_pers")]
    mse = {c: float(((M[f"y_{c}"] - M["y_true"]) ** 2).mean()) for c in ["full", "cvss", "pers"] + base}
    print("== MSE terkumpul (skala 0-100) =="); [print(f"  {k:10} {v:9.3f}") for k, v in sorted(mse.items(), key=lambda t: t[1])]
    res = boot_ss(M, [("full", c) for c in ["cvss", "pers"] + base], a.boot, a.boot_seed)
    print(f"== SS HANFIS (rata-rata 5 seed, E4-bis) terhadap pembanding; CI95 bootstrap per image; SS > 0 = HANFIS lebih baik ({len(M)} baris) ==")
    for r in res: print(f"  vs {r['b']:9} SS = {r['ss']:+.3f}  [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}]   (MSE {r['mse_a']:.3f} vs {r['mse_b']:.3f})")
    od = Path(a.out_dir); od.mkdir(parents=True, exist_ok=True); stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    M.to_csv(od / f"e10_predictions_{stamp}.csv", index=False)
    (od / f"e10_summary_{stamp}.json").write_text(json.dumps({"post_hoc": True, "baris": int(len(M)), "mse": mse, "ss_hanfis_vs": res}, indent=1), encoding="utf-8"); print(f"STATUS=E10_DONE ({od}/e10_summary_{stamp}.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
