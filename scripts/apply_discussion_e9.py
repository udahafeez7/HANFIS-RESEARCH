#!/usr/bin/env python3
"""Tambal naskah: menyelaraskan Discussion dan Conclusion dengan hasil E8-E10 (bingkai: estimator kompak untuk paparan eksploitasi jangka dekat; lingkungan tidak terbukti menambah prediksi).
Tiga sisipan/perubahan; jangkar fleksibel terhadap pemisah baris; gagal-tertutup (semua cocok tepat sekali atau tidak ada yang ditulis); idempoten; cadangan .pre-disc.bak. Dari akar repo."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
flex = lambda t: r"\s+".join(map(re.escape, t.split()))
PARA = (r"The post hoc analyses of Sections~\ref{subsec:e8} and~\ref{subsec:e9} qualify how far these findings generalise. Exact Shapley attribution places 78.9\% of the model's attribution on exploitability "
        r"and the KEV indicator, which are ingredients of the realised label, and only 3.3\% on the three environmental inputs; without those two inputs the model shows no demonstrable skill over a single CVSS score, "
        r"and it is not demonstrably better than gradient boosting restricted to them. What the data support is therefore that a 34-rule hierarchical model estimates near-term exploitability exposure from current EPSS and KEV "
        r"signals about as accurately as a persistence forecast that needs past labels (the two are not distinguishable) and more accurately than every learned alternative we tried; they do not support the claim that the "
        r"vulnerability--environment decomposition, or the environmental inputs, improve prediction. A forward evaluation on weeks after the protocol was frozen is planned and will be pre-registered separately.")
CLAUSE = r"which is the premise the environmental subsystem's Kubernetes-exposure input relies on; whether that input improves prediction is a separate question, and on the present inventory the environmental inputs add no demonstrable predictive information (Section~\ref{subsec:e9})."
CONC = (r" Post hoc analyses qualify this further: the model's skill rests on exploitability and KEV (78.9\% of the exact Shapley attribution; without them no skill over CVSS) and is not demonstrably better than gradient boosting "
        r"restricted to those two inputs (Sections~\ref{subsec:e8} and~\ref{subsec:e9}), so the contribution is a compact, transparent estimator of near-term exploitability exposure, and whether environmental context improves forecasts remains open.")
errors, edits = [], []
a1 = re.compile(flex("The instrumentation-overhead results")); m = list(a1.finditer(s))
if "The post hoc analyses of Sections" in s: print("sudah: paragraf Discussion")
elif len(m) == 1: edits.append(("paragraf-discussion", m[0].start(), m[0].start(), PARA + "\n\n"))
else: errors.append(f"paragraf-discussion: jangkar {len(m)}x (harus 1)")
a2 = re.compile(flex("which is the premise the environmental subsystem's Kubernetes-exposure input relies on.")); m = list(a2.finditer(s))
if "the environmental inputs add no demonstrable predictive information (Section~\\ref{subsec:e9})" in s: print("sudah: klausa Discussion")
elif len(m) == 1: edits.append(("klausa-discussion", m[0].start(), m[0].end(), CLAUSE))
else: errors.append(f"klausa-discussion: jangkar {len(m)}x (harus 1)")
a3 = re.compile(flex("of the vulnerability/environmental/threat decomposition") + r"\s+\(Section~\\ref\{[^}]+\}\)\."); m = list(a3.finditer(s))
if "Post hoc analyses qualify this further" in s: print("sudah: kalimat Conclusion")
elif len(m) == 1: edits.append(("kalimat-conclusion", m[0].end(), m[0].end(), CONC))
else: errors.append(f"kalimat-conclusion: jangkar {len(m)}x (harus 1)")
if errors: print("ABORT, tidak ada yang ditulis:"); [print("  -", e) for e in errors]; sys.exit(2)
if not edits: print("Sudah diterapkan seluruhnya."); sys.exit(0)
for name, a, b, new in sorted(edits, key=lambda t: -t[1]): s = s[:a] + new + s[b:]; print(f"diterapkan: {name}")
shutil.copy(P, str(P) + ".pre-disc.bak"); P.write_text(s, encoding="utf-8"); print("OK")
