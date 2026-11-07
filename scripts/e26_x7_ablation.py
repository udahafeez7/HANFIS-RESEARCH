#!/usr/bin/env python
"""E26: x7-only ablation for H4 (POST HOC, descriptive, unregistered; protocols/E26_h4_and_documentation_protocol_2026-11-07.md).

Same procedure as scripts/e9_ablation.py (frozen folds, seeds, embargo, validation split, hyperparameters; helpers imported from
scripts/e4_run.py) but ONLY the threat-intelligence input x7 (KEV indicator) is replaced by the constant 0 in training and test data.
'Full HANFIS' is the y_hanfis column of the E4-bis prediction file. Metrics: pooled-MSE skill score (SS = 1 - MSE_a / MSE_b) with an
image-clustered bootstrap, and E15's weekly ranking metrics (Spearman, precision at top 20%, weeks with >= 15 assets) with a paired
week bootstrap.

  python scripts/e26_x7_ablation.py --run      # real run: 5 folds x 5 seeds x 3 restarts (run once)
  python scripts/e26_x7_ablation.py --smoke    # function check only: 1 seed, 1 restart, 40 epochs; output is discarded
"""
from __future__ import annotations

import argparse, datetime as dt, json, sys, time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "data" / "processed" / "asset_weeks_v2_120assets_e4bis.csv"
E4PRED = ROOT / "results_python" / "e4bis_120_models" / "predictions_20261005T083407Z.csv"
BOOT, BOOT_SEED, MIN_ASSETS, TOP = 2000, 20261107, 15, 0.20
PAIRS = [("masked7", "full", "HANFIS without x7 vs full HANFIS"), ("masked7", "pers", "HANFIS without x7 vs persistence"),
         ("masked7", "cvss", "HANFIS without x7 vs CVSS only"), ("full", "pers", "full HANFIS vs persistence (reference)"),
         ("full", "cvss", "full HANFIS vs CVSS only (reference)")]


def boot_ss(M, pairs, B, seed):
    groups = sorted(M["image_id"].unique()); gi = {g: i for i, g in enumerate(groups)}; idx = M["image_id"].map(gi).to_numpy(); G = len(groups)
    cols = {c for p in pairs for c in p[:2]}; sse = {}
    for c in cols:
        a = np.zeros(G); np.add.at(a, idx, (M[f"y_{c}"].to_numpy() - M["y_true"].to_numpy()) ** 2); sse[c] = a
    rng = np.random.default_rng(seed); counts = rng.multinomial(G, np.full(G, 1.0 / G), size=B); out = []
    for a, b, label in pairs:
        pt = 1.0 - sse[a].sum() / sse[b].sum(); bs = 1.0 - (counts @ sse[a]) / (counts @ sse[b])
        out.append({"pair": label, "ss": float(pt), "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                    "mse_a": float(sse[a].sum() / len(M)), "mse_b": float(sse[b].sum() / len(M))})
    return out


def spearman(x, y):
    if np.ptp(x) == 0 or np.ptp(y) == 0:
        return 0.0
    rx, ry = pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy(); return float(np.corrcoef(rx, ry)[0, 1])


def prec(pred, y, top, rng):   # same definition as scripts/e15_ranking.py
    n = len(y); k = max(1, int(np.ceil(top * n))); thr = np.quantile(y, 1 - top); hi = y >= thr
    order = np.argsort(-(pred + rng.normal(0, 1e-9, n)), kind="stable"); return float(hi[order[:k]].mean())


def ranking(M, B, seed):
    rng = np.random.default_rng(seed); M = M.copy(); M["week"] = M["event_id"].str.rsplit("__", n=1).str[1]; rows = []
    for w, g in M.groupby("week"):
        if len(g) < MIN_ASSETS:
            continue
        y = g["y_true"].to_numpy(float); r = {"week": w, "n": len(g)}
        for m in ("masked7", "full", "pers"):
            p = g[f"y_{m}"].to_numpy(float); r[f"sp_{m}"] = spearman(p, y); r[f"pr_{m}"] = prec(p, y, TOP, rng)
        rows.append(r)
    W = pd.DataFrame(rows); cnt = rng.integers(0, len(W), size=(B, len(W))); out = {"weeks": int(len(W)), "means": {}, "paired": {}}
    for m in ("masked7", "full", "pers"):
        out["means"][m] = {"spearman": float(W[f"sp_{m}"].mean()), "precision_top20": float(W[f"pr_{m}"].mean())}
    for lab, (m1, m2) in {"masked7 - full": ("masked7", "full"), "masked7 - persistence": ("masked7", "pers"), "full - persistence": ("full", "pers")}.items():
        d = {}
        for met, pre in (("spearman", "sp"), ("precision_top20", "pr")):
            x = (W[f"{pre}_{m1}"] - W[f"{pre}_{m2}"]).to_numpy(); bs = x[cnt].mean(axis=1)
            d[met] = {"mean_diff": float(x.mean()), "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]}
        out["paired"][lab] = d
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--run", action="store_true"); g.add_argument("--smoke", action="store_true")
    a = ap.parse_args(argv); smoke = a.smoke
    sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "python_hanfis"))
    import e4_run as E
    seeds = E.SEEDS[:1] if smoke else E.SEEDS; n_restarts = 1 if smoke else 3; epochs = 40 if smoke else 600; min_epochs = 1 if smoke else 200
    mask_idx = [E.INPUTS.index("threat_intelligence")]
    print(f"{'SMOKE (not a result) | ' if smoke else ''}masked input: threat_intelligence (x7) only; seeds {seeds}")
    df = pd.read_csv(TABLE); df["week_start_utc"] = pd.to_datetime(df["week_start_utc"], utc=True)
    df["asset_id"] = df["event_id"].str.rsplit("__", n=1).str[0]; df = df.sort_values(["asset_id", "week_start_utc"]).reset_index(drop=True)
    df["y_lag"] = df.groupby("asset_id")["y"].shift(4); sup = df.dropna(subset=["y"]).reset_index(drop=True)
    X_full = E.normalise(sup); X_m = X_full.copy(); X_m[:, mask_idx] = 0.0
    y_raw = sup["y"].to_numpy(dtype=np.float64); y01 = np.clip(y_raw / 100.0, 0.0, 1.0)
    sp = E.GroupTimeSplit(n_splits=min(5, sup["image_id"].nunique()), embargo_days=30, min_train_weeks=4); folds = sp.split(sup); sp.assert_no_leakage(sup, folds)
    p4 = pd.read_csv(E4PRED)
    for f in folds:
        mine = set(sup.iloc[f.test_index]["event_id"]); theirs = set(p4.loc[p4["fold"] == f.index, "event_id"])
        if mine != theirs:
            print(f"ABORT: fold {f.index} differs from the E4-bis predictions"); return 2
    print(f"folds identical to the E4-bis predictions ({len(folds)})")
    rows, t0 = [], time.time()
    for f in folds:
        tr_all, te = f.train_index, f.test_index; n_val = max(1, int(0.15 * len(tr_all))); rng = np.random.default_rng(20260928 + f.index)
        val_idx = rng.choice(tr_all, size=n_val, replace=False); tr_idx = np.setdiff1d(tr_all, val_idx)
        clim = float(y_raw[tr_idx].mean()); pers_raw = sup["y_lag"].to_numpy()[te]; y_pers = np.where(np.isnan(pers_raw), clim, pers_raw)
        y_cvss = E.ridge_predict(E.ridge_fit(X_full[tr_idx][:, :1], y_raw[tr_idx]), X_full[te][:, :1])
        preds = []
        for seed in seeds:
            model, val = E.train_best_of_restarts(E.fit_hybrid_lower_alternating, lambda: E.HANFIS(m_raw=2, m_intermediate=3, mf_family="gauss", monotone=True),
                                                  X_m[tr_idx], y01[tr_idx], X_m[val_idx], y01[val_idx], n_restarts, seed, epochs=epochs, patience=100, min_epochs=min_epochs, ridge=None)
            preds.append(E.hanfis_predict(model, X_m[te])); print(f"fold {f.index}  HANFIS without x7 seed={seed}  best_val_mse={val:.5f}")
        y_masked = np.mean(preds, axis=0) * 100.0
        for i, ri in enumerate(te):
            rows.append({"event_id": sup.iloc[ri]["event_id"], "image_id": sup.iloc[ri]["image_id"], "fold": f.index, "y_true": y_raw[ri],
                         "y_masked7": y_masked[i], "y_cvss": y_cvss[i], "y_pers": y_pers[i]})
        print(f"fold {f.index} done ({len(te)} test rows, {time.time() - t0:.0f} s)")
    R = pd.DataFrame(rows)
    M = R.merge(p4[["event_id", "y_hanfis", "y_cvss_only", "y_persistence"]], on="event_id", how="left", validate="one_to_one").rename(columns={"y_hanfis": "y_full"})
    chk = {"cvss": float((M["y_cvss"] - M["y_cvss_only"]).abs().max()), "pers": float((M["y_pers"] - M["y_persistence"]).abs().max())}
    print(f"comparator match with the E4-bis file (max abs diff): CVSS {chk['cvss']:.1e}, persistence {chk['pers']:.1e}")
    M = M.rename(columns={"y_masked7": "y_masked7"}); M = M[M["y_full"].notna()]
    res = boot_ss(M, PAIRS, BOOT, BOOT_SEED); rk = ranking(M, BOOT, BOOT_SEED)
    print(f"== E26{' (SMOKE, not a result)' if smoke else ''}: pooled skill score (95% image-clustered bootstrap CI, {BOOT} resamples), {len(M)} rows ==")
    for r in res:
        print(f"  {r['pair']:46} SS = {r['ss']:+.3f}  [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}]   (MSE {r['mse_a']:.3f} vs {r['mse_b']:.3f})")
    print(f"== weekly ranking (E15 definitions), {rk['weeks']} weeks ==")
    for m, v in rk["means"].items():
        print(f"  {m:10} Spearman {v['spearman']:.3f}  precision@20% {v['precision_top20']:.3f}")
    for lab, d in rk["paired"].items():
        print(f"  {lab:24} " + " | ".join(f"{k} {v['mean_diff']:+.3f} [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}]" for k, v in d.items()))
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"); od = ROOT / "results_python" / ("e26_smoke" if smoke else "e26"); od.mkdir(parents=True, exist_ok=True)
    M.to_csv(od / f"e26_predictions_{stamp}.csv", index=False)
    (od / f"e26_summary_{stamp}.json").write_text(json.dumps({"post_hoc": True, "smoke": smoke, "seeds": seeds, "n_restarts": n_restarts, "epochs": epochs, "rows": int(len(M)),
                                                              "comparator_check": chk, "skill_score": res, "ranking": rk}, indent=1), encoding="utf-8")
    print(f"STATUS={'E26_SMOKE_DONE' if smoke else 'E26_DONE'} ({od}/e26_summary_{stamp}.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
