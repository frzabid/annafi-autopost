"""Pembuka 'Misteri Surat Tanpa Nama' Part 1 dengan suara - adegan MENGIKUTI panjang suara (tidak dipercepat).

Urutan: 1) buat suara tiap baris & ukur durasinya  2) hitung panjang tiap adegan  3) render tiap adegan
(animasi CSS direkam frame demi frame)  4) sambung adegan dengan crossfade  5) campur suara + efek.
Pakai:  python cerita/part1_pembuka.py out.mp4
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from tokoh import laras_badan, laras_dada, amplop  # noqa: E402
import suara  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "assets" / "fonts"
W, H, FPS = 1080, 1920, 30
X = 0.35  # crossfade antar adegan (detik)

BARIS = {
    "a": ("narator", "Jam enam pagi. Seperti biasa, Mbak Laras membuka toko."),
    "b": ("narator", "Tapi pagi ini... ada yang berbeda."),
    "c1": ("laras", "Lho? Surat untuk siapa ini?"),
    "c2": ("narator", "Misteri Surat Tanpa Nama."),
}

CSS_DASAR = """
@font-face{font-family:Poppins;src:url('__FONT__/Poppins-Bold.ttf');font-weight:700}
@font-face{font-family:Poppins;src:url('__FONT__/Poppins-Regular.ttf');font-weight:400}
@font-face{font-family:Caveat;src:url('__FONT__/Caveat-Bold.woff2')}
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;background:#000;font-family:Poppins}
.adegan{position:absolute;inset:0;overflow:hidden}
.cam{position:absolute;inset:0;transform-origin:50% 60%}
.cap{position:absolute;left:70px;right:70px;top:150px;background:rgba(255,255,255,.94);border-radius:28px;
  padding:34px 40px;font-size:50px;line-height:1.3;color:#1E3A6B;font-weight:700;box-shadow:0 10px 30px rgba(0,0,0,.18);opacity:0}
.cap small{display:block;font-size:34px;font-weight:400;color:#c26a1b;margin-bottom:8px;letter-spacing:2px}
@keyframes cap{0%{opacity:0;transform:translateY(-30px)}100%{opacity:1;transform:none}}
.kedip{animation:kedip 3.2s infinite;transform-origin:200px 204px}
@keyframes kedip{0%,92%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}
"""


def _buku() -> str:
    warna = ["#e4572e", "#2F6FD1", "#f3a712", "#4f9a55", "#8e5ea2", "#1E3A6B", "#e86a92"]
    out, i = [], 0
    for top in (88, 258, 428):
        x = 40
        while x < 360:
            h = 50 + (i * 13) % 14
            out.append(f'<div class="buku" style="left:{x}px;top:{top + 62 - h}px;height:{h}px;background:{warna[i % len(warna)]}"></div>')
            x += 46
            i += 1
    return "".join(out)


def adegan_a(d: float) -> str:
    return f"""<style>
.cam{{animation:zoom {d}s ease-in-out forwards}}@keyframes zoom{{from{{transform:scale(1)}}to{{transform:scale(1.12)}}}}
.langit{{position:absolute;inset:0;background:linear-gradient(#8fc6ea 0%,#cfe6f2 40%,#ffe0b5 72%,#ffd19a 100%)}}
.matahari{{position:absolute;width:190px;height:190px;border-radius:50%;background:#ffe9a8;box-shadow:0 0 120px 60px rgba(255,220,140,.7);
  right:120px;top:520px;animation:naik {d}s ease-out forwards}}@keyframes naik{{from{{transform:translateY(60px)}}to{{transform:translateY(-20px)}}}}
.awan{{position:absolute;height:70px;border-radius:40px;background:#fff;opacity:.85}}
.gedung{{position:absolute;left:90px;width:900px;top:640px;height:900px;background:#f1e6d0;border-radius:6px}}
.papan{{position:absolute;left:60px;width:960px;top:600px;height:150px;background:#1E3A6B;border-radius:16px;color:#fff;text-align:center;padding-top:18px}}
.papan b{{font-size:66px;letter-spacing:6px;display:block;line-height:1.1}}.papan span{{font-size:30px;letter-spacing:4px;color:#ffd19a}}
.tenda{{position:absolute;left:150px;width:780px;top:760px;height:80px;background:repeating-linear-gradient(90deg,#2F6FD1 0 78px,#fff 78px 156px);border-radius:0 0 40px 40px}}
.pintu{{position:absolute;left:250px;width:580px;top:860px;height:680px;background:#ffe6ad;overflow:hidden;border:14px solid #c9b48c;border-bottom:none}}
.rak{{position:absolute;left:30px;right:30px;height:16px;background:#a77b4f}}.buku{{position:absolute;width:40px;border-radius:4px}}
.fotokopi{{position:absolute;right:40px;bottom:0;width:190px;height:230px;background:#dfe3ea;border-radius:12px;border:6px solid #9aa3b2}}
.rolling{{position:absolute;left:0;right:0;top:0;height:100%;background:repeating-linear-gradient(#a9b0bb 0 26px,#8e96a3 26px 32px);
  animation:buka 2.6s .35s cubic-bezier(.45,.05,.4,1) forwards}}@keyframes buka{{from{{transform:translateY(0)}}to{{transform:translateY(-78%)}}}}
.trotoar{{position:absolute;left:0;right:0;top:1540px;height:150px;background:#d8ccb4}}
.jalan{{position:absolute;left:0;right:0;top:1690px;bottom:0;background:#6d6f75}}
.marka{{position:absolute;top:1800px;height:14px;width:140px;background:#f1f1f1;border-radius:6px}}
.pot{{position:absolute;bottom:400px;width:90px;height:90px;background:#b5653b;border-radius:0 0 22px 22px}}
.daun{{position:absolute;width:130px;height:150px;border-radius:50% 50% 46% 46%;background:#4f9a55}}
#nafiA{{position:absolute;left:690px;top:1000px;width:300px;animation:goyang 1.6s ease-in-out infinite alternate}}
@keyframes goyang{{from{{transform:rotate(-1.2deg)}}to{{transform:rotate(1.2deg)}}}}
.c1{{animation:cap .45s .4s forwards}}
</style>
<div class="adegan"><div class="cam">
  <div class="langit"></div><div class="matahari"></div>
  <div class="awan" style="left:80px;top:300px;width:260px"></div><div class="awan" style="left:620px;top:220px;width:320px"></div>
  <div class="gedung"></div>
  <div class="pintu"><div class="rak" style="top:150px"></div><div class="rak" style="top:320px"></div><div class="rak" style="top:490px"></div>
    {_buku()}<div class="fotokopi"></div><div class="rolling"></div></div>
  <div class="tenda"></div>
  <div class="papan"><b>ANNAFI ATK</b><span>FOTOKOPI · PRINT · ALAT TULIS</span></div>
  <div class="trotoar"></div><div class="jalan"></div>
  <div class="marka" style="left:80px"></div><div class="marka" style="left:470px"></div><div class="marka" style="left:860px"></div>
  <div class="daun" style="left:95px;top:1360px"></div><div class="pot" style="left:115px"></div>
  <div id="nafiA">{laras_badan("senang")}</div>
</div><div class="cap c1"><small>JAM 06.00 PAGI</small>Seperti biasa, Mbak Laras membuka toko…</div></div>"""


def adegan_b(d: float) -> str:
    return f"""<style>
.cam{{animation:zoom {d}s ease-in forwards;transform-origin:50% 66%}}@keyframes zoom{{from{{transform:scale(1)}}to{{transform:scale(1.32)}}}}
.lantai{{position:absolute;inset:0;background:linear-gradient(rgba(255,214,150,0),rgba(255,214,150,.35)),
  repeating-linear-gradient(90deg,#e7dcc6 0 178px,#cdbf9f 178px 184px),#e7dcc6}}
.lantai:after{{content:'';position:absolute;inset:0;background:repeating-linear-gradient(#0000 0 178px,#cdbf9f 178px 184px)}}
.bawahpintu{{position:absolute;left:0;right:0;top:0;height:640px;background:repeating-linear-gradient(#a9b0bb 0 26px,#8e96a3 26px 32px)}}
.celah{{position:absolute;left:0;right:0;top:640px;height:26px;background:#3b3f47}}
.sinar{{position:absolute;left:0;right:0;top:666px;height:500px;background:linear-gradient(rgba(255,226,160,.55),rgba(255,226,160,0))}}
#amplopB{{position:absolute;left:330px;top:1080px;filter:drop-shadow(0 18px 14px rgba(0,0,0,.25));animation:geser 1.2s .1s ease-out both}}
@keyframes geser{{from{{transform:translateY(-330px) rotate(-2deg)}}to{{transform:translateY(0) rotate(-8deg)}}}}
.kilau{{position:absolute;left:640px;top:1060px;width:60px;height:60px;opacity:0;animation:kilau 1s 1.1s ease-out forwards}}
@keyframes kilau{{0%{{opacity:0;transform:scale(.3) rotate(0)}}50%{{opacity:1}}100%{{opacity:0;transform:scale(1.4) rotate(90deg)}}}}
.c2{{animation:cap .45s .3s forwards}}
</style>
<div class="adegan"><div class="cam">
  <div class="lantai"></div><div class="bawahpintu"></div><div class="celah"></div><div class="sinar"></div>
  <div id="amplopB">{amplop(420)}</div>
  <svg class="kilau" viewBox="0 0 60 60"><path d="M30 0 L36 24 L60 30 L36 36 L30 60 L24 36 L0 30 L24 24Z" fill="#fff"/></svg>
</div><div class="cap c2">…tapi pagi ini, ada yang <span style="color:#c26a1b">berbeda.</span></div></div>"""


def adegan_c(d: float, t_nafi: float, t_judul: float) -> str:
    return f"""<style>
.latarC{{position:absolute;inset:-40px;background:radial-gradient(circle at 50% 40%,#ffe8b8,#d9a866 70%,#7a5a36);filter:blur(2px)}}
.vignette{{position:absolute;inset:0;background:radial-gradient(circle at 50% 45%,#0000 45%,rgba(0,0,0,.55));opacity:0;
  animation:gelap 1.2s {max(0, t_judul - 0.2):.2f}s forwards}}@keyframes gelap{{to{{opacity:1}}}}
#amplopC{{position:absolute;left:90px;top:330px;width:900px;animation:dekat {d}s ease-out both}}
@keyframes dekat{{from{{transform:scale(.82) rotate(4deg)}}to{{transform:scale(1) rotate(-2deg)}}}}
.tulisan{{position:absolute;left:170px;top:520px;width:740px;font-family:Caveat;font-size:76px;line-height:1.15;color:#1E3A6B;text-align:center;
  clip-path:inset(0 100% 0 0);animation:tulis 1.6s .3s steps(40,end) forwards}}@keyframes tulis{{to{{clip-path:inset(0 0 0 0)}}}}
#nafiC{{position:absolute;left:-30px;bottom:-40px;width:520px;animation:masuk .6s {max(0, t_nafi - 0.35):.2f}s cubic-bezier(.2,1.6,.4,1) both}}
@keyframes masuk{{from{{transform:translate(-300px,120px) rotate(-8deg)}}to{{transform:none}}}}
.tanya{{position:absolute;left:480px;bottom:330px;font-weight:700;font-size:150px;color:#fff;text-shadow:0 6px 0 #1E3A6B;opacity:0;
  animation:pop .5s {t_nafi + 0.25:.2f}s cubic-bezier(.2,1.8,.4,1) forwards}}@keyframes pop{{from{{opacity:0;transform:scale(.2)}}to{{opacity:1;transform:none}}}}
.judul{{position:absolute;left:0;right:0;top:1000px;text-align:center;opacity:0;animation:judul .9s {t_judul:.2f}s ease-out forwards}}
@keyframes judul{{from{{opacity:0;letter-spacing:30px}}to{{opacity:1;letter-spacing:4px}}}}
.judul b{{display:block;font-size:84px;line-height:1.05;color:#fff;text-shadow:0 8px 24px rgba(0,0,0,.6)}}
.judul span{{display:inline-block;margin-top:22px;font-family:Caveat;font-size:84px;color:#ffb347;text-shadow:0 6px 18px rgba(0,0,0,.6)}}
</style>
<div class="adegan"><div class="latarC"></div>
  <div id="amplopC">{amplop(900, depan=True)}</div>
  <div class="tulisan">Untuk siapa pun yang membuka toko ini paling pagi.</div>
  <div class="vignette"></div><div id="nafiC">{laras_dada("kaget")}</div><div class="tanya">?</div>
  <div class="judul"><b>MISTERI SURAT<br>TANPA NAMA</b><span>Part 1</span></div></div>"""


def _rekam(page, isi: str, durasi: float, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    halaman = folder / "h.html"
    halaman.write_text("<!doctype html><html><head><meta charset='utf-8'><style>"
                       + CSS_DASAR.replace("__FONT__", FONT.as_uri()) + "</style></head><body>" + isi + "</body></html>",
                       encoding="utf-8")
    page.goto(halaman.as_uri())
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(300)
    for i in range(round(durasi * FPS)):
        page.evaluate(f"document.getAnimations().forEach(a=>{{a.pause();a.currentTime={i * 1000 / FPS}}})")
        page.screenshot(path=str(folder / f"f{i:04d}.jpg"), type="jpeg", quality=92)


def _klip(folder: Path, out: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(folder / "f%04d.jpg"),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(out)], check=True)


def _efek(out_wav: str, total: float, sB: float, sC: float, t_judul: float) -> None:
    """Efek suara sintetis mengikuti timeline: suasana pagi, rolling door, denting, nada misteri, dentuman."""
    pad = f"(0.05*sin(2*PI*261.6*t)+0.04*sin(2*PI*392*t))*(1-exp(-t))*if(lt(t,{sC}),1,max(0,1-(t-{sC})/0.6))"
    rolling = "if(between(t,0.35,2.95),0.22*sin(2*PI*55*t)*(0.5+0.5*sin(2*PI*17*t))*sin(PI*(t-0.35)/2.6),0)"
    ting = f"if(gte(t,{sB + 1.1}),(0.28*sin(2*PI*1318.5*t)+0.18*sin(2*PI*1975.5*t))*exp(-3*(t-{sB + 1.1})),0)"
    misteri = f"if(gte(t,{sC + 0.2}),(0.07*sin(2*PI*220*t)+0.06*sin(2*PI*261.6*t)+0.05*sin(2*PI*329.6*t))*min(1,(t-{sC + 0.2})/0.6),0)"
    tj = sC + t_judul
    dentum = f"if(gte(t,{tj}),0.6*sin(2*PI*52*t)*exp(-4*(t-{tj})),0)"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"aevalsrc='{pad}+{rolling}+{ting}+{misteri}+{dentum}':s=44100:d={total:.2f}",
                    "-af", f"afade=t=out:st={total - 0.6:.2f}:d=0.6", out_wav], check=True)


def render(out_mp4: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # 1) suara dulu, ukur durasinya (TIDAK dipercepat)
        klip_suara, dur = {}, {}
        for k, (tokoh, teks) in BARIS.items():
            p = str(tmp / f"v_{k}.wav")
            suara._tts(teks, tokoh, p)
            klip_suara[k], dur[k] = p, suara._durasi(p)
            print(f"  {k}: {dur[k]:.2f}s  {teks}")

        # 2) panjang adegan mengikuti suara (+ jeda napas)
        dA = max(3.8, 0.4 + dur["a"] + 0.7)
        dB = max(3.1, 0.3 + dur["b"] + 0.7)
        t_nafi = 0.9
        t_judul = max(2.0, t_nafi + dur["c1"] + 0.35)
        dC = max(3.4, t_judul + dur["c2"] + 0.9)
        sB = dA - X
        sC = sB + dB - X
        total = sC + dC
        print(f"  adegan A {dA:.2f}s, B {dB:.2f}s, C {dC:.2f}s -> total {total:.2f}s")

        # 3) render tiap adegan
        with sync_playwright() as p:
            b = p.chromium.launch()
            page = b.new_page(viewport={"width": W, "height": H})
            _rekam(page, adegan_a(dA), dA, tmp / "a")
            _rekam(page, adegan_b(dB), dB, tmp / "b")
            _rekam(page, adegan_c(dC, t_nafi, t_judul), dC, tmp / "c")
            b.close()
        for k in "abc":
            _klip(tmp / k, tmp / f"{k}.mp4")

        # 4+5) sambung (crossfade) + campur suara & efek
        efek = str(tmp / "efek.wav")
        _efek(efek, total, sB, sC, t_judul)
        posisi = {"a": 0.4, "b": sB + 0.3, "c1": sC + t_nafi, "c2": sC + t_judul}
        inputs = ["-i", str(tmp / "a.mp4"), "-i", str(tmp / "b.mp4"), "-i", str(tmp / "c.mp4"), "-i", efek]
        filt = [f"[0:v][1:v]xfade=transition=fade:duration={X}:offset={dA - X:.3f}[ab]",
                f"[ab][2:v]xfade=transition=fade:duration={X}:offset={sC:.3f}[v]",
                "[3:a]volume=0.55[e]"]
        for i, k in enumerate(BARIS):
            inputs += ["-i", klip_suara[k]]
            ms = int(posisi[k] * 1000)
            filt.append(f"[{4 + i}:a]adelay={ms}|{ms},volume=1.6[s{i}]")
        filt.append("[e]" + "".join(f"[s{i}]" for i in range(len(BARIS)))
                    + f"amix=inputs={len(BARIS) + 1}:duration=first:normalize=0,alimiter=limit=0.95[a]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt),
                        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out_mp4], check=True)
    return out_mp4


if __name__ == "__main__":
    print("Mesin suara:", suara.MESIN)
    print(render(sys.argv[1] if len(sys.argv) > 1 else "pembuka.mp4"))
