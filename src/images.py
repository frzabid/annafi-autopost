"""Ambil gambar produk: dari link di sheet, atau cari otomatis (DuckDuckGo, cadangan Serper).
Lalu latar dihapus supaya rapi di template."""
import io, re
import numpy as np
import requests
from PIL import Image
from config import SERPER_API_KEY

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
_rembg_session = None


def _drive_direct(url: str) -> str:
    m = re.search(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?.*id=)([\w-]+)", url)
    return f"https://drive.google.com/uc?export=download&id={m[1]}" if m else url


def download(url: str) -> Image.Image:
    r = requests.get(_drive_direct(url), headers=UA, timeout=25)
    r.raise_for_status()
    im = Image.open(io.BytesIO(r.content))
    im.load()
    return im.convert("RGBA")


def cari_kandidat(query: str, n: int = 20) -> list[dict]:
    """Kandidat gambar: {image, teks} — teks = judul + alamat halaman sumber, untuk cek kecocokan."""
    hasil = []
    try:
        from ddgs import DDGS
        for h in DDGS().images(query, region="id-id", safesearch="moderate", max_results=n):
            if h.get("image"):
                hasil.append({"image": h["image"], "teks": f"{h.get('title', '')} {h.get('url', '')} {h['image']}"})
    except Exception as e:  # dibatasi / gagal -> coba Serper
        print(f"  DuckDuckGo gagal: {e}")
    if SERPER_API_KEY and len([h for h in hasil if cocok(query, h["teks"])]) < 2:
        try:
            r = requests.post("https://google.serper.dev/images", timeout=20,
                              headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                              json={"q": query, "gl": "id", "hl": "id", "num": n})
            r.raise_for_status()
            hasil += [{"image": h["imageUrl"], "teks": f"{h.get('title', '')} {h.get('link', '')} {h['imageUrl']}"}
                      for h in r.json().get("images", []) if h.get("imageUrl")]
        except Exception as e:
            print(f"  Serper gagal: {e}")
    return hasil


_UMUM = {"dan", "isi", "pcs", "pack", "warna", "untuk", "dengan", "the", "per", "box", "lusin"}
SINONIM = {"pensil": ("pencil",), "bolpen": ("pen", "pulpen", "ballpoint"), "pulpen": ("pen", "bolpen", "ballpoint"),
           "spidol": ("marker",), "buku": ("book",), "penghapus": ("eraser",), "penggaris": ("ruler",),
           "gunting": ("scissors",), "lem": ("glue",), "kertas": ("paper",), "tas": ("bag",), "kotak": ("box",)}
TOKO_ONLINE = ("tokopedia", "shopee", "blibli", "bukalapak", "lazada", "joyko", "kenko", "snowman", "faber",
               "standard", "deli", "atk", "stationery", "alattulis", "gramedia")


def cocok(nama: str, teks: str) -> bool:
    """Gambar dianggap cocok kalau judul/alamat sumbernya memuat kode model (angka) dan sebagian besar kata nama produk."""
    t_rapat = re.sub(r"[^a-z0-9]", "", teks.lower())
    t_kata = set(re.findall(r"[a-z0-9]+", teks.lower()))
    token = re.findall(r"[a-z0-9]+", nama.lower())
    kode = [k for k in token if re.search(r"\d", k) and len(k) >= 3]
    if any(k not in t_rapat for k in kode):
        return False
    kata = [k for k in token if k.isalpha() and len(k) >= 3 and k not in _UMUM]
    if not kata:
        return bool(kode)
    kena = sum(1 for k in kata if any(s in t_kata for s in (k, *SINONIM.get(k, ()))))
    perlu = -(-len(kata) // 2) if kode else -(-len(kata) * 2 // 3)  # ada kode model: 1/2 kata cukup; tanpa kode: 2/3
    return kena >= max(1, perlu)


def _skor_latar_putih(im: Image.Image) -> float:
    """Persentase piksel tepi yang hampir putih (foto produk katalog biasanya berlatar putih)."""
    a = np.asarray(im.convert("RGB"))
    tepi = np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3),
                           a[:, :8].reshape(-1, 3), a[:, -8:].reshape(-1, 3)])
    return float((tepi.min(axis=1) > 235).mean())


def pilih_terbaik(kandidat: list[dict], nama: str, maks_coba: int = 8):
    """Hanya kandidat yang cocok dengan nama produk; foto latar putih dari toko online diutamakan."""
    cocok_ = [k for k in kandidat if cocok(nama, k["teks"])]
    terbaik = None
    for k in cocok_[:maks_coba]:
        url = k["image"]
        try:
            im = download(url)
        except Exception:
            continue
        w, h = im.size
        if min(w, h) < 350:
            continue
        skor = (_skor_latar_putih(im) * 2 + min(w * h, 1200 * 1200) / (1200 * 1200)
                + (0.5 if any(t in k["teks"].lower() for t in TOKO_ONLINE) else 0))
        if not terbaik or skor > terbaik[0]:
            terbaik = (skor, url, im)
    return (terbaik[1], terbaik[2]) if terbaik else (None, None)


def bersihkan(im: Image.Image) -> Image.Image:
    """Hapus latar. Latar putih -> cara cepat; latar lain -> rembg (AI, open source)."""
    if _skor_latar_putih(im) > 0.85:
        a = np.asarray(im).astype(int).copy()
        m = a[:, :, :3].min(axis=2)
        a[:, :, 3] = np.minimum(a[:, :, 3], np.clip((255 - m) * 255 / 18, 0, 255))
        out = Image.fromarray(a.astype("uint8"))
    else:
        global _rembg_session
        from rembg import new_session, remove
        _rembg_session = _rembg_session or new_session("isnet-general-use")
        out = remove(im, session=_rembg_session)
    out = _buang_bagian_kecil(out)
    bbox = out.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
    return out.crop(bbox) if bbox else out


def _buang_bagian_kecil(im: Image.Image, rasio: float = 0.08) -> Image.Image:
    """Buang objek kecil yang terpisah dari produk (logo, watermark, teks) di foto sumber."""
    from scipy import ndimage
    a = np.asarray(im).copy()
    mask = ndimage.binary_dilation(a[:, :, 3] > 40, iterations=6)  # gabungkan bagian yang berdekatan
    lab, n = ndimage.label(mask)
    if n <= 1:
        return im
    luas = ndimage.sum(mask, lab, range(1, n + 1))
    kecil = [i + 1 for i, v in enumerate(luas) if v < luas.max() * rasio]
    a[np.isin(lab, kecil), 3] = 0
    return Image.fromarray(a)


class GambarTidakKetemu(RuntimeError):
    pass


def siapkan(p: dict, url_tersimpan: str | None, path_out: str) -> str:
    """Kembalikan URL sumber gambar yang dipakai; gambar bersih disimpan ke path_out.
    Kolom gambar: link langsung, "cari" (pakai nama produk), atau "cari: kata kunci"."""
    g = (p["gambar"] or "").strip()
    if g and not g.lower().startswith("cari"):
        url, im = g, download(g)
    elif url_tersimpan:  # pakai gambar yang sama dengan saat pratinjau
        url, im = url_tersimpan, download(url_tersimpan)
    else:
        nama = g.split(":", 1)[1].strip() if ":" in g else p["nama"]
        kat = p.get("kategori", "")
        q = nama if kat.lower() in nama.lower() else f"{nama} {kat.lower()}"
        url, im = pilih_terbaik(cari_kandidat(q), nama)
        if not im:
            raise GambarTidakKetemu(f"Foto yang cocok untuk '{nama}' tidak ketemu.")
    bersihkan(im).save(path_out)
    return url
