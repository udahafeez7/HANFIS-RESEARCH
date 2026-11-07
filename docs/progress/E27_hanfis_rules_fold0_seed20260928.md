# Trained HANFIS rules: fold 0, seed 20260928 (E4-bis, 120 assets)

Descriptive documentation of one pre-specified saved model (`results_python/e4bis_120_models/models/fold0_seed20260928_hanfis.pt`). Reconstruction checked against the model's forward pass on 1,000 fixed rows (max abs difference: V 0.0e+00, E 0.0e+00, I 0.0e+00). Membership functions are named by index (MF1, MF2, MF3), not by linguistic labels, because the centres are free parameters. Gaussian membership functions mu(z) = exp(-0.5 ((z - c) / s)^2), normalised Sugeno firing, consequent f = b0 + sum b_i z_i with softplus slopes (A-04). Inputs z are in normalised units; for the raw inputs raw = shift + scale * z (x1 CVSS: 0 to 10; x3 Patch Risk: 0 to 2; x6 Asset Criticality: 1 to 5). v and e are the clipped panel outputs.

## Panel V: 8 rules, 12 premise and 32 consequent parameters

Membership functions (centre c, width s; raw-unit centre in brackets where an input has a raw scale):

- x1 CVSS: MF1: c=0.153, s=0.174 [raw 1.53]; MF2: c=0.546, s=0.454 [raw 5.46]
- x2 Exploitability: MF1: c=0.682, s=0.176 [raw 0.682]; MF2: c=0.282, s=0.385 [raw 0.282]
- x3 Patch Risk: MF1: c=-0.099, s=0.176 [raw -0.198]; MF2: c=0.371, s=0.468 [raw 0.743]

Ordering check (do the centres keep the order of the membership-function index?): x1: centres in index order [0.153, 0.546] -> increasing; x2: centres in index order [0.682, 0.282] -> NOT increasing; x3: centres in index order [-0.099, 0.371] -> increasing.

| Rule | IF | b0 | b(x1) | b(x2) | b(x3) |
|---|---|---|---|---|---|
| 1 | x1 is MF1 AND x2 is MF1 AND x3 is MF1 | +0.001 | 0.000 | 0.000 | 0.000 |
| 2 | x1 is MF1 AND x2 is MF1 AND x3 is MF2 | +0.001 | 0.000 | 0.000 | 0.000 |
| 3 | x1 is MF1 AND x2 is MF2 AND x3 is MF1 | +0.839 | 0.000 | 0.000 | 0.000 |
| 4 | x1 is MF1 AND x2 is MF2 AND x3 is MF2 | +0.760 | 0.014 | 0.000 | 0.037 |
| 5 | x1 is MF2 AND x2 is MF1 AND x3 is MF1 | +0.001 | 0.000 | 0.000 | 0.000 |
| 6 | x1 is MF2 AND x2 is MF1 AND x3 is MF2 | +0.044 | 0.037 | 0.003 | 0.036 |
| 7 | x1 is MF2 AND x2 is MF2 AND x3 is MF1 | +0.621 | 0.001 | 0.001 | 0.001 |
| 8 | x1 is MF2 AND x2 is MF2 AND x3 is MF2 | +0.767 | 0.000 | 1.420 | 0.000 |

## Panel E: 8 rules, 12 premise and 32 consequent parameters

Membership functions (centre c, width s; raw-unit centre in brackets where an input has a raw scale):

- x4 MFA Risk: MF1: c=0.631, s=0.390 [raw 0.631]; MF2: c=0.998, s=0.184 [raw 0.998]
- x5 Kubernetes Exposure: MF1: c=0.347, s=0.257 [raw 0.347]; MF2: c=1.072, s=0.174 [raw 1.07]
- x6 Asset Criticality: MF1: c=-0.061, s=0.194 [raw 0.755]; MF2: c=0.593, s=0.284 [raw 3.37]

Ordering check (do the centres keep the order of the membership-function index?): x4: centres in index order [0.631, 0.998] -> increasing; x5: centres in index order [0.347, 1.072] -> increasing; x6: centres in index order [-0.061, 0.593] -> increasing.

| Rule | IF | b0 | b(x4) | b(x5) | b(x6) |
|---|---|---|---|---|---|
| 1 | x4 is MF1 AND x5 is MF1 AND x6 is MF1 | +0.086 | 0.000 | 0.025 | 0.000 |
| 2 | x4 is MF1 AND x5 is MF1 AND x6 is MF2 | +0.078 | 0.172 | 0.000 | 0.000 |
| 3 | x4 is MF1 AND x5 is MF2 AND x6 is MF1 | +0.085 | 0.024 | 0.060 | 0.000 |
| 4 | x4 is MF1 AND x5 is MF2 AND x6 is MF2 | -0.030 | 0.004 | 0.000 | 0.084 |
| 5 | x4 is MF2 AND x5 is MF1 AND x6 is MF1 | -0.002 | 0.030 | 0.000 | 0.005 |
| 6 | x4 is MF2 AND x5 is MF1 AND x6 is MF2 | +0.019 | 0.000 | 0.000 | 0.000 |
| 7 | x4 is MF2 AND x5 is MF2 AND x6 is MF1 | +0.057 | 0.040 | 0.040 | 0.011 |
| 8 | x4 is MF2 AND x5 is MF2 AND x6 is MF2 | -0.005 | 0.000 | 0.000 | 0.000 |

## Panel I: 18 rules, 16 premise and 72 consequent parameters

Membership functions (centre c, width s; raw-unit centre in brackets where an input has a raw scale):

- v: MF1: c=0.352, s=0.379; MF2: c=0.677, s=0.315; MF3: c=0.659, s=0.252
- e: MF1: c=0.317, s=0.244; MF2: c=0.297, s=0.328; MF3: c=0.484, s=0.362
- x7 Threat Intelligence: MF1: c=0.218, s=0.280 [raw 0.218]; MF2: c=0.605, s=0.296 [raw 0.605]

Ordering check (do the centres keep the order of the membership-function index?): v: centres in index order [0.352, 0.677, 0.659] -> NOT increasing; e: centres in index order [0.317, 0.297, 0.484] -> NOT increasing; x7: centres in index order [0.218, 0.605] -> increasing.

| Rule | IF | b0 | b(v) | b(e) | b(x7) |
|---|---|---|---|---|---|
| 1 | v is MF1 AND e is MF1 AND x7 is MF1 | -0.529 | 0.000 | 0.000 | 0.004 |
| 2 | v is MF1 AND e is MF1 AND x7 is MF2 | -0.002 | 0.008 | 0.000 | 0.084 |
| 3 | v is MF1 AND e is MF2 AND x7 is MF1 | -0.665 | 0.000 | 0.000 | 0.005 |
| 4 | v is MF1 AND e is MF2 AND x7 is MF2 | -0.002 | 0.005 | 0.000 | 0.109 |
| 5 | v is MF1 AND e is MF3 AND x7 is MF1 | -0.455 | 0.000 | 0.000 | 0.004 |
| 6 | v is MF1 AND e is MF3 AND x7 is MF2 | -0.002 | 0.005 | 0.000 | 0.072 |
| 7 | v is MF2 AND e is MF1 AND x7 is MF1 | +0.136 | 0.758 | 0.074 | 0.000 |
| 8 | v is MF2 AND e is MF1 AND x7 is MF2 | +0.027 | 0.030 | 0.008 | 0.000 |
| 9 | v is MF2 AND e is MF2 AND x7 is MF1 | +0.080 | 0.808 | 0.080 | 0.000 |
| 10 | v is MF2 AND e is MF2 AND x7 is MF2 | +0.022 | 0.020 | 0.010 | 0.006 |
| 11 | v is MF2 AND e is MF3 AND x7 is MF1 | +0.092 | 0.613 | 0.061 | 0.000 |
| 12 | v is MF2 AND e is MF3 AND x7 is MF2 | +0.019 | 0.020 | 0.007 | 0.000 |
| 13 | v is MF3 AND e is MF1 AND x7 is MF1 | -0.457 | 0.217 | 0.000 | 0.005 |
| 14 | v is MF3 AND e is MF1 AND x7 is MF2 | +0.030 | 0.037 | 0.005 | 0.103 |
| 15 | v is MF3 AND e is MF2 AND x7 is MF1 | -0.623 | 0.166 | 0.000 | 0.007 |
| 16 | v is MF3 AND e is MF2 AND x7 is MF2 | +0.032 | 0.035 | 0.007 | 0.135 |
| 17 | v is MF3 AND e is MF3 AND x7 is MF1 | -0.406 | 0.158 | 0.000 | 0.004 |
| 18 | v is MF3 AND e is MF3 AND x7 is MF2 | +0.023 | 0.028 | 0.005 | 0.089 |

---
Generated by scripts/e27_rules_and_surface.py with AI assistance (Claude, Anthropic); no training, no data selection.