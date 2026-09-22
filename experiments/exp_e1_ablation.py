"""E1 ablation (Rencana Eksperimen v2.1): MF family x monotone constraint, HANFIS C34, hybrid + restarts.

Factors (pre-registered):
  mf_family  in {gauss, ruspini}   (A-03)
  monotone   in {False, True}      (A-04)
Scenarios S1 (smooth) and S2 (threshold), 5 seeds, best of 3 restarts on validation loss.
The MF family and constraint used in E4 are chosen from this table BEFORE E4 is run.
Synthetic data validates the code path only.

    python experiments/exp_e1_ablation.py --output results_python/e1 --seeds 5
"""
from __future__ import annotations
import argparse, sys, time
from pathlib import Path
import numpy as np, pandas as pd, torch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_hanfis")); sys.path.insert(0, str(ROOT / "experiments"))
from hanfis_7input_experiment import FEATURES, split_indices, synthetic_dataset  # noqa: E402
from hanfis_end2end import HANFIS, fit_hybrid_restarts, predict  # noqa: E402
from exp_integration_mf import metrics, synthetic_threshold  # noqa: E402


def monotonicity_violation(model: HANFIS, x: np.ndarray, eps: float = 0.02) -> float:
    """Share of (row, input) pairs where increasing one input by eps decreases the risk score."""
    base = predict(model, x); viol = 0; total = 0
    for j in range(x.shape[1]):
        xp = x.copy(); xp[:, j] = np.clip(xp[:, j] + eps, 0, 1)
        d = predict(model, xp) - base
        viol += int((d < -1e-6).sum()); total += len(d)
    return viol / total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=Path("results_python/e1"))
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=600)
    ap.add_argument("--restarts", type=int, default=3)
    args = ap.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    for sname, gen in {"S1_repo_smooth": synthetic_dataset, "S2_threshold": synthetic_threshold}.items():
        for seed in [20260721, 1, 2, 3, 4][: args.seeds]:
            f = gen(900, seed); x = f[FEATURES].to_numpy(np.float32); y = f["dynamic_risk_target"].to_numpy(np.float32)
            tr, va, te = split_indices(len(f), seed)
            for mf in ("gauss", "ruspini"):
                for mono in (False, True):
                    t0 = time.time()
                    model, hist = fit_hybrid_restarts(lambda: HANFIS(2, 3, mf_family=mf, monotone=mono), x[tr], y[tr], x[va], y[va],
                                                      n_restarts=args.restarts, seed=seed, epochs=args.epochs)
                    m = metrics(y[te], predict(model, x[te]))
                    rows.append({"scenario": sname, "seed": seed, "mf_family": mf, "monotone": mono, "rules": model.rule_count,
                                 "params": model.parameter_count, **m, "monotonicity_violation": monotonicity_violation(model, x[te]),
                                 "best_epoch": hist["best_epoch"], "restart": hist["restart"], "train_s": round(time.time() - t0, 1)})
                    print(rows[-1], flush=True)
    df = pd.DataFrame(rows); df.to_csv(args.output / "e1_raw.csv", index=False)
    agg = df.groupby(["scenario", "mf_family", "monotone"]).agg(params=("params", "first"), rmse_mean=("rmse", "mean"), rmse_sd=("rmse", "std"),
        rmse_median=("rmse", "median"), rmse_max=("rmse", "max"), r2_mean=("r2", "mean"), mono_viol=("monotonicity_violation", "mean"),
        train_s=("train_s", "mean")).reset_index()
    agg.to_csv(args.output / "e1_summary.csv", index=False); print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
