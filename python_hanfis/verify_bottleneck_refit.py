"""Pure-NumPy mirror of hanfis_bottleneck.py (patch 0058 -> 0059), float64, no torch needed.

    python python_hanfis/verify_bottleneck_refit.py

Reproduces the failing smoke test of patch 0058 (k=2, monotone, 6 closed-form alternations,
MSE ~0.16 with var(y) ~0.0125) and isolates its two causes:
  1. Integration solve_consequents projected slopes (softplus) but left the intercepts stale
     -> alternation oscillates (refit_I=False rows).
  2. forward() clamps v, e to [0,1] while the solves use unclamped v, e -> all remaining MSE
     (clamp=True rows) vs noise floor sigma^2 = 1e-4 (clamp=False rows).
Fix in patch 0059: intercept refit in solve_consequents + clamp_intermediates switch.
"""
import itertools, numpy as np

def softplus(z): return np.logaddexp(0.0, z)
def inv_softplus(z): return np.log(np.expm1(z))

class Panel:
    def __init__(self, m_per_input, k_out, monotone, rng):
        self.m = list(m_per_input); self.n_in = len(self.m); self.k = k_out; self.monotone = monotone
        self.centers = [np.linspace(0.25, 0.75, m) if m > 1 else np.array([0.5]) for m in self.m]
        self.log_sigmas = [np.full(m, np.log(0.25)) for m in self.m]
        self.rules = np.array(list(itertools.product(*[range(m) for m in self.m])))
        self.R = len(self.rules)
        self.cons = rng.normal(0, 0.05, (self.R, self.n_in + 1, self.k))
    def eff(self):
        if not self.monotone: return self.cons
        return np.concatenate([self.cons[:, :1, :], softplus(self.cons[:, 1:, :])], axis=1)
    def firing(self, x):
        ws = []
        for i in range(self.n_in):
            s = np.maximum(np.exp(self.log_sigmas[i]), 1e-3)
            mu = np.exp(-0.5 * ((x[:, i:i+1] - self.centers[i][None]) / s[None]) ** 2)
            ws.append(mu[:, self.rules[:, i]])
        w = np.prod(np.stack(ws, -1), -1)
        return w / np.maximum(w.sum(1, keepdims=True), 1e-12)
    def forward(self, x):
        w = self.firing(x); xa = np.concatenate([np.ones((len(x), 1)), x], 1)
        ro = np.einsum("nd,rdk->nrk", xa, self.eff())
        return (w[:, :, None] * ro).sum(1)
    def solve(self, x, y, ridge, refit_intercepts):
        w = self.firing(x); xa = np.concatenate([np.ones((len(x), 1)), x], 1)
        phi = (w[:, :, None] * xa[:, None, :]).reshape(len(x), -1)
        gram = phi.T @ phi + ridge * np.eye(phi.shape[1])
        beta = np.linalg.solve(gram, phi.T @ y).reshape(self.R, self.n_in + 1, self.k)
        if self.monotone:
            slope = np.maximum(beta[:, 1:, :], 1e-4)
            if refit_intercepts:
                yhat_slope = np.einsum("nr,rdk,nd->nk", w, slope, xa[:, 1:])
                resid = y - yhat_slope
                gram_i = w.T @ w + ridge * np.eye(self.R)
                inter = np.linalg.solve(gram_i, w.T @ resid)          # (R, k)
                beta = np.concatenate([inter[:, None, :], inv_softplus(slope)], 1)
            else:
                beta = np.concatenate([beta[:, :1, :], inv_softplus(slope)], 1)
        self.cons = beta

class Model:
    def __init__(self, k, monotone, rng, m_raw=2, m_i=3):
        self.k = k; self.monotone = monotone
        self.V = Panel([m_raw]*3, k, monotone, rng); self.E = Panel([m_raw]*3, k, monotone, rng)
        self.I = Panel([m_i]*(2*k) + [m_raw], 1, monotone, rng)
    def inter(self, x, clamp):
        v, e = self.V.forward(x[:, 0:3]), self.E.forward(x[:, 3:6])
        if clamp: v, e = np.clip(v, 0, 1), np.clip(e, 0, 1)
        return v, e
    def iin(self, x, clamp):
        v, e = self.inter(x, clamp); return np.concatenate([v, e, x[:, 6:7]], 1)
    def forward(self, x):
        return np.clip(self.I.forward(self.iin(x, True))[:, 0], 0, 1)

def solve_lower(model, x, y, ridge):
    k = model.k
    v, e = model.inter(x, False); xi = np.concatenate([v, e, x[:, 6:7]], 1)
    wI = model.I.firing(xi); bI = model.I.eff()[:, :, 0]
    A = (wI * (bI[:, 0] + bI[:, -1] * x[:, 6][:, None])).sum(1)
    B = wI @ bI[:, 1:1+k]; C = wI @ bI[:, 1+k:1+2*k]
    wV, wE = model.V.firing(x[:, 0:3]), model.E.firing(x[:, 3:6])
    xaV = np.concatenate([np.ones((len(x), 1)), x[:, 0:3]], 1); xaE = np.concatenate([np.ones((len(x), 1)), x[:, 3:6]], 1)
    RV, RE = model.V.R, model.E.R
    phiV = np.einsum("ni,np,nd->npdi", B, wV, xaV).reshape(len(x), -1)
    phiE = np.einsum("nj,nq,nd->nqdj", C, wE, xaE).reshape(len(x), -1)
    phi = np.concatenate([phiV, phiE], 1); target = y - A
    beta = np.linalg.solve(phi.T @ phi + ridge * np.eye(phi.shape[1]), phi.T @ target)
    nv = RV * 4 * k; bV = beta[:nv].reshape(RV, 4, k); bE = beta[nv:].reshape(RE, 4, k)
    if model.monotone:
        sV, sE = np.maximum(bV[:, 1:, :], 1e-4), np.maximum(bE[:, 1:, :], 1e-4)
        vs = np.einsum("np,pdi,nd->ni", wV, sV, xaV[:, 1:]); es = np.einsum("nq,qdj,nd->nj", wE, sE, xaE[:, 1:])
        resid = target - (B * vs).sum(1) - (C * es).sum(1)
        piV = np.einsum("ni,np->npi", B, wV).reshape(len(x), -1); piE = np.einsum("nj,nq->nqj", C, wE).reshape(len(x), -1)
        pi = np.concatenate([piV, piE], 1)
        inter = np.linalg.solve(pi.T @ pi + ridge * np.eye(pi.shape[1]), pi.T @ resid)
        iV = inter[:RV*k].reshape(RV, k); iE = inter[RV*k:].reshape(RE, k)
        bV = np.concatenate([iV[:, None, :], inv_softplus(sV)], 1); bE = np.concatenate([iE[:, None, :], inv_softplus(sE)], 1)
    model.V.cons, model.E.cons = bV, bE

def synthetic(n=400, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.random((n, 7)).astype(np.float32)
    y = (0.3 + 0.4 * x[:, :3].mean(1) + 0.5 * x[:, 3:6].mean(1) + 0.2 * x[:, 6] + rng.normal(0, 0.01, n)).astype(np.float32)
    return x.astype(np.float64), np.clip(y, 0, 1).astype(np.float64)

class ModelNoClamp(Model):
    def forward(self, x):
        return np.clip(self.I.forward(self.iin(x, False))[:, 0], 0, 1)


def run(k, monotone, seed, refit, clamp=True, n=400, iters=6, ridge=1e-3):
    x, y = synthetic(n, seed); rng = np.random.default_rng(seed)
    m = (Model if clamp else ModelNoClamp)(k, monotone, rng); hist = []
    for _ in range(iters):
        m.I.solve(m.iin(x, False), y[:, None], ridge, refit)
        solve_lower(m, x, y, ridge)
        hist.append(np.mean((m.forward(x) - y) ** 2))
    return np.array(hist), np.var(y)


if __name__ == "__main__":
    print("stage 1 -- patch 0058 behaviour (clamp=True) with/without Integration intercept refit")
    for k, mono, seed in [(1, False, 0), (1, True, 1), (2, True, 1), (2, False, 1)]:
        for refit in (False, True):
            h, vy = run(k, mono, seed, refit, clamp=True)
            print(f"  k={k} mono={mono} refit_I={refit}: var(y)={vy:.4f} mse/iter {np.round(h, 5)}")
    print("stage 2 -- patch 0059: refit + clamp_intermediates=False (must reach ~1e-4 = sigma^2)")
    ok = True
    for k, mono, seed, n in [(1, False, 0, 400), (1, True, 1, 400), (2, True, 1, 400), (2, True, 1, 2000), (2, False, 1, 2000)]:
        h, vy = run(k, mono, seed, True, clamp=False, n=n)
        good = np.isfinite(h[-1]) and h[-1] <= h[0] and h[-1] < 0.05 * vy
        ok &= bool(good)
        print(f"  k={k} mono={mono} n={n}: var(y)={vy:.4f} mse/iter {np.round(h, 6)} final/var={h[-1]/vy:.4f} {'OK' if good else 'FAIL'}")
    print("VERIFY_BOTTLENECK_REFIT=" + ("PASS" if ok else "FAIL"))
