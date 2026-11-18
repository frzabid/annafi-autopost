"""Render poster katalog 1080x1350 (4:5) jadi JPEG (format yang diterima Instagram API)."""
import html, pathlib, re
from PIL import Image
from playwright.sync_api import sync_playwright
from config import TOKO, rupiah

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _harga_html(harga):
    out = []
    for i, h in enumerate(harga):
        out.append(f'<div class="pr{" main" if i == 0 else ""}"><div class="lbl">{html.escape(h["label"])}</div>'
                   f'<div class="val">{rupiah(h["nilai"])}</div></div>')
    return "".join(out)


def render(p: dict, gambar_path: str, out_jpg: str) -> str:
    tpl = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
    vals = dict(assets=(ROOT / "assets").as_uri(), gambar=pathlib.Path(gambar_path).resolve().as_uri(),
                kategori=html.escape(p.get("kategori", "")), nama=html.escape(p["nama"]),
                detail=html.escape(p.get("detail", "")), harga_html=_harga_html(p["harga"]), **TOKO)
    page = re.sub(r"\{(\w+)\}", lambda m: vals.get(m.group(1), m.group(0)), tpl)
    tmp_html = pathlib.Path(out_jpg).with_suffix(".html")
    tmp_png = pathlib.Path(out_jpg).with_suffix(".tmp.png")
    tmp_html.write_text(page, encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.goto(tmp_html.as_uri())
        pg.wait_for_load_state("networkidle")
        pg.screenshot(path=str(tmp_png))
        b.close()
    Image.open(tmp_png).convert("RGB").save(out_jpg, "JPEG", quality=92)
    tmp_html.unlink(); tmp_png.unlink()
    return out_jpg
