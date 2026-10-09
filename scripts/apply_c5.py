#!/usr/bin/env python3
"""Tambal C5 (Pendahuluan): sebut pembanding informasi-minimal dan ablasi label-ingredient (post hoc, Sec. subsec:e9) pada daftar kontribusi. Hanya C5; C1-C4 tidak disentuh.
Jangkar fleksibel terhadap pemisah baris; gagal-tertutup (tepat 1 kecocokan); idempoten; cadangan .pre-c5.bak. Dari akar repo."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
flex = lambda t: r"\s+".join(map(re.escape, t.split()))
OLD = "baselines (full and parameter-matched) using predictive and computational metrics"
NEW = ("baselines (full and parameter-matched), complemented by post hoc information-minimal baselines and an ablation of the label-ingredient inputs (Section~\\ref{subsec:e9}), "
       "using predictive and computational metrics")
if "complemented by post hoc information-minimal baselines" in s: print("Sudah diterapkan."); sys.exit(0)
m = list(re.finditer(flex(OLD), s))
if len(m) != 1: print(f"ABORT: jangkar C5 ditemukan {len(m)}x (harus 1); tidak ada yang ditulis"); sys.exit(2)
shutil.copy(P, str(P) + ".pre-c5.bak"); P.write_text(s[:m[0].start()] + NEW + s[m[0].end():], encoding="utf-8"); print("OK: C5 diperbarui")
