"""Verify the multi-output Sugeno panel math (shared firing weights, k consequent heads) in
NumPy before touching the torch class: for k=1 it must reduce EXACTLY to the existing scalar
panel; for k>1 the Integration panel consuming vector v,e must still just be ordinary Sugeno
over a wider input vector (no new math needed there, only wider consequents)."""
import itertools
import numpy as np

def gauss(x_col, c, s):
    return np.exp(-0.5 * ((x_col[:, None] - c[None, :]) / s[None, :]) ** 2)

def firing(x, centers, sigmas, rule_idx):
    mus = [gauss(x[:, i], centers[i], sigmas[i]) for i in range(x.shape[1])]
    w = np.ones((x.shape[0], rule_idx.shape[0]))
    for i in range(x.shape[1]):
        w *= mus[i][:, rule_idx[:, i]]
    return w / w.sum(1, keepdims=True).clip(1e-12)

rng = np.random.default_rng(0)
n_inputs, m = 3, 2
centers = [np.linspace(0.25, 0.75, m) for _ in range(n_inputs)]
sigmas = [np.full(m, 0.25) for _ in range(n_inputs)]
rules = np.array(list(itertools.product(range(m), repeat=n_inputs)))
X = rng.random((50, n_inputs))
w = firing(X, centers, sigmas, rules)
xa = np.c_[np.ones(50), X]

# k=1: existing scalar behaviour
cons1 = rng.normal(0, 0.3, size=(len(rules), n_inputs + 1))
out_scalar = (w * (xa @ cons1.T)).sum(1)

# multi-head with k=1 (consequents shape (R, n_inputs+1, 1)) must match exactly
cons_multi = cons1[:, :, None]  # (R, 4, 1)
rule_out_multi = np.einsum("nd,rdk->nrk", xa, cons_multi)   # (N, R, 1)
out_multi = (w[:, :, None] * rule_out_multi).sum(1)          # (N, 1)
print("k=1 multi-head matches scalar exactly:", np.allclose(out_multi[:, 0], out_scalar))

# k=3: just more consequent columns, same firing weights -> (N, 3)
k = 3
cons_k = rng.normal(0, 0.3, size=(len(rules), n_inputs + 1, k))
rule_out_k = np.einsum("nd,rdk->nrk", xa, cons_k)
out_k = (w[:, :, None] * rule_out_k).sum(1)
print("k=3 output shape:", out_k.shape, "(expected (50, 3))")

# Integration panel consuming a 2k+1-dim vector (v (k), e (k), x7 (1)) is ordinary Sugeno over
# a wider input -- no new math, just more premise dimensions. Sanity-check rule growth:
for k_test in (1, 2, 4):
    m_I, m_raw = 3, 2
    r_integration = m_I ** (2 * k_test) * m_raw
    r_total = 2 * (m_raw ** 3) + r_integration
    premise = 2 * (3 * m_raw * 2) + 2 * ((2 * k_test + 1) * m_I if k_test else 0)  # rough, illustrative
    cons_V_E = 2 * (m_raw ** 3) * (3 + k_test)      # V,E panels each now output k values per rule
    cons_I = r_integration * (2 * k_test + 1 + 1)
    print(f"k={k_test}: integration rules={r_integration}, total rules={r_total}, "
          f"approx total params={2*(m_raw**3)*2*3 + cons_V_E + 2*(2*k_test+1)*m_I + cons_I}")
