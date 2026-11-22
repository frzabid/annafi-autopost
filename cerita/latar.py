"""Latar tetap Toko Annafi - digambar dari foto asli toko (lihat juga cerita/lingkungan_toko.md).

Ciri yang WAJIB konsisten di semua episode:
- Depan: dinding biru muda + roster berpola, kanopi atap seng dengan rangka baja kisi-kisi & tiang besi di atas parkiran,
  jendela/pintu kaca berbingkai putih, spanduk 'ANNAFI print' di kanan, teras keramik krem (tanpa motor parkir).
- Dalam: plafon atap seng terbuka + balok, lampu neon gantung, dinding krem, tiang putih, rak gondola rangka MERAH
  berjaring kawat penuh barang, lantai keramik krem mengkilap, spanduk biru ANNAFI print, bendera merah-putih;
  KANAN = satu area layanan: meja + mesin fotokopi + printer + komputer + etalase kaca + kursi plastik + TV CCTV.
- Pintu: bingkai putih, keset bermotif daun.
Semua berupa potongan HTML/CSS ukuran 1080x1920; kelas diawali 'tk-' supaya tidak bentrok.
"""
import random

WARNA = ["#e4572e", "#2F6FD1", "#f3a712", "#4f9a55", "#8e5ea2", "#e86a92", "#17a2b8", "#ffcf3f", "#ff7f50", "#ffffff"]
BIRU_DINDING = "#a9d1e8"
SENG = "repeating-linear-gradient(90deg,#9aa4ad 0 22px,#b9c2ca 22px 34px)"


# ---------------------------------------------------------------- isi rak
def _barang(lebar: int, rng: random.Random) -> str:
    out, x = [], 4
    while x < lebar - 16:
        w = rng.choice([14, 18, 24, 30, 38, 46])
        h = rng.randint(28, 58)
        c = rng.choice(WARNA)
        out.append(f'<i style="left:{x}px;width:{w}px;height:{h}px;background:{c};border-radius:3px"></i>')
        x += w + rng.randint(2, 5)
    return "".join(out)


def _gondola(x: int, y: int, w: int, h: int, baris: int, seed: int) -> str:
    """Rak gondola: tiang merah, papan putih, latar jaring kawat, penuh barang warna-warni."""
    rng = random.Random(seed)
    t = h // baris
    rows = "".join(f'<div class="tk-papan-rak" style="top:{(b + 1) * t - 10}px"></div>'
                   f'<div class="tk-isi" style="top:{b * t + 6}px;height:{t - 16}px">{_barang(w - 20, rng)}</div>'
                   for b in range(baris))
    return f'<div class="tk-gondola" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">{rows}</div>'


CSS = """
.tk-gondola{position:absolute;background-color:#f4f4f4;
  background-image:linear-gradient(#cfd4d9 2px,transparent 2px),linear-gradient(90deg,#cfd4d9 2px,transparent 2px);
  background-size:22px 22px;border-left:16px solid #d62f2f;border-right:16px solid #d62f2f;border-top:10px solid #d62f2f}
.tk-papan-rak{position:absolute;left:0;right:0;height:12px;background:#fff;box-shadow:0 4px 0 #c9cdd2}
.tk-isi{position:absolute;left:10px;right:10px;overflow:hidden}
.tk-isi i{position:absolute;bottom:0;box-shadow:inset 0 -5px rgba(0,0,0,.12)}
.tk-neon{position:absolute;height:12px;border-radius:6px;background:#fff;box-shadow:0 0 26px 8px rgba(255,255,240,.7)}
.tk-tali{position:absolute;width:3px;background:#e8e8e8}
"""


# ---------------------------------------------------------------- dalam toko
def latar_dalam(terang: float = 1.0) -> str:
    """Interior (tampak dari pintu masuk). terang 0..1 untuk efek lampu menyala."""
    bendera = "".join(f'<i style="left:{40 + i * 58}px;background:{"#d62828" if i % 2 == 0 else "#fff"}"></i>' for i in range(10))
    return f"""<style>{CSS}
.tk-dalam{{position:absolute;inset:0;background:#f3eedf;filter:brightness({0.5 + 0.5 * terang})}}
.tk-plafon{{position:absolute;left:0;right:0;top:0;height:330px;background:{SENG};
  clip-path:polygon(0 0,100% 0,100% 70%,0 100%)}}
.tk-balok{{position:absolute;height:26px;background:#c9c7c0;transform-origin:0 0}}
.tk-dinding{{position:absolute;left:0;right:0;top:250px;height:1110px;background:#f2ecd9}}
.tk-tiang{{position:absolute;top:240px;width:80px;height:1160px;background:#f7f5ef;box-shadow:inset -10px 0 #e3e0d5}}
.tk-lantai{{position:absolute;left:0;right:0;top:1360px;bottom:0;background:
  linear-gradient(rgba(255,255,255,.35),rgba(255,255,255,0) 40%),
  repeating-linear-gradient(90deg,#e3d9c6 0 214px,#d2c6b0 214px 218px),#e3d9c6}}
.tk-lantai:after{{content:'';position:absolute;inset:0;background:repeating-linear-gradient(#0000 0 160px,#d2c6b0 160px 164px)}}
.tk-spanduk{{position:absolute;left:40px;top:430px;width:400px;height:200px;background:#2a9fd6;border:6px solid #1c6ea4;border-radius:6px;
  color:#fff;font:700 54px Poppins,sans-serif;padding:14px 22px;line-height:1;box-sizing:border-box}}
.tk-spanduk small{{display:block;font:400 22px Poppins,sans-serif;margin-top:14px;line-height:1.5;color:#e9f6ff}}
.tk-bendera{{position:absolute;left:0;top:660px;width:700px;height:60px}}
.tk-bendera i{{position:absolute;top:0;width:50px;height:56px;clip-path:polygon(0 0,100% 0,50% 100%)}}
.tk-tv{{position:absolute;left:900px;top:560px;width:130px;height:80px;background:#222;border:6px solid #111;border-radius:6px}}
.tk-tv:after{{content:'';position:absolute;inset:8px;background:linear-gradient(90deg,#5d6d7e 50%,#7f8c8d 50%)}}
.tk-kipas{{position:absolute;left:790px;top:560px;width:64px;height:64px;border-radius:50%;border:8px solid #333}}
.tk-raklayan{{position:absolute;left:640px;top:720px;width:420px;height:300px;border:8px solid #8e979f;border-top:none;
  background:repeating-linear-gradient(#0000 0 92px,#8e979f 92px 100px)}}
.tk-raklayan i{{position:absolute;width:70px;height:50px;background:#3b3b3b;border-radius:4px}}
.tk-meja{{position:absolute;left:600px;width:480px;top:1110px;height:250px;background:#e9dcc3;border-top:18px solid #cbb48f}}
.tk-fc{{position:absolute;width:170px;height:150px;background:#f1efe8;border:6px solid #c9c4b8;border-radius:10px}}
.tk-fc:before{{content:'';position:absolute;left:10px;right:10px;top:-34px;height:34px;background:#e5e2d9;border-radius:8px 8px 0 0}}
.tk-fc:after{{content:'';position:absolute;left:20px;top:18px;width:60px;height:18px;background:#5d6d7e;border-radius:3px}}
.tk-pc{{position:absolute;left:860px;top:1000px;width:110px;height:84px;background:#1f1f1f;border:5px solid #444;border-radius:6px}}
.tk-printer{{position:absolute;left:975px;top:1036px;width:100px;height:72px;background:#2f3640;border-radius:10px}}
.tk-printer:before{{content:'';position:absolute;left:16px;top:-22px;width:68px;height:26px;background:#fff}}
.tk-etalase{{position:absolute;left:700px;top:1210px;width:360px;height:150px;background:rgba(190,225,235,.55);
  border:6px solid #c4ccd3;box-sizing:border-box}}
.tk-kursi{{position:absolute;top:1300px;width:80px;height:70px;border-radius:8px 8px 4px 4px}}
.tk-kardus{{position:absolute;background:#f8f8f8;border:3px solid #d9d9d9}}
</style>
<div class="tk-dalam">
  <div class="tk-dinding"></div>
  <div class="tk-plafon"></div>
  <div class="tk-balok" style="left:0;top:180px;width:1100px;transform:rotate(4deg)"></div>
  <div class="tk-balok" style="left:0;top:40px;width:1100px;transform:rotate(-3deg)"></div>
  <div class="tk-tali" style="left:200px;top:150px;height:170px"></div><div class="tk-neon" style="left:110px;top:318px;width:200px"></div>
  <div class="tk-tali" style="left:560px;top:150px;height:150px"></div><div class="tk-neon" style="left:470px;top:298px;width:200px"></div>
  <div class="tk-tali" style="left:900px;top:120px;height:160px"></div><div class="tk-neon" style="left:810px;top:278px;width:200px"></div>
  <div class="tk-lantai"></div>
  <div class="tk-spanduk">"ANNAFI" print<small>Sertifikat · Amplop · Kwitansi · Kop Surat<br>Buku · Yasin · Stiker · Foto Copy</small></div>
  <div class="tk-bendera">{bendera}</div>
  <div class="tk-tv"></div><div class="tk-kipas"></div>
  <div class="tk-tiang" style="left:520px"></div>
  {_gondola(20, 760, 230, 600, 5, 41)}
  {_gondola(270, 800, 230, 560, 5, 42)}
  <div class="tk-raklayan"><i style="left:20px;top:30px"></i><i style="left:110px;top:30px"></i><i style="left:300px;top:130px"></i>
    <i style="left:60px;top:230px;background:#c8a77a"></i><i style="left:210px;top:230px;background:#e9e2d4"></i></div>
  <div class="tk-kardus" style="left:440px;top:1240px;width:120px;height:120px"></div>
  <div class="tk-kardus" style="left:460px;top:1150px;width:90px;height:90px"></div>
  <div class="tk-meja"></div>
  <div class="tk-fc" style="left:620px;top:960px"></div>
  <div class="tk-pc"></div><div class="tk-printer"></div>
  <div class="tk-etalase"></div>
  <div class="tk-kursi" style="left:640px;background:#1fb5a8"></div>
  <div class="tk-kursi" style="left:980px;background:#e8a25a"></div>
</div>"""


# ---------------------------------------------------------------- depan toko
def _motor(x: int, y: int, warna: str, balik: bool = False) -> str:
    flip = "scaleX(-1)" if balik else "none"
    return f"""<svg style="position:absolute;left:{x}px;top:{y}px;width:260px;transform:{flip}" viewBox="0 0 260 180">
    <circle cx="52" cy="140" r="34" fill="#2b2b2b"/><circle cx="52" cy="140" r="14" fill="#9aa"/>
    <circle cx="208" cy="140" r="34" fill="#2b2b2b"/><circle cx="208" cy="140" r="14" fill="#9aa"/>
    <path d="M40 120 C60 70 120 70 150 92 L200 92 C222 92 232 110 226 126 L60 130Z" fill="{warna}"/>
    <path d="M96 78 L170 78 C180 78 180 92 170 92 L96 92Z" fill="#222"/>
    <path d="M200 90 L222 30 L236 30" stroke="#333" stroke-width="8" fill="none" stroke-linecap="round"/>
    </svg>"""


def latar_depan() -> str:
    """Eksterior. Elemen animasi: .tk-terang (lampu dalam menyala), .tk-flip (papan TUTUP -> BUKA)."""
    roster = "".join(f'<i style="left:{40 + i * 128}px"></i>' for i in range(8))
    return f"""<style>{CSS}
.tk-langit{{position:absolute;inset:0;background:linear-gradient(#bcdcef 0%,#e3eef3 45%,#fde5c4 80%)}}
.tk-atap{{position:absolute;left:-40px;right:-40px;top:250px;height:200px;background:{SENG};transform:skewY(-3deg)}}
.tk-rangka{{position:absolute;left:-20px;right:-20px;height:44px;background:#d7dbdf;border:5px solid #b7bec5;
  background-image:repeating-linear-gradient(60deg,#b7bec5 0 6px,transparent 6px 30px),repeating-linear-gradient(-60deg,#b7bec5 0 6px,transparent 6px 30px)}}
.tk-besi{{position:absolute;width:26px;background:#c9ced3;border-left:6px solid #e5e8eb;border-right:6px solid #a9b0b7}}
.tk-tembok{{position:absolute;left:0;right:0;top:450px;height:1070px;background:{BIRU_DINDING}}}
.tk-roster{{position:absolute;left:0;right:0;top:530px;height:60px}}
.tk-roster i{{position:absolute;width:104px;height:50px;background:#eef5f9;border:4px solid #8fbad4;border-radius:4px;
  background-image:radial-gradient(ellipse 34px 14px at 50% 50%,transparent 60%,#8fbad4 64% 78%,transparent 82%)}}
.tk-kaca{{position:absolute;left:50px;width:700px;top:640px;height:880px;overflow:hidden;background:#d5e6ee}}
.tk-intip{{position:absolute;left:-40px;top:-200px;width:1080px;height:1920px;transform:scale(.8);transform-origin:40% 30%}}
.tk-gelap{{position:absolute;inset:0;background:rgba(15,25,40,.6)}}
.tk-kilap{{position:absolute;inset:0;background:linear-gradient(115deg,rgba(255,255,255,0) 28%,rgba(255,255,255,.4) 36%,rgba(255,255,255,0) 44%,
  rgba(255,255,255,0) 62%,rgba(255,255,255,.25) 68%,rgba(255,255,255,0) 74%)}}
.tk-bingkai{{position:absolute;inset:0;border:14px solid #fff;
  background:linear-gradient(#fff,#fff) 0 190px/100% 14px no-repeat}}
.tk-mullion{{position:absolute;top:0;bottom:0;width:14px;background:#fff}}
.tk-pintu{{position:absolute;left:230px;width:250px;top:204px;bottom:0;border:12px solid #f4f4f4;box-shadow:inset 0 0 0 3px #ddd}}
.tk-gagang{{position:absolute;top:290px;width:10px;height:120px;background:#c9ced3;border-radius:5px}}
.tk-cctv{{position:absolute;left:40px;top:240px;width:110px;height:130px;background:#fff;border:3px solid #c0392b;
  font:700 15px Poppins,sans-serif;color:#c0392b;text-align:center;padding-top:10px;line-height:1.35;box-sizing:border-box}}
.tk-papanpintu{{position:absolute;left:295px;top:400px;width:120px;height:56px;perspective:600px}}
.tk-papanpintu .tk-flip{{position:absolute;inset:0;transform-style:preserve-3d}}
.tk-papanpintu .tk-flip div{{position:absolute;inset:0;border-radius:8px;font:700 26px Poppins,sans-serif;color:#fff;text-align:center;line-height:56px;
  backface-visibility:hidden}}
.tk-tutup{{background:#c0392b}}.tk-buka{{background:#27ae60;transform:rotateY(180deg)}}
.tk-spanduk2{{position:absolute;left:775px;top:650px;width:290px;height:330px;background:#fff;border:6px solid #2a9fd6;border-radius:6px;overflow:hidden}}
.tk-spanduk2 .logo{{position:absolute;left:12px;top:14px;width:66px;height:66px;border-radius:50%;background:#d62828;color:#fff;
  font:700 44px Poppins,sans-serif;text-align:center;line-height:66px}}
.tk-spanduk2 b{{position:absolute;left:86px;top:14px;font:700 40px Poppins,sans-serif;color:#1c6ea4;line-height:1}}
.tk-spanduk2 em{{position:absolute;left:90px;top:56px;font:italic 400 24px Poppins,sans-serif;color:#d62828}}
.tk-spanduk2 .ikon{{position:absolute;left:12px;right:12px;top:100px;height:50px;
  background:repeating-linear-gradient(90deg,#ffd23f 0 40px,#fff 40px 50px,#2a9fd6 50px 90px,#fff 90px 100px)}}
.tk-spanduk2 small{{position:absolute;left:12px;right:12px;top:164px;font:700 20px Poppins,sans-serif;color:#1E3A6B;line-height:1.45}}
.tk-teras{{position:absolute;left:0;right:0;top:1520px;height:70px;background:#e8dcc6;border-top:6px solid #f4ecdd;
  box-shadow:0 12px 0 #cdbf9f}}
.tk-parkir{{position:absolute;left:0;right:0;top:1602px;bottom:0;background:#bdb8ad}}
</style>
<div class="tk-langit"></div>
<div class="tk-tembok"></div>
<div class="tk-roster">{roster}</div>
<div class="tk-kaca">
  <div class="tk-intip">{latar_dalam(1.0)}</div>
  <div class="tk-gelap tk-terang"></div>
  <div class="tk-kilap"></div>
  <div class="tk-bingkai"></div>
  <div class="tk-mullion" style="left:230px"></div><div class="tk-mullion" style="left:480px"></div>
  <div class="tk-pintu"><div class="tk-gagang" style="left:96px"></div><div class="tk-gagang" style="left:118px"></div></div>
  <div class="tk-cctv">PERHATIAN!<br>AREA INI<br>DIAWASI<br>CCTV 24 JAM</div>
  <div class="tk-papanpintu"><div class="tk-flip"><div class="tk-tutup">TUTUP</div><div class="tk-buka">BUKA</div></div></div>
</div>
<div class="tk-spanduk2"><div class="logo">A</div><b>"ANNAFI"</b><em>print</em><div class="ikon"></div>
  <small>SERTIFIKAT · AMPLOP<br>KWITANSI · KOP SURAT<br>BUKU · YASIN · STIKER<br>FOTO COPY</small></div>
<div class="tk-atap"></div>
<div class="tk-rangka" style="top:420px;transform:skewY(-3deg)"></div>
<div class="tk-besi" style="left:14px;top:440px;height:1300px"></div>
<div class="tk-besi" style="left:752px;top:420px;height:1320px"></div>
<div class="tk-teras"></div><div class="tk-parkir"></div>
"""


# ---------------------------------------------------------------- close-up bawah pintu
def latar_pintu_bawah() -> str:
    """Close-up bawah pintu kaca berbingkai putih + keset bermotif daun di depannya."""
    daun = []
    rng = random.Random(7)
    for i in range(16):
        c = rng.choice(["#e9a23b", "#c0392b", "#7f8c8d", "#e8d9b5", "#5d4037", "#3b7ea1"])
        daun.append(f'<i style="left:{40 + (i % 8) * 92}px;top:{30 + (i // 8) * 120 + rng.randint(-14, 14)}px;background:{c};'
                    f'transform:rotate({rng.randint(-60, 60)}deg)"></i>')
    return f"""<style>
.tk-kacab{{position:absolute;left:0;right:0;top:0;height:620px;overflow:hidden;background:#d5e6ee}}
.tk-kacab .tk-intip{{position:absolute;left:-120px;top:-560px;width:1080px;height:1920px;transform:scale(1.35);filter:blur(6px)}}
.tk-kacab:after{{content:'';position:absolute;inset:0;background:linear-gradient(115deg,rgba(255,255,255,0) 35%,rgba(255,255,255,.4) 45%,rgba(255,255,255,0) 55%)}}
.tk-relb{{position:absolute;left:0;right:0;top:620px;height:56px;background:#fff;box-shadow:inset 0 -6px #e1e1e1}}
.tk-terasb{{position:absolute;left:0;right:0;top:676px;bottom:0;background:
  linear-gradient(rgba(255,214,150,.2),rgba(255,214,150,0)),repeating-linear-gradient(90deg,#e8dcc6 0 214px,#d2c6b0 214px 218px),#e8dcc6}}
.tk-terasb:after{{content:'';position:absolute;inset:0;background:repeating-linear-gradient(#0000 0 214px,#d2c6b0 214px 218px)}}
.tk-keset{{position:absolute;left:110px;top:980px;width:860px;height:330px;background:#7d7f84;border-radius:22px;
  border:10px solid #66686d;overflow:hidden}}
.tk-keset i{{position:absolute;width:110px;height:58px;border-radius:0 60px 0 60px;opacity:.95}}
</style>
<div class="tk-kacab"><div class="tk-intip">{latar_dalam(1.0)}</div></div>
<div class="tk-relb"></div><div class="tk-terasb"></div>
<div class="tk-keset">{"".join(daun)}</div>"""


# ---------------------------------------------------------------- close-up lain
def latar_meja() -> str:
    """Close-up di meja layanan: toko kabur di belakang, meja kayu di bawah (untuk membaca surat/amplop)."""
    return f"""<style>
.tk-mejab{{position:absolute;inset:0;overflow:hidden}}
.tk-mejab .tk-intip{{position:absolute;left:-200px;top:-300px;width:1080px;height:1920px;transform:scale(1.5);filter:blur(14px) brightness(.9)}}
.tk-papan-meja{{position:absolute;left:-40px;right:-40px;top:1240px;bottom:-40px;background:
  repeating-linear-gradient(90deg,rgba(0,0,0,.05) 0 3px,transparent 3px 60px),linear-gradient(#c9a274,#a87d4f);
  border-top:26px solid #dcbc8f;box-shadow:0 -10px 30px rgba(0,0,0,.25)}}
.tk-cahaya{{position:absolute;inset:0;background:radial-gradient(circle at 50% 38%,rgba(255,236,190,.55),rgba(0,0,0,0) 60%)}}
</style>
<div class="tk-mejab"><div class="tk-intip">{latar_dalam(1.0)}</div><div class="tk-cahaya"></div><div class="tk-papan-meja"></div></div>"""


def latar_bawah_mesin() -> str:
    """Close-up sejajar lantai: bagian bawah mesin fotokopi, celah gelap, lantai keramik krem."""
    return """<style>
.tk-mesinb{position:absolute;left:-60px;right:-60px;top:0;height:1080px;background:linear-gradient(90deg,#e9e6dd,#f4f2ec 40%,#dcd8ce);
  border-bottom:30px solid #c9c4b8}
.tk-mesinb:before{content:'';position:absolute;left:140px;top:260px;width:520px;height:150px;background:#d9d5cb;border-radius:14px;
  box-shadow:inset 0 -12px #c4bfb3}
.tk-mesinb:after{content:'';position:absolute;left:760px;top:300px;width:220px;height:40px;background:#9aa4ad;border-radius:8px}
.tk-celah{position:absolute;left:-60px;right:-60px;top:1110px;height:110px;background:linear-gradient(#0b0b0d,#2a2a2e)}
.tk-roda{position:absolute;top:1150px;width:120px;height:120px;border-radius:50%;background:#2b2b2b;border:18px solid #444}
.tk-lantaib{position:absolute;left:0;right:0;top:1220px;bottom:0;background:
  linear-gradient(rgba(255,255,255,.3),rgba(255,255,255,0) 50%),repeating-linear-gradient(90deg,#e3d9c6 0 300px,#d2c6b0 300px 306px),#e3d9c6}
.tk-debu{position:absolute;left:0;right:0;top:1100px;height:260px;background:radial-gradient(ellipse at 50% 20%,rgba(255,240,200,.25),transparent 60%)}
</style>
<div class="tk-mesinb"></div><div class="tk-celah"></div>
<div class="tk-roda" style="left:60px"></div><div class="tk-roda" style="left:900px"></div>
<div class="tk-lantaib"></div><div class="tk-debu"></div>"""


def latar_polos(warna: str = "#14141c") -> str:
    return f'<div style="position:absolute;inset:0;background:radial-gradient(circle at 50% 40%,#2c2c3a,{warna})"></div>'
