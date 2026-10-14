#!/usr/bin/env python3
r"""Penyuntingan isi tahap 2 untuk manuscript/sn-article.tex: sembilan suntingan yang disetujui (A1, A2, B, C, D, E, F, G1, G2) untuk akurasi klaim, batas klaim, dan kejujuran akademik.
  A1, A2 : abstrak dan Discussion diselaraskan dengan Tabel E3 (SS_clim persistence 0,974; CVSS 0,222) dan Results;
  B      : hapus janji perbandingan Fuzzyfortify (Section 4.3 menyatakan tidak dibandingkan);
  C      : policy-translation layer bukan kontribusi: paragraf Introduction diringkas, C4 dihapus (C5 menjadi C4), rujukan di Conclusion disesuaikan;
  D      : 'interpretable by construction' diganti 'designed to be interpretable' + tujuan menguji fidelitas penjelasan (E6);
  E      : definisi 'pre-registered' diberi pengecualian OSF untuk E7;  F: salah ketik;  G: pernyataan post hoc dan validitas eksternal di Limitations.
Terapkan SETELAH apply_prose_edits_1.py (A2 dan C3 memakai teks hasil tahap 1; bila belum terapan, keduanya DILEWATI dan dapat diterapkan dengan menjalankan ulang skrip ini).
Setiap suntingan hanya mengganti teks lama yang COCOK PERSIS dan muncul TEPAT SEKALI; yang tidak cocok DILEWATI dan dilaporkan; cocok lebih dari sekali membatalkan seluruh proses.
Kutipan, rumus, dan angka di luar yang sengaja diubah sudah diperiksa identik. Idempoten. Akhir baris dipertahankan. Cadangan: .pre-prose2.bak.
   python scripts/apply_prose_edits_2.py [--tex manuscript/sn-article.tex] [--dry-run]"""
import argparse, shutil, sys
from pathlib import Path
EDITS = [
  ('A1', 'A1',
   "A 4-week persistence baseline already explains most of the label's variance; a single CVSS score, almost none.",
   'A 4-week persistence baseline lowers mean squared error relative to climatology by 97\\%; a single CVSS score, by 22\\%.'),
  ('A2a', 'A2',
   "A 4-week persistence forecast recovers 96\\% of the climatology-relative skill on the pilot inventory, so any claim that HANFIS ``predicts risk'' is a claim about improving on a strong autoregressive baseline, not about beating an uninformative one.",
   "A 4-week persistence forecast reduces mean squared error relative to climatology by 97\\% on the 120-asset inventory (Table~\\ref{tab:e3-baselines}; 96\\% on the earlier pilot), so any claim that HANFIS ``predicts risk'' is a claim about improving on a strong autoregressive baseline, not about beating an uninformative one."),
  ('A2b', 'A2',
   'Second, a single CVSS score carries essentially no explanatory power for the realised 30-day exploitability exposure ($\\mathrm{SS}_{\\mathrm{clim}}\\approx0$). Severity and realised exploitation are different quantities, and conflating them is a plausible source of alert fatigue in practice; this is itself evidence for the research gap that C3 claims to address.',
   'Second, a single CVSS score has limited explanatory power for the realised 30-day exploitability exposure ($\\mathrm{SS}_{\\mathrm{clim}}=0.222$ on the 120-asset inventory, against about 0 on the earlier pilot). Severity and realised exploitation are different quantities, and conflating them is a plausible source of alert fatigue in practice; this is consistent with the research gap that C3 claims to address.'),
  ('B', 'B',
   'The proposed architecture must therefore be compared against Fuzzyfortify, a flat grid-partitioned ANFIS, and a rule-reduced or clustering-based flat ANFIS using identical observations, data partitions, and evaluation conditions.',
   'The proposed architecture must therefore be compared against a flat grid-partitioned ANFIS and a rule-reduced or clustering-based flat ANFIS, together with simple baselines, using identical observations, data partitions, and evaluation conditions. Fuzzyfortify is not compared, because its native inputs are not produced by the asset-week data (Section~\\ref{subssec4.3}).'),
  ('C1', 'C',
   'A dynamic score is operationally useful only when it can support a controlled security decision. The proposed framework therefore specifies a policy-translation layer, designed but not evaluated in this paper, that maps validated risk states to predefined responses, such as generating an alert, restricting communication, pausing a container, or isolating a compromised workload. This layer is designed as an auditable policy enforcement mechanism rather than an unconstrained autonomous controller. Critical safeguards include monotonicity checks, explicit high-risk override rules, confidence thresholds, response logging, and a configurable requirement for human authorization for disruptive actions. In this way, the framework is designed to connect adaptive assessment to measurable time-to-mitigation in future work, while preserving accountability and operational safety.',
   'A policy-translation layer that maps validated risk states to bounded responses is designed but not evaluated here, and it is outside the claims of this paper (Section~\\ref{sec6}).'),
  ('C2', 'C',
   '\\item[\\textbf{C4.}] An auditable policy-translation mechanism (designed but not evaluated in this paper) that converts validated risk states into bounded response recommendations with monotonicity constraints, critical-risk overrides, confidence controls, and an execution log.\n    \\item[\\textbf{C5.}]',
   '\\item[\\textbf{C4.}]'),
  ('C3', 'C',
   'The auditable policy-translation layer (contribution C4) and edge deployment (originally hypothesis H5, now future work because the present testbed runs HANFIS cluster-side rather than on its edge node) remain designed but unevaluated.',
   'The policy-translation layer (not a contribution of this paper) and edge deployment (originally hypothesis H5, now future work because the present testbed runs HANFIS cluster-side rather than on its edge node) remain designed but unevaluated.'),
  ('D', 'D',
   'The aim of this study is to design, implement, and evaluate a HANFIS with a reduced rule base and intermediate variables that are interpretable by construction, for dynamic cybersecurity risk assessment in cloud-native environments.',
   'The aim of this study is to design, implement, and evaluate a HANFIS with a reduced rule base and intermediate variables designed to be interpretable, and to test how faithful its rule-level explanations are (Section~\\ref{sec:e6}), for dynamic cybersecurity risk assessment in cloud-native environments.'),
  ('E', 'E',
   "Throughout, ``pre-registered'' means that a dated protocol was committed to the project's version-controlled repository and tagged before the corresponding training run; it does not refer to an entry in an external registry.",
   "Throughout, ``pre-registered'' means that a dated protocol was committed to the project's version-controlled repository and tagged before the corresponding training run. This does not refer to an entry in an external registry, except for the forward evaluation (Section~\\ref{subsec:e7}), which was also registered on the Open Science Framework."),
  ('F', 'F',
   "H2$'$ is reported as the uncriteria'd capacity reference.",
   "H2$'$ is reported as the capacity reference, without a decision criterion."),
  ('G', 'G1+G2',
   'The confirmatory comparison (Table~\\ref{tab:e4-results}) uses the full 120-asset inventory.',
   'All analyses labelled post hoc were designed after the confirmatory results and run on the same data; they are descriptive, carry no multiplicity correction, and none of them changes a registered decision.\n\nThe inventory consists of public container images and a small number of testbed assets built from a public base image, and the label reflects exploitation signals of public vulnerabilities (EPSS, KEV), not incidents in a specific organisation; generalisation to other workloads or to incident-based outcomes is untested.\n\nThe confirmatory comparison (Table~\\ref{tab:e4-results}) uses the full 120-asset inventory.'),

]
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--tex", default="manuscript/sn-article.tex"); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
p = Path(a.tex)
if not p.exists(): sys.exit(f"ABORT: {p} tidak ada")
text = open(p, encoding="utf-8", newline="").read(); crlf = "\r\n" in text
if crlf: text = text.replace("\r\n", "\n")
applied, already, skipped, multi = [], [], [], []
for i, code, old, new in EDITS:
    n_old, n_new = text.count(old), text.count(new)
    # 'sudah terpasang': bila teks lama berada di dalam teks baru (mis. G) cukup teks baru ada; selain itu teks lama harus sudah hilang dan teks baru ada (mis. C2, teks baru bagian dari teks lama)
    done = (n_new >= 1) if old in new else (n_old == 0 and n_new >= 1)
    if done: already.append(i); continue
    if n_old > 1: multi.append(i); continue
    if n_old == 1: text = text.replace(old, new, 1); applied.append(i)
    else: skipped.append(i)
if multi: sys.exit("ABORT, tidak ada yang ditulis: teks lama muncul lebih dari sekali untuk " + ", ".join(multi))
print(f"Diterapkan ({len(applied)}): {', '.join(applied) or '-'}")
print(f"Sudah ada sebelumnya ({len(already)}): {', '.join(already) or '-'}")
print(f"DILEWATI, teks lama tidak cocok ({len(skipped)}): {', '.join(skipped) or '-'}")
if a.dry_run or not applied: print("(dry-run atau tidak ada perubahan; tidak ada yang ditulis)"); sys.exit(0)
out = text.replace("\n", "\r\n") if crlf else text
shutil.copy(p, str(p) + ".pre-prose2.bak"); open(p, "w", encoding="utf-8", newline="").write(out)
print("OK: berkas ditulis" + ("; sebagian dilewati: terapkan apply_prose_edits_1.py lebih dulu lalu jalankan ulang skrip ini, atau unggah sn-article.tex terbaru" if skipped else ""))
