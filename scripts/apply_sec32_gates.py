#!/usr/bin/env python3
"""Patch 0069: paragraf 'System preparation...' (sec. 3.2) ditulis ulang sebagai deskripsi
prosedur gerbang; klaim lolos disandarkan pada arsip Run 7-16, bukan pada B4.10-B4.11B
(F4: PASS B4.10 tidak dapat diverifikasi ulang). Gagal-tertutup, idempoten."""
import sys, shutil, pathlib
P = pathlib.Path("manuscript/sn-article.tex")
s = P.read_text(encoding="utf-8")
if "are retained as scripts but are not used as evidence" in s:
    print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)
START = "System preparation was organised as a sequence of auditable gates."
END = "did not itself interrupt the target service.\n"
if s.count(START) != 1 or s.count(END) != 1:
    sys.exit(f"ABORT: jangkar {s.count(START)}x/{s.count(END)}x (harus 1/1)")
i, j = s.index(START), s.index(END) + len(END)
if not i < j: sys.exit("ABORT: urutan jangkar salah")
NEW = (
"System preparation was organised as a sequence of auditable gates. The gates cover the baseline workload, cluster health, the observability deployment, the measurement procedure, protocol freezing and the generation of SHA-256 manifests; the criterion applied at each gate is listed in Table~\\ref{tab1}. "
"The first gates of the protocol-development phase (O5--B4.10 to O5--B4.11B) are retained as scripts but are not used as evidence in this paper, because their original console output cannot be independently re-verified. "
"The evidence that the gates were satisfied is the set of run archives and manifests for Runs~7--16 (Section~\\ref{subsec:overhead-protocol}), in each of which both conditions were admitted only after the gate criteria held. "
"Because P0 stayed at two of two ready replicas with HTTP status 200 across every admitted transition, the change in observability state did not itself interrupt the target service.\n"
)
shutil.copy(P, str(P) + ".pre-0069.bak")
P.write_text(s[:i] + NEW + s[j:], encoding="utf-8"); print("OK")
