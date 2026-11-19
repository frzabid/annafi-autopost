"""Render poster jadi JPEG (format yang diterima Instagram API).

- story  : story katalog 1080x1920 (src/story.html)
- konten : poster feed edukasi/promo/info/momen 1080x1350 (src/konten.html)
- feed   : poster feed katalog 1080x1350 (src/template.html)
"""
import html, pathlib, re
from PIL import Image
from playwright.sync_api import sync_playwright
from config import TOKO, rupiah

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = {"story": ("story.html", 1080, 1920), "konten": ("konten.html", 1080, 1350),
            "feed": ("template.html", 1080, 1350)}
LABEL = {"edukasi": "TIPS & EDUKASI", "promo": "PROMO", "info": "INFO TOKO", "momen": "SPESIAL"}


def _harga_html(harga):
    out = []
    for i, h in enumerate(harga):
        kelas = " main" if i == 0 else " coret" if any(k in h["label"].lower() for k in ("normal", "asli", "coret")) else ""
        out.append(f'<div class="pr{kelas}"><div class="lbl">{html.escape(h["label"])}</div>'
                   f'<div class="val">{rupiah(h["nilai"])}</div></div>')
    return "".join(out)


def _poin_html(poin):
    out = []
    for t in poin:
        t = html.escape(t)
        if ":" in t and t.index(":") < 40:  # "Judul: isi" -> judul ditebalkan
            a, b = t.split(":", 1)
            t = f"<b>{a}:</b>{b}"
        out.append(f"<li><span>{t}</span></li>")
    return "".join(out)


def _ukuran(p, ada_gambar):
    n = max(len(p.get("poin", [])), 1)
    panjang = sum(len(x) for x in p.get("poin", [])) * (1.6 if ada_gambar else 1)
    poin = 34 if n <= 3 and panjang < 260 else 30 if n <= 4 and panjang < 420 else 26 if panjang < 650 else 23
    judul = 66 if len(p["nama"]) <= 32 else 56 if len(p["nama"]) <= 55 else 48
    besar = 40 if n <= 4 and panjang < 300 else 34 if panjang < 500 else poin
    return {"ukuran_poin": str(poin), "ukuran_poin_besar": str(besar), "ukuran_judul": str(judul), "jarak_poin": "18" if n <= 4 else "12"}


def render(p: dict, gambar_path: str | None, out_jpg: str) -> str:
    nama_tpl, w, h = TEMPLATE[p.get("format", "story")]
    tpl = (ROOT / "src" / nama_tpl).read_text(encoding="utf-8")
    ada_gambar = bool(gambar_path)
    vals = dict(assets=(ROOT / "assets").as_uri(),
                gambar=pathlib.Path(gambar_path).resolve().as_uri() if ada_gambar else "",
                kelas_body="" if ada_gambar else "noimg",
                kategori=html.escape(p.get("kategori", "")), nama=html.escape(p["nama"]),
                detail=html.escape(p.get("detail", "")), harga_html=_harga_html(p.get("harga", [])),
                poin_html=_poin_html(p.get("poin", [])), jenis=p.get("jenis", ""),
                label=LABEL.get(p.get("jenis", ""), p.get("kategori", "")), **_ukuran(p, ada_gambar), **TOKO)
    page = re.sub(r"\{(\w+)\}", lambda m: vals.get(m.group(1), m.group(0)), tpl)
    tmp_html = pathlib.Path(out_jpg).with_suffix(".html")
    tmp_png = pathlib.Path(out_jpg).with_suffix(".tmp.png")
    tmp_html.write_text(page, encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.goto(tmp_html.as_uri())
        pg.wait_for_load_state("networkidle")
        pg.screenshot(path=str(tmp_png))
        b.close()
    Image.open(tmp_png).convert("RGB").save(out_jpg, "JPEG", quality=92)
    tmp_html.unlink(); tmp_png.unlink()
    return out_jpg
