# Rencana harian HANFIS: Rabu 4 November 2026

Disusun 3 November 2026 dari keadaan repositori (memori v2.60, A-80). Pengingat ini hanya berisi pekerjaan yang masih terbuka. Perintah ditulis lengkap; semuanya hanya membaca kecuali yang tertulis lain.

## Keadaan singkat

- Evaluasi maju E7 selesai dan terkunci (tag `e7-results-2026-11-02`). Naskah memuat hasilnya, 48 halaman format referee, Additional file 1 13 halaman.
- Prometheus v4.1 merekam sejak 3 November 09.25 WIB. Pemeriksa kesehatan berjalan sebagai timer pengguna.
- Zenodo versi baru ditunda.
- Berkas naskah terbaru: `docs/progress/sn-article_2026-11-03.pdf`.

## Urutan kerja

| Urutan | Pekerjaan | Keluaran yang diharapkan |
|---|---|---|
| 1 | Baca ulang naskah utuh | Daftar kalimat janggal, dikirim sebagai pasangan teks lama dan teks baru |
| 2 | Cocokkan kebijakan AI Springer Nature dengan Methods ("Use of AI tools") dan Declarations | Catatan cocok atau tidak cocok |
| 3 | Audit bibliografi | Tabel status per entri; selisih diperiksa manual |
| 4 | Periksa asal peringatan Overfull baris 407 | Penyebab dan perlu atau tidaknya diperbaiki |
| 5 | Putuskan apakah rubrik MFA (x4) perlu dikonfirmasi | Bila ya, kalimat di subbagian 3.5 dipertegas |

## 0. Cek cepat keadaan (3 perintah, hanya membaca)

```bash
cd /mnt/c/Research/ANFIS
source /home/hafiz/.venvs/anfis/bin/activate
set +H
git status --short | grep -v '^??'
git --no-pager log --oneline -3
journalctl --user -u hanfis-prometheus-watch.service -n 2 --no-pager
```

Harapan: `git status` kosong; tiga komit terbaru; baris terakhir jurnal berisi `PROM_OK targets=2`. Bila `PROM_UNREACHABLE` atau `PROM_DEGRADED`, kirim keluarannya; jangan menyalakan ulang Docker sendiri.

## 3. Audit bibliografi (butuh jaringan, tidak mengubah berkas .bib)

```bash
cd /mnt/c/Research/ANFIS
source /home/hafiz/.venvs/anfis/bin/activate
set +H
python scripts/audit_bib_dois.py
python scripts/bib_deep_audit.py
```

Harapan: tabel di layar dengan status `OK`, `PERIKSA`, `TIDAK_DITEMUKAN`, `TANPA_DOI`; CSV di `results_python/bib_audit/`. Kirim baris yang bukan `OK`. Keputusan akhir ada pada Anda: selisih bisa berasal dari BibTeX atau dari metadata.

## 4. Kompilasi untuk memeriksa Overfull

```bash
cd /mnt/c/Research/ANFIS/manuscript
pdflatex -interaction=nonstopmode sn-article.tex >/dev/null
bibtex sn-article | tail -3
pdflatex -interaction=nonstopmode sn-article.tex >/dev/null
pdflatex -interaction=nonstopmode sn-article.tex | grep -E '^!|undefined|Overfull|Output written'
```

Harapan: satu baris `Overfull \hbox (6.05336pt too wide) ... lines 407--407` dan `Output written on sn-article.pdf (48 pages ...)`. Tidak boleh ada baris yang diawali `!` atau kata `undefined`. Additional file 1 dikompilasi setelah naskah (butuh `sn-article.aux`):

```bash
cd /mnt/c/Research/ANFIS/manuscript
pdflatex -interaction=nonstopmode additional_file_1.tex >/dev/null
pdflatex -interaction=nonstopmode additional_file_1.tex | grep -E '^!|undefined|Output written'
```

Harapan: `Output written on additional_file_1.pdf (13 pages ...)`.

## Aturan yang tetap berlaku

- Tidak ada analisis tambahan atau penyetelan atas hasil E7; tanpa `--today`; `evaluate` dan `formula` tidak diulang.
- Berkas beku E7 (23 berkas, tag `e7-prereg-2026-10-12`) tidak diubah.
- Perubahan naskah yang dikomit lewat skrip teks-persis yang gagal-tertutup dan diuji di salinan.
- Jangan `git add -A`.

---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) dari keadaan repositori pada 3 November 2026.
