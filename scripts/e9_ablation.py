#!/usr/bin/env python
"""E9 -- ablasi tanpa bahan label (POST HOC, eksploratori; bukan bagian protokol E4).

Pertanyaan: berapa banyak kemampuan HANFIS yang tersisa bila masukan yang juga bahan label (x2 exploitability dan x7 KEV; E8: 78,9% atribusi) disembunyikan?
Prosedur: HANFIS dilatih ulang dengan x2 dan x7 diganti konstanta 0 (latih DAN uji), lipatan, seed, embargo, validasi, dan hiperparameter IDENTIK dengan scripts/e4_run.py
(diimpor dari sana; lipatan diperiksa sama dengan prediksi E4-bis). Pembanding pada informasi yang sama: ridge pada lima masukan sisa (x1, x3, x4, x5, x6); pembanding E4 (CVSS-saja,
persistence, ridge-7) dihitung ulang dan dicocokkan dengan berkas prediksi E4-bis.
Keluaran: results_python/e9/e9_predictions_*.csv, e9_summary_*.json, tabel skill score (SS = 1 - MSE_model/MSE_pembanding) dengan CI bootstrap berkelompok per image.
  python scripts/e9_ablation.py                  (penuh; 5 fold x 5 seed x 3 restart; jalankan di latar belakang)
  python scripts/e9_ablation.py --smoke          (uji cepat: 1 seed, 1 restart, 40 epoch; HASILNYA BUKAN HASIL E9)"""
from __future__ import annotations

import argparse, datetime as dt, json, sys, time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "data" / "processed" / "asset_weeks_v2_120assets_e4bis.csv"
E4PRED = ROOT / "results_python" / "e4bis_120_models" / "predictions_20261005T083407Z.csv"
PAIRS = [("masked", "cvss", "HANFIS tanpa x2,x7 vs CVSS-saja"), ("masked", "ridge5", "HANFIS tanpa x2,x7 vs ridge-5 (informasi sama)"), ("masked", "pers", "HANFIS tanpa x2,x7 vs persistence"),
         ("masked", "full", "HANFIS tanpa x2,x7 vs HANFIS penuh"), ("full", "cvss", "HANFIS penuh vs CVSS-saja (acuan H1a)"), ("full", "pers", "HANFIS penuh vs persistence (acuan H1b)"),
         ("ridge5", "cvss", "ridge-5 vs CVSS-saja")]


def boot_ss(M: pd.DataFrame, pairs, B: int, seed: int):
    """SS terkumpul dan CI95 bootstrap berkelompok per image untuk tiap pasangan (a, b): 1 - MSE_a / MSE_b."""
    groups = sorted(M["image_id"].unique()); gi = {g: i for i, g in enumerate(groups)}; idx = M["image_id"].map(gi).to_numpy(); G = len(groups)
    cols = {c for p in pairs for c in p[:2]}; sse = {}
    for c in cols:
        a = np.zeros(G); np.add.at(a, idx, (M[f"y_{c}"].to_numpy() - M["y_true"].to_numpy()) ** 2); sse[c] = a
    rng = np.random.default_rng(seed); counts = rng.multinomial(G, np.full(G, 1.0 / G), size=B); out = []
    for a, b, label in pairs:
        pt = 1.0 - sse[a].sum() / sse[b].sum(); bs = 1.0 - (counts @ sse[a]) / (counts @ sse[b])
        out.append({"pasangan": label, "ss": float(pt), "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                    "mse_a": float(sse[a].sum() / len(M)), "mse_b": float(sse[b].sum() / len(M))})
    return out


def per_fold(M: pd.DataFrame, pairs):
    rows = []
    for f, g in M.groupby("fold"):
        r = {"fold": int(f), "baris": int(len(g))}
        for a, b, _ in pairs[:3]:
            r[f"ss_{a}_vs_{b}"] = float(1.0 - ((g[f"y_{a}"] - g["y_true"]) ** 2).sum() / ((g[f"y_{b}"] - g["y_true"]) ** 2).sum())
        rows.append(r)
    return pd.DataFrame(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", default=str(TABLE)); ap.add_argument("--e4-pred", default=str(E4PRED)); ap.add_argument("--out-dir", default=str(ROOT / "results_python" / "e9"))
    ap.add_argument("--mask", nargs="+", default=["exploitability", "threat_intelligence"]); ap.add_argument("--n-splits", type=int, default=5); ap.add_argument("--embargo-days", type=int, default=30)
    ap.add_argument("--min-train-weeks", type=int, default=4); ap.add_argument("--n-restarts", type=int, default=3); ap.add_argument("--epochs", type=int, default=600); ap.add_argument("--lag-weeks", type=int, default=4)
    ap.add_argument("--boot", type=int, default=2000); ap.add_argument("--boot-seed", type=int, default=20261009); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--skip-fold-check", action="store_true")
    a = ap.parse_args(argv)
    sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "python_hanfis"))
    import torch  # noqa: E402
    import e4_run as E  # noqa: E402
    seeds = E.SEEDS[:1] if a.smoke else E.SEEDS; n_restarts = 1 if a.smoke else a.n_restarts; epochs = 40 if a.smoke else a.epochs; min_epochs = 1 if a.smoke else 200
    mask_idx = [E.INPUTS.index(n) for n in a.mask]; keep = [j for j in range(len(E.INPUTS)) if j not in mask_idx]
    print(f"{'SMOKE (bukan hasil E9) | ' if a.smoke else ''}masukan disembunyikan: {a.mask}; sisa: {[E.INPUTS[j] for j in keep]}; seed {seeds}")

    df = pd.read_csv(a.table); df["week_start_utc"] = pd.to_datetime(df["week_start_utc"], utc=True)
    df["asset_id"] = df["event_id"].str.rsplit("__", n=1).str[0]; df = df.sort_values(["asset_id", "week_start_utc"]).reset_index(drop=True)
    df["y_lag"] = df.groupby("asset_id")["y"].shift(a.lag_weeks); sup = df.dropna(subset=["y"]).reset_index(drop=True)
    X_full = E.normalise(sup); X_m = X_full.copy(); X_m[:, mask_idx] = 0.0
    y_raw = sup["y"].to_numpy(dtype=np.float64); y01 = np.clip(y_raw / 100.0, 0.0, 1.0)
    n_groups = min(a.n_splits, sup["image_id"].nunique()); sp = E.GroupTimeSplit(n_splits=n_groups, embargo_days=a.embargo_days, min_train_weeks=a.min_train_weeks)
    folds = sp.split(sup); sp.assert_no_leakage(sup, folds)
    p4 = pd.read_csv(a.e4_pred)
    if not a.skip_fold_check:
        for f in folds:
            mine = set(sup.iloc[f.test_index]["event_id"]); theirs = set(p4.loc[p4["fold"] == f.index, "event_id"])
            if mine != theirs:
                print(f"ABORT: lipatan {f.index} berbeda dari prediksi E4-bis ({len(mine ^ theirs)} event_id selisih); parameter --table/--n-splits/--embargo-days harus sama"); return 2
        print(f"lipatan identik dengan prediksi E4-bis ({len(folds)} fold)")

    rows, t0 = [], time.time()
    for f in folds:
        tr_all, te = f.train_index, f.test_index
        n_val = max(1, int(0.15 * len(tr_all))); rng = np.random.default_rng(20260928 + f.index)
        val_idx = rng.choice(tr_all, size=n_val, replace=False); tr_idx = np.setdiff1d(tr_all, val_idx)
        clim = float(y_raw[tr_idx].mean()); pers_raw = sup["y_lag"].to_numpy()[te]; y_pers = np.where(np.isnan(pers_raw), clim, pers_raw)
        y_cvss = E.ridge_predict(E.ridge_fit(X_full[tr_idx][:, :1], y_raw[tr_idx]), X_full[te][:, :1])
        y_ridge7 = E.ridge_predict(E.ridge_fit(X_full[tr_idx], y_raw[tr_idx]), X_full[te])
        y_ridge5 = E.ridge_predict(E.ridge_fit(X_full[tr_idx][:, keep], y_raw[tr_idx]), X_full[te][:, keep])
        preds = []
        for seed in seeds:
            model, val = E.train_best_of_restarts(E.fit_hybrid_lower_alternating, lambda: E.HANFIS(m_raw=2, m_intermediate=3, mf_family="gauss", monotone=True),
                                                  X_m[tr_idx], y01[tr_idx], X_m[val_idx], y01[val_idx], n_restarts, seed, epochs=epochs, patience=100, min_epochs=min_epochs, ridge=None)
            preds.append(E.hanfis_predict(model, X_m[te])); print(f"fold {f.index}  HANFIS tanpa {a.mask} seed={seed}  best_val_mse={val:.5f}")
        y_masked = np.mean(preds, axis=0) * 100.0
        for i, ri in enumerate(te):
            rows.append({"event_id": sup.iloc[ri]["event_id"], "image_id": sup.iloc[ri]["image_id"], "fold": f.index, "y_true": y_raw[ri], "y_masked": y_masked[i], "y_cvss": y_cvss[i],
                         "y_pers": y_pers[i], "y_ridge7": y_ridge7[i], "y_ridge5": y_ridge5[i]})
        print(f"fold {f.index} selesai ({len(te)} baris uji, {time.time() - t0:.0f} dtk)")
    R = pd.DataFrame(rows)
    M = R.merge(p4[["event_id", "y_hanfis", "y_cvss_only", "y_persistence", "y_ridge_7inputs"]], on="event_id", how="left", validate="one_to_one")
    chk = {"cvss": float((M["y_cvss"] - M["y_cvss_only"]).abs().max()), "pers": float((M["y_pers"] - M["y_persistence"]).abs().max()), "ridge7": float((M["y_ridge7"] - M["y_ridge_7inputs"]).abs().max())}
    print(f"pencocokan pembanding dengan prediksi E4-bis (selisih maks): CVSS {chk['cvss']:.1e}, persistence {chk['pers']:.1e}, ridge-7 {chk['ridge7']:.1e}")
    M = M.rename(columns={"y_hanfis": "y_full"}); ok = M["y_full"].notna()
    if not ok.all(): print(f"PERINGATAN: {int((~ok).sum())} baris tanpa prediksi HANFIS penuh dibuang dari tabel SS"); M = M[ok]
    res = boot_ss(M, PAIRS, a.boot, a.boot_seed); pf = per_fold(M, PAIRS)
    print(f"== E9{' (SMOKE, bukan hasil)' if a.smoke else ''}: skill score terkumpul (CI95 bootstrap per image, {a.boot} resampel), {len(M)} baris ==")
    for r in res: print(f"  {r['pasangan']:48} SS = {r['ss']:+.3f}  [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}]   (MSE {r['mse_a']:.3f} vs {r['mse_b']:.3f})")
    print("== per fold (SS) ==\n" + pf.round(3).to_string(index=False))
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"); od = Path(a.out_dir); od.mkdir(parents=True, exist_ok=True)
    M.to_csv(od / f"e9_predictions_{stamp}.csv", index=False)
    (od / f"e9_summary_{stamp}.json").write_text(json.dumps({"post_hoc": True, "smoke": a.smoke, "mask": a.mask, "seeds": seeds, "n_restarts": n_restarts, "epochs": epochs, "baris": int(len(M)), "kecocokan_pembanding": chk,
                                                              "skill_score": res, "per_fold": pf.to_dict(orient="records")}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"STATUS=E9_DONE{' (SMOKE)' if a.smoke else ''} ({od}/e9_summary_{stamp}.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
