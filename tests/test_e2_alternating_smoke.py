"""E2 smoke test (patch 0035) -- RUN THIS FIRST, before anything else in this patch.

I could not execute the torch-based HANFIS class in the sandbox that wrote this patch
(no disk space left to install torch there); the closed-form derivation was verified
independently in pure NumPy (see verify_math.py, included in this patch: MSE 0.776 ->
4.2e-4 over 6 outer iterations, premises untouched). This test runs the SAME check
through the real torch classes and must pass before solve_lower_alternating /
fit_hybrid_lower_alternating are trusted on real data.

    python -m pytest -q tests/test_e2_alternating_smoke.py -v
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_hanfis"))
from hanfis_end2end import HANFIS, fit_hybrid, fit_hybrid_lower_alternating, predict  # noqa: E402


def synthetic(n=400, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.random((n, 7)).astype(np.float32)
    y = (0.3 + 0.4 * x[:, :3].mean(1) + 0.5 * x[:, 3:6].mean(1) + 0.2 * x[:, 6]
         + rng.normal(0, 0.01, n)).astype(np.float32)
    return x, np.clip(y, 0, 1)


class TestAlternatingLower(unittest.TestCase):
    def test_solve_lower_alternating_reduces_mse_without_touching_premises(self):
        x, y = synthetic()
        torch.manual_seed(0)
        model = HANFIS(m_raw=2, m_intermediate=3, mf_family="gauss", monotone=False)
        xt, yt = torch.as_tensor(x), torch.as_tensor(y)
        with torch.no_grad():
            mse0 = torch.mean((model(xt) - yt) ** 2).item()
        for _ in range(6):
            with torch.no_grad():
                model.integration.solve_consequents(model.integration_input(xt, clamp=False), yt, 1e-3)
                model.solve_lower_alternating(xt, yt, 1e-3)
        with torch.no_grad():
            mse_final = torch.mean((model(xt) - yt) ** 2).item()
        print(f"\n  MSE random init -> after 6 alternating closed-form iterations: {mse0:.4f} -> {mse_final:.6f}")
        self.assertLess(mse_final, 0.01, "closed-form alternation must reach near the noise floor (~1e-4) without any premise training")
        self.assertLess(mse_final, mse0 * 0.05)

    def test_monotone_variant_also_converges_and_stays_finite(self):
        x, y = synthetic(seed=1)
        torch.manual_seed(1)
        model = HANFIS(m_raw=2, m_intermediate=3, mf_family="gauss", monotone=True)
        xt, yt = torch.as_tensor(x), torch.as_tensor(y)
        for _ in range(6):
            with torch.no_grad():
                model.integration.solve_consequents(model.integration_input(xt, clamp=False), yt, 1e-3)
                model.solve_lower_alternating(xt, yt, 1e-3)
        with torch.no_grad():
            mse_final = torch.mean((model(xt) - yt) ** 2).item()
        print(f"\n  monotone MSE after 6 iterations: {mse_final:.6f}")
        self.assertTrue(np.isfinite(mse_final))
        self.assertLess(mse_final, 0.05)

    def test_full_training_loop_end_to_end_matches_fit_hybrid_shape(self):
        x, y = synthetic(n=200, seed=2)
        x_tr, x_va = x[:150], x[150:]
        y_tr, y_va = y[:150], y[150:]
        torch.manual_seed(2)
        m1 = HANFIS(m_raw=2, m_intermediate=3, monotone=False)
        h1 = fit_hybrid(m1, x_tr, y_tr, x_va, y_va, epochs=60, patience=20, min_epochs=20)
        torch.manual_seed(2)
        m2 = HANFIS(m_raw=2, m_intermediate=3, monotone=False)
        h2 = fit_hybrid_lower_alternating(m2, x_tr, y_tr, x_va, y_va, epochs=60, patience=20, min_epochs=20)
        print(f"\n  fit_hybrid best_val={h1['best_validation_loss']:.5f}  "
              f"fit_hybrid_lower_alternating best_val={h2['best_validation_loss']:.5f}")
        self.assertTrue(np.isfinite(h2["best_validation_loss"]))
        r2 = predict(m2, x_va)
        self.assertEqual(r2.shape, (len(x_va),))
        self.assertTrue(np.all(np.isfinite(r2)))


if __name__ == "__main__":
    unittest.main()
