# Reference implementations and results

`exp_integration_mf_jax.py` is the JAX (CPU) reference used on 2026-09-22 to run
E-INT before the PyTorch port. `eint_results/` holds the raw and summarised
results (synthetic data S1/S2, 5 seeds, 600 epochs). Synthetic data validates
the code path only; the numbers are not scientific claims.

Run (requires `pip install jax jaxlib`): `python reference/exp_integration_mf_jax.py results_eint`

## 2026-09-22 (later): WSL/PyTorch replication and patch 0003 ablation

- `eint_results/eint_*_wsl_torch_2026-09-22.csv`: E-INT replicated on the team's WSL machine with the
  PyTorch port (patch 0002). Same pattern as JAX: hybrid >> adam; C34 median <= C24 in 9/10 seeds;
  flat128 hybrid ill-posed (1,024 consequents vs 630 rows).
- `eint_results/p0003_check.csv`: JAX check of a *bundled* stability package (soft range + quantile
  init + premise lr 3e-3) — did not improve on average; the bundle is therefore NOT the default.
- Ablation on the failing seed (C34, S2, seed 4; baseline RMSE 3.53 @ epoch 152):
  restart with a fresh initialisation 0.12 / 0.27; soft range only 1.83; premise lr only 1.99;
  quantile init only 3.48. Remedy adopted: pre-registered restarts (best of 3 on validation loss).

## 2026-09-22 (evening): patch 0003 verified on WSL/PyTorch — training configuration frozen (A-09)

`eint_results/eint_p3_*`: with best-of-3 pre-registered restarts and patience 100 / min 200 epochs,
every hybrid seed converged (max RMSE 0.116 S1, 0.169 S2 on the 0-100 scale; criterion "< 1.0" met).
C24 vs C34 vs C54 hybrid are statistically indistinguishable on synthetic data (S1 0.090/0.093/0.077;
S2 0.117/0.117/0.126). A non-zero restart index was selected in 18 of 30 HANFIS runs, confirming that
initialisation basins, not capacity, caused the earlier failures. Frozen for E4: hybrid LSE + Adam,
3 restarts, patience 100, min_epochs 200, lr 1e-2, ridge 1e-3 (A-09).

## 2026-09-22 (night): E1 ablation and the monotone-consequent fix

E1 (C34, hybrid, 3 restarts, 5 seeds) on WSL/PyTorch:

| mf_family | monotone | params | S1 median | S2 median | monotonicity violations |
|---|---|---|---|---|---|
| gauss   | off | 176 | 0.099 | 0.137 | 0.4% |
| gauss   | on  | 176 | 0.353 | 5.677 | 0.3% |
| ruspini | off | 147 | 0.020 | 0.631 | 0.6% |
| ruspini | on  | 147 | 0.052 | 1.907 | 0.9% |

The monotone penalty was an artefact of the crude projection in solve_consequents: slopes were
clamped to >= 0 while the intercepts kept their unconstrained values. Patch 0009 refits the
intercepts with the slopes held fixed (a second well-posed least-squares problem). JAX check
(3 seeds): S1 0.103 / 0.567 / 0.157 and S2 0.186 / 5.473 / 0.282 for mono=off / projection only /
projection + intercept refit. Ruspini wins on S1 (fewer parameters, lower error) but loses on S2,
where sharp sigmoid gates favour the smoother Gaussian overlap; the E1 decision is therefore
re-run after patch 0009 before E4 is configured.
