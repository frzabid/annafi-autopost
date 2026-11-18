"""Baca jadwal dari Google Sheet yang di-'Publikasikan ke web' sebagai CSV."""
import csv, hashlib, io, json, re
from datetime import datetime
import requests
from config import TZ

KOLOM = ["tanggal", "jam", "nama", "kategori", "detail",
         "label_harga_1", "harga_1", "label_harga_2", "harga_2",
         "gambar", "caption", "tunda"]


def _harga(s: str):
    digit = re.sub(r"[^\d]", "", s or "")
    return int(digit) if digit else None


def _waktu(tgl: str, jam: str):
    tgl, jam = (tgl or "").strip(), (jam or "").strip().replace(".", ":")
    for f in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        try:
            d = datetime.strptime(tgl, f)
            break
        except ValueError:
            d = None
    if not d:
        return None
    m = re.match(r"^(\d{1,2}):(\d{2})", jam)
    if not m:
        return None
    try:
        return d.replace(hour=int(m[1]), minute=int(m[2]), tzinfo=TZ)
    except ValueError:  # misal jam 25:99
        return None


def parse(text: str):
    rows, errors = [], []
    reader = csv.DictReader(io.StringIO(text))
    reader.fieldnames = [(h or "").strip().lower().replace(" ", "_") for h in reader.fieldnames or []]
    for i, r in enumerate(reader, start=2):
        r = {k: (v or "").strip() for k, v in r.items() if k}
        if not r.get("nama"):
            continue
        waktu = _waktu(r.get("tanggal"), r.get("jam"))
        if not waktu:
            errors.append(f"Baris {i} ({r['nama']}): tanggal/jam tidak terbaca")
            continue
        harga = []
        for n in (1, 2):
            v = _harga(r.get(f"harga_{n}"))
            if v:
                harga.append({"label": r.get(f"label_harga_{n}") or ("Harga" if n == 1 else "Harga lain"), "nilai": v})
        if not harga:
            errors.append(f"Baris {i} ({r['nama']}): harga kosong")
            continue
        p = {
            "baris": i, "waktu": waktu, "nama": r["nama"], "kategori": r.get("kategori", "").upper(),
            "detail": r.get("detail", ""), "harga": harga, "gambar": r.get("gambar", ""),
            "caption": r.get("caption", ""), "tunda": r.get("tunda", "").lower() in ("ya", "y", "tunda", "1", "true"),
        }
        # id tetap selama tanggal, jam & nama sama; hash isi untuk mendeteksi perubahan setelah pratinjau
        p["id"] = hashlib.sha1(f"{waktu.isoformat()}|{p['nama'].lower()}".encode()).hexdigest()[:10]
        p["hash_isi"] = hashlib.sha1(json.dumps(
            [p["kategori"], p["detail"], p["harga"], p["gambar"], p["caption"]], sort_keys=True).encode()).hexdigest()[:10]
        rows.append(p)
    return rows, errors


def load(url_or_path: str):
    if url_or_path.startswith("http"):
        resp = requests.get(url_or_path, timeout=30)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        return parse(resp.text)
    with open(url_or_path, encoding="utf-8") as f:
        return parse(f.read())
