# CLAUDE.md: HANFIS-RESEARCH

Berkas ini dibaca otomatis oleh Claude Code di VS Code. Isinya aturan kerja yang stabil. Keadaan terkini ada di `docs/progress/` (berkas bertanggal terbaru) dan di `HANFIS_RESEARCH_MEMORY.md`.

Repo: `udahafeez7/HANFIS-RESEARCH`, cabang `research/amend-a02-a06`, lokal `/mnt/c/Research/ANFIS` (WSL Ubuntu). Bahasa kerja: Indonesia (kode, pesan komit, dan teks naskah dalam bahasa Inggris).

## 1. Mulai setiap sesi (urutan wajib)

1. Baca `SESSION_PROCEDURE.md` di akar repo bila ada.
2. Baca kepala `HANFIS_RESEARCH_MEMORY.md` (versi, tanggal), bagian 1 sampai 3 (sumber kebenaran, keputusan beku, klaim yang boleh dan tidak boleh), dan amendemen A-xx terakhir.
3. Baca berkas bertanggal terbaru di `docs/progress/`.
4. Jalankan `git status --short` dan `git --no-pager log --oneline -10`.
5. Baca pembaruan terbaru di folder `Patch/` (`ls -lt Patch | head -20`). **Bila langsung menulis atau menjalankan skrip tanpa membaca `Patch/`, tulis pemberitahuan itu di awal balasan.**
6. Bila status di memori tidak cocok dengan repo, repo yang benar. Laporkan selisihnya, jangan menebak.

## 2. Tujuan

- Naskah Q1 untuk Springer *Journal of Cloud Computing*, kirim awal Desember 2026. Judul kerja: *HANFIS: Hierarchical ANFIS for Evidence-Based Dynamic Risk Scoring of Cloud-Native Kubernetes Deployments*.
- Kode yang dapat direproduksi (repo ini), arsip Zenodo (versi 1: `10.5281/zenodo.23357118`), registrasi OSF (`10.17605/OSF.IO/AHCVS`).
- Pendanaan: Penelitian Kepakaran LPPM Universitas Andalas 2026 (pendana tidak berperan dalam desain, data, atau analisis).

## 3. Aturan keras

**Evaluasi maju E7 (D2 = Senin 2 November 2026, mulai paling cepat 07.00 WIB karena runner memakai tanggal UTC)**
- Tag beku `e7-prereg-2026-10-12` (komit `dbed812`), 23 berkas beku. Jangan ubah satu pun. Berkas beku yang ternyata cacat butuh amendemen bernomor, bukan suntingan diam-diam.
- Sebelum D2 hanya `scripts/e7_d2.py ... --dry-run` yang boleh dijalankan (`--stage fetch` ditolak penjaga tanggal dan aman). **Tidak pernah memakai `--today`.**
- `evaluate` dan `formula` berjalan sekali. Tidak ada penyetelan, pemilihan ulang, atau analisis tambahan setelah hasil terlihat. `--redo` hanya untuk `fetch`, `rescan`, `build`, `predict`.
- Jangan tarik snapshot setelah 2026-09-21, jangan hitung label forward, jangan `--download-db` sebelum D2, jangan `e7_rescan.py --resume` langsung. Ulangan rescan yang gagal di tengah: hapus berkas state `data/evidence/e7_rescan_2026-11-02.json` dengan sengaja, lalu `--stage rescan` dari awal (belum pernah diuji).
- Runbook: `protocols/E7_D2_runbook.md`. Templat teks hasil D2: `protocols/E7_results_text_templates_2026-10-14.md` (ditulis sebelum D2; pilih varian dari string `keputusan`, bukan dari preferensi).

**Klaim (pagar P11)**: tidak boleh di naskah pertama: HANFIS sebagai istilah baru (Soozanchi dkk. 2010 memakainya lebih dulu), edge/Jetson, policy enforcement, overhead kausal observabilitas, DMM, penjelasan berlapis (dicabut oleh A-43; H6c gagal). Kontribusi naskah kini C1 sampai C4 (policy layer bukan kontribusi; A-63).

**Lapisan dan dokumen (pagar P1)**: setiap usulan perubahan harus menyebut lapisan (arsitektur model, pipeline data, prosedur mutu) dan dokumen yang berubah. Tanpa itu ditolak.

**P13**: tag image unik; tanpa `apk add` pada image kontrol.

**Kejujuran akademik dan etika**
- Laporkan hasil negatif apa adanya. Jangan melonggarkan ambang setelah gagal (contoh: H6c).
- Tandai analisis post hoc sebagai post hoc, tanpa koreksi multiplisitas, dan tidak mengubah keputusan terdaftar. P7e dan P7f berasal dari analisis post hoc dan harus dinyatakan begitu. P7e yang tidak terkonfirmasi ditulis "tidak dibuktikan", bukan "tidak berbeda".
- "Pre-registered" di naskah berarti protokol bertanggal dan bertag di repo; hanya E7 yang juga terdaftar di OSF.
- Setiap angka di abstrak harus terlacak ke tabel di badan naskah. Jangan menulis sitasi dari ingatan: metadata referensi diambil dari doi.org lewat `scripts/bib_from_doi.py` dan diaudit dengan `scripts/audit_bib_dois.py` dan `scripts/bib_deep_audit.py`.
- Penggunaan AI diungkapkan di Methods ("Use of AI tools") dan Declarations; kebijakan AI Springer Nature masih harus dicocokkan (lihat handoff).
- Topik OSF sudah selesai dan tidak diangkat lagi.

## 4. Cara bekerja (metode tetap, jangan diubah-ubah)

- Setiap perubahan berkas yang dikomit lewat **skrip teks-persis yang gagal-tertutup**: teks lama harus cocok persis dan muncul tepat sekali, kalau tidak tidak ada yang ditulis; idempoten (ulangan tidak mengubah hash berkas); menyimpan cadangan `.pre-*.bak`; akhir baris (CRLF) dipertahankan. Skrip diuji dulu pada salinan: terapkan, ulangi (hash sama), urutan terbalik, CRLF, satu teks lama diubah.
- Naskah: tiga hal diperiksa identik antara teks lama dan baru kecuali yang sengaja diubah: `\cite`, `\ref`/`\label`/rumus, dan semua angka.
- Verifikasi sebelum klaim selesai: jalankan, baca keluarannya, baru nyatakan. Jangan menyatakan "selesai" tanpa keluaran terminal.
- Memori: `HANFIS_RESEARCH_MEMORY.md` hanya diperbarui lewat amendemen bernomor (A-xx) atau penutupan blocker (F-xx); jangan menimpa entri lama; naikkan versi dan tanggal di kepala; pesan komit `memory: A-xx ...`.
- Penyampaian ke pengguna: tulis **persis** apa yang harus diketik atau ditempel dan keluaran yang diharapkan. Tanpa placeholder `<...>` (bash menolaknya); masukan yang harus diisi lewat berkas atau variabel yang sudah terisi. Beri perintah lengkap (`cd`, `source`, `set +H`). Laporan dalam Word, pengingat dalam markdown (`claude_daily-plan-YYYY-MM-DD.md`).
- Jangan mengubah cara kerja ini tanpa diminta.

## 5. Perintah rutin

```bash
cd /mnt/c/Research/ANFIS
source /home/hafiz/.venvs/anfis/bin/activate
set +H
python -m pytest -q test tests                      # baseline: 126 passed, 11 subtests passed
git status --short | grep -v '^??'                  # harus kosong sebelum D2
cd manuscript
pdflatex -interaction=nonstopmode sn-article.tex >/dev/null
bibtex sn-article | tail -3
pdflatex -interaction=nonstopmode sn-article.tex >/dev/null
pdflatex -interaction=nonstopmode sn-article.tex | grep -E '^!|undefined|Overfull|Output written'
cd ..
python scripts/e7_d2.py --d2 2026-11-02 --tag e7-prereg-2026-10-12 --dry-run   # aman
```

Jangan `git add -A`. `results_python/` dan `data/` diabaikan git: pakai `git add -f` untuk berkas tertentu. Jangan menjalankan `pytest` tanpa argumen dari akar repo. Perubahan Docker atau testbed menjelang D2 dihindari (restart tak terduga memutus bind-mount Prometheus pada 8 dan 15 Oktober).

## 6. Peta berkas

| Jalur | Isi |
|---|---|
| `manuscript/sn-article.tex`, `sn-bibliography.bib` | Naskah (gaya `sn-basic`, opsi `referee` dan `lineno`) dan bibliografi |
| `protocols/` | Protokol beku E7, runbook D2, catatan analisis Run 17, templat teks hasil |
| `scripts/` | Pipeline (`e7_*.py`, `fetch_snapshots.py`, `build_asset_weeks.py`), analisis post hoc (`e8` sampai `e24`), skrip penerap `apply_*.py`, audit bibliografi |
| `python_hanfis/` | Model dan pembagian data |
| `configs/assets.csv` | 120 aset (119 grup image); `assets_v3.csv` dibuat tahap `rescan` D2, bukan berkas beku |
| `data/evidence/`, `data/real/snapshots/` | Bukti Trivy dan snapshot EPSS/KEV bersegel (diabaikan git) |
| `results_python/` | Hasil eksperimen (diabaikan git) |
| `HANFIS_RESEARCH_MEMORY.md` | Memori proyek (sumber status) |
| `docs/progress/` | Handoff dan laporan harian |
