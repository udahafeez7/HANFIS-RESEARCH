import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_HANFIS_DIR = PROJECT_ROOT / "python_hanfis"
if str(PYTHON_HANFIS_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_HANFIS_DIR))

import torch  # noqa: E402

from hanfis_end2end import HANFIS, SugenoPanel, fit_hybrid, fit_hybrid_restarts, predict  # noqa: E402
from hanfis_7input_experiment import FEATURES, split_indices, synthetic_dataset  # noqa: E402


class TestHanfisEndToEnd(unittest.TestCase):
    def test_rule_and_parameter_counts_match_scheme(self):
        m24 = HANFIS(m_raw=2, m_intermediate=2)
        m34 = HANFIS(m_raw=2, m_intermediate=3)
        self.assertEqual(m24.rule_count, 24)
        self.assertEqual(m24.parameter_count, 132)
        self.assertEqual(m34.rule_count, 34)
        self.assertEqual(m34.parameter_count, 176)

    def test_forward_shape_and_range(self):
        model = HANFIS()
        x = torch.rand(50, 7)
        r = model(x)
        self.assertEqual(tuple(r.shape), (50,))
        self.assertTrue(bool(((r >= 0) & (r <= 1)).all()))

    def test_gradients_reach_lower_panels(self):
        """End-to-end: the loss on r must produce gradients on V and E parameters (K1)."""
        model = HANFIS()
        x = torch.rand(64, 7)
        y = torch.rand(64)
        loss = torch.mean((model(x) - y) ** 2)
        loss.backward()
        grad_v = sum(p.grad.abs().sum().item() for p in model.vulnerability.parameters())
        grad_e = sum(p.grad.abs().sum().item() for p in model.environment.parameters())
        self.assertGreater(grad_v, 0.0)
        self.assertGreater(grad_e, 0.0)

    def test_closed_form_consequents_reduce_loss(self):
        panel = SugenoPanel([2, 2, 2])
        x = torch.rand(200, 3)
        y = 0.4 * x[:, 0] + 0.3 * x[:, 1] * x[:, 2]
        before = torch.mean((panel(x) - y) ** 2).item()
        panel.solve_consequents(x, y)
        after = torch.mean((panel(x) - y) ** 2).item()
        self.assertLess(after, before)

    def test_hybrid_fit_on_synthetic_reaches_low_error(self):
        frame = synthetic_dataset(600, 20260722)
        x = frame[FEATURES].to_numpy(np.float32)
        y = frame["dynamic_risk_target"].to_numpy(np.float32)
        tr, va, te = split_indices(len(frame), 20260722)
        torch.manual_seed(0)
        model = HANFIS(m_raw=2, m_intermediate=3)
        hist = fit_hybrid(model, x[tr], y[tr], x[va], y[va], epochs=150, patience=30, min_epochs=50)
        rmse = float(np.sqrt(np.mean((predict(model, x[te]) - y[te]) ** 2))) * 100.0
        self.assertLess(rmse, 3.0, msg=f"RMSE on 0-100 scale too high: {rmse:.3f}")
        self.assertEqual(hist["method"], "hybrid_lse_adam")

    def test_training_forward_keeps_gradient_when_intermediate_leaves_unit_interval(self):
        """Patch 0003: no hard clamp in training, so a saturated lower panel still receives gradient."""
        model = HANFIS()
        with torch.no_grad():
            model.vulnerability.consequents[:, 0] += 5.0  # push v far above 1
        x = torch.rand(64, 7)
        r, penalty = model.training_forward(x)
        loss = torch.mean((r - torch.rand(64)) ** 2) + 0.1 * penalty
        loss.backward()
        grad_v = sum(p.grad.abs().sum().item() for p in model.vulnerability.parameters())
        self.assertGreater(grad_v, 0.0)
        self.assertGreater(penalty.item(), 0.0)

    def test_every_registered_parameter_receives_gradient(self):
        """Patch 0008: no dead parameters for either MF family (they would break the gradient test and Adam groups)."""
        for mf in ("gauss", "ruspini"):
            model = HANFIS(2, 3, mf_family=mf)
            loss = torch.mean((model(torch.rand(32, 7)) - torch.rand(32)) ** 2)
            loss.backward()
            for name, p in model.named_parameters():
                self.assertIsNotNone(p.grad, msg=f"{mf}: {name} has no gradient")

    def test_quantile_initialisation_orders_centres(self):
        model = HANFIS(m_raw=2, m_intermediate=3)
        model.init_from_data(np.random.default_rng(0).random((300, 7)).astype(np.float32))
        for panel in (model.vulnerability, model.environment, model.integration):
            for c in panel.centers:
                self.assertTrue(bool((c[1:] > c[:-1]).all()) if len(c) > 1 else True)
                self.assertTrue(bool(((c >= 0) & (c <= 1)).all()))

    def test_restarts_return_best_validation(self):
        frame = synthetic_dataset(400, 7)
        x = frame[FEATURES].to_numpy(np.float32)
        y = frame["dynamic_risk_target"].to_numpy(np.float32)
        tr, va, _ = split_indices(len(frame), 7)
        model, hist = fit_hybrid_restarts(lambda: HANFIS(2, 3), x[tr], y[tr], x[va], y[va], n_restarts=2, epochs=60, patience=30, min_epochs=20)
        self.assertIn("restart", hist)
        self.assertIsInstance(model, HANFIS)

    def test_ruspini_memberships_form_partition_of_unity(self):
        panel = SugenoPanel([3, 2, 4], mf_family="ruspini")
        with torch.no_grad():
            for w in panel.raw_widths:
                w.copy_(torch.randn_like(w))
        x = torch.rand(200, 3)
        for i in range(3):
            mu = panel.memberships(x, i)
            self.assertTrue(torch.allclose(mu.sum(dim=1), torch.ones(200), atol=1e-5))
            self.assertTrue(bool((mu >= 0).all()))
            c = panel.ruspini_centers(i)
            self.assertTrue(bool((c[1:] > c[:-1]).all()))
            c = c.detach()
            self.assertAlmostEqual(float(c[0]), 0.0); self.assertAlmostEqual(float(c[-1]), 1.0, places=5)

    def test_ruspini_parameter_count(self):
        m = HANFIS(2, 3, mf_family="ruspini")   # premises: V,E: 3*(2-1)=3 each; I: 2+2+1=5 -> 11; consequents 96
        self.assertEqual(m.parameter_count, 11 + 32 + 32 + 18 * 4)

    def test_monotone_consequents_have_nonnegative_slopes(self):
        panel = SugenoPanel([2, 2, 2], monotone=True)
        with torch.no_grad():
            panel.consequents.copy_(torch.randn_like(panel.consequents) * 3)
        eff = panel.effective_consequents()
        self.assertTrue(bool((eff[:, 1:] >= 0).all()))
        x = torch.rand(100, 3); y = torch.rand(100)
        panel.solve_consequents(x, y)
        self.assertTrue(bool((panel.effective_consequents()[:, 1:] >= 0).all()))

    def test_rule_trace_shapes(self):
        model = HANFIS(m_raw=2, m_intermediate=3)
        trace = model.rule_trace(torch.rand(10, 7))
        self.assertEqual(tuple(trace["vulnerability"].shape), (10, 8))
        self.assertEqual(tuple(trace["integration"].shape), (10, 18))
        self.assertTrue(torch.allclose(trace["integration"].sum(dim=1), torch.ones(10), atol=1e-5))


if __name__ == "__main__":
    unittest.main()
