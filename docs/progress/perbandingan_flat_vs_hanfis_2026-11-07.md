# Flat ANFIS lawan HANFIS: perbandingan dalam bahasa sederhana (7 November 2026)

Sumber angka: E4-bis (terdaftar, out-of-fold, 1.080 baris), E25 (pengukuran biaya, tidak terdaftar, deskriptif), E7 (evaluasi maju). Skor dan kesimpulan di bagian akhir adalah pertimbangan, bukan pengukuran.

## 1. Tiga model yang dibandingkan

- Flat ANFIS penuh: satu sistem besar, semua tujuh masukan dicampur sekaligus. 128 aturan, 1.052 parameter.
- FlatANFISMatched: satu sistem datar yang sengaja dibuat sebesar HANFIS (176 parameter, 8 aturan dari pengelompokan data).
- HANFIS: tiga sistem kecil bertingkat. Dua panel menilai tiga masukan masing-masing, satu panel menggabungkan hasilnya dengan x7. 34 aturan, 176 parameter.

## 2. Perbandingan

| Hal yang diukur | Flat penuh | FlatANFISMatched | HANFIS | Siapa unggul | Status bukti |
|---|---|---|---|---|---|
| Aturan dan parameter | 128 dan 1.052 | 8 dan 176 | 34 dan 176 | HANFIS dan matched jauh lebih ringkas daripada flat penuh | Hitungan rumus (Tabel 1) |
| Akurasi, skill HANFIS terhadap model itu | 0,253 (tanpa kriteria) | 0,665 [0,269; 0,844] | | HANFIS lebih kecil galatnya daripada keduanya | E4-bis, terdaftar untuk matched; flat penuh hanya dilaporkan |
| Akurasi bila fold 0 dibuang | 0,084 | 0,183 | | Keunggulan menyusut besar | Analisis post hoc |
| Rentang prediksi | tidak dilaporkan | -6,679 sampai 11,059 | 0,000 sampai 10,401 | HANFIS tetap masuk akal, matched melenceng | E4-bis, dilaporkan |
| Waktu latih, median (detik) | 7,30 | 0,95 | 8,51 | Matched jauh lebih cepat; HANFIS sedikit lebih lambat daripada flat penuh | E25, deskriptif |
| Kenaikan memori latih (MiB) | 3,83 | 194,13 | 0,40 | HANFIS | E25, deskriptif |
| Latensi satu baris (mikrodetik) | 95,6 | 49,1 | 398,2 | Matched, lalu flat penuh; HANFIS paling lambat | E25, deskriptif |
| Throughput batch (baris per detik) | 264.865 | 2.456.989 | 388.665 | Matched jauh di depan; HANFIS di atas flat penuh | E25, deskriptif |
| Evaluasi maju E7 | tidak ikut | tidak ikut | kalah dari persistence dan rumus | Tidak ada perbandingan | E7 hanya menguji HANFIS, persistence, hibrida, dan rumus |

## 3. Cara membacanya

*ELI5.* Bayangkan tiga juri menilai kerentanan. Juri datar besar punya 128 aturan catatan, juri datar kecil punya 8, dan juri HANFIS punya 34 catatan yang dibagi ke tiga meja. Di data kita, juri HANFIS salah paling sedikit di antara ketiganya. Tetapi ia lambat memutuskan satu kasus, dan juri kecil yang paling cepat. Dan ada juri sederhana yang tidak ikut lomba ini, yaitu rumus empat angka, yang justru mengalahkan HANFIS.

*Teacher.* Ada tiga pertanyaan berbeda. Apakah hierarki membuat model lebih akurat daripada model datar? Ya pada E4-bis, tetapi sebagian besar keunggulan terhadap matched datang dari satu fold, dan matched sendiri pembanding yang lemah (prediksinya melenceng). Apakah hierarki membuat model lebih murah? Memori dan jumlah parameter terhadap flat penuh, ya. Waktu latih dan latensi satu baris, tidak. Apakah hierarki membuat model berguna? Itu soal E7, dan di sana model ini tidak mengalahkan persistence maupun rumus sederhana.

*Argue.* Pembela flat: "FlatANFISMatched dilatih sekali dengan 0,95 detik dan latensi 49 mikrodetik, jadi untuk apa tiga panel?" Pembela HANFIS: "Matched memakai memori puncak 194 MiB yang tumbuh dengan data, dan prediksinya keluar dari rentang label; HANFIS stabil dan lebih akurat di E4-bis." Keduanya benar pada ukurannya masing-masing. Hasilnya tidak memberi pemenang tunggal.

*Brutal.* Keunggulan HANFIS atas model datar itu nyata tetapi kecil nilainya: pembandingnya model datar yang dibuat sendiri, bukan baseline yang sungguh dipakai praktisi (persistence dan rumus). Mengalahkan flat ANFIS tidak membuat HANFIS berguna. Dan bagian "lebih murah" hanya separuh benar.

## 4. Kesimpulan yang boleh ditarik

- Boleh: pada data E4-bis, HANFIS lebih akurat daripada flat penuh dan FlatANFISMatched, memakai memori latih jauh lebih kecil daripada keduanya, dan 6 kali lebih sedikit parameter daripada flat penuh.
- Boleh dengan syarat: keunggulan atas matched sebagian besar dari fold 0 dan matched pembanding lemah.
- Tidak boleh: HANFIS lebih cepat dilatih atau lebih cepat menjawab daripada model datar; hierarki terbukti membantu prediksi; keunggulan atas flat ANFIS berlaku di evaluasi maju (flat ANFIS tidak ikut E7).

## 5. Apakah dimasukkan ke naskah?

Ya, sebagai satu tabel ringkas di badan naskah (Results, setelah Tabel 4 atau di Discussion) dan versi lengkap per fold di Additional file 1. Alasannya: perbandingan inilah isi H2 dan H3, penelaah akan mencarinya, dan tabel yang jujur (termasuk kolom yang merugikan HANFIS) melindungi naskah dari tuduhan memilih hasil. Tabel harus memuat kolom status bukti (terdaftar, dilaporkan tanpa kriteria, deskriptif tidak terdaftar) dan satu kalimat bahwa flat ANFIS tidak ikut evaluasi maju. Ini masuk batch perubahan naskah berikutnya, belum diterapkan.

---
Dokumen ini disusun dengan bantuan asisten AI (Claude, Anthropic) dari hasil E4-bis, E7, E25, dan angka di naskah.
