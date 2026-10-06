#!/usr/bin/env python3
"""Ganti placeholder nist_zta_cloudnative_2023 (tercetak 'NEEDS INPUT' di PDF) dengan entri kandidat
NIST SP 800-207A, format sama dengan nist_zta_2020. KANDIDAT: harus diverifikasi di csrc.nist.gov.
Gagal-tertutup: kunci tepat 1x dan blok memuat 'NEEDS INPUT'. Idempoten."""
import sys, shutil, pathlib
P = pathlib.Path("manuscript/sn-bibliography.bib")
s = P.read_text(encoding="utf-8")
KEY = "@misc{nist_zta_cloudnative_2023,"
if "number      = {800-207A}" in s:
    print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
if s.count(KEY) != 1: sys.exit(f"ABORT: kunci ditemukan {s.count(KEY)}x (harus 1)")
i = s.index(KEY); j = s.index("\n}", i) + 2
if "NEEDS INPUT" not in s[i:j]: sys.exit("ABORT: blok tidak berisi placeholder 'NEEDS INPUT'")
NEW = ("% VERIFY at csrc.nist.gov (title, authors, number, year) before submission; entry written from memory, not from a database.\n"
       "@techreport{nist_zta_cloudnative_2023,\n"
       "  author      = {Chandramouli, Ramaswamy and Butcher, Zack},\n"
       "  title       = {A Zero Trust Architecture Model for Access Control in Cloud-Native Applications in Multi-Location Environments},\n"
       "  institution = {National Institute of Standards and Technology},\n"
       "  type        = {NIST Special Publication},\n"
       "  number      = {800-207A},\n"
       "  year        = {2023},\n"
       "  doi         = {10.6028/NIST.SP.800-207A}\n"
       "}")
shutil.copy(P, str(P) + ".pre-nist.bak")
P.write_text(s[:i] + NEW + s[j:], encoding="utf-8"); print("OK")
