# ADR 0001: Kaggle sebagai resource komputasi

- **Status:** diterima
- **Tanggal:** 2026-11-15

## Konteks
Proyek memerlukan inferensi untuk B0-B6 dan pelatihan QLoRA (B5) dengan model kompak (kelas 0.5B-1.5B). Pengerjaan individu dan tenggat 21 Desember 2026.

## Keputusan
Memakai Kaggle (GPU T4/P100) untuk pelatihan dan inferensi eksperimen. Serving UI+API untuk demo dijalankan lokal atau lewat tunnel sementara.

## Konsekuensi
- Kuota GPU mingguan dan sesi terbatas: checkpoint dan adapter disimpan berkala ke Kaggle Dataset.
- Model dibatasi kelas 0.5B-1.5B dengan QLoRA 4-bit.
- Bukti konfigurasi (versi library, tipe GPU, seed, log training) disimpan di `runs/`.
- Serving tidak permanen: siapkan rekaman layar demo sebagai cadangan.

## Alternatif
Google Colab dan laptop GPU, tidak dipilih sebagai utama karena resource yang sudah tersedia adalah Kaggle.
