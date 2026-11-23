from pathlib import Path
import csv

# Folder utama repository
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUTPUT = ROOT / "registry" / "url_audit.csv"

results = []

# Periksa semua PDF di E16 sampai E30
for entity_number in range(16, 31):
    entity_id = f"E{entity_number:02d}"
    entity_folder = RAW_DIR / entity_id

    if not entity_folder.exists():
        print(f"[FOLDER TIDAK ADA] {entity_id}")
        continue

    for pdf in entity_folder.rglob("*.pdf"):
        host_url = ""
        referrer_url = ""
        status = "URL TIDAK DITEMUKAN"

        # Baca metadata Zone.Identifier Windows
        stream_path = str(pdf) + ":Zone.Identifier"

        try:
            with open(stream_path, "r", encoding="utf-8",
                      errors="replace") as f:
                content = f.read()

            for line in content.splitlines():
                if line.startswith("HostUrl="):
                    host_url = line.split("=", 1)[1].strip()

                elif line.startswith("ReferrerUrl="):
                    referrer_url = line.split("=", 1)[1].strip()

            if host_url or referrer_url:
                status = "URL DITEMUKAN"

        except (FileNotFoundError, OSError):
            pass

        results.append({
            "entity_id": entity_id,
            "nama_file": pdf.name,
            "path": pdf.relative_to(ROOT).as_posix(),
            "host_url": host_url,
            "referrer_url": referrer_url,
            "status": status
        })

# Simpan hasil pemeriksaan
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "entity_id",
            "nama_file",
            "path",
            "host_url",
            "referrer_url",
            "status"
        ]
    )
    writer.writeheader()
    writer.writerows(results)

found = sum(
    1 for item in results
    if item["status"] == "URL DITEMUKAN"
)

print("\n===== HASIL PEMERIKSAAN =====")
print(f"Jumlah PDF diperiksa : {len(results)}")
print(f"URL ditemukan        : {found}")
print(f"URL tidak ditemukan  : {len(results) - found}")
print(f"Hasil disimpan di    : {OUTPUT}")