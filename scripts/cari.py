"""Cari kata kunci di teks hasil ingest dan tampilkan doc_id, halaman, kutipan.

Contoh:
  python scripts/cari.py E01 2024-FY "laba bersih"
  python scripts/cari.py E01 2024-FY "laba bersih" --angka 54.836.305
  python scripts/cari.py E01 "" "laba bersih" --max 20      (semua periode)
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "data" / "processed" / "pages"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entitas", help="mis. E01")
    ap.add_argument("periode", help="mis. 2024-FY, kosongkan dengan '' untuk semua")
    ap.add_argument("kata", help="kata kunci, tidak peka huruf besar/kecil")
    ap.add_argument("--angka", help="hanya halaman yang memuat angka ini persis")
    ap.add_argument("--max", type=int, default=8, help="jumlah hasil maksimum")
    ap.add_argument("--lebar", type=int, default=110, help="panjang kutipan")
    a = ap.parse_args()

    files = sorted(PAGES.glob(f"{a.entitas}_{a.periode}*.jsonl" if a.periode else f"{a.entitas}_*.jsonl"))
    if not files:
        sys.exit(f"Tidak ada file di {PAGES} untuk {a.entitas} {a.periode}. Sudah menjalankan src/ingest.py?")
    pola = re.compile(re.escape(a.kata), re.I)
    n = 0
    for fp in files:
        for line in fp.open(encoding="utf-8"):
            r = json.loads(line)
            t = r.get("text", "")
            if a.angka and a.angka not in t:
                continue
            for m in pola.finditer(t):
                s = max(0, m.start() - 20)
                kutip = " ".join(t[s:s + a.lebar].split())
                print(f"{r['doc_id']}  {fp.stem.split('.')[0]}  hal {r['page']}:  ...{kutip}...")
                n += 1
                break
            if n >= a.max:
                print(f"(dibatasi {a.max}; pakai --max untuk lebih banyak)")
                return
    if n == 0:
        print("Tidak ketemu. Coba kata lain (mis. 'laba tahun berjalan', 'profit for the year').")


if __name__ == "__main__":
    main()
