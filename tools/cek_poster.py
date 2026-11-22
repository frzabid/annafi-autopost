"""Render poster story tanpa memposting, ke cek_foto/, untuk dicek (foto terpotong/salah?).
  python tools/cek_poster.py 7                          -> story jadwal 7 hari ke depan (dari sheet)
  python tools/cek_poster.py "Nama|URL|harga|KATEGORI" ... -> poster uji dari daftar link foto"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import config, sheet, images, render  # noqa: E402

out = (ROOT / "cek_foto").resolve(); out.mkdir(exist_ok=True)
args = sys.argv[1:] or ["7"]
if args[0].isdigit():
    now = datetime.now(config.TZ)
    rows, _ = sheet.load(config.SHEET_CSV_URL)
    daftar = [(f"{p['waktu']:%m%d-%H%M}", p) for p in rows if p["format"] == "story" and not p["tunda"]
              and now - timedelta(hours=2) <= p["waktu"] <= now + timedelta(days=int(args[0]))]
else:
    daftar = []
    for k, a in enumerate(args):
        nama, url, harga, kat = (a.split("|") + ["", "", "", ""])[:4]
        daftar.append((f"{k:02d}", {"id": f"uji{k}", "format": "story", "jenis": "katalog", "nama": nama.strip(),
                                    "kategori": (kat or "PENSIL WARNA & KRAYON").strip().upper(), "detail": "", "poin": [],
                                    "harga": [{"label": "Harga", "nilai": int(harga or 0)}], "gambar": url.strip(),
                                    "caption": "", "tema": "", "produk": [], "foto_produk": []}))
for kode, p in daftar:
    img = out / f"{kode}-foto.png"
    try:
        sumber = images.siapkan(p, None, str(img))
    except Exception as e:
        print(kode, p["nama"], "TANPA FOTO:", e); img, sumber = None, ""
    render.render(p, str(img) if img else None, str(out / f"{kode}.jpg"))
    print(kode, p["nama"], "|", sumber)
