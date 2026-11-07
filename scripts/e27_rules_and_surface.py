#!/usr/bin/env python
"""E27: documentation of one trained HANFIS (descriptive; protocols/E26_h4_and_documentation_protocol_2026-11-07.md, section 6).

Prints the 34 rules of ONE pre-specified saved model (fold 0, seed 20260928) as a Markdown table, using the model's own accessors
(rule_indices, centers, log_sigmas, effective_consequents). Before writing anything it checks that a reconstruction of each panel's output
from those accessors equals the model's own forward pass on 1,000 fixed rows (max abs difference must be below 1e-5; otherwise the script
aborts and writes nothing). No training, no data selection. Membership centres and widths are reported in normalised units and in raw units
via the shift/scale recorded in the E4-bis meta file.

  python scripts/e27_rules_and_surface.py
"""
from __future__ import annotations

import json, sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "python_hanfis"))
import e4_run as E  # noqa: E402
from hanfis_end2end import HANFIS  # noqa: E402

MODEL = ROOT / "results_python" / "e4bis_120_models" / "models" / "fold0_seed20260928_hanfis.pt"
META = ROOT / "results_python" / "e4bis_120_models" / "meta_20261005T083407Z.json"
OUT = ROOT / "results_python" / "e27"; OUT.mkdir(parents=True, exist_ok=True)
NAMES = {"cvss": "x1 CVSS", "exploitability": "x2 Exploitability", "patch_risk": "x3 Patch Risk", "mfa_risk": "x4 MFA Risk",
         "kubernetes_exposure": "x5 Kubernetes Exposure", "asset_criticality": "x6 Asset Criticality", "threat_intelligence": "x7 Threat Intelligence"}


def panel_reconstruct(panel, x):
    """Panel output rebuilt from the model's accessors (gauss MFs, normalised Sugeno firing, effective consequents)."""
    mu = []
    for r in range(panel.rule_count):
        w = torch.ones(x.shape[0], dtype=x.dtype)
        for i in range(panel.n_inputs):
            j = int(panel.rule_indices[r, i]); c = panel.centers[i][j]; s = torch.exp(panel.log_sigmas[i][j]).clamp_min(1e-3)
            w = w * torch.exp(-0.5 * ((x[:, i] - c) / s) ** 2)
        mu.append(w)
    w = torch.stack(mu, dim=1); w = w / w.sum(dim=1, keepdim=True).clamp_min(1e-12)
    B = panel.effective_consequents().to(x.dtype); xa = torch.cat([torch.ones(x.shape[0], 1, dtype=x.dtype), x], dim=1)
    return (w * (xa @ B.T)).sum(dim=1)


def mf_label(level, m, name):
    # Index labels only. Gaussian centres are free parameters and are NOT constrained to keep the order of their index, so a name
    # such as "low" or "high" would assert a meaning the trained model need not have (see the ordering check in the output).
    return f"MF{level + 1}"


def main() -> int:
    meta = json.loads(META.read_text()); ss = meta["normalisation_shift_scale"]
    model = HANFIS(m_raw=2, m_intermediate=3, mf_family="gauss", monotone=True); model.load_state_dict(torch.load(MODEL, map_location="cpu", weights_only=True)); model.eval()
    rng = np.random.default_rng(20261107); x = torch.tensor(rng.random((1000, 7)), dtype=torch.float32)
    with torch.no_grad():
        v_ref, e_ref = model.vulnerability(x[:, 0:3]), model.environment(x[:, 3:6]); v, e = torch.clamp(v_ref, 0, 1), torch.clamp(e_ref, 0, 1)
        diffs = {"V": float((panel_reconstruct(model.vulnerability, x[:, 0:3]) - v_ref).abs().max()),
                 "E": float((panel_reconstruct(model.environment, x[:, 3:6]) - e_ref).abs().max()),
                 "I": float((panel_reconstruct(model.integration, torch.stack([v, e, x[:, 6]], dim=1)) - model.integration(torch.stack([v, e, x[:, 6]], dim=1))).abs().max())}
    print("max abs difference, reconstruction vs model forward pass:", diffs)
    if max(diffs.values()) >= 1e-5:
        print("ABORT: reconstruction does not match the model's forward pass; nothing written"); return 2
    lines = ["# Trained HANFIS rules: fold 0, seed 20260928 (E4-bis, 120 assets)", "",
             "Descriptive documentation of one pre-specified saved model (`results_python/e4bis_120_models/models/fold0_seed20260928_hanfis.pt`). "
             f"Reconstruction checked against the model's forward pass on 1,000 fixed rows (max abs difference: V {diffs['V']:.1e}, E {diffs['E']:.1e}, I {diffs['I']:.1e}). "
             "Membership functions are named by index (MF1, MF2, MF3), not by linguistic labels, because the centres are free parameters. Gaussian membership functions mu(z) = exp(-0.5 ((z - c) / s)^2), normalised Sugeno firing, consequent f = b0 + sum b_i z_i with softplus slopes (A-04). "
             "Inputs z are in normalised units; for the raw inputs raw = shift + scale * z (x1 CVSS: 0 to 10; x3 Patch Risk: 0 to 2; x6 Asset Criticality: 1 to 5). v and e are the clipped panel outputs.", ""]
    inputs_V, inputs_E = ["cvss", "exploitability", "patch_risk"], ["mfa_risk", "kubernetes_exposure", "asset_criticality"]
    panels = [("V", model.vulnerability, [NAMES[n] for n in inputs_V], inputs_V), ("E", model.environment, [NAMES[n] for n in inputs_E], inputs_E),
              ("I", model.integration, ["v", "e", "x7 Threat Intelligence"], [None, None, "threat_intelligence"])]
    for pname, panel, labels, raw_names in panels:
        lines += [f"## Panel {pname}: {panel.rule_count} rules, {panel.premise_parameter_count} premise and {panel.consequents.numel()} consequent parameters", "",
                  "Membership functions (centre c, width s; raw-unit centre in brackets where an input has a raw scale):", ""]
        for i, lab in enumerate(labels):
            parts = []
            for j in range(panel.m_per_input[i]):
                c = float(panel.centers[i][j]); s = float(torch.exp(panel.log_sigmas[i][j]).clamp_min(1e-3))
                raw = ""
                if raw_names[i]:
                    sh, sc = ss[raw_names[i]]; raw = f" [raw {sh + sc * c:.3g}]"
                parts.append(f"{mf_label(j, panel.m_per_input[i], lab)}: c={c:.3f}, s={s:.3f}{raw}")
            lines.append(f"- {lab}: " + "; ".join(parts))
        order = []
        for i, lab in enumerate(labels):
            cs = [float(panel.centers[i][j]) for j in range(panel.m_per_input[i])]
            order.append(f"{lab.split()[0]}: centres in index order {[round(c, 3) for c in cs]} -> " + ("increasing" if all(a < b for a, b in zip(cs, cs[1:])) else "NOT increasing"))
        lines += ["", "Ordering check (do the centres keep the order of the membership-function index?): " + "; ".join(order) + ".",
                  "", "| Rule | IF | b0 | " + " | ".join(f"b({l.split()[0]})" for l in labels) + " |", "|---|---|---|" + "---|" * len(labels)]
        B = panel.effective_consequents().detach()
        for r in range(panel.rule_count):
            cond = " AND ".join(f"{labels[i].split()[0]} is {mf_label(int(panel.rule_indices[r, i]), panel.m_per_input[i], labels[i])}" for i in range(panel.n_inputs))
            lines.append(f"| {r + 1} | {cond} | {float(B[r, 0]):+.3f} | " + " | ".join(f"{float(B[r, i + 1]):.3f}" for i in range(panel.n_inputs)) + " |")
        lines.append("")
    lines += ["---", "Generated by scripts/e27_rules_and_surface.py with AI assistance (Claude, Anthropic); no training, no data selection."]
    path = OUT / "hanfis_rules_fold0_seed20260928.md"; path.write_text("\n".join(lines), encoding="utf-8"); print("written", path)
    print("STATUS=E27_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
