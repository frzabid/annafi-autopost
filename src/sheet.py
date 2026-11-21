"""Baca jadwal dari Google Sheet (link bagikan biasa atau 'Publikasikan ke web' CSV)."""
import csv, hashlib, io, json, re
from collections import defaultdict
from datetime import datetime, timedelta
import requests
from config import TZ, JAM_STORY, JAM_FEED, JAM_CERITA, MODE_PROMO

KOLOM = ["tanggal", "jam", "jenis", "nama", "kategori", "detail", "poin", "tema", "produk",
         "label_harga_1", "harga_1", "label_harga_2", "harga_2",
         "gambar", "caption", "tunda"]

# jenis -> katalog tayang sebagai Story IG; lainnya jadi postingan feed IG + FB (wajib disetujui)
JENIS = {"katalog": "katalog", "produk": "katalog", "story": "katalog", "": "katalog",
         "edukasi": "edukasi", "tips": "edukasi", "promo": "promo", "diskon": "promo",
         "info": "info", "pengumuman": "info", "momen": "momen", "spesial": "momen", "ucapan": "momen",
         "cerita": "cerita", "reel": "cerita", "reels": "cerita"}


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
                          f"(pakai katalog/edukasi/promo/info/momen/cerita)")
            continue
        fmt = "story" if jenis == "katalog" else "reel" if jenis == "cerita" else "konten"
        jam_otomatis = not r.get("jam")
        ditunda = r.get("tunda", "").lower() in ("ya", "y", "tunda", "1", "true")
        if jam_otomatis and ditunda:  # baris ditunda tidak memakai jatah jam ramai
            waktu = _waktu(r.get("tanggal"), "23:59")
        elif jam_otomatis:  # jam kosong -> pakai jam ramai
            tgl = _tanggal(r.get("tanggal"))
            if not tgl:
                errors.append(f"Baris {i} ({r['nama']}): tanggal tidak terbaca")
                continue
            daftar = JAM_STORY if fmt == "story" else JAM_CERITA if fmt == "reel" else JAM_FEED
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
            "butuh_setuju": fmt != "story", "nama": r["nama"], "kategori": r.get("kategori", "").upper(),
            "detail": r.get("detail", ""), "poin": poin[:6], "harga": harga, "gambar": r.get("gambar", ""),
            "caption": r.get("caption", ""), "tunda": r.get("tunda", "").lower() in ("ya", "y", "tunda", "1", "true"),
            "tema": r.get("tema", "").strip(),
            "produk": [x.strip() for x in re.split(r"[;\n]", r.get("produk", "")) if x.strip()][:4],
            "foto_produk": [],
        }
        # id tetap selama tanggal, jam & nama sama; hash isi untuk mendeteksi perubahan setelah pratinjau
        p["id"] = hashlib.sha1(f"{waktu.isoformat()}|{p['nama'].lower()}".encode()).hexdigest()[:10]
        if fmt == "reel":
            m = re.search(r"part\s*(\d+)", f"{p['nama']} {p['detail']}", re.I)
            if not m:
                errors.append(f"Baris {i} ({r['nama']}): cerita harus menyebut nomor part, misal 'Part 1'")
                continue
            p["part"] = int(m[1])
            p["poin"], p["harga"] = [], []
        p["hash_isi"] = _hash(p)
        rows.append(p)
    return rows, errors


def _hash(p):
    isi = [p["jenis"], p["kategori"], p["detail"], p["poin"], p["harga"], p["gambar"], p["caption"]]
    if p.get("tema") or p.get("produk"):  # kolom baru: hanya ikut kalau terisi, supaya hash lama tetap sama
        isi += [p.get("tema", ""), p.get("produk", []), p.get("foto_produk", [])]
    return hashlib.sha1(json.dumps(isi, sort_keys=True).encode()).hexdigest()[:10]


def _token(nama: str):
    return sorted(re.findall(r"[a-z0-9]+", nama.lower()))


def pakai_foto_produk(rows, produk):
    """Story yang kolom gambarnya kosong memakai foto dari tab Produk (kiriman bot / folder Drive).
    Nama dicocokkan per kata, jadi "Pensil Joyko 6151 HB" = "Pensil Joyko HB 6151"."""
    foto = [(set(_token(n)), _token(n), link) for n, link in produk if link.startswith("http")]
    nama_asli = {link: n for n, link in produk}

    def cari(nama):
        t = _token(nama)
        sama = [link for _, tok, link in foto if tok == t]
        if not sama:  # semua kata ada di nama produk, dan hanya satu produk yang cocok
            sama = [link for st, _, link in foto if set(t) <= st]
            sama = sama if len(sama) == 1 else []
        return sama[0] if sama else None

    for p in rows:  # feed: kolom produk -> foto dari tab Produk untuk slide kolase (tanpa harga)
        if p["format"] == "konten" and p.get("produk"):
            p["foto_produk"] = [(nama_asli[l], l) for l in (cari(n) for n in p["produk"]) if l]
            p["hash_isi"] = _hash(p)
    for p in rows:
        if p["format"] != "story" or (p["gambar"] and not p["gambar"].lower().startswith("cari")):
            continue
        link = cari(p["nama"])
        if link:
            p["gambar"] = link
            p["hash_isi"] = _hash(p)
    return rows


def _tab(url: str, nama_tab: str) -> str | None:
    m = re.search(r"docs\.google\.com/spreadsheets/d/([\w-]+)", url or "")
    if not m or m[1] == "e":
        return None
    try:
        r = requests.get(f"https://docs.google.com/spreadsheets/d/{m[1]}/gviz/tq",
                         params={"tqx": "out:csv", "sheet": nama_tab}, timeout=30)
        r.raise_for_status()
        r.encoding = "utf-8"
        return r.text
    except Exception as e:
        print(f"  tab {nama_tab} tidak terbaca: {e}")
        return None


def load_permintaan(url: str):
    """Permintaan contoh poster dari chat bot (tab 'Permintaan'): daftar (id, data dict) berstatus baru."""
    teks = _tab(url, "Permintaan")
    hasil = []
    for row in csv.DictReader(io.StringIO(teks or "")):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        if row.get("id") and row.get("status", "baru") == "baru" and row.get("data"):
            try:
                hasil.append((row["id"], json.loads(row["data"])))
            except ValueError:
                print(f"  permintaan {row['id']}: data rusak")
    return hasil


def baris_dari_dict(d: dict, url: str | None = None):
    """Ubah satu baris (dict kolom Jadwal) jadi item siap render, lewat parser yang sama dengan sheet."""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=KOLOM, extrasaction="ignore")
    w.writeheader()
    w.writerow({k: d.get(k, "") if not isinstance(d.get(k), list) else "; ".join(d[k]) for k in KOLOM})
    rows, errors = parse(buf.getvalue())
    if rows and url:
        pakai_foto_produk(rows, load_foto_produk(url))
    return (rows[0] if rows else None), errors


def load_foto_produk(url: str):
    teks = _tab(url, "Produk")
    if not teks:
        return []
    hasil = []
    for row in csv.DictReader(io.StringIO(teks)):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        if row.get("nama") and row.get("gambar", "").startswith("http"):
            hasil.append((row["nama"], row["gambar"]))
    return hasil


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
        rows, errors = parse(resp.text)
        return pakai_foto_produk(rows, load_foto_produk(url_or_path)), errors
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
