#!/usr/bin/env python3
"""Bukti silang audit Fuzzyfortify: port Python dari logika aplikasi web asli (scripts2.js, 11 aturan, rata-rata terbobot) dibandingkan dengan
nilai terbit dan nilai Python lama di fuzzyfortify_reproduction_audit.csv. Port ini diverifikasi terhadap eksekusi scripts2.js asli di Node.
Hanya MEMBACA csv audit; menulis fuzzyfortify_js_crosscheck.csv. Jalankan dari akar repo:
  python scripts/fuzzyfortify_js_crosscheck.py [--audit <csv>] [--out <csv>]"""
import argparse, csv, math, sys
from pathlib import Path
D = "Jetson Orin/Telemetry/hanfis_protocol_v3/comparison_20260914_v3"
def tm(x, a, b, c, d):                      # persis trapezoidalMembership di scripts2.js (x<=a atau x>=d -> 0, termasuk saat a==b)
    if x <= a or x >= d: return 0.0
    if b <= x <= c: return 1.0
    if a < x < b: return (x - a) / (b - a)
    return (d - x) / (d - c)
W = {1: 20, 2: 55, 3: 80, 4: 100, 5: 80, 6: 55, 7: 75, 8: 30, 9: 55, 10: 74, 11: 85}
def rules(cri, imp, base, expl):
    L, M, H, VH = tm(cri,1,1,8,15), tm(cri,10,15,18,25), tm(cri,20,25,45,55), tm(cri,50,55,100,100)
    f = lambda x: [tm(x,0,0,2.5,2.5), tm(x,3,4,6,7), tm(x,6.5,7.5,8.5,9.5), tm(x,9,9.5,10,10)]
    I, B, E = f(imp), f(base), f(expl)
    return {1:min(L,I[0],B[0],E[0]), 2:min(M,I[1],B[1],E[1]), 3:min(H,I[2],B[2],E[2]), 4:min(VH,I[3],B[3],E[3]),
            5:min(H,I[1],B[0],E[2]), 6:min(H,I[1],B[0],E[1]), 7:min(M,I[3],B[1],E[1]), 8:min(L,I[2],B[0],E[2]),
            9:min(H,I[1],B[1],E[0]), 10:min(H,I[1],B[2],E[0]), 11:min(VH,I[2],B[2],E[1])}
def risk(r, use=None):
    ks = [k for k in r if use is None or k in use]; den = sum(r[k] for k in ks)
    return sum(r[k] * W[k] for k in ks) / den if den > 0 else float("nan")
def level(v): return "-" if math.isnan(v) else "Catastrophic" if v >= 90 else "High" if v >= 70 else "Medium" if v >= 40 else "Low"
def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--audit", default=f"{D}/fuzzyfortify_reproduction_audit.csv")
    ap.add_argument("--out", default=f"{D}/fuzzyfortify_js_crosscheck.csv"); a = ap.parse_args(argv)
    rows = list(csv.DictReader(open(a.audit, encoding="utf-8"))); out = []
    print(f"{'kasus':26}{'terbit':>8}{'JS11':>8}{'selisih':>9}{'JS 8 aturan':>13}{'Python lama':>13}  level terbit/JS/Python  aturan menyala")
    for r in rows:
        cri, imp, base, expl = (float(r[k]) for k in ("complexity_resilience_index", "impact", "base_score", "exploitability"))
        pub, py = float(r["published_risk_score"]), float(r["reproduced_risk_score"]); ru = rules(cri, imp, base, expl)
        v11, v8 = risk(ru), risk(ru, set(range(1, 9))); act = {k: round(x, 3) for k, x in ru.items() if x > 0}
        diff = v11 - pub if not math.isnan(v11) else float("nan")
        print(f"{r['adversarial_technique']:26}{pub:8.2f}{v11:8.2f}{diff:9.2f}{v8:13.2f}{py:13.2f}  {level(pub)}/{level(v11)}/{level(py)}  {act}")
        out.append(dict(technique=r["adversarial_technique"], cri=cri, impact=imp, base_score=base, exploitability=expl, published=pub, js_11_rules=v11,
                        js_minus_published=diff, js_8_rules=v8, python_audit=py, level_published=level(pub), level_js=level(v11), level_python=level(py), rules_firing=str(act)))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    ok = [o for o in out if not math.isnan(o["js_11_rules"])]
    print(f"\nJS menghasilkan keluaran pada {len(ok)}/{len(out)} kasus; rerata |JS - terbit| = {sum(abs(o['js_minus_published']) for o in ok)/len(ok):.2f}; ditulis ke {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
