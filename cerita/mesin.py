"""Mesin animasi cerita: papan cerita (JSON) -> video reel 1080x1920 bersuara.

Papan cerita (dibuat oleh sutradara.py / Gemini, atau ditulis tangan):
{"part": 1, "judul": "...", "adegan": [
  {"latar": "depan_buka", "waktu": "pagi", "kamera": "zoom_in", "kilas_balik": false,
   "tokoh": [{"id": "laras", "ekspresi": "senang", "posisi": "kanan", "masuk": ""}],
   "objek": {"jenis": "amplop", "tulisan": "..."},            # atau null
   "efek": ["bel"],
   "urutan": [{"tokoh": "narator", "ucap": "...", "emosi": ""},
              {"tokoh": "laras", "ucap": "...", "ekspresi": "kaget", "emosi": "kaget"},
              {"teks": "tulisan di layar / surat"}, {"jeda": 1.0}]}]}
Panjang tiap adegan MENGIKUTI panjang suara (tidak dipercepat). Di akhir otomatis ada kartu "Bersambung".
"""
import html as _html
import math
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
import latar as L  # noqa: E402
import suara  # noqa: E402
import tokoh as T  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "assets" / "fonts"
W, H, FPS = 1080, 1920, 30
X = 0.35  # crossfade antar adegan
DURASI_SAMPUL = 3.0  # detik; cover Reel di Make = frame 2500 ms
AKUN = "@annafi_atk_menganti"
JUDUL_SERI = "MISTERI SURAT TANPA NAMA"

LATAR = {
    "depan_buka": "depan toko pagi, lampu dalam menyala & papan TUTUP berbalik jadi BUKA",
    "depan": "depan toko (sudah buka)",
    "depan_malam": "depan toko malam, sudah tutup",
    "dalam": "dalam toko: rak gondola merah, area fotokopi/printer di kanan",
    "meja": "close-up di meja layanan (untuk membaca surat/amplop, wajah tokoh dari dekat)",
    "pintu_bawah": "close-up lantai depan pintu kaca + keset daun (amplop diselipkan dari bawah pintu)",
    "bawah_mesin": "close-up sejajar lantai di bawah mesin fotokopi (ada celah gelap)",
    "beringin": "halaman belakang sekolah: pohon beringin tua besar (tokoh tampil seluruh badan)",
    "ukiran": "close-up batang beringin dengan ukiran lama A·H·R (R dicoret)",
    "polos": "latar gelap polos (untuk teks/kejutan)",
}
LEBAR = {"depan_buka", "depan", "depan_malam", "dalam", "beringin"}  # tokoh tampil seluruh badan
TANGGAL_AMPLOP_TUA = "12-03-2011"  # tanggal di amplop tua (Part 1: "tanggalnya lima belas tahun lalu")
OBJEK = {"amplop": "amplop krem bergambar bintang biru", "amplop_tua": "amplop tua kekuningan",
         "surat": "kertas surat bertulisan tangan"}
KAMERA = ["diam", "zoom_in", "zoom_out", "geser", "goyang"]
EFEK = {"bel": 1.6, "klik": 0.2, "kertas": 0.6, "deg": 1.4, "langkah": 1.6, "lari": 1.4, "jantung": 2.4,
        "angin": 3.0, "detik": 2.0, "pintu": 1.2, "petir": 3.0}
WAKTU = ["pagi", "siang", "sore", "malam"]
POSISI_LEBAR = {"kiri": 230, "tengah": 540, "kanan": 850}
POSISI_DEKAT = {"kiri": 290, "tengah": 540, "kanan": 790}
BASIS = {"depan_buka": 1790, "depan": 1790, "depan_malam": 1790, "dalam": 1800, "beringin": 1800}

CSS_DASAR = """
@font-face{font-family:Poppins;src:url('__FONT__/Poppins-Bold.ttf');font-weight:700}
@font-face{font-family:Poppins;src:url('__FONT__/Poppins-Regular.ttf');font-weight:400}
@font-face{font-family:Caveat;src:url('__FONT__/Caveat-Bold.woff2')}
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;background:#000;font-family:Poppins}
.adegan{position:absolute;inset:0;overflow:hidden}
.cam{position:absolute;inset:0}
.kedip{animation:kedip 3.2s infinite;transform-origin:200px 204px}
@keyframes kedip{0%,92%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}
@keyframes tampil{to{opacity:1}}@keyframes sembunyi{to{opacity:0}}
@keyframes mangap{0%,49%{opacity:1}50%,100%{opacity:0}}
@keyframes napas{from{transform:scaleY(1)}to{transform:scaleY(1.012)}}
.tkh{position:absolute;transform-origin:50% 100%}
.bintang{position:absolute;left:14%;top:0;width:72%;height:44%;background:#111;clip-path:polygon(50% 0,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%)}
.samar{position:absolute;left:17%;top:3%;width:66%;height:40%;border-radius:50%;backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px)}
.tkh .badan{position:absolute;inset:0;animation:napas 2.2s ease-in-out infinite alternate;transform-origin:50% 100%}
.ek{position:absolute;inset:0;opacity:0}.ek svg{width:100%;height:100%;display:block}
.sub{position:absolute;left:60px;right:60px;top:150px;background:rgba(255,255,255,.95);border-radius:26px;padding:26px 36px;
  font-size:46px;line-height:1.28;color:#1E3A6B;font-weight:700;box-shadow:0 10px 30px rgba(0,0,0,.2);opacity:0}
.sub small{display:block;font-size:30px;font-weight:700;color:#c26a1b;letter-spacing:2px;margin-bottom:6px}
.sub.nar{background:rgba(20,22,34,.82);color:#fff;font-weight:400;font-style:italic}
.sub.nar small{color:#ffb347;font-style:normal}
.banner{position:absolute;left:70px;right:70px;top:1000px;padding:30px 40px;border-radius:24px;background:rgba(10,12,20,.72);
  color:#fff;font-family:Caveat;font-size:72px;line-height:1.15;text-align:center;opacity:0}
.judulkecil{position:absolute;left:0;right:0;top:56px;text-align:center}
.judulkecil span{display:inline-block;background:#1E3A6B;color:#fff;font-size:28px;letter-spacing:3px;padding:10px 26px;border-radius:40px}
.lapis{position:absolute;inset:0;pointer-events:none}
"""


def _esc(s):
    return _html.escape(str(s or ""))


def _cerah(waktu, kilas):
    """Lapisan warna suasana (malam/sore/kilas balik)."""
    out = ""
    if waktu == "malam":
        out += '<div class="lapis" style="background:rgba(14,22,70,.55);mix-blend-mode:multiply"></div>'
    elif waktu == "sore":
        out += '<div class="lapis" style="background:rgba(255,140,60,.18)"></div>'
    if kilas:
        out += ('<div class="lapis" style="background:radial-gradient(circle at 50% 45%,#0000 50%,rgba(60,40,20,.6))"></div>'
                '<div style="position:absolute;left:60px;top:1780px;font-family:Caveat;font-size:64px;color:#fff3d6">2011</div>')
    return out


def _latar(nama):
    if nama == "depan_buka":
        return (L.latar_depan() + "<style>.tk-terang{animation:nyala .5s 1.0s steps(3,end) forwards}"
                "@keyframes nyala{to{opacity:0}}.tk-flip{animation:balik .6s 1.7s ease-in-out forwards}"
                "@keyframes balik{to{transform:rotateY(180deg)}}</style>")
    if nama == "depan":
        return L.latar_depan() + "<style>.tk-terang{opacity:0}.tk-flip{transform:rotateY(180deg)}</style>"
    if nama == "depan_malam":
        return L.latar_depan() + "<style>.tk-langit{background:linear-gradient(#0b1030,#1d2350)!important}</style>"
    if nama == "dalam":
        return L.latar_dalam(1.0)
    if nama == "meja":
        return L.latar_meja()
    if nama == "pintu_bawah":
        return L.latar_pintu_bawah()
    if nama == "bawah_mesin":
        return L.latar_bawah_mesin()
    if nama == "beringin":
        return L.latar_beringin()
    if nama == "ukiran":
        return L.latar_ukiran()
    return L.latar_polos()


def _kamera(k, d):
    a = {"zoom_in": "from{transform:scale(1)}to{transform:scale(1.12)}",
         "zoom_out": "from{transform:scale(1.14)}to{transform:scale(1)}",
         "geser": "from{transform:scale(1.12) translateX(40px)}to{transform:scale(1.12) translateX(-40px)}",
         "goyang": "0%{transform:scale(1.06)}4%{transform:scale(1.06) translate(-14px,8px)}8%{transform:scale(1.06) translate(12px,-6px)}"
                   "12%,100%{transform:scale(1.06)}"}.get(k)
    if not a:
        return ""
    return f".cam{{animation:kam {d:.2f}s ease-in-out forwards;transform-origin:50% 60%}}@keyframes kam{{{a}}}"


def _visibilitas(sel, interval, akhir):
    """CSS untuk menampilkan elemen pada interval waktu [(mulai, selesai|None)]."""
    an = []
    for s, e in interval:
        if s > 0.001:
            an.append(f"tampil .01s linear {s:.2f}s forwards")
        if e is not None and e < akhir:
            an.append(f"sembunyi .01s linear {e:.2f}s forwards")
    awal = "opacity:1;" if interval and interval[0][0] <= 0.001 else ""
    return f"{sel}{{{awal}animation:{','.join(an) or 'none'}}}"


# ------------------------------------------------------------------ satu adegan
def adegan_html(a, idx, info_part):
    d = a["_durasi"]
    lebar = a["latar"] in LEBAR
    css, isi = [_kamera(a.get("kamera"), d)], []
    pos_tabel = POSISI_LEBAR if lebar else POSISI_DEKAT
    # ---- tokoh
    for i, t in enumerate(a.get("tokoh", [])):
        sp = T.TOKOH[t["id"]]
        if lebar:
            w = 330 * sp["skala"]
            h = w * 900 / 400
            top = BASIS[a["latar"]] - h * 868 / 900
            vb = "badan"
        elif a["latar"] in ("pintu_bawah", "bawah_mesin"):  # sudut pandang lantai: tokoh mengintip kecil di pojok
            w, h = 420, 546
            top = H - h + 30
            vb = "dada"
        else:
            w, h = 600, 780
            top = H - h + 20
            vb = "dada"
        left = pos_tabel[t["posisi"]] - w / 2
        if a["latar"] in ("pintu_bawah", "bawah_mesin"):
            left = (840 if i == 0 else 240) - w / 2
        flip = "scaleX(-1)" if (t["posisi"] == "kanan" and len(a["tokoh"]) > 1) else "none"
        lapisan = ""
        for j, (ek, interval) in enumerate(t["_ekspresi"].items()):
            svg = T.badan(t["id"], ek) if vb == "badan" else T.dada(t["id"], ek)
            lapisan += f'<div class="ek e{j}">{svg}</div>'
            css.append(_visibilitas(f"#t{i} .e{j}", interval, d))
        if t["_bicara"]:
            css.append(f"#t{i} .mb{{animation:" + ",".join(
                f"mangap .24s linear {s:.2f}s {max(1, math.floor(dur / 0.24))}" for s, dur in t["_bicara"]) + "}")
        masuk = ""
        if t.get("masuk") in ("kiri", "kanan"):
            dari = -900 if t["masuk"] == "kiri" else 900
            css.append(f"@keyframes msk{i}{{from{{transform:translateX({dari}px) {flip}}}to{{transform:{flip}}}}}")
            masuk = f"animation:msk{i} .8s cubic-bezier(.2,.8,.3,1) {t['_masuk']:.2f}s both;"
        isi.append(f'<div class="tkh" id="t{i}" style="left:{left:.0f}px;top:{top:.0f}px;width:{w:.0f}px;height:{h:.0f}px;'
                   f'transform:{flip};{masuk}"><div class="badan">{lapisan}</div>'
                   + ('<div class="bintang"></div>' if t.get("samar") == "bintang" else '<div class="samar"></div>' if t.get("samar") else '') + '</div>')
    # ---- objek
    ob = a.get("objek")
    if ob:
        tulis_mulai = a.get("_teks_pertama", 0.5)
        tulisan = _esc(ob.get("tulisan") or (TANGGAL_AMPLOP_TUA if ob["jenis"] == "amplop_tua" else ""))
        if a["latar"] in ("pintu_bawah", "bawah_mesin"):
            gambar = T.amplop(440, tua=ob["jenis"] == "amplop_tua")
            gerak = ("from{transform:translateY(-420px) rotate(-2deg)}to{transform:translateY(0) rotate(-8deg)}"
                     if a["latar"] == "pintu_bawah" else "from{transform:translateY(-110px) scale(.92);opacity:.2}to{transform:rotate(-4deg)}")
            css.append(f"#ob{{position:absolute;left:320px;top:1090px;filter:drop-shadow(0 18px 14px rgba(0,0,0,.3));"
                       f"animation:obm 1.3s .2s ease-out both}}@keyframes obm{{{gerak}}}")
            isi.append(f'<div id="ob">{gambar}</div>')
        else:
            if ob["jenis"] == "surat":
                kertas = ('<div style="width:860px;height:640px;background:#fbf6e8;border-radius:10px;'
                          'background-image:repeating-linear-gradient(#0000 0 70px,#d9cfb8 70px 72px);box-shadow:0 20px 50px rgba(0,0,0,.35)"></div>')
            else:
                kertas = T.amplop(860, tua=ob["jenis"] == "amplop_tua", depan=True)
            warna = "#6b4a1f" if ob["jenis"] == "amplop_tua" else "#1E3A6B"
            redup = '<div class="lapis" style="background:rgba(0,0,0,.35)"></div>' if lebar else ""
            css.append(f"#obw{{position:absolute;left:{'222' if lebar else '110'}px;top:{'420' if lebar else '470'}px;width:860px;"
                       f"transform:scale({'.74' if lebar else '1'});transform-origin:0 0}}"
                       f"#ob{{position:relative;width:860px;animation:obm .9s .15s cubic-bezier(.2,1.2,.4,1) both}}@keyframes obm{{from{{transform:scale(.7) rotate(6deg);opacity:0}}"
                       f"to{{transform:rotate(-2deg)}}}}"
                       f"#ob .tl{{position:absolute;left:70px;right:70px;top:{'120' if ob['jenis'] == 'surat' else '150'}px;font-family:Caveat;"
                       f"font-size:{'66' if len(tulisan) < 70 else '54'}px;line-height:1.15;color:{warna};text-align:center;"
                       f"clip-path:inset(0 100% 0 0);animation:tulis {min(2.4, 0.6 + len(tulisan) / 40):.2f}s {tulis_mulai:.2f}s steps(40,end) forwards}}"
                       "@keyframes tulis{to{clip-path:inset(0 0 0 0)}}")
            isi.append(f'{redup}<div id="obw"><div id="ob">{kertas}<div class="tl">{tulisan}</div></div></div>')
    # ---- overlay di luar kamera
    luar = []
    for k, it in enumerate(a["urutan"]):
        if it.get("ucap"):
            nar = it["tokoh"] == "narator"
            nama = "NARATOR" if nar else T.TOKOH[it["tokoh"]]["nama"].split(" (")[0].upper()
            luar.append(f'<div class="sub{" nar" if nar else ""}" id="s{k}"><small>{_esc(nama)}</small>{_esc(it["ucap"])}</div>')
            css.append(_visibilitas(f"#s{k}", [(it["_mulai"], it["_mulai"] + it["_durasi"] + 0.25)], d))
        elif it.get("teks") and not it.get("_di_objek"):
            luar.append(f'<div class="banner" id="b{k}">{_esc(it["teks"])}</div>')
            css.append(_visibilitas(f"#b{k}", [(it["_mulai"], None)], d))
    if idx == 0:
        luar.append(f'<div class="judulkecil"><span>{JUDUL_SERI} · PART {info_part}</span></div>')
    filt = "filter:sepia(.75) contrast(.95);" if a.get("kilas_balik") else ""
    return (f"<style>{''.join(css)}</style><div class=\"adegan\"><div class=\"cam\" style=\"{filt}\">{_latar(a['latar'])}"
            f"{''.join(isi)}{_cerah(a.get('waktu'), a.get('kilas_balik'))}</div>{''.join(luar)}</div>")


def _tokoh_sampul(papan):
    """Dua tokoh yang paling banyak bicara di part ini (untuk sampul)."""
    hitung = {}
    for a in papan.get("adegan", []):
        for it in a.get("urutan", []):
            if it.get("ucap") and it.get("tokoh") not in (None, "narator", "siluet"):
                hitung[it["tokoh"]] = hitung.get(it["tokoh"], 0) + len(it["ucap"])
    ids = sorted(hitung, key=hitung.get, reverse=True)[:2] or ["laras", "raka"]
    if len(ids) == 1:
        ids.append("raka" if ids[0] != "raka" else "laras")
    ada_siluet = any(t["id"] == "siluet" for a in papan.get("adegan", []) for t in a.get("tokoh", []))
    return ids, ada_siluet


def sampul_html(papan, animasi=True):
    """Sampul/cover seri (aman dipotong 4:5 di grid profil: isi penting di y 300-1620)."""
    part = papan.get("part", 1)
    judul = _esc(papan.get("judul", ""))
    (kiri, kanan), siluet = _tokoh_sampul(papan)
    an = animasi
    return f"""<style>
.sp{{position:absolute;inset:0;overflow:hidden;background:#0b0d1c}}
.sp-bg{{position:absolute;inset:-40px;filter:blur(10px) brightness(.45) saturate(.8);{'animation:spz 3.2s ease-out both;' if an else ''}}}
@keyframes spz{{from{{transform:scale(1.12)}}to{{transform:scale(1.02)}}}}
.sp-vig{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%,rgba(255,190,90,.18),rgba(5,6,16,.2) 40%,rgba(5,6,16,.92) 85%)}}
.sp-pill{{position:absolute;top:330px;left:0;right:0;text-align:center}}
.sp-pill span{{display:inline-block;border:3px solid #ffb347;color:#ffb347;font:700 30px Poppins;letter-spacing:8px;padding:10px 30px;border-radius:50px}}
.sp-j1{{position:absolute;top:400px;left:0;right:0;text-align:center;color:#fff;font:700 150px/1 Poppins;letter-spacing:6px;
  text-shadow:0 8px 30px rgba(0,0,0,.6);{'animation:spin .7s .1s cubic-bezier(.2,1.3,.4,1) both;' if an else ''}}}
.sp-j2{{position:absolute;top:555px;left:0;right:0;text-align:center;color:#ffcf6b;font:120px/1 Caveat;transform:rotate(-3deg);
  text-shadow:0 6px 24px rgba(0,0,0,.6);{'animation:spin .7s .3s cubic-bezier(.2,1.3,.4,1) both;' if an else ''}}}
@keyframes spin{{from{{opacity:0;transform:scale(1.4)}}}}
.sp-amp{{position:absolute;left:270px;top:720px;width:540px;transform:rotate(-8deg);filter:drop-shadow(0 0 40px rgba(255,200,110,.55));
  {'animation:spf 3s ease-in-out infinite alternate;' if an else ''}}}
@keyframes spf{{from{{transform:rotate(-8deg) translateY(0)}}to{{transform:rotate(-5deg) translateY(-18px)}}}}
.sp-q{{position:absolute;left:770px;top:690px;font:700 170px Poppins;color:#ffb347;text-shadow:0 0 30px rgba(255,170,60,.7)}}
.sp-t{{position:absolute;top:1080px;width:560px;height:728px}}
.sp-t svg{{width:100%;height:100%}}
.sp-sil{{position:absolute;left:340px;top:1010px;width:400px;height:520px;opacity:.85;filter:blur(1px)}}
.sp-sil svg{{width:100%;height:100%}}
.sp-fade{{position:absolute;left:0;right:0;top:1380px;height:560px;background:linear-gradient(rgba(5,6,16,0),rgba(5,6,16,.95) 45%)}}
.sp-part{{position:absolute;top:1420px;left:0;right:0;text-align:center;{'animation:spin .6s .55s cubic-bezier(.2,1.4,.4,1) both;' if an else ''}}}
.sp-part b{{display:inline-block;background:#e4572e;color:#fff;font:700 96px/1 Poppins;padding:18px 54px;border-radius:24px;
  box-shadow:0 10px 0 #a33a1c,0 20px 40px rgba(0,0,0,.5);transform:rotate(-2deg)}}
.sp-sub{{position:absolute;top:1560px;left:60px;right:60px;text-align:center;color:#fff;font:700 46px/1.2 Poppins}}
</style>
<div class="sp">
  <div class="sp-bg">{L.latar_depan()}<style>.tk-langit{{background:linear-gradient(#0b1030,#1d2350)!important}}</style></div>
  <div class="sp-vig"></div>
  {f'<div class="sp-sil">{T.dada("siluet")}</div>' if siluet else ''}
  <div class="sp-t" style="left:-70px">{T.dada(kiri, "kaget")}</div>
  <div class="sp-t" style="left:590px;transform:scaleX(-1)">{T.dada(kanan, "bingung")}</div>
  <div class="sp-amp">{T.amplop(540, depan=True)}</div>
  <div class="sp-q">?</div>
  <div class="sp-pill"><span>CERITA BERSAMBUNG</span></div>
  <div class="sp-j1">MISTERI</div>
  <div class="sp-j2">Surat Tanpa Nama</div>
  <div class="sp-fade"></div>
  <div class="sp-part"><b>PART {part}</b></div>
  <div class="sp-sub">{judul}</div>
</div>"""


def render_sampul(papan, out_jpg):
    """Simpan sampul sebagai gambar JPG (untuk pilih sampul saat upload & grid profil)."""
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_page(viewport={"width": W, "height": H})
        halaman = Path(out_jpg).with_suffix(".html")
        halaman.write_text("<!doctype html><html><head><meta charset='utf-8'><style>" + CSS_DASAR.replace("__FONT__", FONT.as_uri())
                           + "</style></head><body>" + sampul_html(papan, animasi=False) + "</body></html>", encoding="utf-8")
        page.goto(halaman.as_uri())
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(300)
        page.screenshot(path=str(out_jpg), type="jpeg", quality=92)
        halaman.unlink()
        b.close()
    return out_jpg


def kartu_akhir(part, terakhir):
    atas = "TAMAT" if terakhir else "Bersambung…"
    bawah = "Musim 1 selesai · terima kasih sudah mengikuti" if terakhir else f"Part {part + 1} segera tayang"
    return f"""<style>.ka{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;color:#fff}}
.ka b{{font-family:Caveat;font-size:150px;color:#ffb347;opacity:0;animation:tampil .8s .2s forwards}}
.ka span{{font-size:46px;margin-top:20px;opacity:0;animation:tampil .8s .7s forwards}}
.ka em{{font-style:normal;font-size:40px;margin-top:70px;background:#fff;color:#1E3A6B;padding:18px 40px;border-radius:60px;opacity:0;
  animation:tampil .8s 1.2s forwards}}</style>
<div class="adegan">{L.latar_polos()}<div class="ka"><b>{atas}</b><span>{bawah}</span><em>🔔 Follow untuk part selanjutnya</em></div></div>"""


# ------------------------------------------------------------------ timeline
def susun_waktu(a):
    """Isi _mulai/_durasi tiap urutan, interval ekspresi & bicara tiap tokoh, dan _durasi adegan."""
    ada_masuk = any(t.get("masuk") in ("kiri", "kanan") for t in a["tokoh"])
    t = 1.0 if ada_masuk else 0.5
    if a.get("objek") and a["latar"] in ("pintu_bawah", "bawah_mesin"):
        t = max(t, 0.9)
    tulisan = (a.get("objek") or {}).get("tulisan", "")
    for it in a["urutan"]:
        it["_mulai"] = t
        if it.get("ucap"):
            t += it["_durasi"] + 0.3
        elif it.get("teks"):
            it["_durasi"] = min(4.5, max(1.8, 1.2 + 0.3 * len(it["teks"].split())))
            it["_di_objek"] = bool(tulisan) and it["teks"].strip(' "“”') == tulisan.strip(' "“”')
            if it["_di_objek"] and "_teks_pertama" not in a:
                a["_teks_pertama"] = t
            t += it["_durasi"] + 0.2
        else:
            it["_durasi"] = min(2.5, float(it.get("jeda", 1.0)))
            t += it["_durasi"]
    a["_durasi"] = max(2.6, t + 0.6)
    for tk in a["tokoh"]:
        ek = {tk["ekspresi"]: [[0.0, None]]}
        sekarang = tk["ekspresi"]
        tk["_bicara"] = []
        bicara_pertama = None
        for it in a["urutan"]:
            if it.get("tokoh") != tk["id"] or not it.get("ucap"):
                continue
            bicara_pertama = it["_mulai"] if bicara_pertama is None else bicara_pertama
            tk["_bicara"].append((it["_mulai"], it["_durasi"]))
            baru = it.get("ekspresi")
            if baru and baru != sekarang:
                ek[sekarang][-1][1] = it["_mulai"]
                ek.setdefault(baru, []).append([it["_mulai"], None])
                sekarang = baru
        tk["_ekspresi"] = {k: [tuple(x) for x in v] for k, v in ek.items()}
        tk["_masuk"] = max(0.1, (bicara_pertama or 0.9) - 0.9)
    return a


# ------------------------------------------------------------------ rekam & suara
def _rekam(page, isi, durasi, folder):
    folder.mkdir(parents=True, exist_ok=True)
    halaman = folder / "h.html"
    halaman.write_text("<!doctype html><html><head><meta charset='utf-8'><style>"
                       + CSS_DASAR.replace("__FONT__", FONT.as_uri()) + "</style></head><body>" + isi + "</body></html>",
                       encoding="utf-8")
    page.goto(halaman.as_uri())
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(250)
    for i in range(round(durasi * FPS)):
        page.evaluate(f"document.getAnimations().forEach(a=>{{a.pause();a.currentTime={i * 1000 / FPS}}})")
        page.screenshot(path=str(folder / f"f{i:04d}.jpg"), type="jpeg", quality=90)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(folder / "f%04d.jpg"),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", str(folder / "klip.mp4")],
                   check=True)
    for f in folder.glob("f*.jpg"):
        f.unlink()
    return folder / "klip.mp4"


SFX = {
    "bel": "(0.22*sin(2*PI*1046.5*t)+0.16*sin(2*PI*1568*t))*exp(-4*t)+if(gte(t,0.2),(0.2*sin(2*PI*1318.5*t)+0.14*sin(2*PI*1975.5*t))*exp(-4*(t-0.2)),0)",
    "klik": "0.35*sin(2*PI*2200*t)*exp(-60*t)",
    "kertas": "0.3*(random(0)*2-1)*exp(-5*t)*(0.55+0.45*sin(2*PI*11*t))",
    "deg": "0.7*sin(2*PI*52*t)*exp(-4*t)+0.25*sin(2*PI*104*t)*exp(-6*t)",
    "langkah": "0.5*sin(2*PI*85*t)*(exp(-28*t)+if(gte(t,0.38),exp(-28*(t-0.38)),0)+if(gte(t,0.76),exp(-28*(t-0.76)),0)"
               "+if(gte(t,1.14),exp(-28*(t-1.14)),0))",
    "lari": "0.5*sin(2*PI*95*t)*(exp(-35*t)+if(gte(t,0.2),exp(-35*(t-0.2)),0)+if(gte(t,0.4),exp(-35*(t-0.4)),0)+if(gte(t,0.6),exp(-35*(t-0.6)),0)"
            "+if(gte(t,0.8),exp(-35*(t-0.8)),0)+if(gte(t,1.0),exp(-35*(t-1.0)),0))*(1.2-t/1.4)",
    "jantung": "0.9*sin(2*PI*55*t)*(exp(-22*t)+if(gte(t,0.24),0.7*exp(-22*(t-0.24)),0)+if(gte(t,1.2),exp(-22*(t-1.2)),0)"
               "+if(gte(t,1.44),0.7*exp(-22*(t-1.44)),0))",
    "angin": "0.22*(random(0)*2-1)*(0.55+0.45*sin(2*PI*0.35*t))*min(1,t/0.8)*min(1,(3-t)/0.8)",
    "detik": "0.35*sin(2*PI*2100*t)*exp(-90*mod(t,0.5))*if(lt(mod(t,1),0.5),1,0.7)",
    "pintu": "0.18*sin(2*PI*(300+180*sin(2*PI*1.7*t))*t)*min(1,t/0.1)*exp(-1.5*t)",
    "petir": "0.6*(random(0)*2-1)*exp(-3*t)*if(lt(t,0.08),2,1)+0.6*sin(2*PI*38*t)*exp(-1.2*t)",
    # otomatis (dipasang mesin, bukan dipilih AI)
    "whoosh": "0.45*(random(0)*2-1)*pow(sin(PI*t/0.7),2)",
    "stinger": "0.75*sin(2*PI*46*t)*exp(-2.4*t)+0.22*sin(2*PI*880*t)*exp(-3*t)*(1+0.5*sin(2*PI*7*t))+0.14*sin(2*PI*1318.5*t)*exp(-4*t)"
               "+0.12*sin(2*PI*622*t)*exp(-2.5*t)",
    "riser": "0.22*sin(2*PI*(180*t+90*t*t))*pow(t/3,2)+0.22*(random(0)*2-1)*pow(t/3,3)",
    "burung": "0.07*sin(2*PI*(2600+900*sin(2*PI*14*t))*t)*gt(sin(2*PI*1.1*t+1),0.82)"
              "+0.05*sin(2*PI*(3400+700*sin(2*PI*18*t))*t)*gt(sin(2*PI*0.7*t),0.9)",
    "jangkrik": "0.05*sin(2*PI*4300*t)*gt(sin(2*PI*28*t),0)*gt(sin(2*PI*0.9*t),0.2)"
                "+0.04*sin(2*PI*3900*t)*gt(sin(2*PI*24*t+1),0)*gt(sin(2*PI*0.6*t+2),0.3)",
}
SFX_AF = {  # filter tambahan supaya efek sintetis terdengar lebih alami
    "kertas": "highpass=f=1200,lowpass=f=7000", "angin": "lowpass=f=600,highpass=f=80",
    "whoosh": "highpass=f=300,lowpass=f=2600", "riser": "highpass=f=150", "petir": "lowpass=f=1800",
    "langkah": "lowpass=f=900", "lari": "lowpass=f=900",
}
DURASI_OTO = {"whoosh": 0.7, "stinger": 2.6, "riser": 3.0}
# rantai suara: buang dengung rendah, tonjolkan kejelasan (presence), ratakan volume
SUARA_JERNIH = ("aresample=44100,highpass=f=90,lowpass=f=11000,equalizer=f=220:t=q:w=1:g=-3,"
                "equalizer=f=3200:t=q:w=1.3:g=4,equalizer=f=6500:t=q:w=2:g=1.5,"
                "acompressor=threshold=-22dB:ratio=3.5:attack=4:release=90:makeup=5,loudnorm=I=-15:TP=-1.5:LRA=7")


def _wav(expr, d, out, af=""):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=44100:d={d:.2f}",
                    *(["-af", af] if af else []), out], check=True)
    return out


# Tokoh yang wajahnya diblur sampai part tertentu (supaya misteri tidak bocor):
# Pak Hadi baru muncul Part 4 & hubungannya dengan Ana terungkap Part 5; Rani terungkap Part 6.
SAMAR_SAMPAI = {"hadi_sma": 5, "rani_sma": 6, "rani": 6}


def render(papan, out_mp4, terakhir=False):
    """papan = dict papan cerita yang sudah lolos sutradara.rapikan(). Kembalikan path video."""
    part = papan.get("part", 1)
    adegan = papan["adegan"]
    for a in adegan:  # wajah tokoh yang identitasnya belum terungkap di part ini dibuat blur
        for t in a.get("tokoh", []):
            if part < SAMAR_SAMPAI.get(t["id"], 0):
                t["samar"] = "bintang" if t["id"] == "rani_sma" and part == 5 else True  # Part 5: wajah ditutup bintang hitam
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # 1) suara tiap ucapan (panjang adegan mengikuti suara)
        n = 0
        for a in adegan:
            for it in a["urutan"]:
                if it.get("ucap"):
                    p = str(tmp / f"v{n:03d}.wav")
                    n += 1
                    suara._tts(it["ucap"], it["tokoh"].split("_")[0], p, it.get("emosi", ""))
                    it["_wav"], it["_durasi"] = p, suara._durasi(p)
                    print(f"  {it['_durasi']:.2f}s {it['tokoh']}: {it['ucap']}")
            susun_waktu(a)
        # 2) render tiap adegan + kartu akhir
        klip, mulai, off = [], [], [0.0]
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            page = b.new_page(viewport={"width": W, "height": H})
            # sampul di awal video (dipakai juga sebagai cover Reel: frame detik ke-2,5)
            klip.append(_rekam(page, sampul_html(papan), DURASI_SAMPUL, tmp / "sampul"))
            t = DURASI_SAMPUL - X
            for i, a in enumerate(adegan):
                print(f"  adegan {i + 1}/{len(adegan)}: {a['latar']} {a['_durasi']:.1f}s")
                mulai.append(t)
                off.append(t)
                klip.append(_rekam(page, adegan_html(a, i, part), a["_durasi"], tmp / f"a{i}"))
                t += a["_durasi"] - X
            d_akhir = 3.2
            mulai.append(t)
            off.append(t)
            klip.append(_rekam(page, kartu_akhir(part, terakhir), d_akhir, tmp / "akhir"))
            b.close()
        total = t + d_akhir
        # 3) audio: musik latar + efek + suara
        inputs, filt, label = [], [], []
        for k in klip:
            inputs += ["-i", str(k)]
        vlab = "[0:v]"
        for i in range(1, len(klip)):
            filt.append(f"{vlab}[{i}:v]xfade=transition=fade:duration={X}:offset={off[i]:.3f}[v{i}]")
            vlab = f"[v{i}]"
        idx = len(klip)
        # musik latar misteri: drone rendah + pulsa pelan, naik sedikit menjelang akhir
        musik = ("(0.045*sin(2*PI*110*t)+0.03*sin(2*PI*164.8*t)+0.025*sin(2*PI*220*t)+0.018*sin(2*PI*261.6*t))"
                 "*(0.7+0.3*sin(2*PI*0.2*t))*min(1,t/1.5)"
                 f"*(1+0.5*min(1,max(0,(t-{max(0, mulai[-1] - 6):.2f})/6)))"
                 "+0.05*sin(2*PI*48*t)*exp(-9*mod(t,1.6))")
        inputs += ["-i", _wav(musik, total, str(tmp / "musik.wav"), "lowpass=f=1500")]
        bg, vo = [f"[{idx}:a]"], []
        idx += 1
        cache = {}

        def efek(nama, d=None):
            d = d or EFEK.get(nama) or DURASI_OTO[nama]
            k = f"{nama}-{d:.2f}"
            if k not in cache:
                cache[k] = _wav(SFX[nama], d, str(tmp / f"sfx_{k}.wav"), SFX_AF.get(nama, ""))
            return cache[k]

        def taruh(path, detik, vol, nama, suara=False):
            nonlocal idx
            ms = int(max(0, detik) * 1000)
            inputs.extend(["-i", path])
            rantai = (SUARA_JERNIH + "," if suara else "aresample=44100,")
            filt.append(f"[{idx}:a]{rantai}aformat=channel_layouts=mono,adelay={ms}|{ms},volume={vol}[{nama}]")
            (vo if suara else bg).append(f"[{nama}]")
            idx += 1

        for i, a in enumerate(adegan):
            m = mulai[i]
            taruh(efek("whoosh"), m - 0.35, 0.55, f"w{i}")  # transisi antar adegan
            # suasana: burung di pagi hari (luar toko), jangkrik + angin di malam hari
            if a.get("waktu") == "malam":
                taruh(efek("jangkrik", a["_durasi"]), m, 0.7, f"amb{i}")
                taruh(efek("angin", a["_durasi"]), m, 0.5, f"ang{i}")
            elif a.get("waktu") == "pagi" and a["latar"] in ("depan", "depan_buka"):
                taruh(efek("burung", a["_durasi"]), m, 0.6, f"amb{i}")
            for j, e in enumerate(a.get("efek", [])):
                taruh(efek(e), m + 0.25 + 0.45 * j, 0.85, f"e{i}_{j}")
            tegang = any(t["ekspresi"] in ("kaget", "takut") for t in a["tokoh"]) or any(
                it.get("ekspresi") in ("kaget", "takut") for it in a["urutan"])
            stinger = False
            for k, it in enumerate(a["urutan"]):
                if it.get("_wav"):
                    taruh(it["_wav"], m + it["_mulai"], 1.0, f"s{i}_{k}", suara=True)
                if not stinger and (it.get("teks") or it.get("ekspresi") in ("kaget", "takut")):
                    taruh(efek("stinger"), m + it["_mulai"] - 0.05, 0.7, f"st{i}_{k}")
                    stinger = True
                if it.get("jeda"):
                    taruh(efek("detik", min(2.0, it["_durasi"] + 0.4)), m + it["_mulai"], 0.6, f"dt{i}_{k}")
            if tegang and "jantung" not in a.get("efek", []):
                taruh(efek("jantung"), m + 0.3, 0.6, f"j{i}")
        taruh(efek("stinger"), 0.15, 0.9, "buka")  # hantaman pembuka di sampul
        # menjelang kartu "Bersambung": riser lalu hantaman
        taruh(efek("riser"), mulai[-1] - 3.0, 0.6, "riser")
        taruh(efek("stinger"), mulai[-1], 0.95, "hit")
        # campur: latar (musik+efek) diredam otomatis saat ada suara (ducking), suara di depan
        if not vo:  # tanpa ucapan sama sekali: suara kosong
            taruh(_wav("0", total, str(tmp / "hening.wav")), 0, 1, "hening", suara=False)
            vo.append(bg.pop())
        filt.append("".join(vo) + f"amix=inputs={len(vo)}:duration=longest:normalize=0,apad=whole_dur={total:.2f},"
                    "asplit=2[vo1][vo2]")
        filt.append("".join(bg) + f"amix=inputs={len(bg)}:duration=first:normalize=0[bg0]")
        filt.append("[bg0][vo1]sidechaincompress=threshold=0.04:ratio=5:attack=15:release=350:makeup=1[bg]")
        filt.append(f"[bg][vo2]amix=inputs=2:duration=first:normalize=0,afade=t=out:st={total - 0.8:.2f}:d=0.8,"
                    "loudnorm=I=-14:TP=-1.2:LRA=11,alimiter=limit=0.95[a]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt),
                        "-map", vlab, "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-movflags", "+faststart", out_mp4], check=True)
    render_sampul(papan, sampul_path(out_mp4))
    print(f"  selesai: {total:.1f} detik -> {out_mp4} (+ sampul)")
    return out_mp4


def sampul_path(out_mp4):
    return str(Path(out_mp4).with_name(Path(out_mp4).stem + "-sampul.jpg"))
