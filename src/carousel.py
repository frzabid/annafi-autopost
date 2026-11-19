"""Carousel feed Instagram/Facebook (1080x1350, beberapa slide) dengan tema per momen.

Susunan slide:
  1. sampul      : panel bertema + judul besar + detail
  2..n. poin     : satu poin per slide ("Judul: isi"), nomor besar + ilustrasi bertema
  (opsional)     : kolase foto produk dari tab Produk (tanpa harga)
  terakhir       : penutup bertema + kartu kontak toko
"""
import html, pathlib
from datetime import datetime
from PIL import Image
from playwright.sync_api import sync_playwright
from config import TOKO
import tema as T

ROOT = pathlib.Path(__file__).resolve().parent.parent
LABEL = {"edukasi": "TIPS & EDUKASI", "promo": "PROMO", "info": "INFO TOKO", "momen": "SPESIAL"}
NAMA_TOKO = "Annafi ATK Menganti"
BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober",
         "November", "Desember"]

CSS = """
@font-face{font-family:Poppins;src:url(%(a)s/fonts/Poppins-Regular.ttf);font-weight:400}
@font-face{font-family:Poppins;src:url(%(a)s/fonts/Poppins-Bold.ttf);font-weight:700}
@font-face{font-family:Caveat;src:url(%(a)s/fonts/Caveat-Bold.woff2);font-weight:700}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Poppins,sans-serif;color:#1d2a44;background:#ccc}
.slide{width:1080px;height:1350px;position:relative;overflow:hidden;margin-bottom:10px;background:var(--bg);
  background-image:radial-gradient(var(--dot) 2.2px,transparent 2.4px);background-size:44px 44px}
.top{position:absolute;top:56px;left:70px;right:70px;display:flex;justify-content:space-between;align-items:center;z-index:5}
.pill{background:var(--accent);color:#fff;font-weight:700;font-size:26px;letter-spacing:2px;padding:12px 26px;border-radius:40px;max-width:760px}
.logo{width:120px}
.foot{position:absolute;bottom:50px;left:70px;right:70px;display:flex;justify-content:space-between;align-items:center;font-size:24px;color:#6b5a3e;z-index:5}
.dots{display:flex;gap:10px}.dots i{width:14px;height:14px;border-radius:50%;background:var(--dot)}.dots i.on{background:var(--primary);width:38px;border-radius:8px}
.swipe{font-weight:700;color:var(--primary);min-width:110px;text-align:right}
.hias{position:absolute;z-index:4}.hias svg{width:100%;height:auto;display:block}
.hand{font-family:Caveat;font-weight:700}
/* panel sampul */
.panel{position:absolute;left:90px;right:90px;top:250px;height:640px;display:flex;flex-direction:column;align-items:center;
  justify-content:center;text-align:center;color:#fff;z-index:2;padding:0 60px}
.panel .h{font-family:Caveat;font-size:118px;line-height:.9;color:var(--hand)}
.panel .t{font-weight:700;line-height:1.06;margin-top:14px}
.panel .d{margin-top:26px;font-size:30px;letter-spacing:5px;font-weight:700;opacity:.85}
.panel-papan{background:#2d5a49;border-radius:26px;border:26px solid #b97a41;box-shadow:0 26px 0 -6px #8d5a2c,0 40px 60px rgba(90,60,20,.25)}
.panel-biru{background:var(--primary);border-radius:40px;box-shadow:14px 14px 0 #1d2a44;
  background-image:radial-gradient(rgba(255,255,255,.12) 2px,transparent 2.4px);background-size:36px 36px}
.panel-kubah{background:#0f5a46;border:10px solid #d4a73a;border-radius:330px 330px 34px 34px;top:220px;height:690px;padding-top:70px;
  box-shadow:0 0 0 10px #0f5a46,0 30px 60px rgba(15,90,70,.25)}
.panel-malam{background:linear-gradient(#121d40,#2a3d7a);border:10px solid #d4a73a;border-radius:330px 330px 34px 34px;top:220px;
  height:690px;padding-top:70px;box-shadow:0 30px 60px rgba(27,42,90,.3)}
.panel-hijau{background:#1f7a4d;border-radius:40px;border:10px solid #d4a73a;box-shadow:0 30px 60px rgba(31,122,77,.25)}
.panel-merahputih{background:linear-gradient(#d32f2f 0 62%,#fff 62%);border-radius:36px;border:6px solid #1d2a44;box-shadow:14px 14px 0 #1d2a44}
.panel-merahputih .d{color:#fff;opacity:.95}
.panel-kubah,.panel-malam{padding-bottom:230px}.panel-hijau{padding-bottom:200px}
.panel-merahputih{justify-content:flex-start;padding-top:90px}
.panel-kertas{background:#fff;color:#1d2a44;border-radius:18px;border:5px solid #1d2a44;box-shadow:14px 14px 0 var(--primary);
  background-image:linear-gradient(90deg,transparent 88px,#f28b82 88px,#f28b82 92px,transparent 92px),
  repeating-linear-gradient(transparent 0 58px,#cfe0f7 58px 61px)}
.panel-kuning{background:#f2b33d;color:#1d2a44;border-radius:40px;border:6px solid #1d2a44;box-shadow:14px 14px 0 #1d2a44}
.bawah{position:absolute;left:0;right:0;top:960px;text-align:center;font-family:Caveat;font-weight:700;font-size:76px;color:var(--primary);z-index:5}
.sub{position:absolute;left:120px;right:120px;text-align:center;font-size:32px;line-height:1.45;color:#5a4a30;z-index:5}
/* slide poin */
.num{position:absolute;top:190px;left:70px;font-weight:700;font-size:210px;line-height:1;color:transparent;-webkit-text-stroke:4px var(--primary)}
.ttl{position:absolute;top:410px;left:70px;right:70px;font-weight:700;line-height:1.08}
.ttl span{background:linear-gradient(transparent 62%,var(--soft0) 62%)}
.txt{position:absolute;left:70px;right:90px;line-height:1.5;color:#3b3325}
.blob{position:absolute;right:-60px;bottom:80px;width:700px;height:590px;border-radius:52% 48% 46% 54%/55% 45% 55% 45%}
.art{position:absolute;right:20px;bottom:110px;width:660px;height:520px}
.art svg{width:100%;height:100%}
/* kolase produk */
.kol{position:absolute;top:180px;left:70px;right:70px}.kol-h{font-weight:700;font-size:66px;line-height:1.08}
.kol-s{font-size:32px;color:#5a4a30;margin-top:12px}
.grid{position:absolute;top:440px;left:70px;right:70px;bottom:150px;display:grid;gap:30px}
.grid.n1{grid-template-columns:1fr}.grid.n2{grid-template-columns:1fr 1fr}.grid.n3,.grid.n4{grid-template-columns:1fr 1fr}
.kartu{background:#fff;border:4px solid #1d2a44;border-radius:28px;box-shadow:8px 8px 0 var(--primary);display:flex;flex-direction:column;
  align-items:center;justify-content:center;padding:24px;overflow:hidden}
.kartu img{flex:1;min-height:0;max-width:100%;object-fit:contain}
.kartu b{font-size:28px;text-align:center;margin-top:14px;line-height:1.2}
.grid.n3 .kartu:first-child{grid-column:1 / span 2}
/* penutup */
.cw{position:absolute;top:210px;left:70px;right:70px;text-align:center}
.cw .h{font-family:Caveat;font-weight:700;font-size:104px;color:var(--primary);line-height:1}
.cw .t{font-size:38px;line-height:1.45;margin-top:22px;color:#3b3325}
.card{position:absolute;left:110px;right:110px;top:600px;background:#fff;border-radius:34px;padding:46px 54px;border:3px solid #1d2a44;
  box-shadow:12px 12px 0 var(--primary)}
.card .nm{font-weight:700;font-size:46px;display:flex;align-items:center;gap:22px}
.card .nm img{width:96px}
.card .row{display:flex;align-items:center;gap:18px;font-size:32px;margin-top:22px}
.card .row img,.card .row b.fb{width:44px;height:44px;border-radius:10px}
.card .row b.fb{background:#1877f2;color:#fff;display:flex;align-items:center;justify-content:center;font-size:32px}
.save{position:absolute;left:0;right:0;top:1120px;text-align:center;font-size:30px;font-weight:700;color:var(--accent)}
"""


def _e(s):
    return html.escape(s or "")


def _ukuran_judul(teks, besar=(96, 84, 72, 62)):
    n = len(teks)
    return besar[0] if n <= 20 else besar[1] if n <= 32 else besar[2] if n <= 48 else besar[3]


def _pecah_poin(poin):
    out = []
    for t in poin:
        if ":" in t and t.index(":") < 50:
            a, b = t.split(":", 1)
            out.append((a.strip(), b.strip()))
        else:
            out.append((t.strip(), ""))
    return out


def _judul_sampul(nama):
    """'Selamat Hari Guru Nasional' -> ('Selamat', 'Hari Guru Nasional')."""
    for awal in ("Selamat", "Tips", "Yuk", "Cara"):
        if nama.lower().startswith(awal.lower() + " ") and len(nama) > len(awal) + 4:
            return awal, nama[len(awal) + 1:]
    return "", nama


def _tgl(dt):
    return f"{dt.day} {BULAN[dt.month]} {dt.year}" if dt else ""


def _bagian_atas(t, pill):
    return (f'<div class="top"><div class="pill">{_e(pill)}</div>'
            f'<img class="logo" src="{{A}}/logo.png"></div>')


def _bagian_bawah(i, n, terakhir=False):
    dots = "".join(f'<i class="{"on" if k == i else ""}"></i>' for k in range(n))
    return (f'<div class="foot"><span>{_e(TOKO["ig"])}</span><div class="dots">{dots}</div>'
            f'<span class="swipe">{"" if terakhir else "Geser &rarr;"}</span></div>')


def susun_html(p: dict, foto_produk=None) -> tuple[str, int]:
    """Bangun halaman HTML berisi semua slide. foto_produk: list (nama, path_png)."""
    kunci = T.pilih(p)
    t = T.TEMA[kunci]
    foto_produk = foto_produk or []
    poin = _pecah_poin(p.get("poin", []))[:4]
    n = 1 + len(poin) + (1 if foto_produk else 0) + 1
    pill = t["pill"] if kunci != "umum" else LABEL.get(p.get("jenis", ""), t["pill"])
    slides, i = [], 0

    # 1. sampul
    h, judul = _judul_sampul(p["nama"])
    hline = f'<div class="h">{_e(h)}</div>' if h else ""
    dline = _tgl(p.get("waktu")) if p.get("jenis") == "momen" or kunci != "umum" else LABEL.get(p.get("jenis", ""), "")
    gaya = (f'top:{t["bawah_top"]}px;color:{t["bawah_warna"]};font-size:{t["bawah_besar"]}px' if t.get("bawah_top") else "")
    sub_top = 1060 if t.get("bawah") and not t.get("bawah_top") else 975
    bawah = f'<div class="bawah" style="{gaya}">{_e(t["bawah"])}</div>' if t.get("bawah") else ""
    slides.append(
        f'<div class="slide">{_bagian_atas(t, pill)}'
        f'<div class="panel {t["panel"]}">{hline}'
        f'<div class="t" style="font-size:{_ukuran_judul(judul)}px">{_e(judul)}</div><div class="d">{_e(dline.upper())}</div></div>'
        f'{T.hiasan_sampul(t)}'
        f'{bawah}'
        f'<div class="sub" style="top:{sub_top}px">{_e(p.get("detail", ""))}</div>'
        f'{_bagian_bawah(i, n)}</div>')
    i += 1

    # 2. poin
    for k, (judul_p, isi) in enumerate(poin):
        kata = judul_p.split()
        sorot = " ".join(kata[:2]) if len(kata) > 2 else judul_p
        sisa = " ".join(kata[2:]) if len(kata) > 2 else ""
        ttl = f'<span>{_e(sorot)}</span>' + (f" {_e(sisa)}" if sisa else "")
        uk = _ukuran_judul(judul_p, (84, 74, 64, 56))
        baris_judul = 1 if len(judul_p) * uk * 0.55 < 940 else 2 if len(judul_p) * uk * 0.55 < 1880 else 3
        top_txt = 410 + int(uk * 1.08 * baris_judul) + 40
        uk_txt = 44 if len(isi) <= 70 else 38 if len(isi) <= 140 else 32
        art = T.ART[t["art"][k % len(t["art"])]]
        slides.append(
            f'<div class="slide">{_bagian_atas(t, pill)}<div class="num">0{k + 1}</div>'
            f'<div class="ttl" style="font-size:{uk}px">{ttl}</div>'
            f'<div class="txt" style="top:{top_txt}px;font-size:{uk_txt}px">{_e(isi)}</div>'
            f'<div class="blob" style="background:{t["soft"][k % len(t["soft"])]}"></div><div class="art">{art}</div>'
            f'{_bagian_bawah(i, n)}</div>')
        i += 1

    # 3. kolase produk (tanpa harga)
    if foto_produk:
        kartu = "".join(f'<div class="kartu"><img src="{pathlib.Path(path).resolve().as_uri()}"><b>{_e(nama)}</b></div>'
                        for nama, path in foto_produk[:4])
        slides.append(
            f'<div class="slide">{_bagian_atas(t, pill)}<div class="kol"><div class="kol-h">Perlengkapan yang bisa disiapkan</div>'
            f'<div class="kol-s">Tersedia di {_e(NAMA_TOKO)}</div></div>'
            f'<div class="grid n{min(len(foto_produk), 4)}">{kartu}</div>{_bagian_bawah(i, n)}</div>')
        i += 1

    # 4. penutup
    th, tt = t["tutup"]
    slides.append(
        f'<div class="slide">{_bagian_atas(t, pill)}<div class="cw"><div class="h">{_e(th)}</div><div class="t">{_e(tt)}</div></div>'
        f'<div class="card"><div class="nm"><img src="{{A}}/logo.png">{_e(NAMA_TOKO)}</div>'
        f'<div class="row"><img src="{{A}}/ic_wa.png">{_e(TOKO["wa"])}</div>'
        f'<div class="row"><img src="{{A}}/ic_ig.png">{_e(TOKO["ig"])}</div>'
        f'<div class="row"><img src="{{A}}/ic_tt.png">{_e(TOKO["tiktok"])}</div>'
        f'<div class="row"><b class="fb">f</b>{_e(TOKO["fb"])}</div></div>'
        f'<div class="save">Simpan &amp; bagikan ke teman</div>'
        f'<div class="hias" style="left:80px;top:1040px;width:70px">{T.bintang("#f2b33d")}</div>'
        f'<div class="hias" style="left:930px;top:500px;width:56px">{T.bintang(t["accent"])}</div>'
        f'{_bagian_bawah(i, n, terakhir=True)}</div>')

    a = (ROOT / "assets").as_uri()
    var = (f':root{{--bg:{t["bg"]};--dot:{t["dot"]};--primary:{t["primary"]};--accent:{t["accent"]};'
           f'--hand:{t["hand"]};--soft0:{t["soft"][1]}}}')
    page = (f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS.replace("%(a)s", a)}{var}</style></head><body>'
            + "".join(slides).replace("{A}", a) + "</body></html>")
    return page, len(slides)


def render(p: dict, out_prefix: str, foto_produk=None) -> list[str]:
    """Render semua slide ke JPEG: <out_prefix>-1.jpg, -2.jpg, ... Kembalikan daftar path."""
    page, n = susun_html(p, foto_produk)
    out = pathlib.Path(out_prefix)
    tmp = out.with_name(out.name + ".html")
    tmp.write_text(page, encoding="utf-8")
    hasil = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.goto(tmp.as_uri())
        pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        for k in range(n):
            png = out.with_name(f"{out.name}-{k + 1}.png")
            pg.locator(".slide").nth(k).screenshot(path=str(png))
            jpg = png.with_suffix(".jpg")
            Image.open(png).convert("RGB").save(jpg, "JPEG", quality=90)
            png.unlink()
            hasil.append(str(jpg))
        b.close()
    tmp.unlink()
    return hasil
