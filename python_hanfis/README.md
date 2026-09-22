# Python HANFIS — Seven Cybersecurity Inputs

This is the Python counterpart of `hanfis_basic_experiment.m`. It implements
first-order Sugeno ANFIS directly in PyTorch so the hierarchy remains explicit,
trainable, reproducible, and suitable for later Jetson Orin Nano inference.

## Architecture

1. Vulnerability ANFIS: CVSS, Exploitability, Patch Risk → Vulnerability Score.
2. Environmental ANFIS: MFA Risk, Kubernetes Exposure, Asset Criticality → Environmental Score.
3. Integration ANFIS: Vulnerability Score, Environmental Score, Threat Intelligence → Dynamic Risk Score.
4. Optional comparator: one flat ANFIS using all seven inputs.

With two membership functions per input, HANFIS has `8 + 8 + 8 = 24` rules,
while the flat seven-input model has `2^7 = 128` rules.

## Run in the existing WSL virtual environment

```bash
cd /home/hafiz/ANFIS
source ~/.venvs/anfis/bin/activate
python -m pip install -r python_hanfis/requirements.txt
python python_hanfis/hanfis_7input_experiment.py
```

Do not create another virtual environment. If the WSL username/project path is
`/home/mhafizhersyah/ANFIS`, use that path but activate the same established
environment if it is accessible.

For a real model-ready telemetry dataset:

```bash
python python_hanfis/hanfis_7input_experiment.py \
  --data Datasets/model_ready/telemetry_7input.csv \
  --output results_python/telemetry_experiment
```

Required normalized columns are `cvss`, `exploitability`, `patch_risk`,
`mfa_risk`, `kubernetes_exposure`, `asset_criticality`, and
`threat_intelligence`. During supervised training, the CSV must also contain
`vulnerability_target`, `environment_target`, and `dynamic_risk_target`.

## Why these libraries

- `torch`: differentiable Gaussian membership functions, Sugeno consequents,
  optimization, model serialization, and future Jetson inference.
- `numpy`: numeric arrays and deterministic data generation.
- `pandas`: telemetry CSV schema, validation, and exported results.
- `scikit-learn`: RMSE, MAE, and R² calculated consistently.
- `matplotlib`: evaluation figure.

The synthetic labels validate the computation pipeline only. Publication-level
claims require real telemetry and independently justified/annotated targets.

## End-to-end HANFIS (amendments A-02, A-06) — `hanfis_end2end.py`

`HANFIS(m_raw=2, m_intermediate=3)` composes three `SugenoPanel`s and is
trained end-to-end on the final risk score only (no intermediate targets):

- `m_intermediate=2` → 24 rules / 132 parameters (historical configuration C24)
- `m_intermediate=3` → 34 rules / 176 parameters (configuration C34, A-02)

Use `fit_hybrid` (closed-form ridge LSE for the Integration consequents +
Adam for premises and lower panels). `fit_adam` is kept only for the E2
comparison; pure gradient training was unstable end-to-end in E-INT
(`reference/eint_results/eint_summary.csv`).

```bash
python experiments/exp_integration_mf.py --output results_python/eint --seeds 5
```
