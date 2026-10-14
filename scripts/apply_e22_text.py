#!/usr/bin/env python3
r"""Memperbarui subbagian E21 di manuscript/sn-article.tex dengan hasil E22 (bootstrap per minggu, post hoc) dan MENGOREKSI kalimat penutup E21 ("a bootstrap clustered by week would give wider intervals"), yang dibantah E22.
Gagal-tertutup: kalimat lama harus ada tepat sekali; tidak ada yang ditulis bila tidak. Idempoten (penanda E22 sudah ada -> tidak berubah). Cadangan .pre-e22.bak.   python scripts/apply_e22_text.py [--tex manuscript/sn-article.tex]"""
import argparse, shutil, sys
from pathlib import Path
OLD = r"The intervals resample images and treat weekly shocks shared by all images as fixed, so a bootstrap clustered by week would give wider intervals; we read the results as descriptive."
NEW = (r"The intervals above resample images and treat the weekly shocks shared by all images as fixed. A bootstrap clustered by week (E22, post hoc; 45 weeks, 37 of them unaffected by the model change) gives narrower intervals for these statistics, not wider ones: for HANFIS the slope is $1.025$ ($1.015$ to $1.035$) on all rows and $1.031$ ($1.020$ to $1.042$) on unaffected rows, and the intercept $-0.115$ ($-0.189$ to $-0.037$) and $-0.193$ ($-0.242$ to $-0.147$). "
       r"To compare predictors we took the distance from the ideal value ($\beta=1$, $\alpha=0$, mean error $0$) and subtracted that of the formula from that of HANFIS, so that a positive number means HANFIS is further away. For the slope the excess is $0.023$ ($0.011$ to $0.033$) on all rows and $0.031$ ($0.018$ to $0.042$) on unaffected rows; with intervals clustered by image the first is $0.023$ ($0.001$ to $0.041$), a borderline result. "
       r"The excess in the intercept and in the mean error includes zero on all rows ($0.068$, $-0.072$ to $0.179$, and $-0.024$, $-0.061$ to $0.061$; week-clustered) but is positive on unaffected rows ($0.182$, $0.131$ to $0.230$, and $0.055$, $0.034$ to $0.068$). Against persistence the picture on unaffected rows is the same (slope $0.028$, intercept $0.167$, mean error $0.053$; all intervals above zero). "
       r"We read the miscalibration of HANFIS as small but consistent where the model change does not interfere, and as descriptive.")
ap = argparse.ArgumentParser(); ap.add_argument("--tex", default="manuscript/sn-article.tex"); a = ap.parse_args()
P = Path(a.tex); s = P.read_text(encoding="utf-8")
if "(E22, post hoc; 45 weeks" in s: print("Tidak ada perubahan (hasil E22 sudah ada)."); sys.exit(0)
n = s.count(OLD)
if n != 1: sys.exit(f"ABORT, tidak ada yang ditulis: kalimat lama E21 ditemukan {n}x (harus 1)")
shutil.copy(P, str(P) + ".pre-e22.bak"); P.write_text(s.replace(OLD, NEW, 1), encoding="utf-8"); print("OK: kalimat E21 dikoreksi dan hasil E22 ditambahkan")
