"""Verify the closed-form alternating-lower-panel derivation generalises from scalar v,e (E2,
patch 0035) to vector v,e in R^k (needed to de-confound E5). Derivation:

Given Integration's frozen firing weights w_I and consequents beta_I (per rule m: intercept +
k slopes on v + k slopes on e + 1 slope on x7), the output is
  r_n = A_n + sum_i B_{n,i} v_{n,i} + sum_j C_{n,j} e_{n,j}
with A_n, B_{n,i}, C_{n,j} aggregated (over m) from w_I and beta_I -- purely data, not unknowns.

v_{n,i} is itself affine in V-panel's own (frozen-firing-weight) consequents beta_V[p, d, i], so
r is linear in the FLATTENED beta_V, beta_E given this iteration's firing weights: one joint
ridge LSE solves both panels' full consequent tensors at once, generalising the k=1 case exactly.
"""
import numpy as np

rng = np.random.default_rng(20260928)

def gauss_fire(X, centers, sigmas, rule_idx):
    mus = [np.exp(-0.5*((X[:,i:i+1]-centers[i][None,:])/sigmas[i][None,:])**2) for i in range(X.shape[1])]
    w = np.ones((X.shape[0], rule_idx.shape[0]))
    for i in range(X.shape[1]):
        w *= mus[i][:, rule_idx[:, i]]
    return w / w.sum(1, keepdims=True).clip(1e-12)

import itertools
def make_rules(m_per_input):
    return np.array(list(itertools.product(*[range(m) for m in m_per_input])))

def ridge_solve(phi, y, lam):
    return np.linalg.solve(phi.T @ phi + lam*np.eye(phi.shape[1]), phi.T @ y)

def run_case(k, N=500, outer_iters=8, lam=1e-3, seed=0):
    r = np.random.default_rng(seed)
    X = r.random((N, 7))
    # ground truth target, k-independent (just for a converging sanity check)
    y = 0.3 + 0.4*X[:,:3].mean(1) + 0.5*X[:,3:6].mean(1) + 0.2*X[:,6] + r.normal(0,0.01,N)
    y = np.clip(y, 0, 1)

    mV = [2,2,2]; mE = [2,2,2]; mI = [3]*(2*k) + [2]
    cV = [np.linspace(0.25,0.75,m) for m in mV]; sV=[np.full(m,0.25) for m in mV]; rV = make_rules(mV)
    cE = [np.linspace(0.25,0.75,m) for m in mE]; sE=[np.full(m,0.25) for m in mE]; rE = make_rules(mE)
    cI = [np.linspace(0.25,0.75,m) for m in mI]; sI=[np.full(m,0.25) for m in mI]; rI = make_rules(mI)
    R_V, R_E, R_I = len(rV), len(rE), len(rI)
    betaV = r.normal(0,0.1,(R_V,4,k)); betaE = r.normal(0,0.1,(R_E,4,k)); betaI = r.normal(0,0.1,(R_I, 2*k+2))

    def forward():
        wV = gauss_fire(X[:,0:3], cV, sV, rV)
        wE = gauss_fire(X[:,3:6], cE, sE, rE)
        xaV = np.c_[np.ones(N), X[:,0:3]]; xaE = np.c_[np.ones(N), X[:,3:6]]
        v = np.einsum("np,pdi,nd->ni", wV, betaV, xaV)   # (N,k)
        e = np.einsum("nq,qdj,nd->nj", wE, betaE, xaE)   # (N,k)
        v, e = np.clip(v,0,1), np.clip(e,0,1)
        xi = np.concatenate([v, e, X[:,6:7]], axis=1)
        wI = gauss_fire(xi, cI, sI, rI)
        xaI = np.c_[np.ones(N), xi]
        rpred = (wI * (xaI @ betaI.T)).sum(1)
        return rpred, v, e, wV, wE, wI

    mses = []
    for it in range(outer_iters):
        rpred, v, e, wV, wE, wI = forward()
        mses.append(float(np.mean((rpred-y)**2)))

        # step 1: solve Integration consequents given current v,e (standard, k-agnostic)
        xi = np.concatenate([v, e, X[:,6:7]], axis=1)
        xaI = np.c_[np.ones(N), xi]
        phiI = (wI[:,:,None]*xaI[:,None,:]).reshape(N,-1)
        betaI = ridge_solve(phiI, y, lam).reshape(R_I, -1)

        # step 2: alternating closed-form for BOTH vector-valued lower panels
        A = (wI * (betaI[:,0] + betaI[:,-1]*X[:,6][:,None])).sum(1)          # (N,)
        B = wI @ betaI[:, 1:1+k]        # (N,k)  coefficients on v_i
        C = wI @ betaI[:, 1+k:1+2*k]    # (N,k)  coefficients on e_j
        xaV = np.c_[np.ones(N), X[:,0:3]]; xaE = np.c_[np.ones(N), X[:,3:6]]
        # Phi_V[n, (p,d,i)] = B[n,i] * wV[n,p] * xaV[n,d]
        phiV = np.einsum("ni,np,nd->npdi", B, wV, xaV).reshape(N, -1)
        phiE = np.einsum("nj,nq,nd->nqdj", C, wE, xaE).reshape(N, -1)
        phi_lower = np.concatenate([phiV, phiE], axis=1)
        target = y - A
        beta_lower = ridge_solve(phi_lower, target, lam)
        betaV = beta_lower[:phiV.shape[1]].reshape(R_V, 4, k)
        betaE = beta_lower[phiV.shape[1]:].reshape(R_E, 4, k)

    rpred, *_ = forward()
    mses.append(float(np.mean((rpred-y)**2)))
    return mses

for k in (1, 2, 3):
    mses = run_case(k)
    print(f"k={k}: MSE {mses[0]:.4f} -> {mses[-1]:.6f}  (over {len(mses)-1} outer iters)")

print("\n--- monotone variant: clamp slopes >=0, refit intercepts only (generalised) ---")
def run_case_monotone(k, N=500, outer_iters=8, lam=1e-3, seed=0):
    r = np.random.default_rng(seed)
    X = r.random((N, 7))
    y = 0.3 + 0.4*X[:,:3].mean(1) + 0.5*X[:,3:6].mean(1) + 0.2*X[:,6] + r.normal(0,0.01,N)
    y = np.clip(y, 0, 1)
    mV=[2,2,2]; mE=[2,2,2]; mI=[3]*(2*k)+[2]
    cV=[np.linspace(.25,.75,m) for m in mV]; sV=[np.full(m,.25) for m in mV]; rV=make_rules(mV)
    cE=[np.linspace(.25,.75,m) for m in mE]; sE=[np.full(m,.25) for m in mE]; rE=make_rules(mE)
    cI=[np.linspace(.25,.75,m) for m in mI]; sI=[np.full(m,.25) for m in mI]; rI=make_rules(mI)
    R_V,R_E,R_I=len(rV),len(rE),len(rI)
    betaV=r.normal(0,0.1,(R_V,4,k)); betaE=r.normal(0,0.1,(R_E,4,k)); betaI=r.normal(0,0.1,(R_I,2*k+2))
    def forward():
        wV=gauss_fire(X[:,0:3],cV,sV,rV); wE=gauss_fire(X[:,3:6],cE,sE,rE)
        xaV=np.c_[np.ones(N),X[:,0:3]]; xaE=np.c_[np.ones(N),X[:,3:6]]
        v=np.clip(np.einsum("np,pdi,nd->ni",wV,betaV,xaV),0,1); e=np.clip(np.einsum("nq,qdj,nd->nj",wE,betaE,xaE),0,1)
        xi=np.concatenate([v,e,X[:,6:7]],1); wI=gauss_fire(xi,cI,sI,rI); xaI=np.c_[np.ones(N),xi]
        return (wI*(xaI@betaI.T)).sum(1), v,e,wV,wE,wI
    mses=[]
    for it in range(outer_iters):
        rpred,v,e,wV,wE,wI=forward(); mses.append(float(np.mean((rpred-y)**2)))
        xi=np.concatenate([v,e,X[:,6:7]],1); xaI=np.c_[np.ones(N),xi]
        phiI=(wI[:,:,None]*xaI[:,None,:]).reshape(N,-1)
        betaI_raw = ridge_solve(phiI, y, lam).reshape(R_I,-1)
        betaI = np.concatenate([betaI_raw[:, :1], np.clip(betaI_raw[:, 1:], 0, None)], axis=1)  # monotone I too
        A=(wI*(betaI[:,0]+betaI[:,-1]*X[:,6][:,None])).sum(1); B=wI@betaI[:,1:1+k]; C=wI@betaI[:,1+k:1+2*k]
        xaV=np.c_[np.ones(N),X[:,0:3]]; xaE=np.c_[np.ones(N),X[:,3:6]]
        phiV=np.einsum("ni,np,nd->npdi",B,wV,xaV).reshape(N,-1); phiE=np.einsum("nj,nq,nd->nqdj",C,wE,xaE).reshape(N,-1)
        phi_lower=np.concatenate([phiV,phiE],1); target=y-A
        beta_unc = ridge_solve(phi_lower, target, lam)
        R_Vp = phiV.shape[1]
        slope_mask = np.ones(phi_lower.shape[1], dtype=bool)
        slope_mask[0:R_Vp:4] = False; slope_mask[R_Vp::4] = False   # crude: intercept columns every 4th (d=0)
        slopes = np.where(slope_mask, np.clip(beta_unc, 0, None), beta_unc)
        # refit intercepts only (phi columns at intercept positions), holding slopes fixed
        resid = target - phi_lower[:, slope_mask] @ np.where(slope_mask, 0, 1)[slope_mask]*0  # placeholder, see below
        # simpler: just use clamped slopes/intercepts jointly re-solved once more for intercepts alone
        phi_int = phi_lower.copy(); phi_int[:, slope_mask] = 0
        resid2 = target - phi_lower[:, slope_mask] @ slopes[slope_mask]
        beta_int_only = ridge_solve(phi_int[:, ~slope_mask], resid2, lam)
        beta_final = slopes.copy(); beta_final[~slope_mask] = beta_int_only
        betaV = beta_final[:R_Vp].reshape(R_V,4,k); betaE = beta_final[R_Vp:].reshape(R_E,4,k)
    rpred,*_ = forward(); mses.append(float(np.mean((rpred-y)**2)))
    return mses

for k in (1,2):
    mses = run_case_monotone(k)
    print(f"k={k} (monotone): MSE {mses[0]:.4f} -> {mses[-1]:.6f}")
