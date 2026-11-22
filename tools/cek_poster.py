"""Render poster story jadwal N hari ke depan (tanpa memposting) ke cek_foto/ untuk dicek: foto terpotong/salah?
  python tools/cek_poster.py [hari=7]"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import config, sheet, images, render  # noqa: E402

out = Path("cek_foto"); out.mkdir(exist_ok=True)
hari = int(sys.argv[1]) if len(sys.argv) > 1 else 7
now = datetime.now(config.TZ)
rows, _ = sheet.load(config.SHEET_CSV_URL)
for p in rows:
    if p["format"] != "story" or p["tunda"] or not (now - timedelta(hours=2) <= p["waktu"] <= now + timedelta(days=hari)):
        continue
    nama = f"{p['waktu']:%m%d-%H%M}"
    img = out / f"{nama}-foto.png"
    try:
        sumber = images.siapkan(p, None, str(img))
    except Exception as e:
        print(nama, p["nama"], "TANPA FOTO:", e); img, sumber = None, ""
    render.render(p, str(img) if img else None, str(out / f"{nama}.jpg"))
    print(nama, p["nama"], "|", sumber)
