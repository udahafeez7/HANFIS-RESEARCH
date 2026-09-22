# Reference implementations and results

`exp_integration_mf_jax.py` is the JAX (CPU) reference used on 2026-09-22 to run
E-INT before the PyTorch port. `eint_results/` holds the raw and summarised
results (synthetic data S1/S2, 5 seeds, 600 epochs). Synthetic data validates
the code path only; the numbers are not scientific claims.

Run (requires `pip install jax jaxlib`): `python reference/exp_integration_mf_jax.py results_eint`
