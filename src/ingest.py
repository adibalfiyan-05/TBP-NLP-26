#!/usr/bin/env python3
"""Ekstraksi teks per halaman dari semua dokumen di registry/documents.csv.

Hasil:
  data/processed/pages/<nama_file>.jsonl      satu baris per halaman (teks + metadata)
  data/processed/pages/<nama_file>.meta.json  ringkasan per dokumen
  registry/extraction_report.csv           laporan kualitas semua dokumen

Pemakaian:
  python src/ingest.py --only E04          # coba dulu satu entitas
  python src/ingest.py                     # semua dokumen (yang sudah selesai dilewati)
  python src/ingest.py --force             # ulang dari awal

Dokumen berstatus PERIKSA di laporan perlu dilihat manual: biasanya teksnya kosong (scan),
atau halaman laporan posisi keuangan / laba rugi tidak ditemukan (mungkin ringkasan saja).
"""
import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:  # versi lama
    import fitz

NUM = re.compile(r"\d{1,3}(?:[.,]\d{3})+")  # angka berformat ribuan, Indonesia (54.851.274) atau Inggris (54,851,274)
BALANCE_SHEET = ["LAPORAN POSISI KEUANGAN", "LAPORAN POSISI", "OF FINANCIAL POSITION", "NERACA", "STATEMENT OF FINANCIAL POSITION",
                 "STATEMENTS OF FINANCIAL POSITION", "BALANCE SHEET"]
INCOME = ["LAPORAN LABA RUGI", "LAPORAN PENGHASILAN KOMPREHENSIF", "LAPORAN LABA DAN RUGI",
          "STATEMENTS OF PROFIT OR LOSS", "STATEMENT OF PROFIT OR LOSS",
          "STATEMENTS OF COMPREHENSIVE INCOME", "STATEMENT OF COMPREHENSIVE INCOME",
          "STATEMENTS OF INCOME", "STATEMENT OF INCOME", "INCOME STATEMENT"]
MIN_NUMBERS = 12          # halaman laporan inti biasanya penuh angka; daftar isi tidak
MIN_CHARS_PER_PAGE = 200  # rata-rata di bawah ini dicurigai scan/kosong


def norm(text: str) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def process(doc_row, raw_dir: Path, out_dir: Path):
    pdf = raw_dir / doc_row["path"]
    key = Path(doc_row["path"]).stem  # unik lintas entitas/periode, aman bila doc_id dua laptop bentrok
    pages_out = out_dir / f"{key}.jsonl"
    meta_out = out_dir / f"{key}.meta.json"
    meta = {"doc_id": doc_row["doc_id"], "entity_id": doc_row["entity_id"], "periode": doc_row["periode"],
            "path": doc_row["path"], "sha256": doc_row["sha256"], "n_pages": 0, "n_chars": 0,
            "empty_pages": 0, "first_balance_sheet_page": "", "first_income_page": "",
            "status": "OK", "catatan": ""}
    try:
        doc = fitz.open(pdf)
    except Exception as exc:
        meta.update(status="PERIKSA", catatan=f"tidak bisa dibuka: {exc}")
        meta_out.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        return meta
    with pages_out.open("w", encoding="utf-8") as f:
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text", sort=True)
            n_nums = len(NUM.findall(text))
            nt = norm(text[:1500])  # judul laporan ada di bagian atas halaman
            is_bs = n_nums >= MIN_NUMBERS and any(p in nt for p in BALANCE_SHEET)
            is_pl = n_nums >= MIN_NUMBERS and any(p in nt for p in INCOME)
            if len(text.strip()) < 30:
                meta["empty_pages"] += 1
            if is_bs and not meta["first_balance_sheet_page"]:
                meta["first_balance_sheet_page"] = i
            if is_pl and not meta["first_income_page"]:
                meta["first_income_page"] = i
            meta["n_chars"] += len(text)
            f.write(json.dumps({
                "doc_id": doc_row["doc_id"], "entity_id": doc_row["entity_id"],
                "periode": doc_row["periode"], "page": i, "n_numbers": n_nums,
                "is_balance_sheet": is_bs, "is_income_statement": is_pl, "text": text,
            }, ensure_ascii=False) + "\n")
        meta["n_pages"] = len(doc)
    doc.close()

    notes = []
    if meta["n_pages"] == 0:
        notes.append("dokumen tanpa halaman")
    elif meta["n_chars"] / meta["n_pages"] < MIN_CHARS_PER_PAGE:
        notes.append("teks sangat sedikit (mungkin hasil scan, perlu OCR)")
    if not meta["first_balance_sheet_page"]:
        notes.append("halaman laporan posisi keuangan tidak ditemukan")
    if not meta["first_income_page"]:
        notes.append("halaman laba rugi tidak ditemukan")
    if notes:
        meta["status"], meta["catatan"] = "PERIKSA", "; ".join(notes)
    meta_out.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    return meta


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registry", default="registry")
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/processed/pages")
    ap.add_argument("--only", help="proses satu entitas saja, mis. E04")
    ap.add_argument("--limit", type=int, help="batasi jumlah dokumen (untuk uji coba)")
    ap.add_argument("--force", action="store_true", help="proses ulang walau sudah ada hasilnya")
    args = ap.parse_args()

    reg, raw, out = Path(args.registry), Path(args.raw), Path(args.out)
    docs_csv = reg / "documents.csv"
    if not docs_csv.exists():
        print("registry/documents.csv tidak ada. Jalankan scripts/update_register.py dulu.", file=sys.stderr)
        return 1
    with docs_csv.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if args.only:
        rows = [r for r in rows if r["entity_id"] == args.only]
    if args.limit:
        rows = rows[: args.limit]
    out.mkdir(parents=True, exist_ok=True)

    metas, started = [], time.time()
    for n, row in enumerate(rows, start=1):
        meta_path = out / f"{Path(row['path']).stem}.meta.json"
        if meta_path.exists() and not args.force:
            old = json.loads(meta_path.read_text(encoding="utf-8"))
            if old.get("sha256") == row["sha256"]:  # file sama, hasil lama masih berlaku
                metas.append(old)
                continue
        t0 = time.time()
        meta = process(row, raw, out)
        metas.append(meta)
        print(f"[{n}/{len(rows)}] {row['path']}  {meta['n_pages']} hlm  {meta['status']}  {time.time() - t0:.1f}s", flush=True)

    fields = ["doc_id", "entity_id", "periode", "path", "n_pages", "n_chars", "empty_pages",
              "first_balance_sheet_page", "first_income_page", "status", "catatan"]
    with (reg / "extraction_report.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(metas)

    check = [m for m in metas if m["status"] != "OK"]
    print(f"\nSelesai: {len(metas)} dokumen, {len(check)} perlu diperiksa. Waktu {time.time() - started:.0f} detik.")
    for m in check[:25]:
        print(f"  PERIKSA {m['path']}: {m['catatan']}")
    if len(check) > 25:
        print(f"  ... dan {len(check) - 25} lainnya (lihat registry/extraction_report.csv)")
    print("Laporan lengkap: registry/extraction_report.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
