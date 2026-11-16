# Contoh Query Awal (Pola, Belum Berlabel Final)

Catatan penting:
- Ini **pola query**, bukan benchmark final. Angka diberi placeholder (X, Y).
- **Label verdict final hanya boleh ditentukan setelah angka diverifikasi langsung dari dokumen di korpus** dan dianotasi oleh dua annotator (sesuai TBP).
- Jangan memasukkan jawaban/label ke prompt model (larangan kebocoran answer key).
- Kolom "Perkiraan verdict" hanya untuk merancang sebaran slice.

| ID | Sektor | Query (klaim) | Slice | Perkiraan verdict | Hal yang diuji |
|---|---|---|---|---|---|
| Q01 | Bank | Laba bersih BBCA tahun 2024 sebesar Rp X triliun. | satu-langkah | SUPPORTED/REFUTED | pengambilan angka langsung |
| Q02 | Bank | Total aset BBRI per 30 September 2025 lebih dari Rp X triliun. | satu-langkah | SUPPORTED/REFUTED | as_of periode tepat |
| Q03 | Bank | NPL gross BMRI pada akhir 2023 di bawah X%. | satu-langkah | SUPPORTED/REFUTED | metrik rasio |
| Q04 | Bank | Laba bersih BBNI Q3 2025 naik X% dibanding Q3 2024. | multi-hop | SUPPORTED/REFUTED | dua periode + hitung ulang |
| Q05 | Bank | BRIS mencatat pendapatan bunga bersih Rp X triliun pada 2024. | konflik istilah | REFUTED/NOT_ENOUGH_EVIDENCE | bank syariah memakai istilah bagi hasil |
| Q06 | Bank | Laba bank A lebih besar dari bank B pada 2024. | multi-hop lintas entitas | SUPPORTED/REFUTED | perbandingan dua entitas |
| Q07 | Bank | Laba bersih BBTN naik setiap tahun dari 2022 sampai 2025. | multi-hop tren | SUPPORTED/REFUTED | 4 titik data, abstain per titik bila ada yang kosong |
| Q08 | Bank | Saham Bank Jateng naik pada 2025. | non-listed | NOT_ENOUGH_EVIDENCE/REFUTED | entitas tidak punya saham tercatat |
| Q09 | Bank | Total aset Bank Jateng per kuartal I 2025 sebesar Rp X triliun. | non-listed, satu-langkah | SUPPORTED/REFUTED | sumber dari situs entitas |
| Q10 | Bank | Laba laporan Q3 yang tidak diaudit sama dengan angka laporan tahunan yang diaudit. | konflik unaudited vs audited | REFUTED/SUPPORTED | beda versi dokumen |
| Q11 | Tambang | Pendapatan PTBA tahun 2023 sebesar Rp X triliun. | satu-langkah | SUPPORTED/REFUTED | angka langsung |
| Q12 | Tambang | Volume penjualan batu bara ITMG 2024 sebesar X juta ton. | satu-langkah | SUPPORTED/REFUTED | satuan produksi |
| Q13 | Tambang | Laba bersih ANTM naik X% pada 2024 dibanding 2023. | multi-hop | SUPPORTED/REFUTED | dua periode + hitung ulang |
| Q14 | Tambang | Pendapatan ADRO 2025 lebih tinggi dari 2023. | periode tidak sebanding | NOT_ENOUGH_EVIDENCE/REFUTED | dampak aksi korporasi pemisahan usaha (verifikasi detail di dokumen) |
| Q15 | Tambang | Laba MDKA dilaporkan dalam jutaan rupiah. | konflik satuan | REFUTED/SUPPORTED | jutaan vs miliar vs USD |
| Q16 | Tambang | Pendapatan MBMA pada 2021 sebesar Rp X triliun. | unanswerable | NOT_ENOUGH_EVIDENCE | periode di luar korpus 2022-2025 |
| Q17 | Tambang | Margin laba bersih TINS lebih tinggi dari ANTM pada 2024. | multi-hop lintas entitas | SUPPORTED/REFUTED | hitung rasio dua entitas |
| Q18 | Lintas | Laba bersih BBCA pada kuartal I 2027 mencapai Rp X triliun. | unanswerable | NOT_ENOUGH_EVIDENCE | periode belum terbit |
| Q19 | Lintas | Perusahaan X akan membagikan dividen Rp Y per saham tahun depan. | unanswerable | NOT_ENOUGH_EVIDENCE | proyeksi, bukan fakta laporan |
| Q20 | Lintas | Saham BBRI sebaiknya dibeli sekarang. | di luar cakupan | NOT_ENOUGH_EVIDENCE (abstain) | batas klaim: bukan rekomendasi investasi |

## Rencana sebaran 100-120 query
| Slice | Jumlah |
|---|---|
| Satu-langkah | ~35 |
| Multi-hop | ~25 |
| Konflik/restatement/satuan/audited | ~20 |
| Unanswerable/di luar cakupan | ~20 |
| Bank Jateng (non-listed) | 3-4 |

Pastikan tiap entitas muncul minimal ±3 kali, sektor seimbang, dan sebagian entitas hanya muncul di test untuk slice OOD.
