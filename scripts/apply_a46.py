#!/usr/bin/env python3
"""A-46: (1) tambah bagian amendemen di protocols/E7_preregistration_DRAFT.md, (2) tambah baris A-46 di HANFIS_RESEARCH_MEMORY.md (setelah A-45). Dari akar repo.
Gagal-tertutup bila A-45 tidak ada tepat satu kali (tidak ada yang ditulis); idempoten; cadangan .pre-a46.bak."""
import re, shutil, sys
from pathlib import Path
D = Path("protocols/E7_preregistration_DRAFT.md"); M = Path("HANFIS_RESEARCH_MEMORY.md")
HEAD = "## Amendemen A-46 (2026-10-08): metrik utilitas dan keterbatasan daya, setelah latihan kode"
SECTION = HEAD + """

Latihan kode `e7_evaluate.py --rehearsal` pada 1.080 baris out-of-fold E4 (**bukan data E7**; lambda dipasang pada baris yang sama) memberi tiga pelajaran, dicatat sebelum pembekuan:

1. **Efek langit-langit pada P7c (level).** Persistence mencapai presisi@20% = 0,969 karena perbedaan antar-asset yang stabil mendominasi label; hibrida 0,889 (selisih -0,080, CI95 [-0,299; -0,020]).
   Margin non-inferioritas -0,05 hampir pasti gagal di E7 bukan karena kualitas hibrida, tetapi karena metrik level tidak mengukur kontribusi dinamis. **P7c (level) diturunkan menjadi deskriptif.**
2. **P7d (utilitas, menggantikan P7c sebagai kriteria utilitas): informasi tambahan di atas persistence.** Rerata mingguan korelasi Spearman antara perubahan prediksi (`y_hanfis - y_lag4`)
   dan perubahan nyata (`y_true - y_lag4`), minggu dengan >= 5 asset. Kriteria: batas bawah CI95 bootstrap berkelompok per image > 0. Sekunder, tanpa koreksi multiplisitas. Hibrida memiliki Spearman perubahan
   identik dengan HANFIS (lambda > 0), sehingga tidak dilaporkan terpisah; ridge-7 dilaporkan sebagai pembanding.
3. **Daya terbatas.** Pada OOF, SS_hibrida = 0,174 dengan CI95 [0,011; 0,236] dan p Holm 0,021 (> ambang 0,0125): P7b gagal pada ambang Holm walaupun batas bawah CI > 0; P7a CI95 [-0,642; 0,241].
   Data forward lebih sedikit (6 minggu x sekitar 120 image). **Aturan keputusan P7a dan P7b tidak diubah karena rehearsal** (Holm dipertahankan). E7 dilaporkan sebagai estimasi prospektif dengan CI;
   hasil "tidak terbukti" bukan bukti kesetaraan.

Perubahan nomor 1 dan 2 didasarkan pada data E4, bukan data forward; data forward belum disentuh.
"""
ROW = ("| A-46 | 2026-10-08 | Eksperimen E7 | Setelah latihan kode (rehearsal) pada prediksi OOF E4: P7c (presisi@20% pada level) diturunkan menjadi deskriptif karena efek langit-langit (persistence 0,969; hibrida -0,080) "
       "dan diganti P7d = rerata mingguan Spearman antara perubahan prediksi dan perubahan nyata terhadap y_lag4, kriteria batas bawah CI95 > 0; daya terbatas P7a dan P7b dinyatakan, aturan Holm tidak diubah karena rehearsal; "
       "`scripts/e7_evaluate.py` diperbarui. Audit E4: tag `e4-prereg-2026-09-29` dibuat 2026-09-30 11:35 +0700 (komit protokol 7b09a4b 11:32 +0700) dan `verify_prereg_tag.py` LOLOS; "
       "gerbang `e4bis-gate-training-authorized-20261002` 17:28 +0700, sekitar 10 menit sebelum run E4-bis pertama. |")
if not D.exists(): sys.exit(f"ABORT: {D} tidak ada")
d = D.read_text(encoding="utf-8"); m_ = M.read_text(encoding="utf-8")
if HEAD in d and re.search(r"^\| A-46 \|", m_, re.M): print("A-46 sudah ada; tidak ada perubahan."); sys.exit(0)
a45 = list(re.finditer(r"^\| A-45 \|.*$", m_, re.M))
if len(a45) != 1 and not re.search(r"^\| A-46 \|", m_, re.M): sys.exit(f"ABORT: baris A-45 ditemukan {len(a45)}x (harus 1); tidak ada yang ditulis")
if HEAD not in d: shutil.copy(D, str(D) + ".pre-a46.bak"); D.write_text(d.rstrip("\n") + "\n\n" + SECTION, encoding="utf-8"); print("OK: bagian A-46 ditambahkan ke draf E7")
if not re.search(r"^\| A-46 \|", m_, re.M):
    m_ = m_[:a45[0].end()] + "\n" + ROW + m_[a45[0].end():]
    h = re.search(r"Versi: (\d+)\.(\d+) · Tanggal: \d{4}-\d{2}-\d{2}", m_)
    if h: m_ = m_.replace(h.group(0), f"Versi: {h.group(1)}.{int(h.group(2)) + 1} · Tanggal: 2026-10-08", 1)
    shutil.copy(M, str(M) + ".pre-a46.bak"); M.write_text(m_, encoding="utf-8"); print("OK: A-46 ditambahkan ke memori repo")
