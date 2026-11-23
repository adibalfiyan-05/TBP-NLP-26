
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "registry" / "documents_filled_preview.csv"
OUTPUT = ROOT / "registry" / "documents_metadata_preview.csv"

COMPANIES = {
    "E16": "Adaro Energy Indonesia",
    "E17": "Bukit Asam",
    "E18": "Indo Tambangraya Megah",
    "E19": "Bayan Resources",
    "E20": "Harum Energy",
    "E21": "Indika Energy",
    "E22": "Bumi Resources",
    "E23": "Alamtri Minerals / Adaro Minerals",
    "E24": "Aneka Tambang",
    "E25": "Vale Indonesia",
    "E26": "Merdeka Copper Gold",
    "E27": "Timah",
    "E28": "Merdeka Battery Materials",
    "E29": "Trimegah Bangun Persada",
    "E30": "Amman Mineral Internasional",
}

with open(INPUT, encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    headers = reader.fieldnames

for row in rows:
    eid = (row.get("entity_id") or "").strip()

    if eid not in COMPANIES:
        continue

    periode = (row.get("periode") or "").upper()
    url = (row.get("url_sumber") or "").lower()

    # Lisensi hak pakai
    if not (row.get("lisensi_hak_pakai") or "").strip() and url:
        if "idx.co.id" in url or "idx.id" in url:
            row["lisensi_hak_pakai"] = "dokumen publik IDX"
        else:
            row["lisensi_hak_pakai"] = (
                f"dokumen publik situs {COMPANIES[eid]}"
            )

    # Status audited
    if "FY" in periode:
        row["audited"] = "ya"
    elif any(q in periode for q in ("Q1", "Q2", "Q3")):
        row["audited"] = "tidak"

    # Catatan sengaja dikosongkan
    row["catatan"] = ""

with open(OUTPUT, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)

print("Selesai!")
print("Hasil:", OUTPUT)
print("documents.csv asli tetap aman.")
