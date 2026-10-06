#!/usr/bin/env python3
"""Samakan empat klaim Fuzzyfortify di naskah dengan bukti audit (HOLD_FUZZYFORTIFY_REPRODUCTION_GAP):
abstrak, C5, kalimat H1b di sec. 1, dan kalimat 'reported separately' di sec. 4.3. Gagal-tertutup, idempoten."""
import sys, shutil, pathlib
P = pathlib.Path("manuscript/sn-article.tex")
s = P.read_text(encoding="utf-8")
if "a Fuzzyfortify comparison is not claimed" in s:
    print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
R = [
 ("and Fuzzyfortify is reported separately as an external, non-retrained reference.}",
  "and a Fuzzyfortify comparison is not claimed because its published benchmark scores could not be reproduced.}"),
 ("A reproducible evaluation against Fuzzyfortify and flat ANFIS baselines using predictive, computational, temporal, and operational metrics under common data partitions and deployment conditions.",
  "A reproducible evaluation against persistence, single-CVSS, ridge and flat ANFIS baselines (full and parameter-matched) using predictive and computational metrics under common grouped, embargoed temporal partitions; a Fuzzyfortify comparison is not claimed (Section~\\ref{subssec4.3})."),
 ("Persistence, not Fuzzyfortify or CVSS, is the empirically strongest baseline observed on the pilot dataset",
  "Persistence, not a single CVSS score, is the empirically strongest baseline observed on the pilot dataset"),
 ("Fuzzyfortify is reported\nseparately as an external, non-retrained reference on its five original benchmark cases rather than\nfolded into the statistical family above.",
  "Fuzzyfortify is not part of the statistical family: it requires four native inputs (complexity-resilience\n"
  "index, impact, base score, exploitability) that the asset-week data do not produce, and the comparison\n"
  "protocol forbids unreported proxy mappings. As an external check, the implementation available to us was\n"
  "run on the five published benchmark cases of the original paper; its scores fall below the published ones\n"
  "in every case, by 5.9 to 21.0 points on the 0--100 scale (mean absolute difference 12.0), and four of the\n"
  "five reproduced scores are identical (49.5). We therefore neither use it as a baseline nor report a\n"
  "Fuzzyfortify comparison."),
]
for old, _ in R:
    n = s.count(old)
    if n != 1: sys.exit(f"ABORT: jangkar {n}x (harus 1): {old[:70]!r}")
for old, new in R: s = s.replace(old, new)
shutil.copy(P, str(P) + ".pre-fuzzyfortify.bak")
P.write_text(s, encoding="utf-8"); print("OK")
