"""FlatANFISMatched smoke test -- RUN THIS FIRST, before using it in E4.

I could not execute torch in the sandbox that wrote this (no disk space to install it there);
the clustering/parameter-budget math was verified independently in pure NumPy first
(python_hanfis/verify_clustering.py: 8/8 independent datasets hit the +/-5% band of 176 params
via per-dataset radius search). This test exercises the same logic through the real torch
FlatANFISMatched class and must pass before it is trusted for E4.

    python -m pytest -q tests/test_flat_anfis_matched_smoke.py -v
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_hanfis"))
from flat_anfis_matched import (  # noqa: E402
    ClusterSearchError, build_matched, fit_hybrid, predict, search_radius_for_budget,
)


def synthetic(n=400, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.random((n, 7)).astype(np.float32)
    y = (0.3 + 0.4 * x[:, :3].mean(1) + 0.5 * x[:, 3:6].mean(1) + 0.2 * x[:, 6]
         + rng.normal(0, 0.01, n)).astype(np.float32)
    return x, np.clip(y, 0, 1)


class TestClusterBudget(unittest.TestCase):
    def test_radius_search_hits_the_176_param_budget_on_several_datasets(self):
        hits = 0
        for seed in range(6):
            rng = np.random.default_rng(seed)
            X = rng.random((300, 7)).astype(np.float64)
            result = search_radius_for_budget(X)
            if result["within_tolerance"]:
                hits += 1
                self.assertEqual(result["n_params"], 176)  # 22 * 8, the only integer in-band solution
                self.assertEqual(result["n_rules"], 8)
        self.assertGreaterEqual(hits, 5, "radius search should hit the +/-5% band on almost every dataset")

    def test_raises_a_named_error_type_available_for_callers(self):
        self.assertTrue(issubclass(ClusterSearchError, RuntimeError))


class TestFlatANFISMatched(unittest.TestCase):
    def test_build_and_train_end_to_end(self):
        x, y = synthetic(n=300, seed=1)
        x_tr, x_va = x[:220], x[220:]
        y_tr, y_va = y[:220], y[220:]
        torch.manual_seed(1)
        model, search = build_matched(x_tr.astype(np.float64))
        print(f"\n  matched model: {search['n_rules']} rules, {model.parameter_count} params "
              f"(target 176, within_tolerance={search['within_tolerance']})")
        self.assertTrue(167 <= model.parameter_count <= 185)
        hist = fit_hybrid(model, x_tr, y_tr, x_va, y_va, epochs=80, patience=30, min_epochs=30)
        print(f"  best_val_mse={hist['best_validation_loss']:.5f} at epoch {hist['best_epoch']}")
        self.assertTrue(np.isfinite(hist["best_validation_loss"]))
        yhat = predict(model, x_va)
        self.assertEqual(yhat.shape, (len(x_va),))
        self.assertTrue(np.all(np.isfinite(yhat)))
        # a model that actually trained should beat a constant-mean baseline on this easy synthetic target
        baseline_mse = float(np.mean((y_va - y_tr.mean()) ** 2))
        model_mse = float(np.mean((yhat - y_va) ** 2))
        print(f"  model_mse={model_mse:.5f}  constant-mean baseline_mse={baseline_mse:.5f}")
        self.assertLess(model_mse, baseline_mse)


if __name__ == "__main__":
    unittest.main()
