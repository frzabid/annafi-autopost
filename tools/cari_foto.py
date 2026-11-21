"""Cari foto produk dari internet (sama seperti bot) lalu simpan pratinjaunya ke cek_foto/ untuk dicek manusia.
  python tools/cari_foto.py "Nama Produk|KATEGORI" ...
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import images  # noqa: E402

out = Path("cek_foto")
out.mkdir(exist_ok=True)
hasil = {}
for arg in sys.argv[1:]:
    nama, _, kat = arg.partition("|")
    q = nama if kat.lower() in nama.lower() else f"{nama} {kat.lower()}".strip()
    slug = re.sub(r"[^a-z0-9]+", "-", nama.lower()).strip("-")
    kandidat = images.cari_kandidat(q)
    cocok = [k for k in kandidat if images.cocok(nama, k["teks"])]
    daftar = []
    for i, k in enumerate((cocok + [k for k in kandidat if k not in cocok])[:6]):
        try:
            im = images.download(k["image"])
            im.convert("RGB").resize((300, int(300 * im.height / im.width))).save(out / f"{slug}-{i}.jpg")
            daftar.append({"i": i, "cocok": k in cocok, "url": k["image"], "teks": k["teks"][:160]})
        except Exception as e:
            print(f"  {nama} #{i}: {e}")
    hasil[nama] = daftar
    print(nama, len(kandidat), "kandidat,", len(cocok), "cocok")
(out / "hasil.json").write_text(json.dumps(hasil, ensure_ascii=False, indent=1))
