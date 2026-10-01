"""E5 smoke test -- RUN THIS FIRST, before using hanfis_bottleneck.py for the sweep.

I could not execute torch in the sandbox that wrote this (same limitation as patches 0035/0049).
The multi-head Sugeno math (k=1 reduces exactly to the scalar panel; k=3 output shape is (N,3))
was verified independently in pure NumPy first (python_hanfis/verify_multihead.py). This test
re-runs the same checks through the real torch classes and must pass before trusting
hanfis_bottleneck.py for the sweep.

    python -m pytest -q tests/test_bottleneck_smoke.py -v
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_hanfis"))
from hanfis_bottleneck import (  # noqa: E402
    BottleneckBudgetError, HANFISBottleneck, estimate_params, fit_hybrid, predict,
)


def synthetic(n=400, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.random((n, 7)).astype(np.float32)
    y = (0.3 + 0.4 * x[:, :3].mean(1) + 0.5 * x[:, 3:6].mean(1) + 0.2 * x[:, 6]
         + rng.normal(0, 0.01, n)).astype(np.float32)
    return x, np.clip(y, 0, 1)


class TestBudget(unittest.TestCase):
    def test_k1_matches_hanfis_param_count(self):
        est = estimate_params(m_raw=2, m_intermediate=3, bottleneck_k=1)
        self.assertEqual(est["total_params"], 176)   # must match the A-09 HANFIS exactly
        self.assertEqual(est["integration_rules"], 18)

    def test_k2_grows_as_predicted(self):
        est = estimate_params(m_raw=2, m_intermediate=3, bottleneck_k=2)
        self.assertEqual(est["integration_rules"], 162)

    def test_k3_refused_by_default(self):
        with self.assertRaises(BottleneckBudgetError):
            HANFISBottleneck(bottleneck_k=3)
        # explicit override still works (caller's choice, not silent)
        model = HANFISBottleneck(bottleneck_k=3, allow_oversize=True)
        self.assertEqual(model.bottleneck_k, 3)


class TestForwardAndTrain(unittest.TestCase):
    def test_k1_forward_runs_and_param_count_matches(self):
        torch.manual_seed(0)
        model = HANFISBottleneck(bottleneck_k=1, monotone=True)
        self.assertEqual(model.parameter_count, 176)
        x, y = synthetic(n=50)
        out = model(torch.as_tensor(x))
        self.assertEqual(tuple(out.shape), (50,))
        self.assertTrue(torch.all(torch.isfinite(out)))

    def test_k2_forward_runs(self):
        torch.manual_seed(0)
        model = HANFISBottleneck(bottleneck_k=2, monotone=True, max_params=2000)
        x, y = synthetic(n=50)
        out = model(torch.as_tensor(x))
        self.assertEqual(tuple(out.shape), (50,))
        self.assertTrue(torch.all(torch.isfinite(out)))

    def test_train_k1_and_k2_end_to_end(self):
        x, y = synthetic(n=250, seed=1)
        x_tr, x_va = x[:180], x[180:]; y_tr, y_va = y[:180], y[180:]
        for k in (1, 2):
            torch.manual_seed(2)
            model = HANFISBottleneck(bottleneck_k=k, monotone=True, max_params=2000)
            hist = fit_hybrid(model, x_tr, y_tr, x_va, y_va, epochs=60, patience=20, min_epochs=20)
            print(f"\n  k={k}  rules={model.rule_count}  params={model.parameter_count}  "
                  f"best_val_mse={hist['best_validation_loss']:.5f}")
            self.assertTrue(np.isfinite(hist["best_validation_loss"]))
            r = predict(model, x_va)
            self.assertEqual(r.shape, (len(x_va),))
            self.assertTrue(np.all(np.isfinite(r)))


if __name__ == "__main__":
    unittest.main()


class TestAlternatingGeneralised(unittest.TestCase):
    def test_k1_alternating_matches_known_good_convergence(self):
        """At k=1 this must behave like the original scalar E2 check: MSE collapses toward the
        noise floor via pure closed-form alternation, premises untouched."""
        import hanfis_bottleneck as hb
        x, y = synthetic(n=400, seed=0)
        torch.manual_seed(0)
        model = hb.HANFISBottleneck(bottleneck_k=1, monotone=False)
        xt, yt = torch.as_tensor(x), torch.as_tensor(y)
        with torch.no_grad():
            mse0 = torch.mean((model(xt) - yt) ** 2).item()
        for _ in range(6):
            with torch.no_grad():
                model.integration.solve_consequents(model.integration_input(xt, clamp=False), yt[:, None], 1e-3)
                hb.solve_lower_alternating(model, xt, yt, 1e-3)
        with torch.no_grad():
            mse_final = torch.mean((model(xt) - yt) ** 2).item()
        print(f"\n  k=1 alternating: {mse0:.4f} -> {mse_final:.6f}")
        self.assertLess(mse_final, 0.01)

    def test_k2_alternating_converges_without_diverging(self):
        import hanfis_bottleneck as hb
        x, y = synthetic(n=400, seed=1)
        torch.manual_seed(1)
        model = hb.HANFISBottleneck(bottleneck_k=2, monotone=True, max_params=2000)
        xt, yt = torch.as_tensor(x), torch.as_tensor(y)
        for _ in range(6):
            with torch.no_grad():
                model.integration.solve_consequents(model.integration_input(xt, clamp=False), yt[:, None], 1e-3)
                hb.solve_lower_alternating(model, xt, yt, 1e-3)
        with torch.no_grad():
            mse_final = torch.mean((model(xt) - yt) ** 2).item()
        print(f"\n  k=2 alternating (monotone): final MSE {mse_final:.6f}")
        self.assertTrue(np.isfinite(mse_final))
        self.assertLess(mse_final, 0.1)

    def test_full_training_loop_k1_and_k2(self):
        import hanfis_bottleneck as hb
        x, y = synthetic(n=250, seed=2)
        x_tr, x_va = x[:180], x[180:]; y_tr, y_va = y[:180], y[180:]
        for k in (1, 2):
            torch.manual_seed(3)
            model = hb.HANFISBottleneck(bottleneck_k=k, monotone=True, max_params=2000)
            hist = hb.fit_hybrid_lower_alternating(model, x_tr, y_tr, x_va, y_va, epochs=60, patience=20, min_epochs=20)
            print(f"\n  fit_hybrid_lower_alternating k={k}: best_val_mse={hist['best_validation_loss']:.5f}")
            self.assertTrue(np.isfinite(hist["best_validation_loss"]))
            r = hb.predict(model, x_va)
            self.assertTrue(np.all(np.isfinite(r)))
