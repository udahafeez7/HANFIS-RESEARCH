#!/usr/bin/env python3
"""Opsi 3 (dua keluarga Holm terpisah): {P7a, P7b} dan {P7e, P7f}. Mengubah protokol (bagian 5 dan 6) dan teks OSF: P7e dan P7f menjadi keluarga KEDUA dengan Holm sendiri (bukan 'sekunder tanpa koreksi'),
menambah angka daya historis (E13) dan keterbatasan ketergantungan antar minggu. Tidak mengubah P7a, P7b, P7d, ambang keluarga pertama, atau angka mana pun. Gagal-tertutup (semua jangkar wajib tepat sekali), idempoten,
cadangan .pre-opt3.bak.  python scripts/apply_option3.py [--protocol protocols/E7_preregistration_CANDIDATE.md] [--osf protocols/E7_osf_registration_DRAFT.md]"""
import argparse, re, shutil, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--protocol", default="protocols/E7_preregistration_CANDIDATE.md"); ap.add_argument("--osf", default="protocols/E7_osf_registration_DRAFT.md"); a = ap.parse_args()
flex = lambda t: r"\s+".join(map(re.escape, t.split()))
PROT = [
 ("**Hipotesis sekunder tambahan (rumus bentuk-maks; sumber post hoc; tanpa koreksi multiplisitas; di luar keluarga Holm {P7a, P7b}).** Metrik, bootstrap (berkelompok per image, 2.000 resampel, seed 20261102), populasi baris, dan SESOI 0,05 identik dengan P7a dan P7b.",
  "**Keluarga kedua (rumus bentuk-maks; asal post hoc; didaftarkan sebelum data forward).** {P7e, P7f} dikoreksi dengan Holm di dalam keluarganya sendiri (alpha satu sisi 0,025; ambang 0,0125 untuk p terkecil dan 0,025 untuk berikutnya; p satu sisi dari bootstrap dengan +1), terpisah dari keluarga pertama {P7a, P7b}. Kedua keluarga menjawab pertanyaan yang berbeda (HANFIS terhadap persistence; rumus sederhana terhadap persistence dan terhadap HANFIS), sehingga kesalahan tipe I dikendalikan per keluarga; gabungan satu sisi paling banyak 0,05 (Bonferroni atas dua keluarga). Metrik, bootstrap (berkelompok per image, 2.000 resampel, seed 20261102), populasi baris, dan SESOI 0,05 identik dengan keluarga pertama. P7d tetap sekunder tanpa koreksi. Sebagai analisis sensitivitas tanpa kriteria, P7e dan P7f juga dilaporkan dengan bootstrap per minggu."),
 ("TERKONFIRMASI bila `SS(rumus terhadap persistence) >= 0,05` dan batas bawah CI95 > 0; LEBIH BURUK", "TERKONFIRMASI bila `SS(rumus terhadap persistence) >= 0,05`, batas bawah CI95 > 0, dan lolos Holm (keluarga kedua); LEBIH BURUK"),
 ("DIDUKUNG bila batas atas CI95 dari `SS(HANFIS terhadap rumus)` < 0,05; DIBANTAH", "DIDUKUNG bila batas atas CI95 dari `SS(HANFIS terhadap rumus)` < 0,05 dan lolos Holm (keluarga kedua); DIBANTAH"),
 ("**Daya P7e dan P7f.** Keduanya mewarisi keterbatasan daya enam minggu dan ekor berat yang sama; hasil TIDAK TERBUKTI atau TIDAK TERKONFIRMASI tidak boleh dibaca sebagai kesetaraan.",
  "**Daya P7e dan P7f.** Keduanya mewarisi keterbatasan daya enam minggu dan ekor berat yang sama; hasil TIDAK TERBUKTI atau TIDAK TERKONFIRMASI tidak boleh dibaca sebagai kesetaraan. Pada 40 jendela enam minggu historis dari prediksi out-of-fold (E13, post hoc; jendela saling tumpang tindih), P7e memenuhi kriterianya di sekitar 35% jendela dan P7f di sekitar 72% sampai 78%, P7a di sekitar 38% dan P7b di sekitar 28% sampai 30%; hasil TIDAK TERKONFIRMASI pada P7e karena itu sering diperkirakan dan tidak boleh dibaca sebagai penolakan rumus.\n- **Ketergantungan antar minggu.** Bootstrap berkelompok per image memperlakukan guncangan mingguan yang dialami semua image (misalnya perubahan skor EPSS) sebagai tetap; dengan enam minggu, jumlah titik waktu efektif adalah enam dan CI dapat terlalu sempit. Perbandingan kemampuan prediksi pada deret waktu biasanya memperhitungkan ketergantungan ini; bootstrap per minggu dilaporkan sebagai sensitivitas, tanpa kriteria."),
]
OSF = [
 ("- **P7e (secondary; post hoc origin).**", "- **P7e (second family; post hoc origin).**"),
 ("- **P7f (secondary; post hoc origin).**", "- **P7f (second family; post hoc origin).**"),
 ("P7e and P7f are secondary, are reported with their confidence intervals, and are not part of the Holm family.",
  "P7e and P7f form a second family with its own Holm correction (one-sided alpha 0.025; thresholds 0.0125 and 0.025), controlled separately from {P7a, P7b} because the two families answer different questions; the combined one-sided error is at most 0.05. A week-level cluster bootstrap is reported as a sensitivity analysis without criteria."),
 ("Results that are not significant will be reported as not demonstrated, not as equivalence.",
  "Results that are not significant will be reported as not demonstrated, not as equivalence. On historical six-week windows of out-of-fold predictions (post hoc, overlapping windows), the formula's advantage over persistence met its criterion in about one third of windows, so a non-confirmation of P7e must not be read as a refutation. The image-clustered bootstrap treats weekly shocks shared by all images as fixed; with six weeks the effective number of time points is six."),
]
def plan(path, items, marker):
    p = Path(path)
    if not p.exists(): return p, None, [f"{path}: berkas tidak ada"]
    s = p.read_text(encoding="utf-8")
    if marker in s: return p, s, ["__sudah__"]
    edits, errs = [], []
    for old, new in items:
        m = list(re.finditer(flex(old), s))
        if len(m) != 1: errs.append(f"{path}: jangkar '{old[:55]}...' ditemukan {len(m)}x (harus 1)"); continue
        edits.append((m[0].start(), m[0].end(), new))
    return p, (s, edits), errs
results = [plan(a.protocol, PROT, "Keluarga kedua (rumus"), plan(a.osf, OSF, "(second family; post hoc origin)")]
errors = [e for _, _, errs in results for e in errs if e != "__sudah__" and not e.endswith("tidak ada")]
missing_osf = [e for _, _, errs in results for e in errs if e.endswith("tidak ada")]
if errors or (missing_osf and Path(a.protocol).exists() is False): print("ABORT, tidak ada yang ditulis:"); [print("  -", e) for e in errors + missing_osf]; sys.exit(2)
for p, data, errs in results:
    if errs == ["__sudah__"]: print(f"sudah diterapkan: {p}"); continue
    if data is None: print(f"DILEWATI (periksa manual): {errs[0]}"); continue
    s, edits = data
    for st, en, new in sorted(edits, key=lambda t: -t[0]): s = s[:st] + new + s[en:]
    shutil.copy(p, str(p) + ".pre-opt3.bak"); p.write_text(s, encoding="utf-8"); print(f"OK: {len(edits)} perubahan di {p}")
