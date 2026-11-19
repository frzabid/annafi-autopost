"""Baca jadwal dari Google Sheet (link bagikan biasa atau 'Publikasikan ke web' CSV)."""
import csv, hashlib, io, json, re
from collections import defaultdict
from datetime import datetime, timedelta
import requests
from config import TZ, JAM_STORY, JAM_FEED, MODE_PROMO

KOLOM = ["tanggal", "jam", "jenis", "nama", "kategori", "detail", "poin",
         "label_harga_1", "harga_1", "label_harga_2", "harga_2",
         "gambar", "caption", "tunda"]

# jenis -> katalog tayang sebagai Story IG; lainnya jadi postingan feed IG + FB (wajib disetujui)
JENIS = {"katalog": "katalog", "produk": "katalog", "story": "katalog", "": "katalog",
         "edukasi": "edukasi", "tips": "edukasi", "promo": "promo", "diskon": "promo",
         "info": "info", "pengumuman": "info", "momen": "momen", "spesial": "momen", "ucapan": "momen"}


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


def _tanggal(tgl: str):
    return _waktu(tgl, "00:00")


def parse(text: str):
    rows, errors = [], []
    reader = csv.DictReader(io.StringIO(text))
    reader.fieldnames = [(h or "").strip().lower().replace(" ", "_") for h in reader.fieldnames or []]
    slot_terpakai = defaultdict(int)  # (tanggal, format) -> jumlah jam otomatis yang sudah dipakai
    for i, r in enumerate(reader, start=2):
        r = {k: (v or "").strip() for k, v in r.items() if k}
        if not r.get("nama"):
            continue
        jenis = JENIS.get(r.get("jenis", "").lower())
        if not jenis:
            errors.append(f"Baris {i} ({r['nama']}): jenis '{r.get('jenis')}' tidak dikenal "
                          f"(pakai katalog/edukasi/promo/info/momen)")
            continue
        fmt = "story" if jenis == "katalog" else "konten"
        jam_otomatis = not r.get("jam")
        if jam_otomatis:  # jam kosong -> pakai jam ramai
            tgl = _tanggal(r.get("tanggal"))
            if not tgl:
                errors.append(f"Baris {i} ({r['nama']}): tanggal tidak terbaca")
                continue
            daftar = JAM_STORY if fmt == "story" else JAM_FEED
            n = slot_terpakai[(tgl.date(), fmt)]
            slot_terpakai[(tgl.date(), fmt)] += 1
            hh, mm = map(int, daftar[n % len(daftar)].split(":"))
            waktu = tgl.replace(hour=hh, minute=mm) + timedelta(minutes=30 * (n // len(daftar)))
        else:
            waktu = _waktu(r.get("tanggal"), r.get("jam"))
        if not waktu:
            errors.append(f"Baris {i} ({r['nama']}): tanggal/jam tidak terbaca")
            continue
        harga = []
        for n in (1, 2):
            v = _harga(r.get(f"harga_{n}"))
            if v:
                harga.append({"label": r.get(f"label_harga_{n}") or ("Harga" if n == 1 else "Harga lain"), "nilai": v})
        if jenis == "katalog" and not harga:
            errors.append(f"Baris {i} ({r['nama']}): harga kosong")
            continue
        if fmt == "konten" and not MODE_PROMO:
            if jenis == "promo":
                errors.append(f"Baris {i} ({r['nama']}): konten promo sedang dimatikan, baris ini dilewati "
                              "(ubah jenisnya ke edukasi/info/momen kalau tetap mau diposting)")
                continue
            harga = []  # feed umum: tanpa harga
        poin = [x.strip(" •-") for x in re.split(r"[;\n]", r.get("poin", "")) if x.strip(" •-")]
        if fmt == "konten" and not poin and not harga:
            errors.append(f"Baris {i} ({r['nama']}): kolom poin kosong (pisahkan tiap poin dengan ;)")
            continue
        p = {
            "baris": i, "waktu": waktu, "jam_otomatis": jam_otomatis, "jenis": jenis, "format": fmt,
            "butuh_setuju": fmt == "konten", "nama": r["nama"], "kategori": r.get("kategori", "").upper(),
            "detail": r.get("detail", ""), "poin": poin[:6], "harga": harga, "gambar": r.get("gambar", ""),
            "caption": r.get("caption", ""), "tunda": r.get("tunda", "").lower() in ("ya", "y", "tunda", "1", "true"),
        }
        # id tetap selama tanggal, jam & nama sama; hash isi untuk mendeteksi perubahan setelah pratinjau
        p["id"] = hashlib.sha1(f"{waktu.isoformat()}|{p['nama'].lower()}".encode()).hexdigest()[:10]
        p["hash_isi"] = hashlib.sha1(json.dumps(
            [p["jenis"], p["kategori"], p["detail"], p["poin"], p["harga"], p["gambar"], p["caption"]],
            sort_keys=True).encode()).hexdigest()[:10]
        rows.append(p)
    return rows, errors


def csv_url(url: str) -> str:
    """Terima link 'Publikasikan ke web' (CSV) ATAU link bagikan biasa
    (docs.google.com/spreadsheets/d/<ID>/edit...), lalu ubah ke link ekspor CSV."""
    m = re.search(r"docs\.google\.com/spreadsheets/d/([\w-]+)", url)
    if not m or m[1] == "e" or "output=csv" in url or "format=csv" in url:
        return url
    gid = re.search(r"[#&?]gid=(\d+)", url)
    return f"https://docs.google.com/spreadsheets/d/{m[1]}/export?format=csv" + (f"&gid={gid[1]}" if gid else "")


def load(url_or_path: str):
    if url_or_path.startswith("http"):
        resp = requests.get(csv_url(url_or_path), timeout=30)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        return parse(resp.text)
    with open(url_or_path, encoding="utf-8") as f:
        return parse(f.read())


def load_persetujuan(url: str):
    """Baca tab 'Persetujuan' (diisi Manajer AI di Apps Script saat tombol ✅/❌ ditekan).
    Kembalikan daftar (id, hash, aksi) urut waktu. Kosong kalau tab belum ada."""
    m = re.search(r"docs\.google\.com/spreadsheets/d/([\w-]+)", url or "")
    if not m or m[1] == "e":
        return []
    try:
        r = requests.get(f"https://docs.google.com/spreadsheets/d/{m[1]}/gviz/tq",
                         params={"tqx": "out:csv", "sheet": "Persetujuan"}, timeout=30)
        r.raise_for_status()
        r.encoding = "utf-8"
    except Exception as e:
        print(f"  tab Persetujuan tidak terbaca: {e}")
        return []
    hasil = []
    for row in csv.DictReader(io.StringIO(r.text)):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        if row.get("id") and row.get("hash") and row.get("aksi") in ("setuju", "batal"):
            hasil.append((row["id"], row["hash"], row["aksi"]))
    return hasil
