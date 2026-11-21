"""Latar tetap Toko Annafi (mengikuti cerita/lingkungan_toko.md) - dipakai sama persis di semua episode.

- latar_depan(): fasad kaca + lampu biru, isi toko terlihat dari luar, pintu kaca dengan papan BUKA/TUTUP.
- latar_dalam(): interior padat; kiri-tengah rak ATK & display mainan; KANAN = satu area kasir + fotokopi + printer.
- latar_pintu_bawah(): close-up bagian bawah pintu kaca (untuk adegan amplop di lantai).
Semua berupa potongan HTML/CSS ukuran 1080x1920, kelas diawali 'tk-' agar tidak bentrok.
"""
import random

WARNA = ["#e4572e", "#2F6FD1", "#f3a712", "#4f9a55", "#8e5ea2", "#1E3A6B", "#e86a92", "#17a2b8", "#ffcf3f", "#ff7f50"]


def _isi_rak(lebar: int, rng: random.Random, jenis: str) -> str:
    """Satu baris rak penuh barang (buku, kotak, gantungan) - padat seperti toko ATK lokal."""
    out, x = [], 6
    while x < lebar - 20:
        w = rng.choice([14, 18, 22, 26, 34, 42]) if jenis == "buku" else rng.choice([30, 38, 46, 54])
        h = rng.randint(46, 78) if jenis == "buku" else rng.randint(34, 70)
        c = rng.choice(WARNA)
        rad = 3 if jenis == "buku" else 6
        out.append(f'<i style="left:{x}px;width:{w}px;height:{h}px;background:{c};border-radius:{rad}px"></i>')
        x += w + rng.randint(2, 6)
    return "".join(out)


def _rak(x: int, y: int, w: int, h: int, baris: int, seed: int, jenis="campur") -> str:
    rng = random.Random(seed)
    tinggi = h // baris
    isi = []
    for b in range(baris):
        j = jenis if jenis != "campur" else rng.choice(["buku", "kotak"])
        isi.append(f'<div class="tk-baris" style="top:{b * tinggi}px;height:{tinggi}px">{_isi_rak(w, rng, j)}</div>')
    return f'<div class="tk-rak" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">{"".join(isi)}</div>'


def _gantungan(x: int, y: int, w: int, seed: int) -> str:
    """Papan gantung di atas rak: tas sekolah & kemasan pulpen tergantung (bikin toko terasa penuh)."""
    rng = random.Random(seed)
    out, xx = [], 10
    while xx < w - 60:
        if rng.random() < .4:
            c = rng.choice(["#e4572e", "#2F6FD1", "#8e5ea2", "#e86a92", "#17a2b8"])
            out.append(f'<i style="left:{xx}px;top:-110px;width:70px;height:92px;background:{c};border-radius:18px 18px 10px 10px;'
                       f'box-shadow:inset 0 -26px rgba(0,0,0,.12)"></i>')
            xx += 80
        else:
            c = rng.choice(WARNA)
            out.append(f'<i style="left:{xx}px;top:-60px;width:34px;height:52px;background:#fff;border-top:10px solid {c};'
                       f'border-radius:3px"></i>')
            xx += 42
    return f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:0">{"".join(out)}</div>'.replace(
        '<i ', '<i class="tk-gantung" ')


def _mainan(x: int, y: int, w: int, seed: int) -> str:
    """Display mainan: balok susun, kotak kartu, blind box, squishy & slime."""
    rng = random.Random(seed)
    out = []
    for i in range(7):  # balok susun bertingkat
        c = rng.choice(WARNA)
        out.append(f'<i class="tk-balok" style="left:{10 + (i % 4) * 46}px;top:{120 - (i // 4) * 30}px;background:{c}"></i>')
    for i in range(4):  # blind box (kotak pastel bertanda ?)
        c = rng.choice(["#ffd1dc", "#c9f0ff", "#e6d9ff", "#fff1b8"])
        out.append(f'<b class="tk-blind" style="left:{w - 200 + i * 48}px;background:{c}">?</b>')
    for i in range(5):  # toples slime/squishy
        c = rng.choice(["#7ee0c3", "#ff9ecf", "#b39bff", "#ffd36e", "#8fd3ff"])
        out.append(f'<i class="tk-toples" style="left:{14 + i * 58}px;background:{c}"></i>')
    for i in range(4):  # kotak kartu permainan (merah, tanpa merek)
        out.append(f'<i class="tk-kartu" style="left:{w - 210 + i * 50}px"></i>')
    return f'<div class="tk-mainan" style="left:{x}px;top:{y}px;width:{w}px">{"".join(out)}</div>'


CSS = """
.tk-rak{position:absolute;background:#c9a57b;border:8px solid #a57e52;border-radius:6px}
.tk-baris{position:absolute;left:0;right:0;border-bottom:8px solid #a57e52;overflow:hidden}
.tk-baris i{position:absolute;bottom:0}
.tk-mainan{position:absolute;height:260px;background:#f3ece0;border:8px solid #d0b48c;border-radius:8px}
.tk-balok{position:absolute;width:42px;height:26px;border-radius:4px;box-shadow:inset 0 -4px rgba(0,0,0,.15)}
.tk-blind{position:absolute;top:96px;width:42px;height:50px;border-radius:6px;font:700 30px Poppins;color:#8e5ea2;text-align:center;line-height:50px}
.tk-toples{position:absolute;top:184px;width:48px;height:58px;border-radius:12px 12px 8px 8px;box-shadow:inset 0 8px rgba(255,255,255,.45)}
.tk-kartu{position:absolute;top:186px;width:40px;height:56px;border-radius:5px;background:#d62828;border:4px solid #fff}
.tk-gantung{position:absolute;display:block}
.tk-lampu{position:absolute;height:14px;border-radius:7px;background:#fffbe8;box-shadow:0 0 40px 14px rgba(255,248,210,.75)}
"""


def latar_dalam(terang: float = 1.0) -> str:
    """Interior toko (tampak depan). terang 0..1 untuk efek lampu menyala."""
    return f"""<style>{CSS}
.tk-dalam{{position:absolute;inset:0;background:#f4efe6;filter:brightness({0.55 + 0.45 * terang})}}
.tk-plafon{{position:absolute;left:0;right:0;top:0;height:230px;background:#ece6da}}
.tk-dinding{{position:absolute;left:0;right:0;top:230px;height:1170px;background:#f7f2e8}}
.tk-lantai{{position:absolute;left:0;right:0;top:1400px;bottom:0;background:
  repeating-linear-gradient(90deg,#ddd2bf 0 134px,#cfc2ab 134px 138px),#ddd2bf}}
.tk-lantai:after{{content:'';position:absolute;inset:0;background:repeating-linear-gradient(#0000 0 134px,#cfc2ab 134px 138px)}}
.tk-meja{{position:absolute;left:640px;width:440px;top:1080px;height:330px;background:#8d6748;border-radius:10px 0 0 10px;
  box-shadow:inset 0 22px #a47a58}}
.tk-fotokopi{{position:absolute;left:820px;top:760px;width:250px;height:330px;background:#e6e9ee;border:8px solid #a6aeba;border-radius:16px}}
.tk-fotokopi:before{{content:'';position:absolute;left:18px;right:18px;top:18px;height:46px;background:#b9c1cc;border-radius:6px}}
.tk-fotokopi:after{{content:'';position:absolute;left:30px;top:120px;width:120px;height:26px;background:#34495e;border-radius:4px;
  box-shadow:0 150px 0 -4px #fff}}
.tk-printer{{position:absolute;left:670px;top:950px;width:150px;height:110px;background:#2f3640;border-radius:12px}}
.tk-printer:before{{content:'';position:absolute;left:24px;top:-26px;width:102px;height:34px;background:#fff;border-radius:3px}}
.tk-kasir{{position:absolute;left:700px;top:1000px;width:0}}
.tk-monitor{{position:absolute;left:690px;top:880px;width:120px;height:86px;background:#222;border:6px solid #444;border-radius:8px}}
.tk-kertas{{position:absolute;left:880px;top:1052px;width:110px;height:34px;background:#fff;border-radius:3px;
  box-shadow:0 -8px #f3f3f3,0 -16px #fff}}
.tk-papan{{position:absolute;left:650px;top:300px;width:400px;height:80px;background:#2F6FD1;border-radius:12px;color:#fff;
  font:700 28px Poppins;text-align:center;line-height:80px;letter-spacing:1px;white-space:nowrap}}
</style>
<div class="tk-dalam">
  <div class="tk-plafon"></div><div class="tk-dinding"></div><div class="tk-lantai"></div>
  <div class="tk-lampu" style="left:120px;top:110px;width:260px"></div>
  <div class="tk-lampu" style="left:450px;top:110px;width:260px"></div>
  <div class="tk-lampu" style="left:780px;top:110px;width:260px"></div>
  {_gantungan(30, 240, 590, 31)}
  {_rak(30, 300, 290, 640, 5, 11, "buku")}
  {_rak(340, 300, 280, 640, 5, 12, "campur")}
  {_mainan(30, 980, 590, 21)}
  {_rak(30, 1260, 590, 140, 1, 13, "kotak")}
  <div class="tk-papan">FOTOKOPI · PRINT · KASIR</div>
  <div class="tk-fotokopi"></div><div class="tk-printer"></div><div class="tk-monitor"></div>
  <div class="tk-meja"></div><div class="tk-kertas"></div>
</div>"""


def latar_depan() -> str:
    """Eksterior: fasad kaca berlampu biru, isi toko kelihatan dari luar. Elemen animasi:
    .tk-terang (lampu dalam menyala), .tk-buka/.tk-tutup (papan pintu berbalik)."""
    return f"""<style>{CSS}
.tk-langit{{position:absolute;inset:0;background:linear-gradient(#8fc6ea 0%,#cfe6f2 40%,#ffe0b5 72%,#ffd19a 100%)}}
.tk-gedung{{position:absolute;left:40px;width:1000px;top:520px;height:1030px;background:#f2ede4;border-radius:6px}}
.tk-nama{{position:absolute;left:70px;width:940px;top:560px;height:150px;background:#fff;border:10px solid #1E3A6B;border-radius:14px;
  text-align:center;padding-top:10px}}
.tk-nama b{{display:block;font:700 70px Poppins;color:#1E3A6B;letter-spacing:6px;line-height:1.1}}
.tk-nama span{{font:400 28px Poppins;color:#2F6FD1;letter-spacing:4px}}
.tk-led{{position:absolute;left:70px;width:940px;top:730px;height:14px;border-radius:7px;background:#3aa0ff;
  box-shadow:0 0 30px 10px rgba(58,160,255,.75),0 0 80px 20px rgba(58,160,255,.35)}}
.tk-kaca{{position:absolute;left:70px;width:940px;top:760px;height:790px;overflow:hidden;background:#cfe3ec;border:12px solid #9aa3ad}}
.tk-intip{{position:absolute;left:-40px;top:-300px;width:1080px;height:1920px;transform:scale(.88);transform-origin:50% 30%}}
.tk-gelap{{position:absolute;inset:0;background:rgba(20,30,50,.55)}}
.tk-kilap{{position:absolute;inset:0;background:linear-gradient(115deg,rgba(255,255,255,0) 30%,rgba(255,255,255,.35) 38%,
  rgba(255,255,255,0) 46%,rgba(255,255,255,0) 60%,rgba(255,255,255,.22) 66%,rgba(255,255,255,0) 72%)}}
.tk-tiang{{position:absolute;top:0;bottom:0;width:12px;background:#9aa3ad}}
.tk-pintu{{position:absolute;left:300px;width:330px;top:0;bottom:0;border:10px solid #8d96a1}}
.tk-gagang{{position:absolute;top:330px;width:12px;height:150px;background:#c0c7cf;border-radius:6px}}
.tk-papanpintu{{position:absolute;left:390px;top:150px;width:150px;height:70px;perspective:600px}}
.tk-papanpintu div{{position:absolute;inset:0;border-radius:10px;font:700 34px Poppins;color:#fff;text-align:center;line-height:70px;
  backface-visibility:hidden}}
.tk-tutup{{background:#c0392b}}.tk-buka{{background:#27ae60;transform:rotateY(180deg)}}
.tk-trotoar{{position:absolute;left:0;right:0;top:1550px;height:140px;background:#d8ccb4}}
.tk-jalan{{position:absolute;left:0;right:0;top:1690px;bottom:0;background:#6d6f75}}
.tk-marka{{position:absolute;top:1800px;height:14px;width:140px;background:#f1f1f1;border-radius:6px}}
</style>
<div class="tk-langit"></div>
<div class="tk-gedung"></div>
<div class="tk-nama"><b>ANNAFI</b><span>ATK · FOTOKOPI · PRINT · MAINAN</span></div>
<div class="tk-led"></div>
<div class="tk-kaca">
  <div class="tk-intip">{latar_dalam(1.0)}</div>
  <div class="tk-gelap tk-terang"></div>
  <div class="tk-kilap"></div>
  <div class="tk-tiang" style="left:290px"></div><div class="tk-tiang" style="left:630px"></div>
  <div class="tk-pintu"><div class="tk-gagang" style="left:268px"></div><div class="tk-gagang" style="left:290px"></div></div>
  <div class="tk-papanpintu"><div class="tk-flip" style="position:absolute;inset:0;transform-style:preserve-3d">
    <div class="tk-tutup">TUTUP</div><div class="tk-buka">BUKA</div></div></div>
</div>
<div class="tk-trotoar"></div><div class="tk-jalan"></div>
<div class="tk-marka" style="left:80px"></div><div class="tk-marka" style="left:470px"></div><div class="tk-marka" style="left:860px"></div>"""


def latar_pintu_bawah() -> str:
    """Close-up bawah pintu kaca: kaca (isi toko samar) + rangka aluminium + lantai teras."""
    return f"""<style>
.tk-kacab{{position:absolute;left:0;right:0;top:0;height:650px;overflow:hidden;background:#cfe3ec}}
.tk-kacab .tk-intip{{position:absolute;left:-60px;top:-420px;width:1080px;height:1920px;transform:scale(1.4);filter:blur(5px)}}
.tk-kacab:after{{content:'';position:absolute;inset:0;background:linear-gradient(115deg,rgba(255,255,255,0) 35%,rgba(255,255,255,.35) 45%,rgba(255,255,255,0) 55%)}}
.tk-rel{{position:absolute;left:0;right:0;top:650px;height:40px;background:linear-gradient(#b5bdc6,#8d96a1)}}
.tk-teras{{position:absolute;left:0;right:0;top:690px;bottom:0;background:
  linear-gradient(rgba(255,214,150,.25),rgba(255,214,150,0)),repeating-linear-gradient(90deg,#e7dcc6 0 178px,#cdbf9f 178px 184px),#e7dcc6}}
.tk-teras:after{{content:'';position:absolute;inset:0;background:repeating-linear-gradient(#0000 0 178px,#cdbf9f 178px 184px)}}
.tk-ledb{{position:absolute;left:0;right:0;top:640px;height:8px;background:#3aa0ff;box-shadow:0 0 24px 8px rgba(58,160,255,.6)}}
</style>
<div class="tk-kacab"><div class="tk-intip">{latar_dalam(1.0)}</div></div>
<div class="tk-ledb"></div><div class="tk-rel"></div><div class="tk-teras"></div>"""
