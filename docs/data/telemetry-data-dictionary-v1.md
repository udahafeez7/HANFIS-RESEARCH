 # Kamus Data Telemetri HANFIS Versi 1

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan struktur dataset untuk penelitian Hierarchical Adaptive Neuro-Fuzzy Inference System (HANFIS). Kamus data digunakan sebagai acuan pengumpulan data, validasi, pelatihan model, pengujian, dan inferensi.

Model menggunakan tujuh variabel masukan untuk menghasilkan Dynamic Risk Score pada rentang 0 sampai 1.

## 2. Definisi Satu Record

Satu record merepresentasikan kondisi keamanan satu aset dalam satu jendela observasi selama 60 detik.

Aset yang diamati dapat berupa:

- host;
- server;
- perangkat Jetson Orin Nano;
- container;
- pod Kubernetes; atau
- layanan yang menjadi objek penelitian.

Setiap record terdiri atas:

1. metadata;
2. Vulnerability Layer;
3. Environmental Layer;
4. Integration Layer; dan
5. target pembelajaran untuk record pelatihan.

## 3. Metadata Record

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `experiment_id` | string | Ya | Identitas unik eksperimen |
| `scenario_id` | string | Ya | Identitas skenario normal atau serangan |
| `asset_id` | string | Ya | Identitas aset, host, container, atau pod |
| `timestamp_start` | string | Ya | Waktu awal observasi dalam UTC |
| `timestamp_end` | string | Ya | Waktu akhir observasi dalam UTC |

Contoh waktu yang valid:

```text
2026-07-22T06:00:00Z
```

Ketentuan waktu:

- menggunakan ISO 8601;
- menggunakan zona waktu UTC;
- diakhiri dengan huruf `Z`;
- `timestamp_end` harus lebih akhir daripada `timestamp_start`.

## 4. Struktur Hierarkis HANFIS

Tujuh input dibagi menjadi tiga lapisan.

| Lapisan | Input | Target lapisan |
|---|---|---|
| Vulnerability Layer | `cvss`, `exploitability`, `patch_risk` | `vulnerability_target` |
| Environmental Layer | `mfa_risk`, `kubernetes_exposure`, `asset_criticality` | `environment_target` |
| Integration Layer | `threat_intelligence` serta keluaran dua lapisan sebelumnya | `dynamic_risk_target` |

Semua nilai input dan target menggunakan rentang:

```text
0.0 sampai 1.0
```

Interpretasi umum:

- nilai mendekati `0.0` menunjukkan risiko rendah;
- nilai mendekati `0.5` menunjukkan risiko sedang;
- nilai mendekati `1.0` menunjukkan risiko tinggi.

## 5. Definisi Input `cvss`

`cvss` menunjukkan tingkat keparahan teknis kerentanan berdasarkan CVSS Base Score.

| Atribut | Definisi |
|---|---|
| Nama field | `cvss` |
| Lapisan | Vulnerability Layer |
| Sumber | NVD, CVE, atau vulnerability scanner |
| Rentang mentah | 0.0–10.0 |
| Rentang model | 0.0–1.0 |
| Tipe data | number |

Formula normalisasi:

```text
cvss = cvss_raw / 10
```

Contoh:

```text
CVSS mentah = 8.8
cvss = 8.8 / 10
cvss = 0.88
```

Nilai yang tidak tersedia tidak boleh diganti dengan `0` karena nilai `0` bermakna tingkat keparahan minimum.

## 6. Definisi Input `exploitability`

`exploitability` menunjukkan kemungkinan suatu kerentanan dieksploitasi.

| Atribut | Definisi |
|---|---|
| Nama field | `exploitability` |
| Lapisan | Vulnerability Layer |
| Sumber utama | EPSS |
| Rentang mentah | 0.0–1.0 |
| Rentang model | 0.0–1.0 |
| Tipe data | number |

Karena EPSS telah menggunakan rentang 0 sampai 1, nilainya digunakan langsung:

```text
exploitability = epss_probability
```

Contoh:

```text
EPSS probability = 0.72
exploitability = 0.72
```

Nilai EPSS harus tersedia pada atau sebelum `timestamp_end`. Nilai yang diterbitkan setelah eksperimen tidak boleh digunakan.

## 7. Definisi Input `patch_risk`

`patch_risk` menunjukkan risiko yang disebabkan oleh patch yang belum tersedia, belum diterapkan, atau terlambat diterapkan.

| Atribut | Definisi |
|---|---|
| Nama field | `patch_risk` |
| Lapisan | Vulnerability Layer |
| Sumber | Status patch, versi paket, dan vulnerability scanner |
| Rentang model | 0.0–1.0 |
| Tipe data | number |

Rubrik awal:

| Kondisi | Nilai |
|---|---:|
| Patch telah diterapkan dan diverifikasi | 0.00 |
| Patch tersedia dan dijadwalkan | 0.25 |
| Patch tersedia tetapi terlambat diterapkan | 0.50 |
| Patch belum diterapkan pada aset terekspos | 0.75 |
| Tidak ada patch dan tidak ada mitigasi | 1.00 |

Status patch yang tidak diketahui tidak boleh otomatis diberi nilai `0`.

## 8. Definisi Input `mfa_risk`

`mfa_risk` menunjukkan risiko autentikasi berdasarkan penerapan Multi-Factor Authentication.

| Atribut | Definisi |
|---|---|
| Nama field | `mfa_risk` |
| Lapisan | Environmental Layer |
| Sumber | Identity provider dan konfigurasi autentikasi |
| Rentang model | 0.0–1.0 |
| Tipe data | number |

Rubrik awal:

| Kondisi MFA | Nilai |
|---|---:|
| MFA tahan phishing diterapkan penuh | 0.00 |
| MFA kuat diterapkan untuk seluruh akun | 0.20 |
| MFA hanya diterapkan untuk sebagian akun | 0.50 |
| MFA lemah atau dapat dilewati | 0.75 |
| MFA tidak diterapkan | 1.00 |

Nilai harus berasal dari konfigurasi sebelum serangan. Keberhasilan atau kegagalan serangan tidak boleh digunakan untuk menentukan nilai ini.

## 9. Definisi Input `kubernetes_exposure`

`kubernetes_exposure` menunjukkan tingkat paparan workload Kubernetes berdasarkan konfigurasi keamanannya.

| Atribut | Definisi |
|---|---|
| Nama field | `kubernetes_exposure` |
| Lapisan | Environmental Layer |
| Sumber | Kubernetes API, manifest YAML, dan security scanner |
| Rentang model | 0.0–1.0 |
| Tipe data | number |

Subindikator:

- `public_exposure`;
- `privileged_container`;
- `host_access`;
- `rbac_risk`;
- `network_policy_risk`;
- `secrets_risk`.

Formula awal:

```text
kubernetes_exposure =
    (0.20 × public_exposure) +
    (0.20 × privileged_container) +
    (0.15 × host_access) +
    (0.15 × rbac_risk) +
    (0.15 × network_policy_risk) +
    (0.15 × secrets_risk)
```

Semua subindikator harus berada pada rentang 0 sampai 1.

Bobot tersebut masih merupakan hipotesis awal dan akan diperiksa melalui studi literatur, validasi pakar, sensitivity analysis, dan ablation study.

## 10. Definisi Input `asset_criticality`

`asset_criticality` menunjukkan tingkat kepentingan aset terhadap layanan dan operasi organisasi.

| Atribut | Definisi |
|---|---|
| Nama field | `asset_criticality` |
| Lapisan | Environmental Layer |
| Sumber | Inventaris aset dan analisis dampak bisnis |
| Rentang mentah | 1–5 |
| Rentang model | 0.0–1.0 |
| Tipe data | number |

Formula normalisasi:

```text
asset_criticality = (raw_score - 1) / 4
```

Pemetaan nilai:

| Skor mentah | Kategori | Nilai model |
|---:|---|---:|
| 1 | Dampak minimal | 0.00 |
| 2 | Dampak rendah | 0.25 |
| 3 | Dampak sedang | 0.50 |
| 4 | Dampak tinggi | 0.75 |
| 5 | Aset sangat kritis | 1.00 |

Nilai harus ditentukan sebelum eksperimen, bukan berdasarkan kerusakan yang terjadi setelah serangan.

## 11. Definisi Input `threat_intelligence`

`threat_intelligence` menunjukkan tingkat ancaman berdasarkan informasi eksternal dan aktivitas ancaman lokal.

| Atribut | Definisi |
|---|---|
| Nama field | `threat_intelligence` |
| Lapisan | Integration Layer |
| Sumber | CISA KEV, EPSS, IOC, kampanye ancaman, dan Falco |
| Rentang model | 0.0–1.0 |
| Tipe data | number |

Formula awal:

```text
threat_intelligence =
    (0.35 × known_exploited) +
    (0.25 × exploit_probability) +
    (0.20 × active_local_alert) +
    (0.20 × recent_campaign)
```

Keterangan:

- `known_exploited`: status kerentanan diketahui telah dieksploitasi;
- `exploit_probability`: probabilitas eksploitasi;
- `active_local_alert`: alert lokal selama observasi;
- `recent_campaign`: hubungan dengan kampanye ancaman terbaru.

Hanya informasi yang tersedia sampai `timestamp_end` yang boleh digunakan.

Penggunaan EPSS pada variabel ini perlu diperiksa karena EPSS juga digunakan pada `exploitability`. Pemeriksaan dilakukan untuk mencegah duplikasi informasi.

## 12. Definisi Target Pembelajaran

Target disimpan terpisah dari tujuh input.

### 12.1 `vulnerability_target`

Target keluaran Vulnerability Layer berdasarkan label pakar atau outcome eksperimen yang independen.

Rentang:

```text
0.0–1.0
```

### 12.2 `environment_target`

Target keluaran Environmental Layer yang menggambarkan risiko lingkungan aktual.

Rentang:

```text
0.0–1.0
```

### 12.3 `dynamic_risk_target`

Target akhir HANFIS yang menggambarkan Dynamic Risk Score aktual.

Rentang:

```text
0.0–1.0
```

Target tidak boleh dihitung menggunakan formula yang sama dengan input. Jika formula yang sama digunakan, model hanya akan mempelajari salinan formula dan bukan hubungan risiko yang sebenarnya.

Record pelatihan mempunyai target, sedangkan record inferensi tidak wajib mempunyai target.

## 13. Nilai Hilang dan Pencegahan Data Leakage

Nilai berikut tidak diterima sebagai input model:

```text
null
NaN
Infinity
"0.75"
-0.01
1.01
```

Nilai `"0.75"` tidak diterima karena merupakan string, bukan angka.

Ketentuan pencegahan data leakage:

1. Target disimpan terpisah dari tujuh input.
2. Informasi setelah `timestamp_end` tidak boleh digunakan sebagai input.
3. Record inferensi tidak memuat target.
4. Normalisasi statistik hanya dihitung menggunakan training set.
5. Data dari eksperimen yang sama tidak boleh tersebar sembarangan pada training dan testing.
6. Informasi setelah insiden tidak boleh digunakan untuk memperbaiki input sebelum insiden.
7. Imputasi hanya dipelajari menggunakan training set.
8. Duplikasi antara `exploitability` dan `threat_intelligence` harus diperiksa.

## 14. Status Keputusan dan Kontrol Versi

Keputusan yang telah ditetapkan:

- model menggunakan tujuh input;
- semua input berada pada rentang 0 sampai 1;
- input dibagi menjadi tiga lapisan HANFIS;
- target dipisahkan dari input;
- satu record merepresentasikan observasi selama 60 detik;
- waktu menggunakan ISO 8601 UTC;
- nilai hilang tidak otomatis diganti dengan 0.

Bagian yang belum final:

- formula `patch_risk`;
- bobot `kubernetes_exposure`;
- bobot `threat_intelligence`;
- metode pembentukan target independen;
- metode imputasi data;
- hubungan antara `exploitability` dan `threat_intelligence`.

Informasi dokumen:

```text
Nama    : telemetry-data-dictionary-v1.md
Versi   : 1.0
Tanggal : 22 Juli 2026
Status  : Draf definisi dataset
Proyek  : HANFIS Dynamic Cybersecurity Risk Assessment
```