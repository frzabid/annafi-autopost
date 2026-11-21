"""Unduh foto produk, simpan sebagai PNG bernama = nama produk, lalu kirim ke Telegram sebagai file.
Caption = nama produk persis, jadi tinggal diteruskan (forward) balik ke bot supaya tersimpan permanen
di Drive "Foto Produk Annafi" + tab Produk, atau simpan file-nya ke folder itu lalu kirim /foto.
Pemakaian: python tools/kirim_foto.py "Nama|URL" "Nama|URL" ..."""
import io, os, re, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import requests
from PIL import Image
import notify

HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
os.makedirs("foto_png", exist_ok=True)
daftar = [a.split("|", 1) for a in sys.argv[1:] if "|" in a]
notify.pesan(f"🖼️ <b>{len(daftar)} foto produk</b> (PNG, kualitas asli) untuk story minggu ini.\n"
             "Supaya tersimpan permanen: pilih semua file di bawah → <b>Teruskan</b> ke chat bot ini lagi "
             "(caption = nama produk, otomatis cocok). Atau simpan ke folder Drive <b>Foto Produk Annafi</b> lalu kirim /foto.")
gagal = []
for nama, url in daftar:
    nama, url = nama.strip(), url.strip()
    try:
        r = requests.get(url, headers=HDR, timeout=40); r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)); im.load()
        im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
        path = os.path.join("foto_png", re.sub(r'[\\/:*?"<>|]', "", nama) + ".png")
        im.save(path, "PNG", optimize=True)
        notify.dokumen(path, nama)
        print("ok", nama, im.size)
        time.sleep(1.2)
    except Exception as e:
        print("GAGAL", nama, e); gagal.append(nama)
if gagal:
    notify.pesan("⚠️ Gagal diunduh: " + ", ".join(gagal))
