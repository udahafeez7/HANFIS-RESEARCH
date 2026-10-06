#!/usr/bin/env python3
"""Tambah A-41 (analisis rezim post hoc) setelah A-40 di HANFIS_RESEARCH_MEMORY.md, peta komit 2, dan koreksi 'Wang 1999' -> 'Wang 1998'
(hanya bila tepat 1x; kalau tidak, hanya peringatan). Gagal-tertutup untuk A-40/A-41. Idempoten. Tidak menimpa baris lain."""
import sys, shutil, pathlib
P = pathlib.Path("HANFIS_RESEARCH_MEMORY.md"); lines = P.read_text(encoding="utf-8").split("\n")
if any(l.startswith("| A-41 |") for l in lines): print("A-41 sudah ada; tidak ada perubahan."); sys.exit(0)
idx = [i for i, l in enumerate(lines) if l.startswith("| A-40 |")]
if len(idx) != 1: sys.exit(f"ABORT: baris A-40 ditemukan {len(idx)}x (harus 1)")
i = idx[0]
if i + 1 < len(lines) and lines[i + 1].startswith("| A-"): sys.exit("ABORT: ada amendemen setelah A-40")
A41 = ("| A-41 | 2026-10-06 | Analisis eksploratori + Naskah (abstrak, sec. 4.5, Limitations, Conclusion) | Analisis POST HOC (bukan praregistrasi) atas prediksi E4 penuh dan pra-EPSS "
       "(`scripts/e4_influence.py`, `scripts/e4_regime.py`; hasil `results_python/e4_influence*` dan `e4_regime*`; komit 7f4a0eb). Pemeriksa mereproduksi SS E4 persis "
       "(persistence 0,0146; ridge-7 0,6961; CVSS 0,9674; matched 0,6654; flat 0,2527). Temuan: (1) SS vs persistence bergantung pada fold 3 (buang fold 3: -1,168; fold lain 0,007-0,172); "
       "dalam jendela label tak cocok setelah pergantian EPSS (2026-W24..W27, 95 baris) SS +0,483, di luarnya (985 baris) -0,420; keunggulan agregat +6,5 = +104,1 (jendela) -97,6 (lainnya); "
       "matched ikut beradaptasi (W25/W26: 4,8 dan 5,2 vs persistence 63,1 dan 28,9), jadi efeknya akses ke input EPSS terkini, bukan struktur hierarki; HANFIS reaktif, bukan prediktif. "
       "(2) H2: fold 0 (2,2 obs/parameter) menyumbang 91% selisih ke matched; tanpa fold 0 SS vs matched 0,183, vs flat penuh 0,084; ridge stabil 0,656-0,793 (H1c kuat). "
       "(3) Gerbang >=10 obs/parameter hanya dipenuhi pada total, tidak pada fold 0-1 (2,2; 7,1; pra-EPSS fold 0-2: 2,2; 5,5; 8,7). "
       "Naskah: abstrak menyebut H1b 'unconfirmed rather than a tie'; klaim 'bukan artefak pelatihan' untuk H2 dilunakkan; kalimat spekulatif sec. 4.5 diganti MSE nyata "
       "(matched 1,22 -> 3,77; HANFIS 0,41 -> 0,33). Status konfirmasi H1a/H1c/H2/H1b TIDAK berubah. Hipotesis baru (HANFIS sebagai koreksi di atas persistence; kurva belajar terhadap ukuran data latih) "
       "HARUS dipraregistrasi sebelum dijalankan |")
lines.insert(i + 1, A41); out = "\n".join(lines)
TAG = "## Peta komit lanjutan 2 (2026-10-06)"
if TAG not in out:
    out = out.rstrip("\n") + f"""

{TAG}

| Komit | Isi |
|---|---|
| 00ba12b | memory: v2.20, A-40 |
| 5b54560 | chore: skrip tambalan lama diarsipkan ke `scripts/applied/` |
| 97f7c31, 62bdb4a | bib: nist_zta_cloudnative_2023 = NIST SP 800-207A (entri ditulis dari ingatan; Crossref: OK), penanda VERIFY dihapus |
| 0f3826c | bib: DOI raju1991 dan wang1998 dikoreksi (dicocokkan Crossref), DOI ojha/lee ditambah, tanggal akses entri web; `check_bib_crossref.py`, `search_crossref.py` |
| 7f4a0eb | manuscript: analisis rezim post hoc (A-41); `e4_influence.py`, `e4_regime.py` |

Tag: `m2-gate-e3-checklist-pass-20261006` menunjuk c44d246; `m2-close-manuscript-clean-20261006` menunjuk 00ba12b (sebelum perbaikan bibliografi dan analisis rezim). Keadaan akhir sesi: PDF 26 halaman, 126 passed + 11 subtests.
Koreksi: tahun Wang (universal approximation by hierarchical fuzzy systems, Fuzzy Sets and Systems 93) = 1998 menurut Crossref; "Wang 1999" di catatan lama salah.
Terbuka: selisih Fuzzyfortify paper vs kode (butuh `public/js/scripts2.js` aplikasi web asli); sumber Soozanchi dkk.; praregistrasi hipotesis baru sebelum dijalankan.
"""
note = ""
n = out.count("Wang 1999:**")
if n == 1: out = out.replace("Wang 1999:**", "Wang 1998:**"); note = "; 'Wang 1999' -> 'Wang 1998'"
else: print(f"PERINGATAN: 'Wang 1999:**' ditemukan {n}x; tidak diubah (ubah manual bila perlu)")
shutil.copy(P, str(P) + ".pre-a41.bak"); P.write_text(out, encoding="utf-8"); print("OK: A-41 ditambahkan" + note)
