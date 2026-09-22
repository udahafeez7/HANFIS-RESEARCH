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
- Patch 0003 (stability, E-INT 2026-09-22). Ablation on the failing seed
  (C34, scenario S2, seed 4: RMSE 3.53 at hard clamp / linspace init / single
  lr) showed: a fresh random initialisation fixes it (0.12 and 0.27), a soft
  range penalty instead of a hard clamp helps partially (1.83), a lower premise
  learning rate helps partially (1.99), quantile initialisation does not help
  (3.48). Therefore the *default* remains the original path and the evidence-
  based remedy is ``fit_hybrid_restarts`` (best of n pre-registered
  initialisations on validation loss). Soft range penalty
  (``range_penalty``), premise learning rate (``premise_learning_rate``),
  quantile initialisation (``init_from_data``) and adaptive ridge
  (``ridge=None``) are available as opt-in flags for E1/E2 ablations.
  Early stopping is longer (patience 100, min 200 epochs): with patience 60,
  several seeds stopped before convergence.

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
    """First-order Sugeno ANFIS with a per-input MF count.

    mf_family:
      "gauss"   - free Gaussian MFs (centre, log-sigma per MF): 2m premise parameters per input.
      "ruspini" - connected triangular partition of unity on [0,1] (A-03, after Juston et al. 2024):
                  the m centres are ordered, the two outer ones are pinned to 0 and 1, and the
                  m-2 interior centres are learned through normalised positive widths, so the
                  memberships of every input sum to one at every point. m-1 premise parameters
                  per input; no sigma.
    monotone: if True (A-04) the consequent slopes are constrained non-negative through
              softplus so each rule output is non-decreasing in every input (higher_is_riskier).
              The intercepts stay free.
    """

    def __init__(self, m_per_input: Sequence[int], mf_family: str = "gauss", monotone: bool = False) -> None:
        super().__init__()
        if mf_family not in ("gauss", "ruspini"):
            raise ValueError(f"unknown mf_family {mf_family!r}")
        self.mf_family = mf_family
        self.monotone = monotone
        self.m_per_input = list(int(m) for m in m_per_input)
        self.n_inputs = len(self.m_per_input)
        # Only the parameters of the active MF family are registered, so every registered
        # parameter takes part in the forward pass and receives a gradient (patch 0008).
        if mf_family == "gauss":
            self.centers = nn.ParameterList(
                [nn.Parameter(torch.linspace(0.25, 0.75, m) if m > 1 else torch.tensor([0.5])) for m in self.m_per_input]
            )
            self.log_sigmas = nn.ParameterList(
                [nn.Parameter(torch.full((m,), float(np.log(0.25)))) for m in self.m_per_input]
            )
            self.raw_widths = None
        else:
            self.centers = None
            self.log_sigmas = None
            # ruspini: raw widths (m-1 per input) -> normalised knots in [0,1]
            self.raw_widths = nn.ParameterList(
                [nn.Parameter(torch.zeros(max(m - 1, 1))) for m in self.m_per_input]
            )
        rules = list(itertools.product(*[range(m) for m in self.m_per_input]))
        self.register_buffer("rule_indices", torch.tensor(rules, dtype=torch.long))
        self.consequents = nn.Parameter(torch.zeros(len(rules), self.n_inputs + 1))
        nn.init.normal_(self.consequents, mean=0.0, std=0.05)

    @property
    def rule_count(self) -> int:
        return int(self.rule_indices.shape[0])

    @property
    def premise_parameter_count(self) -> int:
        if self.mf_family == "gauss":
            return sum(2 * m for m in self.m_per_input)
        return sum(max(m - 1, 0) for m in self.m_per_input)

    def effective_consequents(self) -> torch.Tensor:
        """Consequent matrix actually used (A-04 applies softplus to the slopes)."""
        if not self.monotone:
            return self.consequents
        return torch.cat([self.consequents[:, :1], torch.nn.functional.softplus(self.consequents[:, 1:])], dim=1)

    def ruspini_centers(self, i: int) -> torch.Tensor:
        m = self.m_per_input[i]
        if m == 1:
            return torch.tensor([0.5], device=self.raw_widths[i].device)
        widths = torch.nn.functional.softplus(self.raw_widths[i]) + 1e-3     # m-1 positive widths
        knots = torch.cumsum(widths, dim=0) / widths.sum()                   # (m-1,) in (0,1], last == 1
        return torch.cat([torch.zeros(1, device=knots.device), knots])       # (m,): 0 < c1 < ... < 1

    def memberships(self, x: torch.Tensor, i: int) -> torch.Tensor:
        """Membership of input i, shape (N, m_i)."""
        xi = x[:, i : i + 1]
        if self.mf_family == "gauss":
            sigma = torch.exp(self.log_sigmas[i]).clamp_min(1e-3)
            return torch.exp(-0.5 * ((xi - self.centers[i][None, :]) / sigma[None, :]) ** 2)
        c = self.ruspini_centers(i)
        m = c.shape[0]
        if m == 1:
            return torch.ones_like(xi)
        left = torch.cat([c[:1] - 1.0, c[:-1]])           # c_{j-1}, with a virtual point left of 0
        right = torch.cat([c[1:], c[-1:] + 1.0])          # c_{j+1}, with a virtual point right of 1
        up = torch.clamp((xi - left[None, :]) / (c - left)[None, :], 0.0, 1.0)
        down = 1.0 - torch.clamp((xi - c[None, :]) / (right - c)[None, :], 0.0, 1.0)
        mu = up * down
        mu[:, 0] = torch.where(xi[:, 0] <= c[0], torch.ones_like(mu[:, 0]), mu[:, 0])
        mu[:, -1] = torch.where(xi[:, 0] >= c[-1], torch.ones_like(mu[:, -1]), mu[:, -1])
        return mu

    def firing(self, x: torch.Tensor) -> torch.Tensor:
        """Normalised firing strengths, shape (N, R)."""
        selected = [self.memberships(x, i)[:, self.rule_indices[:, i]] for i in range(self.n_inputs)]
        w = torch.stack(selected, dim=-1).prod(dim=-1)
        return w / w.sum(dim=1, keepdim=True).clamp_min(1e-12)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        w = self.firing(x)
        xa = torch.cat([torch.ones((x.shape[0], 1), device=x.device, dtype=x.dtype), x], dim=1)
        return (w * (xa @ self.effective_consequents().T)).sum(dim=1)

    @torch.no_grad()
    def init_centers_from_quantiles(self, x: np.ndarray) -> None:
        """Place MF centres on data quantiles (patch 0003). Gauss: sigma ~ 0.6 x spacing.
        Ruspini: interior knots on quantiles, encoded back into positive widths."""
        for i, m in enumerate(self.m_per_input):
            col = np.asarray(x[:, i], dtype=np.float32)
            if self.mf_family == "gauss":
                if m > 1:
                    q = np.quantile(col, np.linspace(0, 1, m + 2)[1:-1])
                    spacing = float(q[1] - q[0])
                else:
                    q, spacing = np.array([np.median(col)]), 0.5
                self.centers[i].copy_(torch.as_tensor(q, dtype=torch.float32))
                self.log_sigmas[i].fill_(float(np.log(max(spacing * 0.6, 0.05))))
            elif m > 1:
                knots = np.concatenate([np.quantile(np.clip(col, 0, 1), np.linspace(0, 1, m)[1:-1]), [1.0]])
                widths = np.clip(np.diff(np.concatenate([[0.0], knots])), 1e-3, None)
                # inverse of softplus(w) + 1e-3 = width  ->  raw = log(exp(width - 1e-3) - 1)
                raw = np.log(np.expm1(np.clip(widths - 1e-3, 1e-4, None)))
                self.raw_widths[i].copy_(torch.as_tensor(raw, dtype=torch.float32))

    @torch.no_grad()
    def solve_consequents(self, x: torch.Tensor, y: torch.Tensor, ridge: float | None = 1e-3) -> None:
        """Closed-form ridge least squares for the consequent parameters (A-06).

        ridge=None selects lambda = max(1e-3, 0.01 * p / N), which keeps the
        system well-posed when consequent parameters approach the sample size
        (the flat 128-rule model in E-INT was ill-posed with a fixed 1e-3).
        """
        w = self.firing(x)
        xa = torch.cat([torch.ones((x.shape[0], 1), device=x.device, dtype=x.dtype), x], dim=1)
        phi = (w[:, :, None] * xa[:, None, :]).reshape(x.shape[0], -1)
        if ridge is None:
            ridge = max(1e-3, 0.01 * phi.shape[1] / phi.shape[0])
        gram = phi.T @ phi + ridge * torch.eye(phi.shape[1], device=x.device, dtype=x.dtype)
        beta = torch.linalg.solve(gram, phi.T @ y).reshape(self.rule_count, -1)
        if self.monotone:
            # projected least squares: clamp slopes to >= 0, then store the softplus pre-image
            slopes = beta[:, 1:].clamp_min(1e-4)
            beta = torch.cat([beta[:, :1], torch.log(torch.expm1(slopes))], dim=1)
        self.consequents.copy_(beta)


class HANFIS(nn.Module):
    """Three-panel hierarchical Sugeno ANFIS: V(x1..x3) -> v, E(x4..x6) -> e, I(v, e, x7) -> r."""

    def __init__(self, m_raw: int = 2, m_intermediate: int = 3, m_threat: int | None = None,
                 mf_family: str = "gauss", monotone: bool = False) -> None:
        super().__init__()
        m_threat = m_raw if m_threat is None else m_threat
        self.mf_family, self.monotone = mf_family, monotone
        self.vulnerability = SugenoPanel([m_raw, m_raw, m_raw], mf_family, monotone)
        self.environment = SugenoPanel([m_raw, m_raw, m_raw], mf_family, monotone)
        self.integration = SugenoPanel([m_intermediate, m_intermediate, m_threat], mf_family, monotone)

    @property
    def rule_count(self) -> int:
        return self.vulnerability.rule_count + self.environment.rule_count + self.integration.rule_count

    @property
    def parameter_count(self) -> int:
        """Effective parameters: premise parameters of the active MF family + consequents."""
        return sum(p.premise_parameter_count + p.consequents.numel() for p in (self.vulnerability, self.environment, self.integration))

    def intermediates(self, x7: torch.Tensor, clamp: bool = True) -> tuple[torch.Tensor, torch.Tensor]:
        v = self.vulnerability(x7[:, 0:3])
        e = self.environment(x7[:, 3:6])
        if clamp:
            v, e = torch.clamp(v, 0.0, 1.0), torch.clamp(e, 0.0, 1.0)
        return v, e

    def integration_input(self, x7: torch.Tensor, clamp: bool = True) -> torch.Tensor:
        v, e = self.intermediates(x7, clamp=clamp)
        return torch.stack([v, e, x7[:, 6]], dim=1)

    def forward(self, x7: torch.Tensor) -> torch.Tensor:
        """Inference path: intermediates and output clamped to [0,1]."""
        return torch.clamp(self.integration(self.integration_input(x7, clamp=True)), 0.0, 1.0)

    def training_forward(self, x7: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Training path (patch 0003): no hard clamp on v, e; returns (r, range_penalty)."""
        xi = self.integration_input(x7, clamp=False)
        v, e = xi[:, 0], xi[:, 1]
        penalty = torch.mean(torch.relu(-v) + torch.relu(v - 1) + torch.relu(-e) + torch.relu(e - 1))
        return self.integration(xi), penalty

    @torch.no_grad()
    def init_from_data(self, x7: np.ndarray) -> None:
        """Quantile-based membership initialisation (patch 0003)."""
        x = np.asarray(x7, dtype=np.float32)
        self.vulnerability.init_centers_from_quantiles(x[:, 0:3])
        self.environment.init_centers_from_quantiles(x[:, 3:6])
        # intermediates are unknown before training: spread their MFs over [0,1]
        xi = np.column_stack([np.linspace(0, 1, len(x)), np.linspace(0, 1, len(x)), x[:, 6]]).astype(np.float32)
        self.integration.init_centers_from_quantiles(xi)

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
    patience: int = 100,
    ridge: float | None = 1e-3,
    premise_learning_rate: float | None = None,
    range_penalty: float | None = None,
    min_epochs: int = 200,
) -> dict:
    """Hybrid training: closed-form Integration consequents + Adam on everything else (A-06, patch 0003).

    Defaults reproduce the verified E-INT path (hard clamp on v, e; one learning rate;
    ridge 1e-3). ``range_penalty`` switches to the soft-range training path,
    ``premise_learning_rate`` gives premises their own rate, ``ridge=None`` adapts lambda.
    """
    xtr, ytr, xva, yva = map(_to_tensor, (x_train, y_train, x_validation, y_validation))
    premise = [p for n, p in model.named_parameters() if ".centers." in n or ".log_sigmas." in n or ".raw_widths." in n]
    lower_cons = [p for n, p in model.named_parameters() if n.endswith("consequents") and not n.startswith("integration.")]
    optimizer = torch.optim.Adam([{"params": premise, "lr": premise_learning_rate or learning_rate}, {"params": lower_cons, "lr": learning_rate}])
    soft = range_penalty is not None
    best_loss, best_state, best_epoch, stale = float("inf"), copy.deepcopy(model.state_dict()), 0, 0
    history = {"training_loss": [], "validation_loss": []}
    for epoch in range(epochs):
        model.train()
        model.integration.solve_consequents(model.integration_input(xtr, clamp=not soft).detach(), ytr, ridge)
        optimizer.zero_grad()
        if soft:
            r, penalty = model.training_forward(xtr)
            loss = torch.mean((r - ytr) ** 2) + range_penalty * penalty
        else:
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
            if stale >= patience and epoch + 1 >= min_epochs:
                break
    model.load_state_dict(best_state)
    history.update(best_validation_loss=best_loss, best_epoch=best_epoch, method="hybrid_lse_adam")
    return history


def fit_hybrid_restarts(model_factory, x_train, y_train, x_validation, y_validation, n_restarts: int = 3, seed: int = 0, quantile_init: bool = False, **fit_kwargs):
    """Pre-registered restarts: train n_restarts fresh initialisations, keep the best validation loss (patch 0003).

    The selection uses validation loss only; the test split is never consulted.
    """
    best = None
    for k in range(n_restarts):
        torch.manual_seed(seed * 1000 + k)
        model = model_factory()
        if quantile_init:
            model.init_from_data(x_train)
        hist = fit_hybrid(model, x_train, y_train, x_validation, y_validation, **fit_kwargs)
        hist["restart"] = k
        if best is None or hist["best_validation_loss"] < best[1]["best_validation_loss"]:
            best = (model, hist)
    return best


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
