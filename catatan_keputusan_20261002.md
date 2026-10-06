# Catatan Keputusan HANFIS — 2026-10-02

> Pengingat markdown, merekam diskusi dan keputusan hari ini. Rujuk juga
> `HANFIS_RESEARCH_MEMORY.md` amendemen A-30 untuk versi permanen di repo.

## 1. Rekaman Debat: "Apakah HANFIS Seharusnya 100% Berbasis Telemetri?"

**Klaim Hafiz:** HANFIS seharusnya bisa menghilangkan parameter statis supaya tidak
ada bias pendapat ahli dan tidak ketinggalan zaman — penilaian risiko sepenuhnya
dari data telemetri.

**Bantahan Maverick (dicatat sebagai keputusan, bukan opini sepihak):**

1. **Bukti langsung membantah klaim**: kebuntuan hari ini (tiga kolom `ISI_HAFIZ`
   di 11 baris, 11×3 nilai yang harus diisi tangan) ADALAH bukti bahwa x4 (MFA
   Risk), x5 (Kubernetes Exposure), x6 (Asset Criticality) bukan dihitung dari
   telemetri di implementasi saat ini. Argumen bahwa sistem "sudah" berbasis
   telemetri penuh tidak konsisten dengan fakta operasional yang sedang dialami.
2. **Kontribusi HANFIS yang diklaim naskah** adalah parameter *konsekuen/premis*
   beradaptasi dari data (hybrid LSE+Adam) — bukan klaim bahwa *setiap input*
   harus telemetri langsung. x1 (CVSS) statis per rilis vendor dan tidak
   dipersoalkan; prinsip yang sama berlaku x4/x6.
3. **Mendinamiskan x4/x6 paksa memindahkan bias pakar, bukan menghilangkannya** —
   fungsi pemetaan telemetri-mentah → skor 0–1 tetap keputusan desain manusia,
   tapi jadi tersembunyi di kode, bukan di baris CSV yang bisa direview.
4. **Risiko keamanan baru**: skor yang dihitung live dari telemetri cluster bisa
   dimanipulasi oleh siapa pun yang mengubah NetworkPolicy/RBAC — menyerang
   sinyal, bukan sistem. `hanfis_threat_model.tex` belum punya trust boundary
   untuk kelas serangan ini.
5. **x6 (Asset Criticality) secara fundamental adalah value judgment**, bukan
   besaran yang bisa disadap telemetri — sejalan dengan kerangka industri
   (NIST CSF, FAIR) yang juga tidak mengklaim kritikalitas bisa otomatis penuh.

**Keputusan:**
- x6 (`asset_criticality`) **tetap statis**, tapi sekarang diisi lewat **rubrik
  eksplisit dan auditable** (lihat §2), bukan firasat bebas.
- x5 (`kubernetes_exposure`) **berpotensi didinamiskan di masa depan** sebagai
  hipotesis baru bernomor (usulan: **H6**), dipraregistrasi terpisah dari
  H1–H4 yang sudah beku, dijalankan di atas tumpukan Prometheus yang sudah ada.
  **Tidak dikerjakan sekarang** — item roadmap terpisah, tidak menghambat E4 ulang.
- x4 (`mfa_risk`) **tidak mungkin ditelemetri-kan saat ini** — butuh integrasi
  IAM/OIDC yang belum ada di testbed sama sekali. Tetap statis, tetap menunggu
  penilaian Anda (rubrik belum ditulis — di luar cakupan permintaan hari ini).

## 2. Rubrik `kubernetes_exposure` (skala 0 / 0,5 / 1)

Konsisten dengan skala yang sudah dipakai 109 baris `assets.csv` lama.

| Nilai | Kriteria |
|---|---|
| **0** | Tidak menerima trafik jaringan langsung dari pod lain; berjalan sebagai Job/CLI sekali-jalan atau sidecar tanpa port terbuka. |
| **0,5** | Menerima trafik dari subset terbatas pod/namespace, atau diakses periodik lewat API (bukan jalur data langsung), atau di-scope NetworkPolicy. |
| **1** | Menerima/mem-forward trafik dari seluruh/banyak pod cluster, ATAU punya hak admission yang memengaruhi semua workload, ATAU menjadi titik singgah wajib lalu lintas. |

## 3. Rubrik `asset_criticality` (skala tier 0–7, jumlah tiga faktor)

Tiga faktor objektif, dapat dihitung dari arsitektur cluster, dijumlahkan:

| Faktor | 0 poin | 1 poin | 2 poin | 3 poin |
|---|---|---|---|---|
| **A — Cakupan RBAC/privilese** | Tidak ada SA/binding khusus | Role namespace-scoped terbatas | ClusterRole akses luas | cluster-admin / setara penuh |
| **B — Blast radius ketersediaan** | Kegagalan hanya memengaruhi dirinya | Memengaruhi beberapa service bergantung langsung | Melumpuhkan cluster/banyak namespace (SPOF) | — |
| **C — Sensitivitas data yang dipegang** | Tidak ada data sensitif | Data operasional (metrik/log) | Rahasia/kredensial/kunci | — |

`asset_criticality = A + B + C` (rentang 0–7, cocok dengan rentang yang terlihat
di 109 baris lama).

## 4. Draf Hasil Penerapan Rubrik — WAJIB DIREVIEW, BUKAN FINAL

Angka di bawah adalah hasil penerapan rubrik di atas secara mekanis oleh saya,
berdasarkan arsitektur umum tiap komponen (bukan firasat). **Anda yang memutuskan
apakah ini final** — kolom `mfa_risk` sengaja tidak diisi (rubriknya belum ada,
di luar permintaan hari ini).

| asset_id | kubernetes_exposure (draf) | A | B | C | asset_criticality (draf) | Alasan singkat |
|---|---|---|---|---|---|---|
| etcd-3-5 | 0,5 | 3 | 2 | 2 | **7** | Datastore seluruh cluster; kompromi = total takeover |
| opa-0-70 | 0,5 | 2 | 2 | 0 | **4** | Evaluasi kebijakan, admission bisa fail-closed |
| gatekeeper-3-17 | 1 | 3 | 2 | 0 | **5** | Webhook admission untuk SEMUA resource |
| cilium-1-16 | 1 | 3 | 2 | 1 | **6** | CNI — setiap paket lewat sini; lihat traffic pattern |
| istio-proxy-1-23 | 1 | 1 | 1 | 1 | **3** | Sidecar per-pod, dampak per-pod bukan cluster-wide |
| kafka-3-8 | 0,5 | 1 | 1 | 2 | **4** | Bus pesan, data event berpotensi sensitif |
| velero-1-15 | 0,5 | 3 | 1 | 2 | **6** | Baca lintas-namespace penuh; backup berisi semua rahasia |
| metrics-server-0-7 | 0,5 | 1 | 1 | 0 | **2** | Read-only metrik, HPA bergantung tapi tidak fatal |
| cosign-2-4 | 0 | 0 | 0 | 1 | **1** | Job CI sekali-jalan, tidak persisten di cluster |
| external-secrets-0-10 | 0,5 | 2 | 1 | 2 | **5** | Akses vault eksternal + buat Secret langsung |
| kube-state-metrics-2-13 | 0,5 | 1 | 0 | 0 | **1** | Read-only cluster-wide, murni observability |

## 5. Tindak Lanjut Naskah (DITUNDA, Bukan Dikerjakan Sekarang)

Begitu 120 aset final dan E4 diulang, naskah §3.1/§3.7 perlu paragraf tambahan
yang **secara eksplisit membedakan** input statis-tetapi-auditable (x1, x4, x6)
dari input yang berpotensi dinamis (x5, diusulkan H6 future work) — supaya
klaim "data-driven" di abstrak tidak terbaca berlebihan dibanding implementasi
sebenarnya. **Jangan diubah sebelum nilai final dan hasil E4 ulang ada.**

## 6. Tugas Terbuka

- [ ] Hafiz review/revisi tabel draf §4 (kubernetes_exposure + asset_criticality)
- [ ] Hafiz isi `mfa_risk` (rubrik terpisah, belum ditulis)
- [ ] Setelah keduanya final → jalankan `scripts/merge_candidates_into_assets.py --dry-run`
- [ ] Setelah merge sukses → `build_asset_weeks.py` ulang → amendemen E4 ulang → update naskah §3.1/§3.7
