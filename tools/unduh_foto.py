"""Unduh foto asli ke cek_foto/<Nama Produk>.jpg (untuk diunggah ke folder Drive "Foto Produk Annafi").
  python tools/unduh_foto.py "Nama|URL" ..."""
import io, re, sys
from pathlib import Path
import requests
from PIL import Image

out = Path("cek_foto"); out.mkdir(exist_ok=True)
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
for a in sys.argv[1:]:
    nama, url = [x.strip() for x in a.split("|", 1)]
    try:
        r = requests.get(url, headers=HDR, timeout=40); r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
        f = out / (re.sub(r'[\\/:*?"<>|]', "", nama) + ".jpg")
        im.save(f, "JPEG", quality=95)
        print("ok", nama, im.size, f.stat().st_size)
    except Exception as e:
        print("GAGAL", nama, e)
