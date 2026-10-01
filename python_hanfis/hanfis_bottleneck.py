"""E5: bottleneck-width sweep (k in {1, 2}; k >= 3 refused by default -- see below).

Deliberately a SEPARATE module from hanfis_end2end.py, not a modification of it: HANFIS (k=1,
the A-09 default) already produced the confirmatory E4 results and must not be touched by
exploratory code. HANFISBottleneck generalises v, e from scalars to k-dimensional vectors fed
into the Integration panel, via a multi-output Sugeno panel (same firing weights/rules, k
consequent heads instead of 1 -- verified in NumPy first, see verify_multihead.py, including
that k=1 reduces EXACTLY to the scalar panel).

Rule growth is exponential in k under grid partition: integration rules = m_I^(2k) * m_raw.
At the frozen m_I=3: k=1 -> 18 rules (176 total params, matches HANFIS exactly); k=2 -> 162
rules (~1,154 params, 6.5x); k=3 -> 1,458 rules; k=4 -> 13,122 rules (~131,000 params, far
exceeding the ~6,200-row inventory). build_bottleneck_hanfis refuses k values whose estimated
parameter count exceeds a data-driven budget unless explicitly overridden, so an infeasible
sweep point fails loudly rather than hanging or silently training something meaningless.

Training: two schemes. fit_hybrid is the Integration-only closed-form scheme (kept for the
superseded, confounded first E5 run). fit_hybrid_lower_alternating (patch 0058) is E2/A-19
generalised to v, e in R^k: both lower panels solved jointly in closed form every epoch, the
Integration panel solved in closed form, premises left to Adam. This is the sweep's default.

Monotone projection (patch 0059): BOTH the Integration solve (solve_consequents) and the lower
joint solve (solve_lower_alternating) clamp the slopes to >= 0 and then REFIT THE INTERCEPTS in
a second, well-posed ridge solve. Patch 0058 refitted only in the lower solve and left the
Integration intercepts stale after projection -- the exact defect E1 found in the scalar model
("intercept refit is critical"). Diagnosed in pure NumPy (verify_bottleneck_refit.py):
with stale Integration intercepts the pure closed-form alternation oscillates (k=1 monotone:
MSE 0.039 -> 0.220 -> 0.021 -> ...; k=2 monotone: 0.177 ... 0.036, which is what the failing
smoke test saw as 0.157); with the refit it converges to the noise floor (k=1: 1.03e-4;
k=2: 8.5e-5 on sigma^2 = 1e-4).

Intermediate clamping (patch 0059, reframed 0062): hanfis_end2end.py's A-09 model does the
same thing deliberately -- forward()/the training loss/the validation loss all hard-clamp v, e
to [0,1] (the "verified E-INT path", A-09's own code), while every closed-form solve always
uses the UNclamped v, e internally (it must -- linearity). This is NOT a bug to fix; A-09's own
comments document the clamp's accuracy cost (RMSE 3.53 hard clamp vs 1.83 soft range-penalty on
scenario S2) and keep it anyway as the confirmatory convention. `clamp_intermediates` (default
True, matching A-09) lets callers switch it OFF as an explicit ablation -- that scores a
DIFFERENT function, not a more-correct one, and is not directly comparable to A-09/E4 results
without saying so. Per-row parity at k=1, clamp on: pearson r=0.9984 against E4's predictions,
0/981 rows assigned to a different fold (scripts/e5_e4_parity.py, patch 0061) -- this is what
confirms the k=1 reproduction claim at the module docstring's top, not just the pooled skill
being close.
"""
from __future__ import annotations

import copy
import itertools

import numpy as np
import torch
from torch import nn


class BottleneckBudgetError(RuntimeError):
    """Raised when a requested k implies a parameter count the data cannot support."""


def estimate_params(m_raw: int, m_intermediate: int, bottleneck_k: int) -> dict:
    r_ve = m_raw ** 3
    r_i = m_intermediate ** (2 * bottleneck_k) * m_raw
    cons_ve = r_ve * (3 + 1) * bottleneck_k           # each of V, E: R rules x (n_in+1) x k heads
    premise_ve = 2 * 3 * m_raw                        # gauss: 2 params x 3 inputs x m_raw MFs each... per panel
    cons_i = r_i * (2 * bottleneck_k + 1 + 1)
    premise_i = 2 * (2 * bottleneck_k) * m_intermediate + 2 * 1 * m_raw
    total_params = 2 * (premise_ve + cons_ve) + premise_i + cons_i
    return {"bottleneck_k": bottleneck_k, "integration_rules": r_i, "ve_rules_each": r_ve,
            "total_rules": r_i + 2 * r_ve, "total_params": total_params}


class MultiHeadSugenoPanel(nn.Module):
    """Like hanfis_end2end.SugenoPanel, but with k_out >= 1 consequent heads sharing one set of
    rules/firing weights. k_out=1 reduces exactly to the single-output panel (verified in
    verify_multihead.py). Gaussian premises only (the exploratory sweep does not re-run the
    MF-family ablation)."""

    def __init__(self, m_per_input: list[int], k_out: int = 1, monotone: bool = False) -> None:
        super().__init__()
        self.m_per_input = list(int(m) for m in m_per_input)
        self.n_inputs = len(self.m_per_input)
        self.k_out = int(k_out)
        self.monotone = monotone
        self.centers = nn.ParameterList([nn.Parameter(torch.linspace(0.25, 0.75, m) if m > 1 else torch.tensor([0.5])) for m in self.m_per_input])
        self.log_sigmas = nn.ParameterList([nn.Parameter(torch.full((m,), float(np.log(0.25)))) for m in self.m_per_input])
        rules = list(itertools.product(*[range(m) for m in self.m_per_input]))
        self.register_buffer("rule_indices", torch.tensor(rules, dtype=torch.long))
        self.consequents = nn.Parameter(torch.zeros(len(rules), self.n_inputs + 1, self.k_out))
        nn.init.normal_(self.consequents, mean=0.0, std=0.05)

    @property
    def rule_count(self) -> int:
        return int(self.rule_indices.shape[0])

    @property
    def premise_parameter_count(self) -> int:
        return sum(2 * m for m in self.m_per_input)

    @property
    def parameter_count(self) -> int:
        return self.premise_parameter_count + self.consequents.numel()

    def effective_consequents(self) -> torch.Tensor:
        if not self.monotone:
            return self.consequents
        return torch.cat([self.consequents[:, :1, :], torch.nn.functional.softplus(self.consequents[:, 1:, :])], dim=1)

    def memberships(self, x: torch.Tensor, i: int) -> torch.Tensor:
        sigma = torch.exp(self.log_sigmas[i]).clamp_min(1e-3)
        xi = x[:, i : i + 1]
        return torch.exp(-0.5 * ((xi - self.centers[i][None, :]) / sigma[None, :]) ** 2)

    def firing(self, x: torch.Tensor) -> torch.Tensor:
        selected = [self.memberships(x, i)[:, self.rule_indices[:, i]] for i in range(self.n_inputs)]
        w = torch.stack(selected, dim=-1).prod(dim=-1)
        return w / w.sum(dim=1, keepdim=True).clamp_min(1e-12)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Returns (N, k_out); callers wanting the old scalar behaviour use k_out=1 and squeeze."""
        w = self.firing(x)                                                            # (N, R)
        xa = torch.cat([torch.ones((x.shape[0], 1), dtype=x.dtype, device=x.device), x], dim=1)  # (N, n_in+1)
        cons = self.effective_consequents()                                           # (R, n_in+1, k)
        rule_out = torch.einsum("nd,rdk->nrk", xa, cons)                              # (N, R, k)
        return (w[:, :, None] * rule_out).sum(dim=1)                                  # (N, k)

    @torch.no_grad()
    def solve_consequents(self, x: torch.Tensor, y: torch.Tensor, ridge: float | None = 1e-3) -> None:
        """y: (N, k_out). One Gram matrix, k_out right-hand sides solved at once."""
        w = self.firing(x)
        xa = torch.cat([torch.ones((x.shape[0], 1), dtype=x.dtype, device=x.device), x], dim=1)
        phi = (w[:, :, None] * xa[:, None, :]).reshape(x.shape[0], -1)                 # (N, R*(n_in+1))
        if ridge is None:
            ridge = max(1e-3, 0.01 * phi.shape[1] / phi.shape[0])
        gram = phi.T @ phi + ridge * torch.eye(phi.shape[1], dtype=phi.dtype, device=phi.device)
        beta = torch.linalg.solve(gram, phi.T @ y)                                     # (R*(n_in+1), k_out)
        beta = beta.reshape(self.rule_count, self.n_inputs + 1, self.k_out)
        if self.monotone:
            # Clamp slopes >= 0, then refit ONLY the intercepts (one per rule per head) against
            # the residual left by the clamped slopes: one (R x R) Gram, k_out right-hand sides.
            # Without this the intercepts fitted jointly with the (now discarded) negative slopes
            # stay in place and the projected panel is biased -- see module docstring.
            slope = beta[:, 1:, :].clamp_min(1e-4)                                     # (R, n_in, k_out)
            y_slope = torch.einsum("nr,rdk,nd->nk", w, slope, xa[:, 1:])               # (N, k_out)
            gram_i = w.T @ w + ridge * torch.eye(self.rule_count, dtype=phi.dtype, device=phi.device)
            intercepts = torch.linalg.solve(gram_i, w.T @ (y - y_slope))               # (R, k_out)
            beta = torch.cat([intercepts[:, None, :], torch.log(torch.expm1(slope))], dim=1)
        self.consequents.copy_(beta)


class HANFISBottleneck(nn.Module):
    """V(x1..x3)->v in R^k, E(x4..x6)->e in R^k, I(v,e,x7)->r. k=1 matches HANFIS exactly."""

    def __init__(self, m_raw: int = 2, m_intermediate: int = 3, bottleneck_k: int = 1,
                m_threat: int | None = None, monotone: bool = False,
                max_params: int = 2000, allow_oversize: bool = False,
                clamp_intermediates: bool = True) -> None:
        super().__init__()
        m_threat = m_raw if m_threat is None else m_threat
        est = estimate_params(m_raw, m_intermediate, bottleneck_k)
        if est["total_params"] > max_params and not allow_oversize:
            raise BottleneckBudgetError(
                f"bottleneck_k={bottleneck_k} with m_intermediate={m_intermediate} implies "
                f"~{est['total_params']} parameters ({est['integration_rules']} integration rules "
                f"alone), over the {max_params}-parameter budget. This is itself the E5 finding: "
                f"grid-partitioning the integration tier explodes combinatorially with k. Pass "
                f"allow_oversize=True only if you accept the resulting training cost.")
        self.bottleneck_k = bottleneck_k
        self.monotone = monotone
        self.clamp_intermediates = bool(clamp_intermediates)
        self.vulnerability = MultiHeadSugenoPanel([m_raw, m_raw, m_raw], k_out=bottleneck_k, monotone=monotone)
        self.environment = MultiHeadSugenoPanel([m_raw, m_raw, m_raw], k_out=bottleneck_k, monotone=monotone)
        self.integration = MultiHeadSugenoPanel([m_intermediate] * (2 * bottleneck_k) + [m_threat], k_out=1, monotone=monotone)

    @property
    def rule_count(self) -> int:
        return self.vulnerability.rule_count + self.environment.rule_count + self.integration.rule_count

    @property
    def parameter_count(self) -> int:
        return sum(p.parameter_count for p in (self.vulnerability, self.environment, self.integration))

    def intermediates(self, x7: torch.Tensor, clamp: bool = True) -> tuple[torch.Tensor, torch.Tensor]:
        v = self.vulnerability(x7[:, 0:3])     # (N, k)
        e = self.environment(x7[:, 3:6])       # (N, k)
        if clamp:
            v, e = torch.clamp(v, 0.0, 1.0), torch.clamp(e, 0.0, 1.0)
        return v, e

    def integration_input(self, x7: torch.Tensor, clamp: bool = True) -> torch.Tensor:
        v, e = self.intermediates(x7, clamp=clamp)
        return torch.cat([v, e, x7[:, 6:7]], dim=1)   # (N, 2k+1)

    def forward(self, x7: torch.Tensor) -> torch.Tensor:
        # clamp_intermediates=False makes forward() exactly the function the closed-form solves
        # minimise (they always use clamp=False); the output clip to [0,1] is kept in both cases.
        r = self.integration(self.integration_input(x7, clamp=self.clamp_intermediates))   # (N, 1)
        return torch.clamp(r[:, 0], 0.0, 1.0)


def fit_hybrid(model: HANFISBottleneck, x_train: np.ndarray, y_train: np.ndarray,
              x_validation: np.ndarray, y_validation: np.ndarray, epochs: int = 600,
              learning_rate: float = 1e-2, patience: int = 100, ridge: float | None = 1e-3,
              min_epochs: int = 200) -> dict:
    """Integration-only closed form (NOT E2's alternating scheme -- see module docstring)."""
    xtr = torch.as_tensor(x_train, dtype=torch.float32); ytr = torch.as_tensor(y_train, dtype=torch.float32)[:, None]
    xva = torch.as_tensor(x_validation, dtype=torch.float32); yva = torch.as_tensor(y_validation, dtype=torch.float32)[:, None]
    premise = [p for panel in (model.vulnerability, model.environment, model.integration)
              for p in list(panel.centers) + list(panel.log_sigmas)]
    optimizer = torch.optim.Adam(premise, lr=learning_rate)
    best_loss, best_state, best_epoch, stale = float("inf"), copy.deepcopy(model.state_dict()), 0, 0
    history = {"training_loss": [], "validation_loss": []}
    for epoch in range(epochs):
        model.train()
        model.integration.solve_consequents(model.integration_input(xtr, clamp=False), ytr, ridge)
        optimizer.zero_grad()
        loss = torch.mean((model(xtr) - ytr[:, 0]) ** 2)
        loss.backward()
        optimizer.step()
        model.eval()
        with torch.no_grad():
            val = torch.mean((model(xva) - yva[:, 0]) ** 2).item()
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


def predict(model: HANFISBottleneck, x: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        return model(torch.as_tensor(x, dtype=torch.float32)).cpu().numpy()


@torch.no_grad()
def solve_lower_alternating(model: "HANFISBottleneck", x7: torch.Tensor, y: torch.Tensor, ridge: float | None = 1e-3) -> None:
    """Vector generalisation of hanfis_end2end.solve_lower_alternating (E2, patch 0035) to
    bottleneck_k > 1. Given Integration's just-solved consequents and current firing weights
    (frozen this outer iteration), r is affine in v,e in R^k per row:
        r_n = A_n + sum_i B_{n,i} v_{n,i} + sum_j C_{n,j} e_{n,j}
    with A, B, C aggregated from Integration's frozen firing weights and consequents. Since
    v_{n,i} (resp. e_{n,j}) is itself affine in V's (resp. E's) own frozen-firing-weight
    consequents, r is linear in the FLATTENED beta_V, beta_E given this iteration's firing
    weights: one joint ridge LSE solves both panels' full (R, n_in+1, k) consequent tensors at
    once. Verified first in pure NumPy (verify_vector_alternating.py) for k=1,2,3, monotone and
    non-monotone, converging without divergence in every case before this torch transcription.

    Must be called AFTER model.integration.solve_consequents() this same outer iteration/epoch,
    exactly like hanfis_end2end's version.
    """
    k = model.bottleneck_k
    v, e = model.intermediates(x7, clamp=False)
    v, e = v.detach(), e.detach()
    x7d = x7.detach()
    xi = torch.cat([v, e, x7d[:, 6:7]], dim=1)
    wI = model.integration.firing(xi)                                  # (N, R_I)
    betaI = model.integration.effective_consequents()[:, :, 0]          # (R_I, 2k+2)
    A = (wI * (betaI[:, 0] + betaI[:, -1] * x7d[:, 6][:, None])).sum(dim=1)
    B = wI @ betaI[:, 1 : 1 + k]        # (N, k)
    C = wI @ betaI[:, 1 + k : 1 + 2 * k]  # (N, k)

    wV = model.vulnerability.firing(x7d[:, 0:3])   # (N, R_V)
    wE = model.environment.firing(x7d[:, 3:6])     # (N, R_E)
    xaV = torch.cat([torch.ones((x7d.shape[0], 1), dtype=x7d.dtype, device=x7d.device), x7d[:, 0:3]], dim=1)
    xaE = torch.cat([torch.ones((x7d.shape[0], 1), dtype=x7d.dtype, device=x7d.device), x7d[:, 3:6]], dim=1)
    R_V, R_E = model.vulnerability.rule_count, model.environment.rule_count
    # Phi_V[n, (p,d,i)] = B[n,i] * wV[n,p] * xaV[n,d]; flattened to (N, R_V*4*k)
    phi_V = torch.einsum("ni,np,nd->npdi", B, wV, xaV).reshape(x7d.shape[0], -1)
    phi_E = torch.einsum("nj,nq,nd->nqdj", C, wE, xaE).reshape(x7d.shape[0], -1)
    phi = torch.cat([phi_V, phi_E], dim=1)
    target = y - A
    if ridge is None:
        ridge = max(1e-3, 0.01 * phi.shape[1] / phi.shape[0])
    gram = phi.T @ phi + ridge * torch.eye(phi.shape[1], device=phi.device, dtype=phi.dtype)
    beta = torch.linalg.solve(gram, phi.T @ target)
    n_v = R_V * 4 * k
    beta_V = beta[:n_v].reshape(R_V, 4, k)
    beta_E = beta[n_v:].reshape(R_E, 4, k)

    if model.monotone:
        # Clamp every slope entry (both panels, every head) >= 0, then refit ONLY the
        # intercepts (one per rule per head) in a second, well-posed ridge solve -- the same
        # "clamp then refit" idea as the scalar case, generalised across the k heads.
        slope_V = beta_V[:, 1:, :].clamp_min(1e-4)   # (R_V, 3, k)
        slope_E = beta_E[:, 1:, :].clamp_min(1e-4)   # (R_E, 3, k)
        v_slope = torch.einsum("np,pdi,nd->ni", wV, slope_V, xaV[:, 1:])   # (N, k)
        e_slope = torch.einsum("nq,qdj,nd->nj", wE, slope_E, xaE[:, 1:])   # (N, k)
        residual = target - (B * v_slope).sum(dim=1) - (C * e_slope).sum(dim=1)
        phi_int_V = torch.einsum("ni,np->npi", B, wV).reshape(x7d.shape[0], -1)   # (N, R_V*k)
        phi_int_E = torch.einsum("nj,nq->nqj", C, wE).reshape(x7d.shape[0], -1)   # (N, R_E*k)
        phi_int = torch.cat([phi_int_V, phi_int_E], dim=1)
        gram_i = phi_int.T @ phi_int + ridge * torch.eye(phi_int.shape[1], device=phi.device, dtype=phi.dtype)
        intercepts = torch.linalg.solve(gram_i, phi_int.T @ residual)
        int_V = intercepts[: R_V * k].reshape(R_V, k)
        int_E = intercepts[R_V * k :].reshape(R_E, k)
        beta_V = torch.cat([int_V[:, None, :], torch.log(torch.expm1(slope_V))], dim=1)
        beta_E = torch.cat([int_E[:, None, :], torch.log(torch.expm1(slope_E))], dim=1)

    model.vulnerability.consequents.copy_(beta_V)
    model.environment.consequents.copy_(beta_E)


def fit_hybrid_lower_alternating(model: "HANFISBottleneck", x_train: np.ndarray, y_train: np.ndarray,
                                 x_validation: np.ndarray, y_validation: np.ndarray, epochs: int = 600,
                                 learning_rate: float = 1e-2, patience: int = 100, ridge: float | None = 1e-3,
                                 min_epochs: int = 200) -> dict:
    """E2 generalised to bottleneck_k >= 1: both lower panels solved jointly in closed form every
    epoch (solve_lower_alternating), Integration solved in closed form too (as in fit_hybrid),
    premises left to Adam. This is what de-confounds the E5 sweep: at k=1 it is mathematically
    the SAME scheme as hanfis_end2end.fit_hybrid_lower_alternating (A-09), just reimplemented for
    this module's MultiHeadSugenoPanel representation."""
    xtr = torch.as_tensor(x_train, dtype=torch.float32); ytr = torch.as_tensor(y_train, dtype=torch.float32)
    xva = torch.as_tensor(x_validation, dtype=torch.float32); yva = torch.as_tensor(y_validation, dtype=torch.float32)
    premise = [p for panel in (model.vulnerability, model.environment, model.integration)
              for p in list(panel.centers) + list(panel.log_sigmas)]
    optimizer = torch.optim.Adam(premise, lr=learning_rate)
    best_loss, best_state, best_epoch, stale = float("inf"), copy.deepcopy(model.state_dict()), 0, 0
    history = {"training_loss": [], "validation_loss": []}
    for epoch in range(epochs):
        model.train()
        model.integration.solve_consequents(model.integration_input(xtr, clamp=False), ytr[:, None], ridge)
        solve_lower_alternating(model, xtr, ytr, ridge)
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
