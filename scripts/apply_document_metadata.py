import csv
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

ORIGINAL = BASE / "registry" / "documents.csv"
PREVIEW = BASE / "registry" / "documents_metadata_preview.csv"
BACKUP = BASE / "registry" / "documents_backup.csv"

TARGETS = {f"E{i}" for i in range(16, 31)}

# Baca dokumen utama
with ORIGINAL.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    original_rows = list(reader)

# Baca preview terbaru
with PREVIEW.open(encoding="utf-8-sig", newline="") as f:
    preview_rows = list(csv.DictReader(f))

# Ambil hasil E16-E30
updates = {
    row["doc_id"]: row
    for row in preview_rows
    if row["entity_id"] in TARGETS
}

if not updates:
    raise ValueError("Tidak ada dokumen E16-E30 di preview.")

# Pastikan doc_id cocok dengan dokumen utama
original_ids = {row["doc_id"] for row in original_rows}
missing = set(updates) - original_ids

if missing:
    raise ValueError(f"Doc ID tidak ditemukan: {sorted(missing)}")

# Backup dokumen utama
shutil.copy2(ORIGINAL, BACKUP)

# Terapkan pembaruan hanya pada E16-E30
result = []

for row in original_rows:
    if row["doc_id"] in updates:
        result.append(updates[row["doc_id"]])
    else:
        result.append(row)

# Simpan hasil
with ORIGINAL.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(result)

print(f"Berhasil memperbarui {len(updates)} dokumen.")
print("E01-E15 tetap dipertahankan.")
print(f"Backup: {BACKUP}")
