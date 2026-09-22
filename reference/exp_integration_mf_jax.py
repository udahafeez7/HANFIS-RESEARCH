"""E-INT: perbandingan panel Integrasi m_I = 2 (24 aturan) vs m_I = 3 pada v,e (34 aturan).

Referensi JAX (CPU) untuk memverifikasi rancangan sebelum diporting ke PyTorch.
Data sintetis hanya untuk validasi kode; angka tidak untuk diklaim.
"""
from __future__ import annotations
import itertools, json, time, sys
import numpy as np
import jax, jax.numpy as jnp
import pandas as pd

jax.config.update("jax_enable_x64", False)
FEATURES = ["cvss", "exploitability", "patch_risk", "mfa_risk", "kubernetes_exposure", "asset_criticality", "threat_intelligence"]


# ----------------------------------------------------------------- data
def synthetic_repo(n, seed):
    """Identik dengan synthetic_dataset() di repositori (skenario S1, mulus)."""
    rng = np.random.default_rng(seed)
    f = pd.DataFrame(rng.random((n, 7)), columns=FEATURES)
    f["vulnerability_target"] = 0.35 * f.cvss + 0.25 * f.exploitability + 0.20 * f.patch_risk + 0.10 * f.cvss * f.exploitability + 0.10 * f.exploitability * f.patch_risk
    f["environment_target"] = 0.25 * f.mfa_risk + 0.30 * f.kubernetes_exposure + 0.30 * f.asset_criticality + 0.15 * f.kubernetes_exposure * f.asset_criticality
    f["dynamic_risk_target"] = np.clip(0.32 * f.vulnerability_target + 0.28 * f.environment_target + 0.32 * f.threat_intelligence + 0.18 * f.threat_intelligence * f.vulnerability_target, 0, 1)
    return f


def synthetic_threshold(n, seed):
    """Skenario S2: interaksi tajam dan ambang; menguji apakah resolusi v,e (m_I) berpengaruh."""
    rng = np.random.default_rng(seed)
    f = pd.DataFrame(rng.random((n, 7)), columns=FEATURES)
    v = 0.4 * f.cvss + 0.4 * f.exploitability + 0.2 * f.patch_risk + 0.2 * f.cvss * f.exploitability * f.patch_risk
    e = 0.3 * f.mfa_risk + 0.4 * f.kubernetes_exposure + 0.3 * f.asset_criticality
    v = np.clip(v, 0, 1); e = np.clip(e, 0, 1)
    gate_v = 1 / (1 + np.exp(-12 * (v - 0.55)))          # ambang pada kerentanan
    gate_e = 1 / (1 + np.exp(-10 * (e - 0.45)))          # ambang pada lingkungan
    y = 0.15 + 0.55 * gate_v * gate_e + 0.20 * f.threat_intelligence * gate_v + 0.10 * e
    f["vulnerability_target"] = v; f["environment_target"] = e
    f["dynamic_risk_target"] = np.clip(y, 0, 1)
    return f


def split_indices(n, seed):
    order = np.random.default_rng(seed).permutation(n)
    a, b = int(0.7 * n), int(0.15 * n)
    return order[:a], order[a:a + b], order[a + b:]


# ----------------------------------------------------------------- model
def init_panel(key, n_in, m_list):
    """m_list: jumlah MF per input (boleh berbeda, misal [3,3,2])."""
    centers = [jnp.linspace(0.25, 0.75, m) if m > 1 else jnp.array([0.5]) for m in m_list]
    log_sig = [jnp.full((m,), np.log(0.25)) for m in m_list]
    rules = jnp.array(list(itertools.product(*[range(m) for m in m_list])), dtype=jnp.int32)
    cons = 0.05 * jax.random.normal(key, (rules.shape[0], n_in + 1))
    return {"centers": centers, "log_sig": log_sig, "cons": cons}, rules


def panel_forward(params, rules, x):
    """x: (N, n_in) -> (N,) ; juga kembalikan firing ternormalisasi (N, R)."""
    N, n_in = x.shape
    memb = []
    for i in range(n_in):
        sig = jnp.exp(params["log_sig"][i]).clip(1e-3)
        mu = jnp.exp(-0.5 * ((x[:, i:i + 1] - params["centers"][i][None, :]) / sig[None, :]) ** 2)  # (N, m_i)
        memb.append(mu[:, rules[:, i]])                                                              # (N, R)
    firing = jnp.prod(jnp.stack(memb, -1), -1)
    w = firing / firing.sum(1, keepdims=True).clip(1e-12)
    xa = jnp.concatenate([jnp.ones((N, 1)), x], 1)
    out = (w * (xa @ params["cons"].T)).sum(1)
    return out, w, xa


def hanfis_forward(P, R, x7):
    v, _, _ = panel_forward(P["V"], R["V"], x7[:, 0:3]); v = jnp.clip(v, 0, 1)
    e, _, _ = panel_forward(P["E"], R["E"], x7[:, 3:6]); e = jnp.clip(e, 0, 1)
    xi = jnp.stack([v, e, x7[:, 6]], 1)
    r, w, xa = panel_forward(P["I"], R["I"], xi)
    return jnp.clip(r, 0, 1), (v, e, w, xa)


def n_params(P):
    return int(sum(int(np.prod(np.shape(a))) for a in jax.tree_util.tree_leaves(P)))


# ----------------------------------------------------------------- training
def adam_init(P):
    z = jax.tree_util.tree_map(jnp.zeros_like, P)
    return {"m": z, "v": z, "t": 0}


def adam_step(P, g, st, lr, b1=0.9, b2=0.999, eps=1e-8):
    st["t"] += 1
    st["m"] = jax.tree_util.tree_map(lambda m, g: b1 * m + (1 - b1) * g, st["m"], g)
    st["v"] = jax.tree_util.tree_map(lambda v, g: b2 * v + (1 - b2) * g * g, st["v"], g)
    mh = jax.tree_util.tree_map(lambda m: m / (1 - b1 ** st["t"]), st["m"])
    vh = jax.tree_util.tree_map(lambda v: v / (1 - b2 ** st["t"]), st["v"])
    P = jax.tree_util.tree_map(lambda p, m, v: p - lr * m / (jnp.sqrt(v) + eps), P, mh, vh)
    return P, st


def lse_integration(P, R, x, y, ridge=1e-3):
    """Konsekuen panel Integrasi tertutup: beta = (Phi^T Phi + lam I)^-1 Phi^T y."""
    _, (v, e, w, xa) = hanfis_forward(P, R, x)
    N, Rn = w.shape
    Phi = (w[:, :, None] * xa[:, None, :]).reshape(N, -1)          # (N, R*(n_in+1))
    A = Phi.T @ Phi + ridge * jnp.eye(Phi.shape[1])
    beta = jnp.linalg.solve(A, Phi.T @ y)
    P = dict(P); P["I"] = dict(P["I"]); P["I"]["cons"] = beta.reshape(Rn, -1)
    return P


def train(P, R, xtr, ytr, xva, yva, epochs=300, lr=1e-2, patience=40, hybrid=True):
    def loss_fn(P, x, y):
        r, _ = hanfis_forward(P, R, x)
        return jnp.mean((r - y) ** 2)
    grad = jax.jit(jax.value_and_grad(loss_fn))
    val = jax.jit(loss_fn)
    lse = jax.jit(lambda P, x, y: lse_integration(P, R, x, y))
    st = adam_init(P); best = (np.inf, P, 0); stale = 0; hist = []
    for ep in range(epochs):
        if hybrid:
            P = lse(P, xtr, ytr)
        l, g = grad(P, xtr, ytr)
        if hybrid:  # konsekuen Integrasi sudah optimal tertutup; gradien hanya untuk yang lain
            g = dict(g); g["I"] = dict(g["I"]); g["I"]["cons"] = jnp.zeros_like(g["I"]["cons"])
        P, st = adam_step(P, g, st, lr)
        lv = float(val(P, xva, yva)); hist.append((float(l), lv))
        if lv < best[0] - 1e-8:
            best = (lv, P, ep + 1); stale = 0
        else:
            stale += 1
            if stale >= patience:
                break
    return best[1], {"best_val": best[0], "best_epoch": best[2], "epochs_run": len(hist)}


def metrics(y, p):
    y = y * 100; p = p * 100
    rmse = float(np.sqrt(np.mean((y - p) ** 2))); mae = float(np.mean(np.abs(y - p)))
    r2 = float(1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2))
    return {"rmse": rmse, "mae": mae, "r2": r2}


# ----------------------------------------------------------------- configs
def build(key, config):
    k1, k2, k3 = jax.random.split(key, 3)
    if config == "flat128":
        P, R = init_panel(k1, 7, [2] * 7)
        return {"F": P}, {"F": R}
    mI = {"C24": [2, 2, 2], "C34": [3, 3, 2], "C54": [3, 3, 3]}[config]
    PV, RV = init_panel(k1, 3, [2, 2, 2]); PE, RE = init_panel(k2, 3, [2, 2, 2]); PI, RI = init_panel(k3, 3, mI)
    return {"V": PV, "E": PE, "I": PI}, {"V": RV, "E": RE, "I": RI}


def lse_single(P, R, x, y, ridge=1e-3):
    _, w, xa = panel_forward(P, R, x)
    N, Rn = w.shape
    Phi = (w[:, :, None] * xa[:, None, :]).reshape(N, -1)
    beta = jnp.linalg.solve(Phi.T @ Phi + ridge * jnp.eye(Phi.shape[1]), Phi.T @ y)
    P = dict(P); P["cons"] = beta.reshape(Rn, -1); return P


def train_single(P, R, xtr, ytr, xva, yva, epochs, lr, patience, hybrid):
    """Latih satu panel ANFIS terhadap targetnya sendiri (untuk flat dan stacking)."""
    def fwd(P, x):
        r, _, _ = panel_forward(P, R, x); return jnp.clip(r, 0, 1)
    def loss_fn(P, x, y): return jnp.mean((fwd(P, x) - y) ** 2)
    grad = jax.jit(jax.value_and_grad(loss_fn)); val = jax.jit(loss_fn); lse = jax.jit(lambda P, x, y: lse_single(P, R, x, y))
    st = adam_init(P); best = (np.inf, P, 0); stale = 0
    for ep in range(epochs):
        if hybrid: P = lse(P, xtr, ytr)
        l, g = grad(P, xtr, ytr)
        if hybrid: g = dict(g); g["cons"] = jnp.zeros_like(g["cons"])
        P, st = adam_step(P, g, st, lr)
        lv = float(val(P, xva, yva))
        if lv < best[0] - 1e-8: best = (lv, P, ep + 1); stale = 0
        else:
            stale += 1
            if stale >= patience: break
    return best[1], {"best_epoch": best[2]}


def run_stacked(key, f, tr, va, te, epochs, lr, patience, n_splits=5):
    """Metode repositori: panel bawah dilatih terhadap target antara dengan OOF, Integrasi terhadap y (Adam)."""
    from sklearn.model_selection import KFold
    k1, k2, k3 = jax.random.split(key, 3)
    X = f[FEATURES].to_numpy(np.float32); Y = f["dynamic_risk_target"].to_numpy(np.float32)
    preds = {}
    for name, cols, tcol, kk in [("V", slice(0, 3), "vulnerability_target", k1), ("E", slice(3, 6), "environment_target", k2)]:
        x = X[:, cols]; t = f[tcol].to_numpy(np.float32); P, R = init_panel(kk, 3, [2, 2, 2])
        pred = np.full(len(f), np.nan, np.float32)
        for fit_i, hold_i in KFold(n_splits, shuffle=True, random_state=20260721).split(tr):
            fit, hold = tr[fit_i], tr[hold_i]; iv = max(1, int(0.15 * len(fit)))
            Pf, _ = train_single(P, R, jnp.asarray(x[fit[:-iv]]), jnp.asarray(t[fit[:-iv]]), jnp.asarray(x[fit[-iv:]]), jnp.asarray(t[fit[-iv:]]), epochs, lr, patience, False)
            pred[hold] = np.asarray(jnp.clip(panel_forward(Pf, R, jnp.asarray(x[hold]))[0], 0, 1))
        Pfull, _ = train_single(P, R, jnp.asarray(x[tr]), jnp.asarray(t[tr]), jnp.asarray(x[va]), jnp.asarray(t[va]), epochs, lr, patience, False)
        for idx in (va, te): pred[idx] = np.asarray(jnp.clip(panel_forward(Pfull, R, jnp.asarray(x[idx]))[0], 0, 1))
        preds[name] = pred
    xi = np.column_stack([preds["V"], preds["E"], X[:, 6]]).astype(np.float32)
    PI, RI = init_panel(k3, 3, [2, 2, 2])
    PI, info = train_single(PI, RI, jnp.asarray(xi[tr]), jnp.asarray(Y[tr]), jnp.asarray(xi[va]), jnp.asarray(Y[va]), epochs, lr, patience, False)
    pred_te = np.asarray(jnp.clip(panel_forward(PI, RI, jnp.asarray(xi[te]))[0], 0, 1))
    return pred_te, info, 132


def run_flat(P, R, xtr, ytr, xva, yva, xte, epochs, lr, patience, hybrid=False):
    Pf, info = train_single(P["F"], R["F"], xtr, ytr, xva, yva, epochs, lr, patience, hybrid)
    return np.asarray(jnp.clip(panel_forward(Pf, R["F"], xte)[0], 0, 1)), info


def _unused(P, R, xtr, ytr, xva, yva, xte, epochs, lr, patience):
    def fwd(P, x):
        r, _, _ = panel_forward(P["F"], R["F"], x); return jnp.clip(r, 0, 1)
    def loss_fn(P, x, y): return jnp.mean((fwd(P, x) - y) ** 2)
    grad = jax.jit(jax.value_and_grad(loss_fn)); val = jax.jit(loss_fn)
    st = adam_init(P); best = (np.inf, P, 0); stale = 0
    for ep in range(epochs):
        l, g = grad(P, xtr, ytr); P, st = adam_step(P, g, st, lr)
        lv = float(val(P, xva, yva))
        if lv < best[0] - 1e-8: best = (lv, P, ep + 1); stale = 0
        else:
            stale += 1
            if stale >= patience: break
    P = best[1]
    return np.asarray(fwd(P, xte)), {"best_epoch": best[2]}


def main(out_dir="results_eint"):
    import os; os.makedirs(out_dir, exist_ok=True)
    rows = []
    scenarios = {"S1_repo_smooth": synthetic_repo, "S2_threshold": synthetic_threshold}
    seeds = [20260721, 1, 2, 3, 4]
    for sname, gen in scenarios.items():
        for seed in seeds:
            f = gen(900, seed)
            tr, va, te = split_indices(len(f), seed)
            X = jnp.asarray(f[FEATURES].to_numpy(np.float32)); Y = jnp.asarray(f["dynamic_risk_target"].to_numpy(np.float32))
            EPOCHS, LR, PAT = 600, 1e-2, 60
            for config in ["C24", "C34", "C54", "flat128", "stacked24"]:
                opts = ["hybrid", "adam"] if config in ("C24", "C34", "C54", "flat128") else ["adam_oof"]
                for opt in opts:
                    key = jax.random.PRNGKey(seed)
                    t0 = time.time()
                    if config == "stacked24":
                        pred, info, npar = run_stacked(key, f, tr, va, te, EPOCHS, LR, PAT); rules = 24
                    else:
                        P, R = build(key, config); npar = n_params(P)
                        if config == "flat128":
                            pred, info = run_flat(P, R, X[tr], Y[tr], X[va], Y[va], X[te], EPOCHS, LR, PAT, hybrid=(opt == "hybrid")); rules = 128
                        else:
                            P, info = train(P, R, X[tr], Y[tr], X[va], Y[va], epochs=EPOCHS, lr=LR, patience=PAT, hybrid=(opt == "hybrid"))
                            pred = np.asarray(hanfis_forward(P, R, X[te])[0]); rules = sum(int(R[k].shape[0]) for k in R)
                    dt = time.time() - t0
                    m = metrics(np.asarray(Y[te]), pred)
                    rows.append({"scenario": sname, "seed": seed, "config": config, "optimizer": opt, "rules": rules,
                                 "params": npar, **m, "best_epoch": info["best_epoch"], "train_s": round(dt, 2)})
                    print(f"{sname} seed={seed} {config:9s} {opt:8s} rules={rules:4d} params={npar:5d} RMSE={m['rmse']:.3f} R2={m['r2']:.4f} ep={info['best_epoch']} t={dt:.1f}s", flush=True)
    df = pd.DataFrame(rows); df.to_csv(f"{out_dir}/eint_raw.csv", index=False)
    agg = df.groupby(["scenario", "config", "optimizer"]).agg(rules=("rules", "first"), params=("params", "first"),
        rmse_mean=("rmse", "mean"), rmse_sd=("rmse", "std"), rmse_median=("rmse", "median"), rmse_max=("rmse", "max"), mae_mean=("mae", "mean"), r2_mean=("r2", "mean"), r2_sd=("r2", "std"),
        epoch_mean=("best_epoch", "mean"), train_s=("train_s", "mean")).reset_index()
    agg.to_csv(f"{out_dir}/eint_summary.csv", index=False)
    print(agg.to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results_eint")
