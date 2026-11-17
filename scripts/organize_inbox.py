#!/usr/bin/env python3
"""Rapikan dokumen mentah: beri nama dan pindahkan ke data/raw/<ENTITY_ID>/ otomatis.

Cara pakai:
  1. Kumpulkan semua PDF hasil unduhan ke satu folder: data/inbox/ (boleh campur aduk).
  2. Pratinjau (tidak mengubah apa pun):
        python scripts/organize_inbox.py
  3. Periksa tabel di layar dan registry/rename_preview.csv, lalu jalankan:
        python scripts/organize_inbox.py --apply
  4. Jalankan python scripts/update_register.py untuk menghitung hash dan mendaftarkan dokumen.

Skrip membaca 3 halaman pertama setiap PDF untuk menentukan:
  - entitas (dicocokkan dengan nama perusahaan),
  - periode (31 Maret=Q1, 30 Juni=Q2, 30 September=Q3, 31 Desember=FY) dan tahun,
  - bahasa (hanya versi Indonesia yang diproses otomatis),
  - petunjuk status audit (hanya SARAN, tetap perlu dicek sekilas).

File yang meragukan TIDAK dipindahkan dan diberi status REVIEW. Semua pemindahan
dicatat di registry/rename_log.csv agar bisa ditelusuri.
"""
import argparse
import csv
import hashlib
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:  # versi lama
    import fitz

# Nama perusahaan (huruf besar, tanpa tanda baca) untuk mencocokkan halaman judul.
ALIASES = {
    "E01": ["BANK CENTRAL ASIA"],
    "E02": ["BANK RAKYAT INDONESIA"],
    "E03": ["BANK MANDIRI"],
    "E04": ["BANK NEGARA INDONESIA"],
    "E05": ["BANK SYARIAH INDONESIA"],
    "E06": ["CIMB NIAGA"],
    "E07": ["BANK TABUNGAN NEGARA"],
    "E08": ["BANK DANAMON"],
    "E09": ["OCBC NISP", "BANK OCBC", "OCBC INDONESIA"],
    "E10": ["BANK PAN INDONESIA", "PANIN"],
    "E11": ["BANK MEGA"],
    "E12": ["BANK PEMBANGUNAN DAERAH JAWA TENGAH", "BANK JATENG", "BPD JATENG"],
    "E13": ["BANK PEMBANGUNAN DAERAH JAWA TIMUR", "BANK JATIM", "BPD JATIM"],
    "E14": ["BTPN SYARIAH"],
    "E15": ["BANK JAGO"],
    "E16": ["ADARO ENERGY", "ALAMTRI RESOURCES"],
    "E17": ["BUKIT ASAM"],
    "E18": ["INDO TAMBANGRAYA MEGAH"],
    "E19": ["BAYAN RESOURCES"],
    "E20": ["HARUM ENERGY"],
    "E21": ["INDIKA ENERGY"],
    "E22": ["BUMI RESOURCES"],
    "E23": ["ADARO MINERALS", "ALAMTRI MINERALS"],
    "E24": ["ANEKA TAMBANG"],
    "E25": ["VALE INDONESIA"],
    "E26": ["MERDEKA COPPER GOLD"],
    "E27": ["TIMAH"],
    "E28": ["MERDEKA BATTERY MATERIALS"],
    "E29": ["TRIMEGAH BANGUN PERSADA"],
    "E30": ["AMMAN MINERAL"],
}

MONTHS = {
    "JANUARI": 1, "JANUARY": 1, "FEBRUARI": 2, "FEBRUARY": 2, "MARET": 3, "MARCH": 3,
    "APRIL": 4, "MEI": 5, "MAY": 5, "JUNI": 6, "JUNE": 6, "JULI": 7, "JULY": 7,
    "AGUSTUS": 8, "AUGUST": 8, "SEPTEMBER": 9, "OKTOBER": 10, "OCTOBER": 10,
    "NOVEMBER": 11, "DESEMBER": 12, "DECEMBER": 12,
}
PERIOD_END = {(31, 3): "Q1", (30, 6): "Q2", (30, 9): "Q3", (31, 12): "FY"}
MONTH_RE = "|".join(sorted(MONTHS, key=len, reverse=True))
DATE_ID = re.compile(rf"\b(\d{{1,2}}) ({MONTH_RE}) (20\d{{2}})\b")
DATE_EN = re.compile(rf"\b({MONTH_RE}) (\d{{1,2}}) (20\d{{2}})\b")

AUDITOR_PHRASES = ["LAPORAN AUDITOR INDEPENDEN", "INDEPENDENT AUDITORS REPORT", "INDEPENDENT AUDITOR S REPORT"]
REVIEW_PHRASES = ["LAPORAN REVIU", "LAPORAN TINJAUAN", "TINJAUAN TERBATAS", "LIMITED REVIEW",
                  "REVIEW REPORT", "REPORT ON REVIEW"]
UNAUDITED_PHRASES = ["TIDAK DIAUDIT", "UNAUDITED", "BELUM DIAUDIT"]


def norm(text: str) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def extract(path: Path):
    """Kembalikan (teks 3 halaman pertama, teks bagian awal+akhir dokumen), sudah dinormalisasi."""
    doc = fitz.open(path)
    n = len(doc)
    head = " ".join(doc[i].get_text() for i in range(min(3, n)))
    idx = sorted(set(range(min(30, n))) | set(range(max(0, n - 30), n)))
    body = " ".join(doc[i].get_text() for i in idx)
    doc.close()
    return norm(head), norm(body)


def detect_entity(head: str, entity_ids):
    scores = {}
    for eid, names in ALIASES.items():
        if eid not in entity_ids:
            continue
        s = sum(head.count(f" {norm(a)} ") + (1 if head.startswith(norm(a) + " ") else 0) for a in names)
        if s:
            scores[eid] = s
    if not scores:
        return None, "nama entitas tidak terdeteksi"
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return None, f"entitas ambigu ({ranked[0][0]} vs {ranked[1][0]})"
    return ranked[0][0], ""


def detect_period(head: str):
    hits = []
    for m in DATE_ID.finditer(head):
        day, month, year = int(m.group(1)), MONTHS[m.group(2)], int(m.group(3))
        if (day, month) in PERIOD_END:
            hits.append((m.start(), PERIOD_END[(day, month)], year))
    for m in DATE_EN.finditer(head):
        month, day, year = MONTHS[m.group(1)], int(m.group(2)), int(m.group(3))
        if (day, month) in PERIOD_END:
            hits.append((m.start(), PERIOD_END[(day, month)], year))
    if not hits:
        return None, None
    hits.sort()
    return hits[0][1], hits[0][2]  # tanggal pertama = periode laporan (pembanding muncul setelahnya)


def filename_years(name: str):
    years = {int(y) for y in re.findall(r"(?<!\d)(20[2-3]\d)(?!\d)", name)}
    for m in re.finditer(r"(?i)(jan|feb|mar|apr|mei|may|jun|jul|agu|aug|sep|okt|oct|nov|des|dec)[a-z]*[ _-]?(\d{2})(?!\d)", name):
        years.add(2000 + int(m.group(2)))
    for m in re.finditer(r"(?<!\d)(0[1-9]|1[0-2])(2[2-6])(?!\d)", name):
        years.add(2000 + int(m.group(2)))
    return years


def has_any(text: str, phrases):
    return any(p in text for p in phrases)


def audit_hint(period: str, head: str, body: str):
    """Saran status audit + dasar penentuannya (bukan keputusan final)."""
    auditor = has_any(body, AUDITOR_PHRASES)
    review = has_any(body, REVIEW_PHRASES)
    unaudited = has_any(head, UNAUDITED_PHRASES)
    if period == "FY":
        if auditor:
            return "ya", "laporan auditor independen ditemukan di dokumen"
        if unaudited:
            return "tidak", "tertulis tidak diaudit di halaman judul"
        return "ya", "laporan tahunan (label IDX: Audit); teks laporan auditor tidak terdeteksi, cek sekilas"
    if unaudited:
        return "tidak", "tertulis tidak diaudit/unaudited di halaman judul"
    if auditor:
        return "ya", "laporan auditor independen ditemukan pada laporan interim"
    if review:
        return "reviu", "laporan reviu/tinjauan terbatas ditemukan"
    return "tidak", "interim tanpa laporan auditor atau reviu terdeteksi"


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(path: Path, entity_ids):
    item = {"old": path, "status": "OK", "entity": "", "period": "", "year": "", "new": "",
            "audited_hint": "", "basis": "", "note": ""}
    try:
        head, body = extract(path)
    except Exception as exc:  # file rusak/terenkripsi
        item.update(status="REVIEW", note=f"tidak bisa dibuka: {exc}")
        return item
    if len(head) < 40:
        item.update(status="REVIEW", note="tidak ada teks (mungkin hasil scan, perlu OCR)")
        return item
    if "LAPORAN KEBERLANJUTAN" in head or "SUSTAINABILITY REPORT" in head:
        item.update(status="REVIEW", note="laporan keberlanjutan, bukan laporan keuangan")
        return item
    is_id = "LAPORAN KEUANGAN" in head
    is_en = "FINANCIAL STATEMENTS" in head
    if not is_id and is_en:
        item.update(status="REVIEW", note="versi bahasa Inggris, gunakan versi Indonesia")
        return item
    if not is_id:
        item.update(status="REVIEW", note="bukan laporan keuangan? (judul tidak terdeteksi)")
        return item
    eid, why = detect_entity(head, entity_ids)
    if not eid:
        item.update(status="REVIEW", note=why)
        return item
    period, year = detect_period(head)
    if not period:
        item.update(entity=eid, status="REVIEW", note="periode tidak terdeteksi")
        return item
    fy = filename_years(path.name)
    if fy and year not in fy:
        item.update(entity=eid, period=period, year=year, status="REVIEW",
                    note=f"tahun di isi ({year}) beda dengan nama file {sorted(fy)}")
        return item
    hint, basis = audit_hint(period, head, body)
    item.update(entity=eid, period=period, year=year, audited_hint=hint, basis=basis,
                new=f"{eid}/{eid}_{year}-{period}_laporan-keuangan{path.suffix.lower()}")
    return item


def short(s: str, n: int):
    return s if len(s) <= n else s[: n - 3] + "..."


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inbox", default="data/inbox", help="folder PDF mentah (default data/inbox)")
    ap.add_argument("--raw", default="data/raw", help="folder tujuan (default data/raw)")
    ap.add_argument("--registry", default="registry", help="folder register (default registry)")
    ap.add_argument("--apply", action="store_true", help="benar-benar memindahkan file")
    ap.add_argument("--copy", action="store_true", help="salin, bukan pindahkan")
    args = ap.parse_args()

    inbox, raw, reg = Path(args.inbox), Path(args.raw), Path(args.registry)
    if not inbox.is_dir():
        print(f"Folder tidak ditemukan: {inbox}. Buat folder itu dan isi dengan PDF.", file=sys.stderr)
        return 1
    entity_ids = set(ALIASES)
    ent_csv = reg / "source_register.csv"
    if ent_csv.exists():
        with ent_csv.open(newline="", encoding="utf-8") as f:
            entity_ids = {r["entity_id"] for r in csv.DictReader(f)} & set(ALIASES)

    pdfs = sorted(p for p in inbox.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf")
    if not pdfs:
        print("Tidak ada PDF di", inbox)
        return 0
    print(f"Memeriksa {len(pdfs)} PDF ...")
    items = [classify(p, entity_ids) for p in pdfs]

    # tangani target ganda dan target yang sudah ada
    groups = {}
    for it in items:
        if it["status"] == "OK":
            groups.setdefault(it["new"], []).append(it)
    for new, grp in groups.items():
        dest = raw / new
        if dest.exists():
            same = [g for g in grp if sha256(g["old"]) == sha256(dest)]
            for g in grp:
                g["status"] = "SUDAH-ADA" if g in same else "REVIEW"
                g["note"] = "sudah ada di data/raw" if g in same else "nama tujuan sudah dipakai file lain"
            continue
        if len(grp) > 1:
            digests = {sha256(g["old"]) for g in grp}
            if len(digests) == 1:
                for g in grp[1:]:
                    g["status"], g["note"] = "DUPLIKAT", f"isi sama dengan {grp[0]['old'].name}"
            else:
                for g in grp:
                    g["status"] = "REVIEW"
                    g["note"] = "beberapa file berbeda untuk periode yang sama, pilih satu manual"

    # tampilkan ringkasan
    print(f"\n{'STATUS':<10}{'FILE LAMA':<46}{'NAMA BARU':<42}{'AUDIT?':<8}")
    print("-" * 106)
    for it in items:
        target = it["new"] if it["status"] == "OK" else ("- " + short(it["note"], 38))
        print(f"{it['status']:<10}{short(it['old'].name, 44):<46}{short(target, 40):<42}{it['audited_hint']:<8}")

    counts = {}
    for it in items:
        counts[it["status"]] = counts.get(it["status"], 0) + 1
    print("\nRingkasan:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    reg.mkdir(parents=True, exist_ok=True)
    preview = reg / "rename_preview.csv"
    with preview.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["status", "file_lama", "nama_baru", "entitas", "periode", "tahun", "audited_hint", "dasar", "catatan"])
        for it in items:
            w.writerow([it["status"], it["old"], it["new"], it["entity"], it["period"], it["year"],
                        it["audited_hint"], it["basis"], it["note"]])
    print(f"Pratinjau lengkap: {preview}")

    if not args.apply:
        print("\nMode pratinjau: belum ada file yang dipindahkan. Tambahkan --apply untuk menjalankan.")
        return 0

    log = reg / "rename_log.csv"
    new_log = not log.exists()
    moved = 0
    with log.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_log:
            w.writerow(["waktu", "file_lama", "path_baru", "audited_hint", "dasar"])
        for it in items:
            if it["status"] != "OK":
                continue
            dest = raw / it["new"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            (shutil.copy2 if args.copy else shutil.move)(str(it["old"]), str(dest))
            w.writerow([datetime.now().isoformat(timespec="seconds"), it["old"], it["new"],
                        it["audited_hint"], it["basis"]])
            moved += 1
    print(f"\n{moved} file {'disalin' if args.copy else 'dipindahkan'} ke {raw}. Log: {log}")
    print("Berikutnya: python scripts/update_register.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
