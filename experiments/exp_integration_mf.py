"""E-INT: Integration-panel membership count (m_I) comparison, PyTorch runner.

Configurations
  C24       HANFIS m_raw=2, m_intermediate=2  -> 24 rules, 132 params (historical Monev numbers)
  C34       HANFIS m_raw=2, m_intermediate=3  -> 34 rules, 176 params (amendment A-02)
  C54       HANFIS m_raw=2, m_intermediate=3, m_threat=3 -> 43 rules, 214 params
  flat128   flat 7-input ANFIS, m=2 -> 128 rules, 1052 params (reference)
Optimisers: hybrid (closed-form Integration consequents + Adam) and adam (pure gradient).

Synthetic data only validates the code path; results are not scientific claims.
Run from the repository root inside the WSL 'anfis' environment:

    python experiments/exp_integration_mf.py --output results_python/eint --seeds 5
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_hanfis"))

from hanfis_7input_experiment import FEATURES, split_indices, synthetic_dataset  # noqa: E402
from hanfis_end2end import HANFIS, SugenoPanel, fit_adam, fit_hybrid, fit_hybrid_restarts, predict  # noqa: E402


def synthetic_threshold(n: int, seed: int) -> pd.DataFrame:
    """Scenario S2: sharp interactions and thresholds (tests whether m_I matters)."""
    rng = np.random.default_rng(seed)
    f = pd.DataFrame(rng.random((n, 7)), columns=FEATURES)
    v = np.clip(0.4 * f.cvss + 0.4 * f.exploitability + 0.2 * f.patch_risk + 0.2 * f.cvss * f.exploitability * f.patch_risk, 0, 1)
    e = np.clip(0.3 * f.mfa_risk + 0.4 * f.kubernetes_exposure + 0.3 * f.asset_criticality, 0, 1)
    gate_v = 1 / (1 + np.exp(-12 * (v - 0.55)))
    gate_e = 1 / (1 + np.exp(-10 * (e - 0.45)))
    f["vulnerability_target"] = v
    f["environment_target"] = e
    f["dynamic_risk_target"] = np.clip(0.15 + 0.55 * gate_v * gate_e + 0.20 * f.threat_intelligence * gate_v + 0.10 * e, 0, 1)
    return f


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    y, p = y * 100.0, p * 100.0
    return {
        "rmse": float(np.sqrt(np.mean((y - p) ** 2))),
        "mae": float(np.mean(np.abs(y - p))),
        "r2": float(1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)),
    }


class FlatWrapper(torch.nn.Module):
    def __init__(self, m: int = 2) -> None:
        super().__init__()
        self.panel = SugenoPanel([m] * 7)
        self.integration = self.panel  # so fit_hybrid can solve consequents on the single panel

    def integration_input(self, x: torch.Tensor, clamp: bool = True) -> torch.Tensor:
        return x

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.clamp(self.panel(x), 0.0, 1.0)

    def training_forward(self, x: torch.Tensor):
        return self.panel(x), torch.zeros((), dtype=x.dtype)

    def init_from_data(self, x: np.ndarray) -> None:
        self.panel.init_centers_from_quantiles(np.asarray(x, dtype=np.float32))

    @property
    def rule_count(self) -> int:
        return self.panel.rule_count

    @property
    def parameter_count(self) -> int:
        return sum(p.numel() for p in self.parameters())


def build(config: str):
    if config == "C24":
        return HANFIS(2, 2)
    if config == "C34":
        return HANFIS(2, 3)
    if config == "C54":
        return HANFIS(2, 3, m_threat=3)
    if config == "flat128":
        return FlatWrapper(2)
    raise ValueError(config)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=Path("results_python/eint"))
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--samples", type=int, default=900)
    ap.add_argument("--epochs", type=int, default=600)
    ap.add_argument("--restarts", type=int, default=3, help="pre-registered restarts for hybrid (patch 0003)")
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    seeds = [20260721, 1, 2, 3, 4][: args.seeds]
    scenarios = {"S1_repo_smooth": synthetic_dataset, "S2_threshold": synthetic_threshold}
    rows = []
    for sname, gen in scenarios.items():
        for seed in seeds:
            frame = gen(args.samples, seed)
            x = frame[FEATURES].to_numpy(np.float32)
            y = frame["dynamic_risk_target"].to_numpy(np.float32)
            tr, va, te = split_indices(len(frame), seed)
            for config in ["C24", "C34", "C54", "flat128"]:
                for opt in ["hybrid", "adam"]:
                    torch.manual_seed(seed)
                    model = build(config)
                    t0 = time.time()
                    if opt == "hybrid":
                        # patch 0003: best of 3 pre-registered initialisations (validation loss only)
                        model, hist = fit_hybrid_restarts(lambda c=config: build(c), x[tr], y[tr], x[va], y[va],
                                                          n_restarts=args.restarts, seed=seed, epochs=args.epochs)
                    else:
                        hist = fit_adam(model, x[tr], y[tr], x[va], y[va], epochs=args.epochs)
                    m = metrics(y[te], predict(model, x[te]))
                    rows.append({"scenario": sname, "seed": seed, "config": config, "optimizer": opt, "restart": hist.get("restart", 0),
                                 "rules": model.rule_count, "params": model.parameter_count, **m,
                                 "best_epoch": hist["best_epoch"], "train_s": round(time.time() - t0, 2)})
                    print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(args.output / "eint_raw.csv", index=False)
    agg = df.groupby(["scenario", "config", "optimizer"]).agg(
        rules=("rules", "first"), params=("params", "first"),
        rmse_mean=("rmse", "mean"), rmse_sd=("rmse", "std"), rmse_median=("rmse", "median"), rmse_max=("rmse", "max"),
        r2_mean=("r2", "mean"), epoch_mean=("best_epoch", "mean"), train_s=("train_s", "mean")).reset_index()
    agg.to_csv(args.output / "eint_summary.csv", index=False)
    print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
