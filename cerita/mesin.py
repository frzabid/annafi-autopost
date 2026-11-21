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
    "polos": "latar gelap polos (untuk teks/kejutan)",
}
LEBAR = {"depan_buka", "depan", "depan_malam", "dalam"}  # tokoh tampil seluruh badan
OBJEK = {"amplop": "amplop krem bergambar bintang biru", "amplop_tua": "amplop tua kekuningan",
         "surat": "kertas surat bertulisan tangan"}
KAMERA = ["diam", "zoom_in", "zoom_out", "geser", "goyang"]
EFEK = {"bel": 1.6, "klik": 0.2, "kertas": 0.6, "deg": 1.4, "langkah": 1.6}
WAKTU = ["pagi", "siang", "sore", "malam"]
POSISI_LEBAR = {"kiri": 230, "tengah": 540, "kanan": 850}
POSISI_DEKAT = {"kiri": 290, "tengah": 540, "kanan": 790}
BASIS = {"depan_buka": 1790, "depan": 1790, "depan_malam": 1790, "dalam": 1800}

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
                   f'transform:{flip};{masuk}"><div class="badan">{lapisan}</div></div>')
    # ---- objek
    ob = a.get("objek")
    if ob:
        tulis_mulai = a.get("_teks_pertama", 0.5)
        tulisan = _esc(ob.get("tulisan"))
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


def kartu_akhir(part, terakhir):
    atas = "TAMAT" if terakhir else "Bersambung…"
    bawah = "Musim 1 selesai · terima kasih sudah mengikuti" if terakhir else f"Part {part + 1} segera tayang"
    return f"""<style>.ka{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;color:#fff}}
.ka b{{font-family:Caveat;font-size:150px;color:#ffb347;opacity:0;animation:tampil .8s .2s forwards}}
.ka span{{font-size:46px;margin-top:20px;opacity:0;animation:tampil .8s .7s forwards}}
.ka em{{font-style:normal;font-size:40px;margin-top:70px;background:#fff;color:#1E3A6B;padding:18px 40px;border-radius:60px;opacity:0;
  animation:tampil .8s 1.2s forwards}}</style>
<div class="adegan">{L.latar_polos()}<div class="ka"><b>{atas}</b><span>{bawah}</span><em>🔔 Follow {AKUN}</em></div></div>"""


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
    "kertas": "0.22*(random(0)*2-1)*exp(-5*t)*(0.6+0.4*sin(2*PI*9*t))",
    "deg": "0.6*sin(2*PI*52*t)*exp(-4*t)",
    "langkah": "0.45*sin(2*PI*85*t)*(exp(-28*t)+if(gte(t,0.38),exp(-28*(t-0.38)),0)+if(gte(t,0.76),exp(-28*(t-0.76)),0)"
               "+if(gte(t,1.14),exp(-28*(t-1.14)),0))",
}


def _wav(expr, d, out):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=44100:d={d:.2f}", out], check=True)
    return out


def render(papan, out_mp4, terakhir=False):
    """papan = dict papan cerita yang sudah lolos sutradara.rapikan(). Kembalikan path video."""
    part = papan.get("part", 1)
    adegan = papan["adegan"]
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
        klip, mulai = [], []
        t = 0.0
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            page = b.new_page(viewport={"width": W, "height": H})
            for i, a in enumerate(adegan):
                print(f"  adegan {i + 1}/{len(adegan)}: {a['latar']} {a['_durasi']:.1f}s")
                mulai.append(t)
                klip.append(_rekam(page, adegan_html(a, i, part), a["_durasi"], tmp / f"a{i}"))
                t += a["_durasi"] - X
            d_akhir = 3.2
            mulai.append(t)
            klip.append(_rekam(page, kartu_akhir(part, terakhir), d_akhir, tmp / "akhir"))
            b.close()
        total = t + d_akhir
        # 3) audio: musik latar + efek + suara
        inputs, filt, label = [], [], []
        for k in klip:
            inputs += ["-i", str(k)]
        vlab = "[0:v]"
        for i in range(1, len(klip)):
            filt.append(f"{vlab}[{i}:v]xfade=transition=fade:duration={X}:offset={mulai[i]:.3f}[v{i}]")
            vlab = f"[v{i}]"
        idx = len(klip)
        musik = ("(0.035*sin(2*PI*220*t)+0.03*sin(2*PI*261.6*t)+0.025*sin(2*PI*329.6*t))*(0.75+0.25*sin(2*PI*0.25*t))"
                 "*min(1,t/1.5)")
        inputs += ["-i", _wav(musik, total, str(tmp / "musik.wav"))]
        label.append(f"[{idx}:a]")
        idx += 1

        def taruh(path, detik, vol, nama):
            nonlocal idx
            ms = int(max(0, detik) * 1000)
            inputs.extend(["-i", path])
            filt.append(f"[{idx}:a]adelay={ms}|{ms},volume={vol}[{nama}]")
            label.append(f"[{nama}]")
            idx += 1

        sfx_cache = {}
        for i, a in enumerate(adegan):
            for j, e in enumerate(a.get("efek", [])):
                if e not in sfx_cache:
                    sfx_cache[e] = _wav(SFX[e], EFEK[e], str(tmp / f"sfx_{e}.wav"))
                taruh(sfx_cache[e], mulai[i] + 0.25 + 0.45 * j, 0.8, f"e{i}_{j}")
            for k, it in enumerate(a["urutan"]):
                if it.get("_wav"):
                    taruh(it["_wav"], mulai[i] + it["_mulai"], 1.6, f"s{i}_{k}")
        taruh(_wav(SFX["deg"], EFEK["deg"], str(tmp / "dentum.wav")), mulai[-1], 0.9, "dentum")
        filt.append("".join(label) + f"amix=inputs={len(label)}:duration=first:normalize=0,"
                    f"afade=t=out:st={total - 0.8:.2f}:d=0.8,alimiter=limit=0.95[a]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt),
                        "-map", vlab, "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out_mp4], check=True)
    print(f"  selesai: {total:.1f} detik -> {out_mp4}")
    return out_mp4
