#!/usr/bin/env python3
"""Naskah setelah pembekuan E7: (1) sub-bagian Methods 'Prospective evaluation (E7): pre-registered design' (label subsec:e7) disisipkan SEBELUM \\section{Results}; (2) kalimat Discussion 'planned and will be pre-registered separately'
diganti dengan rujukan ke tag beku; (3) opsional: satu kalimat di Limitations tentang mekanisme INSUFFICIENT_EVIDENCE (status Trivy di luar himpunan, mis. under_investigation pada CVE Red Hat baru). Jangkar inti wajib tepat sekali (gagal-tertutup);
(3) dilaporkan bila dilewati. Hasil E7 TIDAK ditulis di sini (menunggu D2). Idempoten; cadangan .pre-e7m.bak.  Dari akar repo."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
flex = lambda t: r"\s+".join(map(re.escape, t.split()))
SUB = r'''\subsection{Prospective evaluation (E7): pre-registered design}\label{subsec:e7}
The confirmatory comparison and the post hoc analyses reported above use data whose labels were already known when the questions were asked. To obtain an evaluation that does not, we froze a forward-evaluation protocol before any label for the test weeks was computed. The protocol, the five final HANFIS models (trained only on labelled weeks up to 2026-07-27, the first test week minus the 30-day embargo), the blend weight, the coefficients of the max-form formula of Section~\ref{subsec:e9}, and all analysis scripts were committed and tagged (\texttt{e7-prereg-2026-10-12}, created on 2026-10-12 at 15:04 +0700); a script verified that the tagged tree is identical to the working files, and the evaluation script refuses to run unless this verification passes, and runs only once.

The test weeks are the Mondays $t$ from 2026-08-31 with $t+28$ days not later than the data date $D_2=\text{2026-11-02}$, six weeks in total; fewer than six matured weeks postpone the study rather than relax its criteria. Weekly EPSS and CISA KEV snapshots after 2026-09-21 are downloaded only after the tag, the vulnerability database is frozen once on $D_2$, and every image is rescanned with it. The predictors are HANFIS (mean of five seeds), persistence (the label of week $t-4$), a fixed blend of the two ($\lambda=0.5109$, fitted on out-of-fold predictions), and the formula. Skill scores against persistence use pooled mean squared error with a bootstrap clustered by image (2{,}000 resamples). Two families of one-sided hypotheses are tested, each with its own Holm correction at $\alpha=0.025$: whether HANFIS and the blend improve on persistence (P7a, P7b), and whether the formula improves on persistence while HANFIS is not better than the formula (P7e, P7f); the direction of predicted change is a secondary hypothesis (P7d). Rows with unresolved vulnerability-range evidence are dropped only if they amount to at most 2\% of the test-week rows, and an asset that loses all of its test weeks leaves the analysis and is reported (\texttt{cockroachdb} is expected to). The results will be added to a later version of this paper.'''
ANCHOR = "\\section{Results}\\label{sec4}"
DISC_OLD = "A forward evaluation on weeks after the protocol was frozen is planned and will be pre-registered separately."
DISC_NEW = "A forward evaluation on weeks after the protocol was frozen is pre-registered (Section~\\ref{subsec:e7}) and will be run once its labels have matured, on 2 November 2026."
LIM_OLD = "which is conservative (at most 7 days late) but not exact."
LIM_NEW = ("which is conservative (at most 7 days late) but not exact. A single CVE whose Trivy status lies outside the accepted set (for example ``under investigation'' for a freshly published Red Hat advisory) makes the whole asset-week unusable; "
           "this affected one of the 120 images for seven consecutive weeks from 2026-08-10, can reach at most the two Red Hat based images of the inventory, and removes such rows from the analysis.")
errors, edits, skipped = [], [], []
if "\\label{subsec:e7}" in s: print("sudah: sub-bagian E7")
elif s.count(ANCHOR) == 1: edits.append((s.index(ANCHOR), s.index(ANCHOR), SUB + "\n\n"))
else: errors.append(f"jangkar '\\section{{Results}}' ditemukan {s.count(ANCHOR)}x (harus 1)")
if "is pre-registered (Section~\\ref{subsec:e7})" in s: print("sudah: Discussion")
else:
    m = list(re.finditer(flex(DISC_OLD), s))
    if len(m) == 1: edits.append((m[0].start(), m[0].end(), DISC_NEW))
    else: errors.append(f"kalimat Discussion ditemukan {len(m)}x (harus 1)")
if "Red Hat advisory" in s: print("sudah: Limitations")
else:
    m = list(re.finditer(flex(LIM_OLD), s))
    if len(m) == 1: edits.append((m[0].start(), m[0].end(), LIM_NEW))
    else: skipped.append(f"kalimat Limitations ({len(m)}x)")
if errors: print("ABORT, tidak ada yang ditulis:"); [print("  -", e) for e in errors]; sys.exit(2)
if not edits: print("Sudah diterapkan seluruhnya."); sys.exit(0)
for st, en, new in sorted(edits, key=lambda t: -t[0]): s = s[:st] + new + s[en:]
shutil.copy(P, str(P) + ".pre-e7m.bak"); P.write_text(s, encoding="utf-8"); print(f"OK: {len(edits)} perubahan")
for k in skipped: print("  DILEWATI (periksa manual):", k)
