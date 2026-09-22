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
