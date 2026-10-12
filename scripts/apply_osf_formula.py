#!/usr/bin/env python3
"""Perbarui draf teks pendaftaran OSF (bahasa Inggris) agar sama dengan protokol E7: tambah P7e dan P7f (sekunder, asal post hoc), kalimat deskripsi, rencana analisis, transparansi, komparator, hash rumus.
Opsional bila jangkarnya masih ada: perbaiki batas data latih (2026-08-24 -> 2026-07-27, A-47) dan ungkapkan snapshot KEV 2026-09-28. Jangkar wajib: '**Hypotheses.**', 'P7d', '## Analysis plan', '**Transparency.**'.
Butir opsional yang jangkarnya tidak ada DILAPORKAN (periksa manual), tidak diam-diam dilewati. Idempoten; cadangan .pre-osf.bak.  python scripts/apply_osf_formula.py [--file protocols/E7_osf_registration_DRAFT.md]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--file", default="protocols/E7_osf_registration_DRAFT.md"); a = ap.parse_args()
P = Path(a.file); s = P.read_text(encoding="utf-8")
if "**P7e" in s: print("Sudah diterapkan (P7e ada)."); sys.exit(0)
flex = lambda t: r"\s+".join(map(re.escape, t.split()))
def find(rx): m = list(re.finditer(rx, s)); return m[0] if len(m) == 1 else None
edits, skipped, errors = [], [], []
# wajib: hipotesis P7e dan P7f setelah butir P7d
m = find(r"- \*\*P7d \(information beyond persistence; secondary\)\.\*\*[^\n]*\n")
if not m: errors.append("butir P7d tidak ditemukan tepat sekali")
else: edits.append((m.end(), m.end(), "- **P7e (secondary; post hoc origin).** A four-parameter formula `y_hat = a + b * max(x2, c * x7)` (x2 = the exploitability input, x7 = the KEV indicator, both at time t), fitted once on the same training rows as the HANFIS models and then frozen (`protocols/E7_formula_2026-10-12.json`), beats persistence: SS >= 0.05 and the lower 95% bound > 0.\n- **P7f (secondary; post hoc origin).** HANFIS is not better than that formula: the upper bound of the 95% CI of the HANFIS skill score against the formula is below 0.05 (refuted if SS >= 0.05 with a lower bound > 0).\n"))
m = find(r"Decision rules as stated in the hypotheses\.")
if not m: errors.append("kalimat 'Decision rules as stated in the hypotheses.' tidak ditemukan tepat sekali")
else: edits.append((m.end(), m.end(), " P7e and P7f are secondary, are reported with their confidence intervals, and are not part of the Holm family."))
m = find(r"An earlier explanation-fidelity study \(E6\)")
if not m: errors.append("kalimat E6 pada Transparency tidak ditemukan tepat sekali")
else: edits.append((m.start(), m.start(), "The formula and hypotheses P7e and P7f originate from post hoc analyses of the same out-of-fold data (their out-of-fold support is not counted as confirmation); the formula coefficients are fixed before any forward label is computed. The target does not depend on the three environmental inputs, so this study cannot test their value. "))
# opsional
m = find(flex("This registration tests that suggestion prospectively on weeks whose labels have not been computed."))
if m: edits.append((m.end(), m.end(), " A further post hoc analysis found that a four-parameter formula of two inputs (the EPSS-based exploitability input and the KEV indicator) has a lower error than HANFIS and than persistence on out-of-fold data; the registration also tests this formula prospectively."))
else: skipped.append("kalimat deskripsi (tambahan tentang rumus)")
m = find(flex("ridge on the seven inputs (descriptive)."))
if m: edits.append((m.start(), m.end(), "ridge on the seven inputs (descriptive), and the four-parameter formula (above)."))
else: skipped.append("komparator (menyebut rumus)")
m = find(flex("(fitted on out-of-fold E4 predictions only)."))
if m: edits.append((m.end(), m.end(), " The formula coefficients are fixed in `protocols/E7_formula_2026-10-12.json` (fitted on the same training rows as the models; SHA256 [FORMULA HASH])."))
else: skipped.append("rencana desain (hash berkas koefisien rumus)")
m = find(flex("retrained on all labelled weeks up to 2026-08-24"))
if m: edits.append((m.start(), m.end(), "trained on labelled weeks up to 2026-07-27 (the first forward week minus a 30-day embargo)"))
elif "2026-08-24" in s: skipped.append("batas data latih: masih ada '2026-08-24' dengan susunan kata lain (periksa manual; yang benar 2026-07-27, A-47)")
m = find(flex("the weekly EPSS/KEV snapshots after 2026-09-21 have not been downloaded"))
if m: edits.append((m.start(), m.end(), "the weekly EPSS snapshots after 2026-09-21 have not been downloaded (one CISA KEV catalog snapshot dated 2026-09-28 was fetched earlier for another analysis and is not used to compute forward labels)"))
elif "2026-09-28" not in s: skipped.append("pengungkapan snapshot KEV 2026-09-28 (periksa manual)")
if errors: print("ABORT, tidak ada yang ditulis:"); [print("  -", e) for e in errors]; sys.exit(2)
for st, en, new in sorted(edits, key=lambda t: -t[0]): s = s[:st] + new + s[en:]
shutil.copy(P, str(P) + ".pre-osf.bak"); P.write_text(s, encoding="utf-8"); print(f"OK: {len(edits)} perubahan di {P}")
for k in skipped: print("  DILEWATI (periksa manual):", k)
