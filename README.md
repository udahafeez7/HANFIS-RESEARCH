# HANFIS-RESEARCH

Hierarchical adaptive neuro-fuzzy (HANFIS) risk scoring for Kubernetes container deployments. This repository holds the research code, the frozen evaluation protocols, the data-building pipeline and the manuscript sources.

**Status:** research code under active development; private repository; no reuse license yet (see [License](#license-and-citation)).

## What this is

The project asks whether a small, interpretable neuro-fuzzy model can score the near-term exploitation exposure of a container image from seven normalized inputs, and how it compares with simple baselines under a strict temporal evaluation. The acronym HANFIS has been used in earlier work by others; here it only names this repository's hierarchical, three-panel Sugeno ANFIS for risk scoring.

Two results shape how the work is framed. A four-parameter formula of two inputs (exploitability and the KEV indicator) is a strong baseline, and HANFIS does not demonstrably exceed it. The manuscript reports this directly instead of treating it as a side note.

## The model

Seven inputs, all normalized to [0, 1] and oriented so that a higher value means higher risk. A missing value is a distinct "unknown" state, not zero.

| Input | Meaning |
|---|---|
| x1 | CVSS (maximum over affected, reachable CVEs) |
| x2 | Exploitability: EPSS times a runtime-reachability factor |
| x3 | Patch risk |
| x4 | MFA risk (per-asset constant) |
| x5 | Kubernetes exposure (per-asset constant) |
| x6 | Asset criticality (per-asset constant) |
| x7 | Threat intelligence (CISA KEV indicator at time t) |

Three first-order Sugeno panels are trained end to end: V(x1, x2, x3) gives v, E(x4, x5, x6) gives e, and I(v, e, x7) gives the final score r, clipped to [0, 1]. The scalar between the panels (the bottleneck) can be widened in a sweep, which gives an accuracy-versus-complexity curve.

## Data and label

- Weekly EPSS score archives and CISA KEV catalog snapshots, sealed with a manifest of SHA-256 hashes.
- Trivy scans of 120 digest-pinned container images; the unit of observation is the image-week.
- Label y(a, t) on a 0 to 100 scale: the mean, over the weekly snapshots in the four weeks after t, of the maximum over active CVEs of X_v times rho_v, where X_v = max(EPSS, KEV indicator) and rho_v is a runtime-reachability factor.

`data/` and `results_python/` are git-ignored by default. Selected evidence bundles, manifests and result files are force-added, so the tracked part is a subset. Everything else is rebuilt with the scripts in `scripts/` (snapshot fetching, image scanning, asset-week table).

## Evaluation design

- Folds grouped by image and blocked in time, with an embargo of at least 30 days between training and test weeks.
- Baselines: persistence (the label of the same image four weeks earlier), climatology, single CVSS, a ridge model on the seven inputs, a flat ANFIS, a parameter-matched flat ANFIS, and Fuzzyfortify.
- Skill score against a reference, MSE-based, with 95% intervals from a bootstrap clustered by image.
- Confirmatory and exploratory analyses are kept apart. Analyses run after a freeze are labelled post hoc.

## Pre-registered forward evaluation (E7)

- Protocol: `protocols/E7_preregistration_2026-10-12.md`; git tag `e7-prereg-2026-10-12` (commit `dbed812`).
- `protocols/E7_freeze_record_2026-10-12.txt` lists the SHA-256 hashes of the 23 frozen files as stored in the tag.
- Data date D2 = 2026-11-02. The pipeline `scripts/e7_d2.py` runs once and refuses reruns.
- OSF registration: https://osf.io/ahcvs/ (DOI [10.17605/OSF.IO/AHCVS](https://doi.org/10.17605/OSF.IO/AHCVS)), public, registered 2026-10-13.

Do not run `scripts/e7_d2.py` before D2. Do not edit any frozen file; changes go through numbered amendments.

## Repository layout

| Path | Contents |
|---|---|
| `python_hanfis/` | Model, training, splits |
| `scripts/` | Data pipeline, experiments (E0 to E21), E7 pipeline, helpers |
| `protocols/` | Frozen protocols, fitted constants, freeze records |
| `configs/` | Asset inventory and run configurations |
| `manuscript/` | LaTeX sources (Springer Nature template), bibliography, figures |
| `kubernetes/` | Testbed deployment manifests |
| `Jetson Orin/` | Telemetry protocol and collector code for the testbed |
| `test/`, `tests/` | Test suites |
| `data/`, `results_python/` | Ignored by default; selected evidence, manifests and results are tracked |
| `HANFIS_RESEARCH_MEMORY.md` | Frozen decisions, amendments (A-xx) and blockers (F-x) |
| `reference/`, `experiments/`, `schemas/`, `telemetry/`, `docs/` | <!-- TODO: one line each --> |

## Setup and tests

Developed on Windows 11 with WSL2 (Ubuntu), Python 3.12 in a virtual environment.

```bash
python3 -m venv ~/.venvs/anfis
source ~/.venvs/anfis/bin/activate
pip install -r requirements.txt
```

`requirements-lock.txt` holds the pinned versions used for the reported runs. Then, from the repository root:

```bash
python -m pytest -q test tests
```

Use exactly these arguments. A bare `pytest` also collects duplicate modules under `Jetson Orin/` and reports collection errors that are not code failures.

## Working rules

- Decisions are recorded as numbered amendments (A-xx) and blockers as F-x in `HANFIS_RESEARCH_MEMORY.md`.
- Every change is one numbered commit, applied with `git am -3` and verified with the full test suite.
- Scripts that read forward data verify the freeze tag before running.
- Null results, confounds and data inconsistencies are written down, not dropped.

## People and funding

Mohammad Hafiz Hersyah, Dr. Derisma M.T., Dr. Eng Budi Rahmadya, Universitas Andalas. Funded by the Penelitian Kepakaran scheme of LPPM Universitas Andalas, 2026.

## License and citation

<!-- TODO: choose a code license and decide what applies to data and derived artifacts before the repository is made public -->

An archived copy with a DOI is planned. Until it exists, please do not cite this repository; cite the manuscript once it is available.
