# Verifikator Klaim Kinerja Entitas Perbankan dan Pertambangan

Temporal Fact-Checking dengan RAG, Self-Corrective Retrieval, dan LoRA/QLoRA (TBP Frontier LLM).
Tenggat: 21 Desember 2026.

## Struktur
| Folder | Isi |
|---|---|
| `data/raw/<ENTITY_ID>/` | Dokumen mentah per entitas (jangan diedit) |
| `data/processed/` | Teks dan tabel hasil ekstraksi |
| `registry/` | `source_register.csv` (per entitas) dan `documents.csv` (per dokumen, otomatis) |
| `benchmark/` | Query, qrels, split, dan manifest hash |
| `src/` | Ingest, retrieval, verifier, agent, training |
| `runs/` | Manifest run, output mentah per item, log training |
| `configs/` | Konfigurasi (seed, model, retrieval) |
| `docs/adr/` | Catatan keputusan desain |
| `reports/` | Laporan dan bukti (screenshot, log) |

## Aturan penamaan dokumen
`data/raw/<ENTITY_ID>/<ENTITY_ID>_<periode>_<jenis>.<ext>`

Contoh: `data/raw/E01/E01_2024-FY_laporan-keuangan.pdf`, `data/raw/E16/E16_2025-Q3_laporan-keuangan.pdf`

Periode: `2024-FY`, `2025-Q1`, `2025-Q2` (atau `2025-S1` untuk semester), `2025-Q3`. Jenis: `laporan-keuangan`, `laporan-tahunan`, `laporan-produksi`, `siaran-pers`.

## Alur harian
1. Unduh dokumen ke `data/raw/<ENTITY_ID>/` sesuai aturan nama.
2. Jalankan `python scripts/update_register.py`.
3. Isi kolom manual di `registry/documents.csv`: `url_sumber`, `versi_dokumen`, `audited`, `lisensi_hak_pakai`. Nilai ini tidak ditimpa saat skrip dijalankan ulang.
4. Baca peringatan di terminal (duplikat, nama di luar aturan, hash berubah).

## Aturan penting
- Dokumen hanya dari sumber resmi publik; catat URL dan hak pakai.
- Jangan masukkan label/jawaban benchmark ke prompt model.
- Test split dikunci (hash di manifest) dan tidak dipakai untuk memilih konfigurasi.
