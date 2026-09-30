"""FlatANFISMatched (amendment A-05): a flat (non-hierarchical) Sugeno ANFIS whose rules come
from subtractive clustering (Chiu 1994) directly in the 7-D raw input space, initialised and
parameter-matched to HANFIS's 176 parameters within +/-5% (167-185), so any accuracy gap between
HANFIS and a flat model is not confounded with capacity (H2/H3, memory review-status.md's
"highest-value experiment").

Design: subtractive clustering is NOT grid partition. Each found cluster center becomes ONE
rule with its OWN per-dimension Gaussian premise (2 params/dim, not shared across rules) and its
own first-order consequent (8 params: intercept + 7 slopes). Total params = R * (2*7 + 8) = 22R,
so R=8 hits 176 exactly. The clustering radius ra is data-dependent (verified in
verify_clustering.py: a single fixed ra does NOT generalise across different folds' training
data -- R varied 5-8 across 5 independent draws), so ra is searched FRESH per fold via bisection
on the achieved rule count, and the search result is reported, never assumed.
"""
from __future__ import annotations

import copy

import numpy as np
import torch
from torch import nn

PARAMS_PER_RULE = 22   # 2 premise params/dim * 7 dims + 8 consequent params (1 intercept + 7 slopes)


class ClusterSearchError(RuntimeError):
    """Raised when no radius search lands within tolerance of the target parameter budget."""


def _subtractive_clustering(X: np.ndarray, ra: float, rb: float | None = None,
                            accept_ratio: float = 0.5, reject_ratio: float = 0.15,
                            max_clusters: int = 30) -> np.ndarray:
    """Chiu's subtractive clustering. X: (N, d) normalised to [0,1]^d. Returns (R, d) centers."""
    rb = rb if rb is not None else ra * 1.5
    alpha, beta = 4.0 / ra ** 2, 4.0 / rb ** 2
    D2 = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1)
    P = np.exp(-alpha * D2).sum(1)
    centers: list[np.ndarray] = []
    first_potential = None
    Pw = P.copy()
    while len(centers) < max_clusters:
        k = int(np.argmax(Pw))
        pk = Pw[k]
        if first_potential is None:
            first_potential = pk
        if pk <= reject_ratio * first_potential:
            break
        if pk < accept_ratio * first_potential and centers:
            dmin = min(float(np.linalg.norm(X[k] - c)) for c in centers)
            if dmin / ra + pk / first_potential < 1.0:
                Pw[k] = -1.0
                continue
        centers.append(X[k].copy())
        d2 = ((X - X[k]) ** 2).sum(-1)
        P = P - pk * np.exp(-beta * d2)
        Pw = P.copy()
        for c in centers:
            hit = np.all(np.isclose(X, c), axis=1)
            Pw[hit] = -1.0
    return np.array(centers) if centers else np.empty((0, X.shape[1]))


def search_radius_for_budget(X: np.ndarray, target_params: int = 176, tol_pct: float = 0.05,
                             params_per_rule: int = PARAMS_PER_RULE, max_iter: int = 40,
                             ra_bounds: tuple[float, float] = (0.05, 1.5)) -> dict:
    """Bisection search: smaller ra -> more clusters/rules/params; larger ra -> fewer. Returns a
    dict with ra, n_rules, n_params, within_tolerance. Raises ClusterSearchError only if the
    search exhausts max_iter with nothing ever found (centers always >= 0); callers should still
    check within_tolerance themselves before trusting the result for a real comparison."""
    lo, hi = target_params * (1 - tol_pct), target_params * (1 + tol_pct)
    ra_lo, ra_hi = ra_bounds
    best = None
    for _ in range(max_iter):
        ra_mid = (ra_lo + ra_hi) / 2
        centers = _subtractive_clustering(X, ra_mid)
        r = len(centers)
        params = params_per_rule * r
        if best is None or abs(params - target_params) < abs(best["n_params"] - target_params):
            best = {"ra": ra_mid, "n_rules": r, "n_params": params, "centers": centers}
        if r > 0 and lo <= params <= hi:
            return {"ra": ra_mid, "n_rules": r, "n_params": params, "centers": centers,
                    "within_tolerance": True, "target_params": target_params}
        if params > target_params:
            ra_lo = ra_mid
        else:
            ra_hi = ra_mid
    if best is None:
        raise ClusterSearchError(f"no clusters ever found in ra in {ra_bounds}")
    best["within_tolerance"] = False
    best["target_params"] = target_params
    return best


class FlatANFISMatched(nn.Module):
    """Flat Sugeno ANFIS with per-rule (non-shared) Gaussian premises, initialised from
    subtractive-clustering centers. n_inputs fixed at 7 (the raw HANFIS inputs)."""

    def __init__(self, centers: np.ndarray, init_sigma: float = 0.25, n_inputs: int = 7) -> None:
        super().__init__()
        if centers.ndim != 2 or centers.shape[1] != n_inputs:
            raise ValueError(f"centers must be (R, {n_inputs}), got {centers.shape}")
        r = centers.shape[0]
        self.n_inputs = n_inputs
        self.centers = nn.Parameter(torch.as_tensor(centers, dtype=torch.float32))          # (R, 7)
        self.log_sigmas = nn.Parameter(torch.full((r, n_inputs), float(np.log(init_sigma))))  # (R, 7)
        self.consequents = nn.Parameter(torch.zeros(r, n_inputs + 1))
        nn.init.normal_(self.consequents, mean=0.0, std=0.05)

    @property
    def rule_count(self) -> int:
        return self.centers.shape[0]

    @property
    def parameter_count(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def firing(self, x: torch.Tensor) -> torch.Tensor:
        sigma = torch.exp(self.log_sigmas).clamp_min(1e-3)                                   # (R, 7)
        d2 = (x[:, None, :] - self.centers[None, :, :]) ** 2 / (sigma[None, :, :] ** 2)       # (N, R, 7)
        w = torch.exp(-0.5 * d2).prod(dim=-1)                                                # (N, R)
        return w / w.sum(dim=1, keepdim=True).clamp_min(1e-12)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        w = self.firing(x)
        xa = torch.cat([torch.ones((x.shape[0], 1), dtype=x.dtype, device=x.device), x], dim=1)
        rule_out = xa @ self.consequents.T
        return (w * rule_out).sum(dim=1)

    @torch.no_grad()
    def solve_consequents(self, x: torch.Tensor, y: torch.Tensor, ridge: float = 1e-3) -> None:
        """Closed-form ridge LSE for the consequents, given current premises (hybrid training,
        mirroring hanfis_end2end.SugenoPanel.solve_consequents but with no monotonicity
        constraint -- FlatANFISMatched is a capacity reference, not a deployable scorer)."""
        w = self.firing(x)
        xa = torch.cat([torch.ones((x.shape[0], 1), dtype=x.dtype), x], dim=1)
        phi = (w[:, :, None] * xa[:, None, :]).reshape(x.shape[0], -1)
        gram = phi.T @ phi + ridge * torch.eye(phi.shape[1], dtype=phi.dtype)
        beta = torch.linalg.solve(gram, phi.T @ y)
        self.consequents.copy_(beta.reshape(self.rule_count, self.n_inputs + 1))


def build_matched(x_train: np.ndarray, target_params: int = 176, tol_pct: float = 0.05) -> tuple[FlatANFISMatched, dict]:
    """Search a clustering radius on x_train and build the matched model. Raises
    ClusterSearchError-adjacent failure (via the returned dict's within_tolerance=False) rather
    than silently accepting an out-of-budget model; caller decides whether to proceed or abort."""
    search = search_radius_for_budget(x_train, target_params=target_params, tol_pct=tol_pct)
    if search["n_rules"] == 0:
        raise ClusterSearchError("subtractive clustering found zero rule centers on this fold's data")
    model = FlatANFISMatched(search["centers"])
    return model, search


def fit_hybrid(model: FlatANFISMatched, x_train: np.ndarray, y_train: np.ndarray,
              x_validation: np.ndarray, y_validation: np.ndarray, epochs: int = 600,
              learning_rate: float = 1e-2, patience: int = 100, ridge: float = 1e-3,
              min_epochs: int = 200) -> dict:
    """Same hybrid scheme as hanfis_end2end.fit_hybrid: closed-form consequents every epoch,
    Adam on premises only. Kept as a separate, simpler function (no monotonicity, single panel)
    rather than importing hanfis_end2end's HANFIS-specific training loop."""
    xtr = torch.as_tensor(x_train, dtype=torch.float32); ytr = torch.as_tensor(y_train, dtype=torch.float32)
    xva = torch.as_tensor(x_validation, dtype=torch.float32); yva = torch.as_tensor(y_validation, dtype=torch.float32)
    premise = [model.centers, model.log_sigmas]
    optimizer = torch.optim.Adam(premise, lr=learning_rate)
    best_loss, best_state, best_epoch, stale = float("inf"), copy.deepcopy(model.state_dict()), 0, 0
    history = {"training_loss": [], "validation_loss": []}
    for epoch in range(epochs):
        model.train()
        model.solve_consequents(xtr, ytr, ridge)
        optimizer.zero_grad()
        loss = torch.mean((model(xtr) - ytr) ** 2)
        loss.backward()
        optimizer.step()
        model.eval()
        with torch.no_grad():
            val = torch.mean((model(xva) - yva) ** 2).item()
        history["training_loss"].append(float(loss.item())); history["validation_loss"].append(val)
        if val < best_loss - 1e-8:
            best_loss, best_state, best_epoch, stale = val, copy.deepcopy(model.state_dict()), epoch + 1, 0
        else:
            stale += 1
            if stale >= patience and epoch + 1 >= min_epochs:
                break
    model.load_state_dict(best_state)
    history.update(best_validation_loss=best_loss, best_epoch=best_epoch)
    return history


def predict(model: FlatANFISMatched, x: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        return model(torch.as_tensor(x, dtype=torch.float32)).cpu().numpy()
