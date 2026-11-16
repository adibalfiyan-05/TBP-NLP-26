#!/usr/bin/env python3
"""Perbarui register dokumen dari folder data/raw.

Konvensi file:  data/raw/<ENTITY_ID>/<ENTITY_ID>_<periode>_<jenis>.<ext>
Contoh:         data/raw/E01/E01_2024-FY_laporan-keuangan.pdf
                data/raw/E16/E16_2025-Q3_laporan-keuangan.pdf

Yang dilakukan:
  1. Menghitung SHA-256 setiap file di data/raw.
  2. Menulis registry/documents.csv (satu baris per dokumen). Kolom yang sudah
     kamu isi manual (url_sumber, versi, audited, lisensi, catatan, ...) TIDAK
     ditimpa saat skrip dijalankan ulang.
  3. Memperbarui jumlah_dok_terkumpul per entitas di registry/source_register.csv.
  4. Memberi peringatan untuk file duplikat (hash sama), nama file di luar
     konvensi, entitas tidak dikenal, dan hash yang berubah.

Pemakaian:
  python scripts/update_register.py
  python scripts/update_register.py --raw data/raw --registry registry
"""
import argparse
import csv
import hashlib
import re
import sys
from datetime import date
from pathlib import Path

DOC_FIELDS = [
    "doc_id", "entity_id", "path", "periode", "jenis_dokumen",
    "url_sumber", "tanggal_akses", "versi_dokumen", "audited",
    "ukuran_byte", "sha256", "lisensi_hak_pakai", "catatan",
]
MANUAL_FIELDS = ["url_sumber", "versi_dokumen", "audited", "lisensi_hak_pakai", "catatan"]
EXTENSIONS = {".pdf", ".docx", ".txt", ".html", ".htm", ".xlsx", ".csv", ".md"}
NAME_RE = re.compile(r"^(?P<ent>E\d{2})_(?P<per>[^_]+)_(?P<jenis>[^.]+)\.[A-Za-z0-9]+$")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path):
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="data/raw", help="folder dokumen mentah")
    ap.add_argument("--registry", default="registry", help="folder register")
    args = ap.parse_args()

    raw = Path(args.raw)
    reg_dir = Path(args.registry)
    entity_csv = reg_dir / "source_register.csv"
    docs_csv = reg_dir / "documents.csv"
    today = date.today().isoformat()

    if not raw.is_dir():
        print(f"Folder tidak ditemukan: {raw}", file=sys.stderr)
        return 1

    entities, entity_fields = read_csv(entity_csv)
    known = {e["entity_id"] for e in entities}
    old_rows, _ = read_csv(docs_csv)
    old = {r["path"]: r for r in old_rows}

    new_rows, by_hash, warnings = [], {}, []
    files = sorted(p for p in raw.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONS)

    for p in files:
        rel = p.relative_to(raw).as_posix()
        m = NAME_RE.match(p.name)
        if m:
            ent, periode, jenis = m["ent"], m["per"], m["jenis"]
        else:
            ent, periode, jenis = (p.parent.name if p.parent != raw else ""), "", ""
            warnings.append(f"Nama di luar konvensi: {rel}")
        if known and ent not in known:
            warnings.append(f"Entitas tidak ada di source_register.csv: {ent} ({rel})")

        digest = sha256_of(p)
        prev = old.get(rel, {})
        if prev.get("sha256") and prev["sha256"] != digest:
            warnings.append(f"Hash berubah sejak run sebelumnya: {rel}")
        if digest in by_hash:
            warnings.append(f"Duplikat isi: {rel} sama dengan {by_hash[digest]}")
        by_hash.setdefault(digest, rel)

        row = {k: prev.get(k, "") for k in DOC_FIELDS}
        row.update({
            "doc_id": prev.get("doc_id") or "",
            "entity_id": ent, "path": rel,
            "periode": prev.get("periode") or periode,
            "jenis_dokumen": prev.get("jenis_dokumen") or jenis,
            "tanggal_akses": prev.get("tanggal_akses") or today,
            "ukuran_byte": p.stat().st_size, "sha256": digest,
        })
        new_rows.append(row)

    # doc_id stabil: pertahankan yang lama, beri nomor baru untuk yang kosong
    used = {r["doc_id"] for r in new_rows if r["doc_id"]}
    counter = 1
    for r in new_rows:
        if not r["doc_id"]:
            while f"D{counter:04d}" in used:
                counter += 1
            r["doc_id"] = f"D{counter:04d}"
            used.add(r["doc_id"])

    reg_dir.mkdir(parents=True, exist_ok=True)
    write_csv(docs_csv, new_rows, DOC_FIELDS)

    counts = {}
    for r in new_rows:
        counts[r["entity_id"]] = counts.get(r["entity_id"], 0) + 1
    if entities:
        for e in entities:
            e["jumlah_dok_terkumpul"] = counts.get(e["entity_id"], 0)
        write_csv(entity_csv, entities, entity_fields)

    total = len(new_rows)
    print(f"Dokumen terdaftar: {total} (target minimal 300)")
    if entities:
        print(f"{'ID':<5}{'Kode':<7}{'Terkumpul':>10}{'Target':>8}")
        for e in entities:
            tgt = e.get("jumlah_dok_target", "")
            print(f"{e['entity_id']:<5}{e['kode']:<7}{e['jumlah_dok_terkumpul']:>10}{tgt:>8}")
    for w in warnings:
        print("PERINGATAN:", w, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
