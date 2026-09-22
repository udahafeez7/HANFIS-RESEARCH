import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_HANFIS_DIR = PROJECT_ROOT / "python_hanfis"
if str(PYTHON_HANFIS_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_HANFIS_DIR))

import torch  # noqa: E402

from hanfis_end2end import HANFIS, SugenoPanel, fit_hybrid, predict  # noqa: E402
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
        hist = fit_hybrid(model, x[tr], y[tr], x[va], y[va], epochs=150, patience=30)
        rmse = float(np.sqrt(np.mean((predict(model, x[te]) - y[te]) ** 2))) * 100.0
        self.assertLess(rmse, 3.0, msg=f"RMSE on 0-100 scale too high: {rmse:.3f}")
        self.assertEqual(hist["method"], "hybrid_lse_adam")

    def test_rule_trace_shapes(self):
        model = HANFIS(m_raw=2, m_intermediate=3)
        trace = model.rule_trace(torch.rand(10, 7))
        self.assertEqual(tuple(trace["vulnerability"].shape), (10, 8))
        self.assertEqual(tuple(trace["integration"].shape), (10, 18))
        self.assertTrue(torch.allclose(trace["integration"].sum(dim=1), torch.ones(10), atol=1e-5))


if __name__ == "__main__":
    unittest.main()
