"""End-to-end hierarchical ANFIS (HANFIS) with hybrid LSE + gradient training.

Amendments implemented here (see HANFIS_RESEARCH_MEMORY.md):
- A-02: the Integration panel may use a different membership count on the
  intermediate variables v and e (``m_intermediate``, default 3) than on the
  raw inputs (``m_raw``, default 2). With m_raw=2 and m_intermediate=3 the
  Integration panel has 3*3*2 = 18 rules and HANFIS has 8+8+18 = 34 rules.
  With m_intermediate=2 the historical 24-rule configuration is recovered.
- A-06: consequents of the Integration panel are solved in closed form
  (ridge least squares) every epoch; premise parameters and lower-panel
  parameters are updated by gradient descent (Adam). ``fit_adam`` keeps the
  pure gradient variant for comparison (E2).
- K1 (Rencana Eksperimen v2): no intermediate targets are required. The loss
  is computed on the final risk score only; gradients flow through v and e.

This module mirrors the JAX reference ``reference/exp_integration_mf_jax.py``
that produced the E-INT results on 2026-09-22.
"""

from __future__ import annotations

import copy
import itertools
from typing import Sequence

import numpy as np
import torch
from torch import nn


class SugenoPanel(nn.Module):
    """First-order Sugeno ANFIS with Gaussian MFs and a per-input MF count."""

    def __init__(self, m_per_input: Sequence[int]) -> None:
        super().__init__()
        self.m_per_input = list(int(m) for m in m_per_input)
        self.n_inputs = len(self.m_per_input)
        self.centers = nn.ParameterList(
            [nn.Parameter(torch.linspace(0.25, 0.75, m) if m > 1 else torch.tensor([0.5])) for m in self.m_per_input]
        )
        self.log_sigmas = nn.ParameterList(
            [nn.Parameter(torch.full((m,), float(np.log(0.25)))) for m in self.m_per_input]
        )
        rules = list(itertools.product(*[range(m) for m in self.m_per_input]))
        self.register_buffer("rule_indices", torch.tensor(rules, dtype=torch.long))
        self.consequents = nn.Parameter(torch.zeros(len(rules), self.n_inputs + 1))
        nn.init.normal_(self.consequents, mean=0.0, std=0.05)

    @property
    def rule_count(self) -> int:
        return int(self.rule_indices.shape[0])

    def firing(self, x: torch.Tensor) -> torch.Tensor:
        """Normalised firing strengths, shape (N, R)."""
        selected = []
        for i in range(self.n_inputs):
            sigma = torch.exp(self.log_sigmas[i]).clamp_min(1e-3)
            mu = torch.exp(-0.5 * ((x[:, i : i + 1] - self.centers[i][None, :]) / sigma[None, :]) ** 2)
            selected.append(mu[:, self.rule_indices[:, i]])
        w = torch.stack(selected, dim=-1).prod(dim=-1)
        return w / w.sum(dim=1, keepdim=True).clamp_min(1e-12)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        w = self.firing(x)
        xa = torch.cat([torch.ones((x.shape[0], 1), device=x.device, dtype=x.dtype), x], dim=1)
        return (w * (xa @ self.consequents.T)).sum(dim=1)

    @torch.no_grad()
    def solve_consequents(self, x: torch.Tensor, y: torch.Tensor, ridge: float = 1e-3) -> None:
        """Closed-form ridge least squares for the consequent parameters (A-06)."""
        w = self.firing(x)
        xa = torch.cat([torch.ones((x.shape[0], 1), device=x.device, dtype=x.dtype), x], dim=1)
        phi = (w[:, :, None] * xa[:, None, :]).reshape(x.shape[0], -1)
        gram = phi.T @ phi + ridge * torch.eye(phi.shape[1], device=x.device, dtype=x.dtype)
        beta = torch.linalg.solve(gram, phi.T @ y)
        self.consequents.copy_(beta.reshape(self.rule_count, -1))


class HANFIS(nn.Module):
    """Three-panel hierarchical Sugeno ANFIS: V(x1..x3) -> v, E(x4..x6) -> e, I(v, e, x7) -> r."""

    def __init__(self, m_raw: int = 2, m_intermediate: int = 3, m_threat: int | None = None) -> None:
        super().__init__()
        m_threat = m_raw if m_threat is None else m_threat
        self.vulnerability = SugenoPanel([m_raw, m_raw, m_raw])
        self.environment = SugenoPanel([m_raw, m_raw, m_raw])
        self.integration = SugenoPanel([m_intermediate, m_intermediate, m_threat])

    @property
    def rule_count(self) -> int:
        return self.vulnerability.rule_count + self.environment.rule_count + self.integration.rule_count

    @property
    def parameter_count(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def intermediates(self, x7: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        v = torch.clamp(self.vulnerability(x7[:, 0:3]), 0.0, 1.0)
        e = torch.clamp(self.environment(x7[:, 3:6]), 0.0, 1.0)
        return v, e

    def integration_input(self, x7: torch.Tensor) -> torch.Tensor:
        v, e = self.intermediates(x7)
        return torch.stack([v, e, x7[:, 6]], dim=1)

    def forward(self, x7: torch.Tensor) -> torch.Tensor:
        return torch.clamp(self.integration(self.integration_input(x7)), 0.0, 1.0)

    @torch.no_grad()
    def rule_trace(self, x7: torch.Tensor) -> dict[str, torch.Tensor]:
        """Normalised firing strengths of every panel for explainability (A-08)."""
        xi = self.integration_input(x7)
        return {
            "vulnerability": self.vulnerability.firing(x7[:, 0:3]),
            "environment": self.environment.firing(x7[:, 3:6]),
            "integration": self.integration.firing(xi),
            "v": xi[:, 0],
            "e": xi[:, 1],
        }


def _to_tensor(a: np.ndarray) -> torch.Tensor:
    return torch.as_tensor(np.asarray(a), dtype=torch.float32)


def fit_hybrid(
    model: HANFIS,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_validation: np.ndarray,
    y_validation: np.ndarray,
    epochs: int = 600,
    learning_rate: float = 1e-2,
    patience: int = 60,
    ridge: float = 1e-3,
) -> dict:
    """Hybrid training: closed-form Integration consequents + Adam on everything else (A-06)."""
    xtr, ytr, xva, yva = map(_to_tensor, (x_train, y_train, x_validation, y_validation))
    others = [p for n, p in model.named_parameters() if not n.startswith("integration.consequents")]
    optimizer = torch.optim.Adam(others, lr=learning_rate)
    best_loss, best_state, best_epoch, stale = float("inf"), copy.deepcopy(model.state_dict()), 0, 0
    history = {"training_loss": [], "validation_loss": []}
    for epoch in range(epochs):
        model.train()
        model.integration.solve_consequents(model.integration_input(xtr).detach(), ytr, ridge)
        optimizer.zero_grad()
        loss = torch.mean((model(xtr) - ytr) ** 2)
        loss.backward()
        optimizer.step()
        model.eval()
        with torch.no_grad():
            val = torch.mean((model(xva) - yva) ** 2).item()
        history["training_loss"].append(float(loss.item()))
        history["validation_loss"].append(val)
        if val < best_loss - 1e-8:
            best_loss, best_state, best_epoch, stale = val, copy.deepcopy(model.state_dict()), epoch + 1, 0
        else:
            stale += 1
            if stale >= patience:
                break
    model.load_state_dict(best_state)
    history.update(best_validation_loss=best_loss, best_epoch=best_epoch, method="hybrid_lse_adam")
    return history


def fit_adam(
    model: HANFIS,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_validation: np.ndarray,
    y_validation: np.ndarray,
    epochs: int = 600,
    learning_rate: float = 1e-2,
    patience: int = 60,
) -> dict:
    """Pure gradient variant kept for E2 comparison; less stable end-to-end (see E-INT)."""
    xtr, ytr, xva, yva = map(_to_tensor, (x_train, y_train, x_validation, y_validation))
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    best_loss, best_state, best_epoch, stale = float("inf"), copy.deepcopy(model.state_dict()), 0, 0
    history = {"training_loss": [], "validation_loss": []}
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        loss = torch.mean((model(xtr) - ytr) ** 2)
        loss.backward()
        optimizer.step()
        model.eval()
        with torch.no_grad():
            val = torch.mean((model(xva) - yva) ** 2).item()
        history["training_loss"].append(float(loss.item()))
        history["validation_loss"].append(val)
        if val < best_loss - 1e-8:
            best_loss, best_state, best_epoch, stale = val, copy.deepcopy(model.state_dict()), epoch + 1, 0
        else:
            stale += 1
            if stale >= patience:
                break
    model.load_state_dict(best_state)
    history.update(best_validation_loss=best_loss, best_epoch=best_epoch, method="adam")
    return history


def predict(model: HANFIS, x: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        return model(_to_tensor(x)).cpu().numpy()
