"""Verify subtractive clustering (Chiu 1994) parameter-matching math in pure NumPy before
writing the torch FlatANFISMatched class. FlatANFISMatched is NOT a grid-partition ANFIS
(that would need m^7 rules): subtractive clustering finds R cluster centers directly in the
7-D input space, each center becomes one rule with its OWN per-dimension Gaussian (not shared
across rules), so params = R * (2*7 premise + 8 consequent) = 22R. To match HANFIS's 176
params within +/-5% (167-185), R must be 8 (22*8=176 exactly).
"""
import numpy as np

def subtractive_clustering(X, ra, rb=None, accept_ratio=0.5, reject_ratio=0.15, max_clusters=30):
    """Chiu's subtractive clustering. X: (N, d) in [0,1]^d. Returns cluster centers (R, d)."""
    rb = rb if rb is not None else ra * 1.5
    alpha = 4.0 / ra**2
    beta = 4.0 / rb**2
    N = X.shape[0]
    D2 = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1)
    P = np.exp(-alpha * D2).sum(1)
    centers = []
    first_potential = None
    Xw = X.copy(); Pw = P.copy()
    while len(centers) < max_clusters:
        k = np.argmax(Pw)
        pk = Pw[k]
        if first_potential is None:
            first_potential = pk
        if pk <= reject_ratio * first_potential:
            break
        if pk >= accept_ratio * first_potential:
            centers.append(Xw[k].copy())
        else:
            # distance test (simplified accept): accept if far enough from existing centers
            if centers:
                dmin = min(np.linalg.norm(Xw[k] - c) for c in centers)
                if dmin / ra + pk / first_potential < 1.0:
                    Pw[k] = -1  # reject and continue searching
                    continue
            centers.append(Xw[k].copy())
        d2 = ((X - Xw[k]) ** 2).sum(-1)
        P = P - pk * np.exp(-beta * d2)
        Pw = P.copy()
        Pw[[i for i, c in enumerate(X) if any(np.allclose(c, cc) for cc in centers)]] = -1
    return np.array(centers)


def find_radius_for_target_rules(X, target_r, ra_grid=None, tol_pct=0.05, params_per_rule=22, target_params=176):
    """Search ra so the resulting rule count R satisfies |22R - 176| <= 5%*176."""
    ra_grid = ra_grid if ra_grid is not None else np.linspace(0.15, 0.9, 60)
    lo, hi = target_params * (1 - tol_pct), target_params * (1 + tol_pct)
    hits = []
    for ra in ra_grid:
        R = len(subtractive_clustering(X, ra))
        if R == 0:
            continue
        params = params_per_rule * R
        if lo <= params <= hi:
            hits.append((ra, R, params))
    return hits


rng = np.random.default_rng(20260928)
X = rng.random((400, 7))  # stand-in for the 7 normalised HANFIS inputs
hits = find_radius_for_target_rules(X, target_r=8)
print("ra values landing within +/-5% of 176 params:", hits[:10], "...", f"({len(hits)} total)")
assert hits, "no radius found 8 clusters -- grid needs widening"
ra_star, R_star, params_star = hits[len(hits) // 2]
print(f"chosen ra={ra_star:.4f} -> R={R_star} rules -> {params_star} params "
      f"(HANFIS=176, diff={100*(params_star-176)/176:+.2f}%)")

# sanity: does the SAME ra generalise across different random draws of X (different folds)?
for seed in (1, 2, 3, 4, 5):
    Xf = np.random.default_rng(seed).random((300, 7))
    Rf = len(subtractive_clustering(Xf, ra_star))
    print(f"seed {seed}: R={Rf}, params={22*Rf} ({'OK' if abs(22*Rf-176) <= 0.05*176 else 'OUT OF BAND'})")

print("\n--- per-dataset radius search (the real approach: search ra freshly for EACH fold) ---")
def search_ra_for_dataset(X, target_params=176, tol_pct=0.05, params_per_rule=22, max_iter=40):
    """Bisection-ish search: shrinking ra -> more clusters (more rules); growing ra -> fewer.
    Returns (ra, R, params) within tolerance, or the CLOSEST found after max_iter if none hits
    exactly (never silently returns something wildly off -- caller checks the tolerance itself)."""
    lo, hi = target_params * (1 - tol_pct), target_params * (1 + tol_pct)
    best = None
    ra_lo, ra_hi = 0.05, 1.5
    for _ in range(max_iter):
        ra_mid = (ra_lo + ra_hi) / 2
        R = len(subtractive_clustering(X, ra_mid))
        params = params_per_rule * R
        if best is None or abs(params - target_params) < abs(best[2] - target_params):
            best = (ra_mid, R, params)
        if lo <= params <= hi:
            return ra_mid, R, params, True
        if params > target_params:   # too many rules -> need FEWER -> increase ra
            ra_lo = ra_mid
        else:                        # too few rules -> need MORE -> decrease ra
            ra_hi = ra_mid
    return (*best, False)

ok = 0
for seed in (1, 2, 3, 4, 5, 6, 7, 8):
    Xf = np.random.default_rng(seed).random((300, 7))
    ra, R, params, hit = search_ra_for_dataset(Xf)
    status = "OK" if hit else f"CLOSEST (diff {100*(params-176)/176:+.1f}%)"
    print(f"seed {seed}: ra={ra:.4f} R={R} params={params}  {status}")
    ok += hit
print(f"\n{ok}/8 datasets hit the +/-5% band via per-dataset search")
