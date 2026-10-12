#!/usr/bin/env python3
"""Tambal naskah untuk E11 (rumus bentuk-maks lebih baik daripada HANFIS). MEMPERBAIKI pernyataan yang kini tidak benar ('lebih akurat daripada setiap pembanding yang belajar'):
(1) sub-bagian E9/E10 -> (E9-E11): kalimat penutup paragraf kedua dilunakkan, paragraf E11 baru, baris tabel E11, keterangan tabel; (2) Discussion: kalimat 'What the data support' diganti;
(3) Conclusion: kalimat post hoc diganti; (4) abstrak: ekor kalimat post hoc diganti; (5) C5 menyebut pembanding rumus. Jangkar fleksibel; gagal-tertutup (semua cocok atau tidak ada yang ditulis); idempoten; cadangan .pre-e11.bak."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
flex = lambda t: r"\s+".join(map(re.escape, t.split()))
E11P = (r"In E11 we asked whether a small formula suffices. Because the label is the window mean of a maximum over $\max(\mathrm{EPSS},\mathbb{1}[\mathrm{KEV}])\,\rho$, we fitted $\hat y=a+b\,\max(x_2,\,c\,x_7)$ on the training rows of each fold, "
        r"choosing $c$ on a grid and $a,b$ by least squares, together with a ridge model with the $x_2x_7$ interaction and monotone gradient boosting on $(x_2,x_7)$. The grid selected $c=0.10$ in all five folds, with $b$ between 99.2 and 100.0 and $a<0.07$, "
        r"that is, almost exactly $100\max(x_2,\,0.1\,x_7)$. This formula has a lower pooled error (0.27) than HANFIS (0.41) and than persistence (0.42); HANFIS is worse than it, with a skill of $-0.534$ (interval $[-1.438,\,-0.208]$), "
        r"and worse than the interaction ridge ($-0.529$), while it is not distinguishable from monotone boosting ($0.538$, $[-0.005,\,0.802]$). We had expected parity or an advantage for HANFIS; the observed disadvantage means that on this target the "
        r"176-parameter model adds no accuracy to what a four-parameter formula of current EPSS and KEV signals already provides. The gains over CVSS, linear models and a flat ANFIS reported in the confirmatory comparisons therefore show that the task is nearly "
        r"determined by those two signals, not that the hierarchical structure helps.")
ROWS = ("\\multicolumn{4}{@{}l}{\\emph{E11: HANFIS with all inputs vs.}}\\\\\n"
        "Max-form formula $a+b\\max(x_2,c\\,x_7)$ & $-0.534$ & $[-1.438,\\,-0.208]$ & 0.41 / 0.27\\\\\n"
        "Ridge on $x_2$, $x_7$, $x_2x_7$ & $-0.529$ & $[-1.415,\\,-0.206]$ & 0.41 / 0.27\\\\\n"
        "Monotone boosting on $(x_2,x_7)$ & $0.538$ & $[-0.005,\\,0.802]$ & 0.41 / 0.88\\\\\n")
DISC_OLD = ("What the data support is therefore that a 34-rule hierarchical model estimates near-term exploitability exposure from current EPSS and KEV signals about as accurately as a persistence forecast that needs past labels "
            "(the two are not distinguishable) and more accurately than every learned alternative we tried; they do not support the claim that the vulnerability--environment decomposition, or the environmental inputs, improve prediction.")
DISC_NEW = ("What the data support is therefore narrower: a 34-rule hierarchical model estimates near-term exploitability exposure from current EPSS and KEV signals about as accurately as a persistence forecast that needs past labels "
            "(the two are not distinguishable), and more accurately than generic linear and boosted models, but not more accurately than a four-parameter formula of the same two signals (Section~\\ref{subsec:e9}), which, together with the interaction ridge, "
            "has the lowest error of all predictors we compared; the data do not support the claim that the vulnerability--environment decomposition, or the environmental inputs, improve prediction.")
CONC_OLD = ("and is not demonstrably better than gradient boosting restricted to those two inputs (Sections~\\ref{subsec:e8} and~\\ref{subsec:e9}), so the contribution is a compact, transparent estimator of near-term exploitability exposure, "
            "and whether environmental context improves forecasts remains open.")
CONC_NEW = ("and a four-parameter formula of those two inputs has a lower error than HANFIS (Sections~\\ref{subsec:e8} and~\\ref{subsec:e9}), so on this target HANFIS offers a compact rule base with a documented response surface rather than "
            "better accuracy than a simple formula, and whether environmental context improves forecasts remains open.")
ABS_NEW = (r"Post hoc analyses qualify these gains: exact Shapley attribution places 78.9\% of the model's attribution on exploitability and the KEV indicator, which are ingredients of the label; without them HANFIS shows no skill over CVSS "
           r"(skill score $-0.14$, 95\% interval $-0.34$ to $0.05$); and a four-parameter formula of those two inputs, $100\max(x_2,0.1\,x_7)$, has a lower error than HANFIS (0.27 versus 0.41; skill $-0.53$, interval $-1.44$ to $-0.21$). "
           r"On this target HANFIS is therefore a compact rule base, not a more accurate predictor than a simple formula, and the data cannot show whether environmental context improves forecasts.")
errors, edits = [], []
def one(rx, what):
    m = list(re.finditer(rx, s, re.S)); 
    if len(m) != 1: errors.append(f"{what}: jangkar ditemukan {len(m)}x (harus 1)"); return None
    return m[0]
if "Within this group, HANFIS has a lower error than every alternative" in s: print("sudah: frase E10")
else:
    m = one(flex("HANFIS has a lower error than every learned alternative with an interval excluding zero"), "E10: frase 'every learned alternative'")
    if m: edits.append(("E10: frase", m.start(), m.end(), "Within this group, HANFIS has a lower error than every alternative with an interval excluding zero"))
if ", but is not distinguishable from persistence." in s and "better only around structural breaks" not in s: print("sudah: resumo curto")
else:
    m = one(flex(", but is not distinguishable from persistence and is better only around structural breaks of the label."), "abstrak: frase de persistence")
    if m: edits.append(("abstrak: frase persistence", m.start(), m.end(), ", but is not distinguishable from persistence."))
if "In E11 we asked whether a small formula suffices" in s: print("sudah: sub-bagian E11")
else:
    m = one(flex("We therefore read HANFIS as a compact nonlinear estimator of exposure from $x_2$ and $x_7$ whose accuracy matches persistence without access to past labels, not as evidence that the vulnerability--environment decomposition improves forecasts."), "sub-bagian: kalimat penutup")
    if m: edits.append(("sub-bagian: kalimat penutup + paragraf E11", m.start(), m.end(),
                        "Taken alone, these comparisons would suggest that HANFIS is a compact estimator of exposure from $x_2$ and $x_7$ that matches persistence without access to past labels; the next comparison qualifies this.\n\n" + E11P))
    m = one(flex("Persistence (lag-4 label) & $0.015$ & $[-0.620,\\,0.243]$ & 0.41 / 0.42\\\\"), "tabel: baris persistence")
    if m: edits.append(("tabel: baris E11", m.end(), m.end(), "\n" + ROWS.rstrip("\n")))
    m = one(flex("\\subsection{Label-ingredient ablation and information-minimal baselines (E9, E10)}"), "sub-bagian: judul")
    if m: edits.append(("judul", m.start(), m.end(), "\\subsection{Label-ingredient ablation and information-minimal baselines (E9--E11)}"))
    m = one(flex("Label-ingredient ablation (E9) and information-minimal baselines (E10), 1{,}080 held-out rows."), "tabel: keterangan")
    if m: edits.append(("keterangan tabel", m.start(), m.end(), "Label-ingredient ablation (E9), information-minimal baselines (E10) and formula baselines (E11), 1{,}080 held-out rows."))
if "but not more accurately than a four-parameter formula" in s: print("sudah: Discussion")
else:
    m = one(flex(DISC_OLD), "Discussion")
    if m: edits.append(("Discussion", m.start(), m.end(), DISC_NEW))
if "so on this target HANFIS offers a compact rule base" in s: print("sudah: Conclusion")
else:
    m = one(flex(CONC_OLD), "Conclusion")
    if m: edits.append(("Conclusion", m.start(), m.end(), CONC_NEW))
if "a four-parameter formula of those two inputs, $100" in s: print("sudah: abstrak")
else:
    m = one(r"Post\s+hoc\s+analyses\s+qualify\s+these\s+gains:.{0,2500}?improves\s+forecasts\.", "abstrak")
    if m: edits.append(("abstrak", m.start(), m.end(), ABS_NEW))
if "information-minimal and formula baselines" in s or "(E9--E11)" in s and "information-minimal and formula" in s: print("sudah: C5")
else:
    m = one(flex("complemented by post hoc information-minimal baselines and an ablation"), "C5")
    if m: edits.append(("C5", m.start(), m.end(), "complemented by post hoc information-minimal and formula baselines and an ablation"))
if errors: print("ABORT, tidak ada yang ditulis:"); [print("  -", e) for e in errors]; sys.exit(2)
if not edits: print("Sudah diterapkan seluruhnya."); sys.exit(0)
for name, a, b, new in sorted(edits, key=lambda t: -t[1]): s = s[:a] + new + s[b:]; print(f"diterapkan: {name}")
shutil.copy(P, str(P) + ".pre-e11.bak"); P.write_text(s, encoding="utf-8"); print("OK")
