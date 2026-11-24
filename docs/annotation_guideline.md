# Guideline Anotasi Benchmark Verifikator Klaim

Versi 1.0, 24 Nov 2026. Berlaku untuk Adib (bank) dan teman (tambang). Perubahan aturan harus disepakati berdua dan dicatat di bagian Riwayat.

## 1. Satu butir benchmark
Setiap query berisi **klaim**, **as_of** (tanggal "per kapan" klaim diperiksa), dan **entitas**. Label yang kamu tulis:
- `verdict`: SUPPORTED / REFUTED / NOT_ENOUGH_EVIDENCE
- `evidence`: doc_id + nomor halaman (nomor halaman di PDF viewer, mulai 1) + angka yang dikutip
- `as_of`: tanggal rilis dokumen yang dipakai

## 2. Aturan emas
1. **Hanya dari korpus.** Jangan memakai pengetahuan luar atau berita. Kalau angkanya tidak ada di dokumen kita, jawabannya NOT_ENOUGH_EVIDENCE.
2. **Tulis angka persis seperti di dokumen**, lengkap dengan satuan (jutaan atau miliar Rupiah).
3. Satu query = satu label. Klaim yang berisi dua fakta dipecah, atau masuk tipe multi-hop dengan aturan: SUPPORTED hanya bila semua bagian benar.

## 3. Definisi verdict
- **SUPPORTED**: angka/fakta di dokumen cocok dengan klaim dalam toleransi (bagian 4).
- **REFUTED**: dokumen memuat angka/fakta yang sama dengan yang diklaim, tetapi nilainya berbeda di luar toleransi (atau arah naik/turun terbalik).
- **NOT_ENOUGH_EVIDENCE**: dokumen untuk entitas/periode/metrik itu tidak ada di korpus, atau metriknya tidak dilaporkan. Contoh: Q1 2022 untuk E30, 2027, rasio yang tidak dilaporkan, kata-kata subjektif ("terbaik").

## 4. Aturan angka
- **Toleransi pembulatan**: selisih di bawah 0,5% dari nilai dokumen, atau klaim dibulatkan ke satuan yang disebutnya ("sekitar Rp54,8 triliun" untuk 54.851.274 juta = SUPPORTED). Di luar itu = REFUTED.
- **Satuan**: ubah ke satuan yang sama sebelum membandingkan. Jutaan Rp × 1.000.000; miliar × 1.000.000.000. Mata uang laporan tambang bisa USD; jangan dikonversi, cocokkan dengan mata uang yang disebut klaim, kalau beda = NOT_ENOUGH_EVIDENCE.
- **Laba bersih tanpa kualifikasi** = laba tahun/periode berjalan **yang diatribusikan kepada pemilik entitas induk**. Kalau klaim menyebut "laba konsolidasi" atau "laba total", pakai laba sebelum dibagi ke kepentingan nonpengendali. Contoh BBCA 2024: 54.851.274 (total) vs 54.836.305 (induk). *(Keputusan default; sepakati berdua sebelum mulai.)*
- **Periode kumulatif**: angka Q2 di laporan = 6 bulan (Jan–Jun), Q3 = 9 bulan. Klaim "laba Q2" dianggap kumulatif kecuali jelas menyebut "kuartal II saja". Angka kuartal murni hanya untuk tipe multi-hop (selisih dua laporan) dan harus dicatat cara hitungnya.
- **Perbandingan tahun**: pertumbuhan dihitung dari angka yang sama-sama ada di korpus. Tulis rumus dan kedua nilai di kolom catatan.
- **Audited**: kalau klaim menyebut "audit", cek kolom `audited` di documents.csv (FY = ya, Q1–Q3 = tidak). Klaim "laba audit Q1" = REFUTED atau NOT_ENOUGH_EVIDENCE sesuai kasus, dan alasannya ditulis.

## 5. Aturan temporal (as_of)
- Dokumen yang boleh dipakai adalah yang **sudah dirilis pada as_of**. Klaim per 31 Maret 2024 tidak boleh memakai laporan Q2 2024.
- Bila angka tahun lalu dilaporkan ulang (restatement) di dokumen lebih baru, tipe **konflik**: tulis kedua nilai dan dokumennya. Jawaban mengikuti as_of: sebelum rilis dokumen baru, pakai nilai lama; sesudahnya, nilai baru.
- Periode di luar 2022 – Q3 2026, atau periode yang tercatat sebagai celah (E05/E07/E22 Q3 2026; E28–E30 periode sebelum IPO) = NOT_ENOUGH_EVIDENCE.

## 6. Tipe query dan komposisi target (100–120 butir)
| Tipe | Target | Isi |
|---|---|---|
| Satu langkah | ±35 | satu angka dari satu dokumen |
| Multi-hop | ±25 | pertumbuhan, rasio, perbandingan antar periode atau entitas |
| Konflik | ±20 | restatement, laba total vs induk, satuan berbeda |
| Unanswerable | ±20 | informasi tidak ada di korpus |
| Bank Jateng (E12) | 3–4 | entitas non-listed |

## 7. Alur anotasi silang
1. Penulis menulis query dan label awal di `benchmark/queries_<nama>.csv`.
2. Anotator kedua **tidak melihat label penulis** (kolom disembunyikan), mengerjakan sendiri dari PDF.
3. Bandingkan. Hitung persen sepakat per tipe. Yang beda dibahas berdua; keputusan dicatat di kolom `catatan_adjudikasi`.
4. Setelah final, split (dev/test) dikunci dengan hash dan tidak diubah lagi. Hapus query duplikat.
5. Pembagian: Adib menulis query bank, anotasi silang tambang; teman sebaliknya.

## 8. Riwayat
- 1.0: draf awal (24 Nov 2026).
