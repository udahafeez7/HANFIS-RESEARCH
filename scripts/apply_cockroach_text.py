#!/usr/bin/env python3
"""Amandemen aturan INSUFFICIENT_EVIDENCE (protokol bagian 2) dan teks OSF (opsi C): aturan 'tidak boleh ada aset yang kehilangan seluruh minggu ujinya' dihapus; yang berlaku hanya batas 2% atas baris minggu uji (aset yang kehilangan semua minggu ujinya otomatis keluar dan dilaporkan); Menyatakan fakta bahwa `cockroachdb` memiliki bukti rentang versi tidak cukup pada 2026-08-10 .. 2026-09-21 (7 minggu berurutan). Aturan 2% atas baris minggu uji tidak berubah.
Jangkar wajib tepat sekali; idempoten; cadangan .pre-cock.bak.  python scripts/apply_cockroach_text.py [--protocol ...] [--osf ...]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--protocol", default="protocols/E7_preregistration_CANDIDATE.md"); ap.add_argument("--osf", default="protocols/E7_osf_registration_DRAFT.md"); a = ap.parse_args()
flex = lambda t: r"\s+".join(map(re.escape, t.split()))
JOBS = [(a.protocol, "hanya dipakai bila baris yang dibuang <= 2% dari baris minggu uji dan tidak ada aset yang kehilangan seluruh minggu ujinya; tiap baris yang dibuang dilaporkan per `asset_id`.",
         "hanya dipakai bila baris yang dibuang pada minggu uji <= 2% dari baris minggu uji; aset yang kehilangan seluruh minggu ujinya otomatis keluar dari analisis forward (ia tidak memiliki baris uji) dan dilaporkan; tiap baris yang dibuang dilaporkan per `asset_id`. Pada inventaris saat ini `cockroachdb` memiliki bukti rentang versi tidak cukup pada tujuh minggu berurutan, 2026-08-10 sampai 2026-09-21, dan diperkirakan keluar; pada 720 baris uji (120 aset x 6 minggu) batas 2% berarti paling banyak 14 baris, yaitu dua aset penuh.", "otomatis keluar dari analisis forward (ia tidak memiliki baris uji)", "replace"),
        (a.osf, "Weeks without a complete snapshot sequence; weeks after a change of EPSS model version are analysed separately as a break regime.",
         " Rows with unresolved vulnerability-range evidence (INSUFFICIENT_EVIDENCE) are dropped only if they are at most 2% of test-week rows; an asset that loses all of its test weeks leaves the forward analysis (it has no test rows) and is reported. At registration, `cockroachdb` has unresolved evidence for seven consecutive weeks (2026-08-10 to 2026-09-21) and is expected to leave. Beyond the 2% limit the analysis is put on hold.", "leaves the forward analysis (it has no test rows)", "append")]
plans = []
for path, anchor, text, marker, mode in JOBS:
    p = Path(path)
    if not p.exists(): print(f"DILEWATI (berkas tidak ada): {path}"); continue
    s = p.read_text(encoding="utf-8")
    if marker in s: print(f"sudah diterapkan: {path}"); continue
    m = list(re.finditer(flex(anchor), s))
    if len(m) != 1: print(f"ABORT, tidak ada yang ditulis: jangkar di {path} ditemukan {len(m)}x (harus 1)"); sys.exit(2)
    plans.append((p, s[:m[0].start()] + text + s[m[0].end():] if mode == "replace" else s[:m[0].end()] + text + s[m[0].end():]))
for p, new in plans: shutil.copy(p, str(p) + ".pre-cock.bak"); p.write_text(new, encoding="utf-8"); print(f"OK: {p}")
