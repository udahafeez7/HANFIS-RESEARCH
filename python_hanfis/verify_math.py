"""Pure-NumPy reimplementation of HANFIS (gauss, non-monotone) to verify the closed-form
alternating-lower-panel LSE derivation before transcribing it into the torch module.
No torch dependency (sandbox has no disk space for it); this is a from-scratch, independent
implementation of the SAME forward math as hanfis_end2end.py, used only to check the algebra.
"""
import itertools
import numpy as np

rng = np.random.default_rng(0)

def gauss_memberships(x_col, centers, sigmas):
    return np.exp(-0.5 * ((x_col[:, None] - centers[None, :]) / sigmas[None, :]) ** 2)

def firing(x, centers_list, sigmas_list, rule_idx):
    mus = [gauss_memberships(x[:, i], centers_list[i], sigmas_list[i]) for i in range(x.shape[1])]
    w = np.ones((x.shape[0], rule_idx.shape[0]))
    for i in range(x.shape[1]):
        w *= mus[i][:, rule_idx[:, i]]
    return w / w.sum(axis=1, keepdims=True).clip(1e-12)

def make_panel(m_per_input, seed):
    r = np.random.default_rng(seed)
    centers = [np.linspace(0.25, 0.75, m) for m in m_per_input]
    sigmas = [np.full(m, 0.25) for m in m_per_input]
    rules = np.array(list(itertools.product(*[range(m) for m in m_per_input])))
    consequents = r.normal(0, 0.3, size=(len(rules), len(m_per_input) + 1))
    return centers, sigmas, rules, consequents

def panel_forward(x, centers, sigmas, rules, consequents):
    w = firing(x, centers, sigmas, rules)
    xa = np.c_[np.ones(len(x)), x]
    return (w * (xa @ consequents.T)).sum(1), w

def ridge_solve(phi, y, lam):
    return np.linalg.solve(phi.T @ phi + lam * np.eye(phi.shape[1]), phi.T @ y)

N = 400
X = rng.random((N, 7))
# ground truth: r = 0.3 + 0.4*mean(x1,x2,x3) + 0.5*mean(x4,x5,x6) + 0.2*x7 + noise
y = 0.3 + 0.4 * X[:, :3].mean(1) + 0.5 * X[:, 3:6].mean(1) + 0.2 * X[:, 6] + rng.normal(0, 0.01, N)

mV = [2, 2, 2]; mE = [2, 2, 2]; mI = [3, 3, 2]
cV, sV, rV, bV = make_panel(mV, 1)
cE, sE, rE, bE = make_panel(mE, 2)
cI, sI, rI, bI = make_panel(mI, 3)
lam = 1e-3

def full_forward():
    v, wV = panel_forward(X[:, 0:3], cV, sV, rV, bV)
    e, wE = panel_forward(X[:, 3:6], cE, sE, rE, bE)
    v_, e_ = np.clip(v, 0, 1), np.clip(e, 0, 1)
    xi = np.c_[v_, e_, X[:, 6]]
    r, wI = panel_forward(xi, cI, sI, rI, bI)
    return r, v_, e_, wV, wE, wI

def mse():
    r, *_ = full_forward()
    return float(np.mean((r - y) ** 2))

print("MSE before any closed-form solve (random init):", mse())

for outer in range(6):
    # step 1: solve Integration consequents given current v,e,x7 (standard, already in fit_hybrid)
    r, v_, e_, wV, wE, wI = full_forward()
    xi = np.c_[v_, e_, X[:, 6]]
    xa_I = np.c_[np.ones(N), xi]
    phi_I = (wI[:, :, None] * xa_I[:, None, :]).reshape(N, -1)
    beta_I = ridge_solve(phi_I, y, lam).reshape(rI.shape[0], -1)
    bI[:] = beta_I

    # step 2: alternating closed-form for LOWER panels, given frozen wI and just-updated beta_I
    A = (wI * (beta_I[:, 0] + beta_I[:, 3] * X[:, 6][:, None])).sum(1)   # (N,) offset incl. x7 term
    B = (wI * beta_I[:, 1]).sum(1)     # (N,) coefficient on v
    C = (wI * beta_I[:, 2]).sum(1)     # (N,) coefficient on e

    xa_V = np.c_[np.ones(N), X[:, 0:3]]     # (N,4)
    xa_E = np.c_[np.ones(N), X[:, 3:6]]     # (N,4)
    RV, RE = rV.shape[0], rE.shape[0]
    phi_V = (B[:, None] * wV)[:, :, None] * xa_V[:, None, :]      # (N, RV, 4)
    phi_E = (C[:, None] * wE)[:, :, None] * xa_E[:, None, :]      # (N, RE, 4)
    phi_lower = np.concatenate([phi_V.reshape(N, -1), phi_E.reshape(N, -1)], axis=1)   # (N, 4RV+4RE)
    target = y - A
    beta_lower = ridge_solve(phi_lower, target, lam)
    beta_V = beta_lower[: 4 * RV].reshape(RV, 4)
    beta_E = beta_lower[4 * RV :].reshape(RE, 4)
    bV[:] = beta_V; bE[:] = beta_E

    print(f"outer {outer}: MSE after Integration solve + lower-alternating solve =", mse())

# sanity: does it match jointly solving EVERYTHING at once via one big linear system with frozen premises?
# (upper bound on what alternating can reach without touching premises)
r, v_, e_, wV, wE, wI = full_forward()
xi = np.c_[v_, e_, X[:, 6]]
xa_I = np.c_[np.ones(N), xi]
phi_I_check = (wI[:, :, None] * xa_I[:, None, :]).reshape(N, -1)
print("residual after convergence (train MSE):", mse())
