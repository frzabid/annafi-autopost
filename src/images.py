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


def cari_kandidat(query: str, n: int = 10) -> list[str]:
    urls = []
    try:
        from ddgs import DDGS
        hasil = DDGS().images(query, region="id-id", safesearch="moderate", max_results=n)
        urls = [h["image"] for h in hasil if h.get("image")]
    except Exception as e:  # dibatasi / gagal -> coba Serper
        print(f"  DuckDuckGo gagal: {e}")
    if len(urls) < 3 and SERPER_API_KEY:
        try:
            r = requests.post("https://google.serper.dev/images", timeout=20,
                              headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                              json={"q": query, "gl": "id", "hl": "id", "num": n})
            r.raise_for_status()
            urls += [h["imageUrl"] for h in r.json().get("images", []) if h.get("imageUrl")]
        except Exception as e:
            print(f"  Serper gagal: {e}")
    return urls


def _skor_latar_putih(im: Image.Image) -> float:
    """Persentase piksel tepi yang hampir putih (foto produk katalog biasanya berlatar putih)."""
    a = np.asarray(im.convert("RGB"))
    tepi = np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3),
                           a[:, :8].reshape(-1, 3), a[:, -8:].reshape(-1, 3)])
    return float((tepi.min(axis=1) > 235).mean())


def pilih_terbaik(urls: list[str], maks_coba: int = 8):
    terbaik = None
    for url in urls[:maks_coba]:
        try:
            im = download(url)
        except Exception:
            continue
        w, h = im.size
        if min(w, h) < 350:
            continue
        skor = _skor_latar_putih(im) * 2 + min(w * h, 1200 * 1200) / (1200 * 1200)
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


def siapkan(p: dict, url_tersimpan: str | None, path_out: str) -> str:
    """Kembalikan URL sumber gambar yang dipakai; gambar bersih disimpan ke path_out."""
    if p["gambar"]:
        url, im = p["gambar"], download(p["gambar"])
    elif url_tersimpan:  # pakai gambar yang sama dengan saat pratinjau
        url, im = url_tersimpan, download(url_tersimpan)
    else:
        q = p["nama"] if len(p["nama"].split()) > 2 else f"{p['nama']} {p['kategori']}"
        url, im = pilih_terbaik(cari_kandidat(q))
        if not im:
            raise RuntimeError(f"Gambar untuk '{p['nama']}' tidak ditemukan. Isi kolom gambar di sheet.")
    bersihkan(im).save(path_out)
    return url
