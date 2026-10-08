#!/usr/bin/env python3
"""Perbaikan Limitations: (1) \\label kembali tepat setelah \\subsection{Limitations}; (2) dua kalimat bernada catatan revisi ('is now complete', 'has since been re-run',
'earlier, partial inventory', 'pilot') ditulis ulang sebagai pernyataan keadaan akhir. Jangkar toleran terhadap pemotongan baris; gagal-tertutup (R1 dan R2 harus cocok
tepat satu kali, panjang cocokan dibatasi); idempoten; cadangan .pre-limfix.bak. Jalankan dari akar repo."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8"); orig = s
R1 = (r"The\s+full\s+inventory\s+of\s+120\s+assets\s+is\s+now\s+complete,.{0,400}?earlier,\s+partial\s+inventory\.",
      r"The confirmatory comparison (Table~\ref{tab:e4-results}) uses the full 120-asset inventory.")
R2 = (r"The\s+mandatory-baseline\s+comparison\s+in\s+Table~\\ref\{tab:e3-baselines\}\s+has\s+since\s+been\s+re-run.{0,900}?comparatively\s+safe\.",
      r"On the full 120-asset inventory (6{,}357 labelled rows; Table~\ref{tab:e3-baselines}), a linear ridge model over all seven inputs underperforms persistence on every one of the five "
      r"grouped-temporal folds ($\mathrm{SS}_{\mathrm{pers}}=-2.293$ pooled, raw scale); we suspect that the linear model over-extrapolates as the inventory's heterogeneity grows, "
      r"where persistence's week-to-week copy remains comparatively safe, but we did not test this explanation.")
errors, notes = [], []
for name, (pat, new) in (("R1-inventaris", R1), ("R2-baseline", R2)):
    m = list(re.finditer(pat, s, re.S))
    if len(m) == 1: s = s[:m[0].start()] + new + s[m[0].end():]; notes.append(f"diterapkan: {name} ({m[0].end() - m[0].start()} karakter diganti)")
    elif len(m) == 0 and new.split()[0:6] and new[:60] in s: notes.append(f"sudah: {name}")
    else: errors.append(f"{name}: cocok {len(m)}x (harus 1)")
pat = re.compile(r"(\\subsection\{Limitations\}\n)(Two limits of construct validity[^\n]*\n)(\\label\{[^}]+\}\n)")
mm = list(pat.finditer(s))
if len(mm) == 1: s = pat.sub(lambda m: m.group(1) + m.group(3) + m.group(2), s, count=1); notes.append("diterapkan: \\label dipindah tepat setelah \\subsection{Limitations}")
else: notes.append("label: tidak ada yang perlu dipindah" if not errors else "label: dilewati")
if errors: print("ABORT, tidak ada yang ditulis:"); [print("  -", e) for e in errors]; sys.exit(2)
if s == orig: print("\n".join(notes)); print("Tidak ada perubahan."); sys.exit(0)
shutil.copy(P, str(P) + ".pre-limfix.bak"); P.write_text(s, encoding="utf-8"); print("\n".join(notes)); print("OK")
