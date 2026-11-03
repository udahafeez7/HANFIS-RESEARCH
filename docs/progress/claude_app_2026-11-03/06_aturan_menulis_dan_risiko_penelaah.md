# Aturan menulis dan risiko penelaah

## Aturan gaya (dari `docs/gaya_jawaban_asisten.md`, ringkas)

1. Kalimat pertama menjawab pertanyaan. Tanpa "Tentu", "Baik", atau penutup yang mengulang.
2. Satu kata yang tepat, bukan tiga yang mirip. Hindari pola "bukan X, melainkan Y" dan daftar tiga hal demi irama.
3. Hindari kata: crucial, pivotal, leverage, holistik, komprehensif, robust tanpa ukuran, "it is worth noting".
4. Tanpa tanda pisah panjang, tanpa emoji, tanpa ekor partisipial di akhir kalimat.
5. Setiap klaim hasil didukung berkas, keluaran, atau komit. Bedakan terbukti, disimpulkan, dan perkiraan. Tulis "belum diperiksa" untuk hal yang belum diperiksa.
6. Skor dan penilaian diberi label sebagai pertimbangan, bukan pengukuran.
7. Perintah untuk peneliti ditulis persis, tanpa placeholder `<...>`, satu langkah satu blok.
8. Dokumen untuk orang lain memuat catatan bahwa penyusunannya dibantu AI; aturan gaya tidak dipakai untuk menyamarkan asal tulisan.

## Aturan teks naskah

- Bahasa Inggris. Setiap angka di abstrak harus terlacak ke tabel di badan naskah.
- Jangan menulis sitasi dari ingatan; metadata referensi diambil dari doi.org.
- Penggunaan AI diungkapkan di Methods dan Declarations.
- Hasil negatif tetap di badan naskah: H1b tidak terkonfirmasi, E11 (rumus lebih baik), H6c gagal, E9 (tanpa x2 dan x7 tidak ada skill), E7 (HANFIS tidak mengalahkan persistence maupun rumus).

## Pertanyaan yang mungkin diajukan penelaah (pertimbangan penyusun, bukan prediksi)

| Pertanyaan | Jawaban yang sudah ada di naskah | Celah yang masih terbuka |
|---|---|---|
| Apa manfaat HANFIS bila rumus empat parameter lebih baik? | Struktur, jumlah aturan 34 dan parameter 176 dibanding 128 dan 1.052, aturan yang bisa dibaca; naskah tidak mengklaim akurasi lebih baik | Interpretabilitas hanya diuji sebagian (E6: benar rata-rata, tidak merata; H6c gagal) |
| Label dan masukan berbagi bahan (EPSS, KEV) | Limitations menyatakannya; persistence dan rumus dipakai sebagai pembanding wajar | Tidak ada data insiden nyata sebagai kebenaran dasar |
| Mengapa E7 hanya enam minggu dan satu jendela? | Dinyatakan di kalimat wajib: hasil tidak meluas; protokol terdaftar di OSF sebelum label maju dihitung | Daya statistik kecil; guncangan mingguan bersama |
| Mengapa HANFIS jauh lebih buruk di E7 daripada out-of-fold? | Tidak diklaim; penyebab tidak diuji | Dugaan pergantian model EPSS belum diuji |
| P7e dan P7f post hoc | Dinyatakan post hoc di subbagian hasil | Tidak dikoreksi multiplisitas di luar keluarga Holm masing-masing |
| Input lingkungan (x4 sampai x6) tidak terbukti membantu | Diakui di Discussion: label tidak bergantung pada masukan itu, jadi inventaris ini tidak dirancang untuk menunjukkan manfaatnya | Memerlukan luaran yang bergantung pada lingkungan, di luar naskah ini |
| Testbed dua node WSL 2 | Limitations menyatakan validitas eksternal belum diuji | Tidak ada klaster produksi |
| Nama HANFIS sudah dipakai | Literature Review menyatakan Soozanchi dkk. (2010) | Judul tetap memakai "HANFIS"; risiko penolakan kebaruan nama, bukan kebaruan metode |

## Cara memberi usulan perubahan naskah ke repositori

Kirim pasangan seperti ini agar bisa diterapkan lewat skrip teks-persis:

```text
LAMA (harus cocok persis, muncul satu kali):
<kalimat lama dari sn-article.tex>

BARU:
<kalimat baru>

Lapisan: pelaporan naskah. Dokumen: manuscript/sn-article.tex.
Diperiksa: \cite, \ref, \label, rumus, dan angka identik kecuali yang sengaja diubah.
```

(Tanda `<...>` di atas hanya bingkai contoh untuk pesan ke Claude di aplikasi, bukan perintah terminal.)


---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) dari berkas repositori dan keluaran terminal sesi kerja 2 sampai 3 November 2026. Angka dan kutipan naskah diambil langsung dari berkas; pertimbangan ditandai sebagai pertimbangan.
