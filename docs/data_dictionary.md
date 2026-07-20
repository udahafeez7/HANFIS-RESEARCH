# ANFIS Cybersecurity Data Dictionary

## Model Objective

The model estimates a dynamic cybersecurity risk score using vulnerability,
asset, authentication, orchestration, patching, and threat-intelligence data.

## Variables

| No. | Variable | Role | Proposed Range | Description |
|---:|---|---|---|---|
| 1 | CVSS Score | Input | 0–10 | Technical severity of the vulnerability |
| 2 | Exploitability | Input | 0–10 | Likelihood or ease of exploitation |
| 3 | Asset Criticality | Input | 1–5 | Importance of the affected asset |
| 4 | MFA Status | Input | 0–2 | MFA protection condition |
| 5 | Kubernetes Exposure | Input | 0–10 | Exposure of the Kubernetes workload or service |
| 6 | Patch Status | Input | 0–2 | Availability and application of security patches |
| 7 | Threat Intelligence | Input | 0–10 | Current external threat evidence |
| 8 | Dynamic Risk Score | Output | 0–100 | Predicted cybersecurity risk level |