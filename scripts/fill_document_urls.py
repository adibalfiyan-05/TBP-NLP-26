from pathlib import Path
import csv

# =====================================
# PENGATURAN
# =====================================

ROOT = Path(__file__).resolve().parent.parent

AUDIT_FILE = ROOT / "registry" / "url_audit.csv"
DOCUMENTS_FILE = ROOT / "registry" / "documents.csv"

# Hasil disimpan sebagai file baru
OUTPUT_FILE = ROOT / "registry" / "documents_filled_preview.csv"


# =====================================
# MEMBACA FILE CSV
# =====================================

def read_csv(file_path):
    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames

    if not headers:
        raise ValueError(f"Header tidak ditemukan: {file_path}")

    return rows, headers


audit_rows, audit_headers = read_csv(AUDIT_FILE)
document_rows, document_headers = read_csv(DOCUMENTS_FILE)

# Memastikan kolom tersedia
if not {"nama_file", "host_url", "status"}.issubset(audit_headers):
    raise ValueError("Kolom url_audit.csv tidak sesuai.")

if not {"path", "url_sumber"}.issubset(document_headers):
    raise ValueError("Kolom documents.csv tidak sesuai.")


# =====================================
# MENCARI URL BERDASARKAN NAMA FILE
# =====================================

url_lookup = {}

for item in audit_rows:
    filename = Path(item["nama_file"]).name
    host_url = (item["host_url"] or "").strip().replace("\x00", "")
    status = (item["status"] or "").strip()

    if status == "URL DITEMUKAN" and host_url:
        if filename in url_lookup and url_lookup[filename] != host_url:
            url_lookup[filename] = None
        else:
            url_lookup[filename] = host_url


# =====================================
# MENCOCOKKAN DENGAN documents.csv
# =====================================

updated = 0
already_filled = 0
not_found = 0
conflict = 0

for row in document_rows:
    filename = Path(row["path"].replace("\\", "/")).name
    current_url = (row["url_sumber"] or "").strip()

    if current_url:
        already_filled += 1
        continue

    if filename not in url_lookup:
        not_found += 1
        continue

    new_url = url_lookup[filename]

    if new_url is None:
        conflict += 1
        print(f"[KONFLIK] {filename}")
        continue

    row["url_sumber"] = new_url.strip().replace("\x00", "").replace("\ufffd", "")
    updated += 1

    print(f"[AKAN DIISI] {filename}")
    print(f"             {new_url}")


# =====================================
# MENYIMPAN KE FILE BARU
# =====================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=document_headers
    )
    writer.writeheader()
    writer.writerows(document_rows)


# =====================================
# RINGKASAN
# =====================================

print("\n========== RINGKASAN ==========")
print(f"URL berhasil dicocokkan : {updated}")
print(f"URL sudah terisi         : {already_filled}")
print(f"Tidak ditemukan         : {not_found}")
print(f"URL konflik              : {conflict}")

print("\n[BERHASIL] File baru dibuat:")
print(OUTPUT_FILE)

print("\ndocuments.csv ASLI TIDAK DIUBAH.")