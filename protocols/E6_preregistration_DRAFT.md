# Praregistrasi E6 — Kesetiaan penjelasan HANFIS (DRAFT)

> **STATUS: DRAFT untuk ditinjau peneliti. BELUM dibekukan.**
> Butir bertanda **[PUTUSKAN]** adalah usulan, bukan keputusan. Ubah atau setujui, lalu bekukan dengan tag git
> `e6-prereg-<tanggal>`. Setelah dibekukan, perubahan hanya lewat amendemen bernomor di `HANFIS_RESEARCH_MEMORY.md`
> (nomor usulan: A-43), tidak dengan menyunting berkas ini.

## Mengapa E6 ada

Memori §3 membolehkan klaim "penjelasan berlapis (jejak, masking, permukaan)" pada naskah pertama. A-08 baru mencatat
kodenya (`rule_trace`, `pair_surface`); tidak ada uji masking dan uji kesetiaan. Klaim itu **hanya** masuk naskah bila E6
lulus. Bila tidak lulus, klaim dihapus dan dilaporkan sebagai batasan.

## Batasan yang dinyatakan sejak awal

Kontrol positif P0-IF memeriksa **implementasi** (apakah alatnya bekerja), bukan **kebenaran kausal** penjelasan.
Pada pasangan ON/OFF hanya satu masukan yang berbeda, sehingga atribusi yang masuk akal akan lulus hampir pasti.
Karena itu bobot pembuktian terletak pada uji penghapusan (H6c) pada seluruh baris uji, bukan pada H6a-H6b.

## Data dan model (beku dari E4-bis; tanpa pelatihan ulang)

- Tabel: `data/processed/asset_weeks_v2_120assets_e4bis.csv`. Model: `results_python/e4bis_120_models/` (5 fold x 5 seed).
- Kode: `python_hanfis/hanfis_end2end.py` (`rule_trace`), `scripts/e4_pdp.py`. Skrip baru `scripts/e6_explain.py`
  ditulis dan diuji pada data sintetis **sebelum** pembekuan dan tidak membaca label pasangan P0-IF.
- **H6c** (uji penghapusan) dihitung hanya pada **baris uji** tiap fold, dengan model fold itu (tidak pada baris latih).
- **H6-0, H6-neg, H6a, H6b** adalah sifat **fungsi** model (identitas, determinisme, arah, struktur panel), bukan ukuran
  generalisasi. Karena itu diperiksa pada **semua 57 minggu** pasangan P0-IF dan **semua 25 model** (5 fold x 5 seed), dalam
  **float64** (model dimuat lalu diubah ke presisi ganda). Kontras masukan sangat kecil (lihat Tahap 0), sehingga float32
  dapat menghasilkan selisih negatif palsu.

## Tahap 0 — prasyarat (bukan hipotesis)

Pasangan kontrol: aset `p0if-on` dan `p0if-off` (image `hanfis/p0if:1.2`, digest tercatat di A-15). Menurut A-11/A-15 yang
berbeda hanya ρ (0,25 vs 1,0). Pemeriksaan **masukan** (bukan label dan bukan prediksi), dijalankan 2026-10-07 pada
`asset_weeks_v2_120assets_e4bis.csv`:

- 57 minggu bersama. Kolom `cvss, patch_risk, mfa_risk, kubernetes_exposure, asset_criticality, threat_intelligence`
  identik pada **semua** 57 minggu (0 minggu berbeda): kontrol sah.
- `exploitability` (x2 = max EPSS x ρ) berbeda pada **23** minggu dan identik pada **34** minggu (maksimum dipegang CVE lain
  yang ρ-nya sama di kedua kondisi, selaras dengan A-15).

Dua strata ditetapkan dari **masukan saja**: **S+** (x2 ON > x2 OFF) dan **S0** (x2 identik). Pada 57 minggu: S+ = 23, S0 = 34.

Penghitungan pada **baris uji** (hanya `event_id`, `fold`, dan masukan; tanpa label dan tanpa prediksi), 2026-10-07: 18 baris
uji P0-IF (9 minggu x 2 aset), seluruhnya di **fold 0**; S+ = 9, S0 = 0, ON < OFF = 0; Δx2 pada S+ antara 0,0003 dan 0,0008
(median 0,0007). Konsekuensi yang dinyatakan sejak awal: (i) pasangan uji hanya ada di fold 0, fold dengan 2,2 observasi per
parameter; (ii) kontrol negatif tidak punya pasangan pada baris uji, maka H6-neg dijalankan pada seluruh 57 minggu; (iii)
kontras masukan sangat kecil, sehingga H6a-H6b adalah pemeriksaan implementasi, bukan bukti kebenaran penjelasan.
Bila ada satu saja pasangan dengan ON < OFF pada masukan, E6 dihentikan dan diselidiki (bertentangan dengan definisi ρ, A-01).

## Hipotesis dan kriteria

| ID | Pernyataan | Kriteria lulus |
|---|---|---|
| H6-0 | **Identitas jejak.** Jumlah kontribusi jejak aturan sama dengan keluaran model (skala 0-1). | `abs(jumlah jejak - y_hat) <= 1e-5` pada **semua** baris uji dan model; 0 pelanggaran. |
| H6-neg | **Kontrol negatif.** Pada minggu S0 (semua masukan ON dan OFF identik) keluaran model dan jejak aturan identik. | `abs(y_hat(on) - y_hat(off)) <= 1e-9` dan `abs(delta firing) <= 1e-9` pada semua pasangan S0 (34 minggu x 25 model, float64); 0 pelanggaran. |
| H6a | **Arah pada kontrol positif.** Keluaran ON tidak lebih rendah dari OFF (dijamin oleh konstrain monoton A-04; memeriksa implementasi pada data nyata). | `y_hat(on) - y_hat(off) >= -1e-9` pada semua pasangan S+ (23 minggu x 25 model, float64); 0 pelanggaran. |
| H6b | **Struktur panel pada kontrol positif.** Karena x4, x5, x6, x7 identik, jejak aturan **panel E tidak berubah**; panel V berubah (x2 masuk di sini); perubahan merambat ke panel I lewat v. | Pada semua pasangan S+: `abs(delta firing panel E) <= 1e-9`; `delta firing panel V` tidak seluruhnya nol (maks > 1e-9). Tidak ada ambang persentase. |
| H6c | **Uji penghapusan.** Menghapus (masking) k aturan dengan kontribusi mutlak terbesar menurut jejak mengubah keluaran lebih besar daripada menghapus k aturan acak. | k = 3 [PUTUSKAN]; 100 undian acak per baris (seed 20261007); (i) rerata `abs(delta top-k)` / rerata `abs(delta acak)` >= 2 [PUTUSKAN], dan (ii) `abs(delta top-k)` > median `abs(delta acak)` pada >= 90% [PUTUSKAN] baris uji. |

Dilaporkan **tanpa kriteria** (tidak masuk keputusan): rerata `y_hat(on) - y_hat(off)` dibanding rerata `y(on) - y(off)`
pada minggu uji; jumlah minggu dikecualikan; sebaran H6c per fold dan per periode (stabil vs setelah 2026-06-08).

## Konsekuensi

- H6-0, H6-neg, H6a, H6b, H6c lulus semua: naskah boleh menyatakan "pemeriksaan kesetiaan lulus pada kontrol positif dan uji
  penghapusan", dengan batasan di atas.
- Salah satu gagal: klaim "penjelasan berlapis" tidak dimasukkan; hasil dilaporkan apa adanya. Gagal H6-0 atau H6a berarti
  cacat implementasi yang harus diperbaiki lewat patch bernomor sebelum E6 dijalankan ulang (ulang pertama dicatat sebagai
  amendemen, bukan menimpa hasil).

## Tidak akan dilakukan

Mengubah k, ambang, atau definisi kelompok aturan setelah hasil terlihat; memilih seed atau fold; memakai baris latih untuk H6c;
melatih ulang model; memeriksa **label** pasangan P0-IF sebelum pembekuan.

## Sumber

`HANFIS_RESEARCH_MEMORY.md` (A-04, A-08, A-11, A-14, A-15, A-34); hasil E4-bis `results_python/e4bis_120*`;
Juston dkk. 2024 (masking aturan); Parthiban-Krishna 2026 (surface view).
