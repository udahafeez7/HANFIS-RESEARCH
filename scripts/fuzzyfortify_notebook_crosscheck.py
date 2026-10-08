#!/usr/bin/env python3
"""Reproduksi lima skor terbit Fuzzyfortify dengan logika NOTEBOOK ASLI (3__FUZZY_LOGIC_CONTROLLER.ipynb): Mamdani, AND=min, OR=max,
implikasi=min, agregasi=max, defuzzifikasi centroid, 4 aturan, semesta bilangan bulat. Numpy murni (tanpa scikit-fuzzy); setara dengan
skfuzzy.control (diverifikasi terhadap skfuzzy: selisih < 1e-9). Hanya MEMBACA csv audit; menulis fuzzyfortify_notebook_crosscheck.csv.
  python scripts/fuzzyfortify_notebook_crosscheck.py [--audit <csv>] [--out <csv>]"""
import argparse, csv, sys
from pathlib import Path
import numpy as np
D = "Jetson Orin/Telemetry/hanfis_protocol_v3/comparison_20260914_v3"
def trimf(x, a, b, c):
    y = np.zeros(len(x))
    if a != b: i = (a < x) & (x < b); y[i] = (x[i] - a) / (b - a)
    if b != c: i = (b < x) & (x < c); y[i] = (c - x[i]) / (c - b)
    y[x == b] = 1.0; return y
def trapmf(x, abcd):                                  # persis skfuzzy.membership.trapmf
    a, b, c, d = abcd; y = np.ones(len(x))
    i = x <= b; y[i] = trimf(x[i], a, b, b)
    i = x >= c; y[i] = trimf(x[i], c, c, d)
    y[x < a] = 0; y[x > d] = 0; return y
def centroid(x, mf):                                  # persis skfuzzy.defuzzify.centroid
    sm = sa = 0.0
    for i in range(1, len(x)):
        x1, x2, y1, y2 = x[i-1], x[i], mf[i-1], mf[i]
        if y1 == y2 == 0.0 or x1 == x2: continue
        if y1 == y2: m, ar = 0.5 * (x1 + x2), (x2 - x1) * y1
        elif y1 == 0.0 and y2 != 0.0: m, ar = 2.0/3.0*(x2 - x1) + x1, 0.5*(x2 - x1)*y2
        elif y2 == 0.0 and y1 != 0.0: m, ar = 1.0/3.0*(x2 - x1) + x1, 0.5*(x2 - x1)*y1
        else: m, ar = (2.0/3.0*(x2 - x1)*(y2 + 0.5*y1))/(y1 + y2) + x1, 0.5*(x2 - x1)*(y1 + y2)
        sm += m * ar; sa += ar
    return float("nan") if sa == 0 else sm / sa
XC, XI, XR = np.arange(1, 101, 1.0), np.arange(0, 11, 1.0), np.arange(0, 101, 1.0)
CPL = {"low": [1,1,8,15], "medium": [10,15,18,25], "high": [20,25,45,55], "vhigh": [50,55,100,100]}
SEV = {"low": [0,0,3.9,3.9], "medium": [4,4,6.9,6.9], "high": [7,7,8.9,8.9], "critical": [9,9,10,10]}
OUT = {"low": [0,0,19.5,39], "medium": [30,40,59,69], "high": [60,70,79.5,89], "catastrophic": [80,90,100,100]}
def fuzzify(x, xs, sets): return {k: float(np.interp(x, xs, trapmf(xs, v))) for k, v in sets.items()}
def risk(cri, imp, base, expl):
    c, i, b, e = fuzzify(cri, XC, CPL), fuzzify(imp, XI, SEV), fuzzify(base, XI, SEV), fuzzify(expl, XI, SEV)
    act = {"low": max(min(c["low"], i["low"]), min(b["low"], e["low"])),
           "medium": min(max(c["medium"], i["medium"]), max(b["medium"], e["medium"])),
           "high": min(max(c["high"], i["high"]), max(b["high"], e["high"])),
           "catastrophic": max(min(c["vhigh"], i["critical"]), min(b["critical"], e["critical"]))}
    # skfuzzy memperhalus semesta keluaran dengan titik potong tiap himpunan pada tingkat aktivasinya (find_memberships), lalu centroid.
    mfs = {k: trapmf(XR, OUT[k]) for k in OUT}; new = []
    for k, a_ in act.items():
        idx = np.where(np.diff(mfs[k] > a_))[0] if a_ == 0.0 else np.where(np.diff(mfs[k] >= a_))[0]
        new.extend((XR[idx] + (a_ - mfs[k][idx]) * (XR[idx + 1] - XR[idx]) / (mfs[k][idx + 1] - mfs[k][idx])).tolist())
    U = np.union1d(XR, new); agg = np.zeros(len(U))
    for k, a_ in act.items(): agg = np.maximum(agg, np.minimum(a_, np.interp(U, XR, mfs[k])))
    return centroid(U, agg), {k: round(a_, 3) for k, a_ in act.items() if a_ > 0}
def level(v): return "-" if v != v else "Catastrophic" if v >= 90 else "High" if v >= 70 else "Medium" if v >= 40 else "Low"
def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--audit", default=f"{D}/fuzzyfortify_reproduction_audit.csv")
    ap.add_argument("--out", default=f"{D}/fuzzyfortify_notebook_crosscheck.csv"); a = ap.parse_args(argv)
    rows = list(csv.DictReader(open(a.audit, encoding="utf-8"))); out = []
    print(f"{'kasus':26}{'terbit':>8}{'notebook':>10}{'selisih':>9}{'Python lama':>13}  aktivasi aturan keluaran")
    for r in rows:
        cri, imp, base, expl = (float(r[k]) for k in ("complexity_resilience_index", "impact", "base_score", "exploitability"))
        pub, py = float(r["published_risk_score"]), float(r["reproduced_risk_score"]); v, act = risk(cri, imp, base, expl)
        print(f"{r['adversarial_technique']:26}{pub:8.2f}{v:10.3f}{v - pub:9.3f}{py:13.2f}  {act}")
        out.append(dict(technique=r["adversarial_technique"], published=pub, notebook_logic=v, diff=v - pub, python_audit=py, level_published=level(pub), level_notebook=level(v), level_python=level(py), activation=str(act)))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    print(f"\nmaks |notebook - terbit| = {max(abs(o['diff']) for o in out):.3f}; ditulis ke {a.out}"); return 0
if __name__ == "__main__": sys.exit(main())
