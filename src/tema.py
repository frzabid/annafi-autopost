"""Pustaka tema carousel feed: warna, gaya panel sampul, ilustrasi, dan kalimat penutup per momen.

Semua ilustrasi digambar sendiri (SVG datar dengan garis tinta), jadi aman dipakai tanpa masalah hak cipta.
Tema dipilih dari kolom `tema` di sheet; kalau kosong, ditebak dari judul/isi postingan (lihat `pilih`).
Menambah tema baru = menambah satu entri di TEMA.
"""
import math, re

INK = "#1d2a44"


def _isi(svg):
    """Isi dalam <svg>…</svg> supaya bisa digabung ke ilustrasi lain."""
    return re.sub(r"^<svg[^>]*>|</svg>$", "", svg)


# ------------------------------------------------------------------ ilustrasi kecil (viewBox 0 0 100 100)
def bintang(c="#f2b33d"):
    return f'<svg viewBox="0 0 24 24"><path d="M12 1l2.6 7.4L22 11l-7.4 2.6L12 21l-2.6-7.4L2 11l7.4-2.6z" fill="{c}"/></svg>'


def hati(c="#e5483d"):
    return (f'<svg viewBox="0 0 100 100"><path d="M50 88C18 64 6 46 12 28c6-16 28-20 38-4 10-16 32-12 38 4 6 18-6 36-38 60z" '
            f'fill="{c}"/></svg>')


def apel():
    return ('<svg viewBox="0 0 100 100"><path d="M50 30c-8-8-30-8-34 14-4 22 12 46 24 46 4 0 6-2 10-2s6 2 10 2c12 0 28-24 '
            '24-46-4-22-26-22-34-14z" fill="#e5483d"/><path d="M30 40c-4 6-4 16 0 22" stroke="#fff" stroke-width="5" '
            'stroke-linecap="round" fill="none" opacity=".5"/><path d="M50 30c0-8 2-14 6-20" stroke="#6b3d1e" '
            'stroke-width="5" stroke-linecap="round" fill="none"/><path d="M56 16c10-8 22-4 24 2-10 8-20 6-24-2z" fill="#4caf50"/></svg>')


def buku_tumpuk(a="#1565d8", b="#f2b33d", c="#e5483d"):
    return (f'<svg viewBox="0 0 150 100"><rect x="10" y="66" width="120" height="22" rx="4" fill="{a}"/>'
            f'<rect x="18" y="72" width="104" height="4" fill="#fff" opacity=".6"/><rect x="20" y="44" width="110" height="22" rx="4" fill="{b}"/>'
            f'<rect x="28" y="50" width="94" height="4" fill="#fff" opacity=".6"/><rect x="4" y="22" width="114" height="22" rx="4" fill="{c}"/>'
            '<rect x="12" y="28" width="98" height="4" fill="#fff" opacity=".6"/></svg>')


def pensil(badan="#f2b33d"):
    return (f'<svg viewBox="0 0 150 30"><rect x="20" y="6" width="100" height="18" fill="{badan}"/>'
            '<rect x="20" y="6" width="100" height="6" fill="#fff" opacity=".3"/><rect x="6" y="6" width="16" height="18" rx="3" fill="#f39aa6"/>'
            '<rect x="18" y="6" width="6" height="18" fill="#b8b8b8"/><path d="M120 6l24 9-24 9z" fill="#f5d7a8"/>'
            '<path d="M136 12l8 3-8 3z" fill="#333"/></svg>')


def bulan_sabit(c="#f4c542"):
    return (f'<svg viewBox="0 0 100 100"><path d="M62 10a42 42 0 1 0 28 66A34 34 0 1 1 62 10z" fill="{c}"/>'
            f'<path d="M78 28l3 8 8 1-6 5 2 8-7-4-7 4 2-8-6-5 8-1z" fill="{c}"/></svg>')


def lentera(badan="#d4a73a", kaca="#ffe9a8"):
    return (f'<svg viewBox="0 0 60 120"><path d="M30 0v14" stroke="{badan}" stroke-width="3"/>'
            f'<path d="M18 22h24l-4-8H22z" fill="{badan}"/><path d="M14 22h32l6 40-8 26H16L8 62z" fill="{kaca}" stroke="{badan}" stroke-width="4" stroke-linejoin="round"/>'
            f'<path d="M30 22v66M14 50h32" stroke="{badan}" stroke-width="3"/><path d="M16 88h28l-6 10H22z" fill="{badan}"/>'
            f'<circle cx="30" cy="56" r="7" fill="#ffb300" opacity=".85"/><path d="M30 98v12" stroke="{badan}" stroke-width="3"/>'
            f'<circle cx="30" cy="114" r="4" fill="{badan}"/></svg>')


def masjid(c="#0c4636", aksen="#d4a73a"):
    return (f'<svg viewBox="0 0 300 140"><rect x="24" y="30" width="16" height="110" fill="{c}"/><path d="M24 30l8-22 8 22z" fill="{c}"/>'
            f'<rect x="260" y="30" width="16" height="110" fill="{c}"/><path d="M260 30l8-22 8 22z" fill="{c}"/>'
            f'<path d="M80 140V86c0-30 30-50 70-62 40 12 70 32 70 62v54z" fill="{c}"/><path d="M150 24v-16" stroke="{aksen}" stroke-width="4"/>'
            f'<circle cx="150" cy="6" r="5" fill="{aksen}"/><rect x="50" y="96" width="200" height="44" fill="{c}"/>'
            f'<path d="M136 140v-26a14 14 0 0 1 28 0v26z" fill="{aksen}" opacity=".9"/>'
            f'<path d="M92 120v-14a8 8 0 0 1 16 0v14zM192 120v-14a8 8 0 0 1 16 0v14z" fill="{aksen}" opacity=".7"/></svg>')


def ketupat(a="#3c9a5f", b="#c9e265"):
    return (f'<svg viewBox="0 0 100 120"><path d="M50 30l34 34-34 34-34-34z" fill="{a}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
            f'<path d="M33 47l34 34M50 30l-17 17M67 47L33 81M50 98l17-17" stroke="{b}" stroke-width="5"/>'
            f'<path d="M50 30c0-12 6-20 14-26M50 30c-4-10-12-16-22-18" stroke="{a}" stroke-width="4" fill="none" stroke-linecap="round"/></svg>')


def bendera():
    return ('<svg viewBox="0 0 120 120"><path d="M14 6v110" stroke="#6b3d1e" stroke-width="6" stroke-linecap="round"/>'
            '<path d="M17 10c30-8 50 8 90 0v26c-40 8-60-8-90 0z" fill="#e53935"/><path d="M17 36c30-8 50 8 90 0v26c-40 8-60-8-90 0z" fill="#fff" '
            f'stroke="{INK}" stroke-width="2"/><circle cx="14" cy="6" r="6" fill="#f2b33d"/></svg>')


def kembang_api(c1="#f2b33d", c2="#e5483d"):
    garis = "".join(f'<path d="M{50 + 14 * math.cos(a):.1f} {50 + 14 * math.sin(a):.1f}L{50 + 44 * math.cos(a):.1f} '
                    f'{50 + 44 * math.sin(a):.1f}"/>' for a in [i * math.pi / 4 for i in range(8)])
    return (f'<svg viewBox="0 0 100 100"><g stroke="{c1}" stroke-width="5" stroke-linecap="round">{garis}</g>'
            f'<circle cx="50" cy="50" r="9" fill="{c2}"/></svg>')


# ------------------------------------------------------------------ ilustrasi besar untuk slide poin (viewBox 0 0 320 260)
def _svg(isi):
    return f'<svg viewBox="0 0 320 260">{isi}</svg>'


ART = {
    "buku_lampu": _svg(
        f'<path d="M40 200c40-14 80-14 120 0v-110c-40-14-80-14-120 0z" fill="#fff" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="M280 200c-40-14-80-14-120 0v-110c40-14 80-14 120 0z" fill="#fff" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
        '<g stroke="#9fb4d6" stroke-width="4" stroke-linecap="round"><path d="M60 120h80M60 140h80M60 160h60M180 120h80M180 140h80M180 160h60"/></g>'
        f'<circle cx="160" cy="50" r="30" fill="#ffd77a" stroke="{INK}" stroke-width="5"/><rect x="148" y="78" width="24" height="16" rx="4" fill="{INK}"/>'
        '<g stroke="#e8792b" stroke-width="6" stroke-linecap="round"><path d="M112 30l-12-8M208 30l12-8M108 64l-14 4M212 64l14 4"/></g>'),
    "amplop_bunga": _svg(
        f'<rect x="50" y="90" width="200" height="140" rx="10" fill="#fff" stroke="{INK}" stroke-width="5"/>'
        f'<path d="M50 100l100 70 100-70" fill="none" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
        f'<rect x="80" y="30" width="140" height="110" rx="8" fill="#fff7e8" stroke="{INK}" stroke-width="5"/>'
        '<path d="M150 112c-26-18-34-30-26-42 6-8 18-6 26 4 8-10 20-12 26-4 8 12 0 24-26 42z" fill="#e5483d"/>'
        '<g transform="translate(272 150)"><path d="M0 0v90" stroke="#4caf50" stroke-width="6"/>'
        '<path d="M0 60c-16-4-24-14-24-24 12 0 22 8 24 24z" fill="#4caf50"/><g fill="#f2b33d"><circle cx="0" cy="-16" r="13"/>'
        '<circle cx="15" cy="-5" r="13"/><circle cx="9" cy="13" r="13"/><circle cx="-9" cy="13" r="13"/><circle cx="-15" cy="-5" r="13"/></g>'
        '<circle r="9" fill="#e8792b"/></g>'),
    "kartu_alat": _svg(
        f'<g transform="rotate(-8 140 150)"><rect x="60" y="70" width="170" height="150" rx="10" fill="#fff" stroke="{INK}" stroke-width="5"/>'
        '<path d="M100 120h90M100 145h90M100 170h60" stroke="#9fb4d6" stroke-width="6" stroke-linecap="round"/>'
        '<path d="M145 210c-14-10-18-16-14-22 3-4 9-3 14 2 5-5 11-6 14-2 4 6 0 12-14 22z" fill="#e5483d"/></g>'
        f'<rect x="236" y="130" width="62" height="96" rx="8" fill="#f2b33d" stroke="{INK}" stroke-width="5"/>'
        '<g stroke-width="10" stroke-linecap="round"><path d="M250 128l-8-60" stroke="#e5483d"/><path d="M266 128v-70" stroke="#1565d8"/>'
        '<path d="M282 128l10-56" stroke="#4caf50"/></g>'
        f'<g transform="rotate(10 120 240)"><rect x="40" y="226" width="190" height="26" rx="4" fill="#ffd77a" stroke="{INK}" stroke-width="4"/>'
        f'<g stroke="{INK}" stroke-width="3"><path d="M60 226v10M80 226v14M100 226v10M120 226v14M140 226v10M160 226v14M180 226v10M200 226v14"/></g></g>'),
    "kertas_cek": _svg(
        f'<g transform="rotate(-5 150 140)"><rect x="70" y="20" width="170" height="220" rx="10" fill="#fff" stroke="{INK}" stroke-width="5"/>'
        '<path d="M96 20v220" stroke="#f28b82" stroke-width="3"/>'
        '<g stroke="#9fb4d6" stroke-width="4" stroke-linecap="round"><path d="M110 70h100M110 110h100M110 150h100M110 190h70"/></g>'
        '<path d="M190 60l12 12 24-26M190 100l12 12 24-26M190 140l12 12 24-26" stroke="#2e9d57" stroke-width="7" fill="none" '
        'stroke-linecap="round" stroke-linejoin="round"/></g>'
        f'<g transform="rotate(-40 270 200)"><rect x="200" y="190" width="120" height="20" fill="#f2b33d" stroke="{INK}" stroke-width="4"/>'
        f'<path d="M320 190l26 10-26 10z" fill="#f5d7a8" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/></g>'),
    "jam_weker": _svg(
        f'<circle cx="160" cy="140" r="90" fill="#fff" stroke="{INK}" stroke-width="6"/><circle cx="160" cy="140" r="74" fill="#eaf2ff"/>'
        f'<path d="M160 140V88M160 140l38 22" stroke="{INK}" stroke-width="8" stroke-linecap="round"/><circle cx="160" cy="140" r="8" fill="#e5483d"/>'
        f'<path d="M86 66a30 30 0 0 1 40-24M234 66a30 30 0 0 0-40-24" stroke="{INK}" stroke-width="10" stroke-linecap="round" fill="none"/>'
        f'<path d="M108 222l-16 22M212 222l16 22" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>'
        '<g stroke="#e8792b" stroke-width="5" stroke-linecap="round"><path d="M46 120h-20M50 160l-18 8M274 120h20M270 160l18 8"/></g>'),
    "tas_sekolah": _svg(
        f'<path d="M120 60a40 40 0 0 1 80 0" stroke="{INK}" stroke-width="8" fill="none"/>'
        f'<rect x="90" y="56" width="140" height="180" rx="30" fill="#1565d8" stroke="{INK}" stroke-width="6"/>'
        f'<rect x="110" y="150" width="100" height="70" rx="14" fill="#5b9bff" stroke="{INK}" stroke-width="5"/>'
        f'<path d="M110 172h100" stroke="{INK}" stroke-width="4"/><rect x="150" y="164" width="20" height="14" rx="3" fill="#f2b33d"/>'
        f'<path d="M90 110h140" stroke="{INK}" stroke-width="5"/>'
        '<g stroke-width="12" stroke-linecap="round"><path d="M260 236l20-120" stroke="#e5483d"/><path d="M286 236l6-110" stroke="#f2b33d"/>'
        '<path d="M60 236l-14-110" stroke="#4caf50"/></g>'),
    "quran_rehal": _svg(
        f'<path d="M60 220l100-60 100 60" stroke="#8d5a2c" stroke-width="12" stroke-linecap="round" fill="none"/>'
        f'<path d="M70 230l90-40 90 40" stroke="#b97a41" stroke-width="10" stroke-linecap="round" fill="none"/>'
        f'<path d="M50 150c40-20 80-20 110 0v-90c-30-20-70-20-110 0z" fill="#0f5a46" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="M270 150c-40-20-80-20-110 0v-90c30-20 70-20 110 0z" fill="#0f5a46" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
        '<path d="M70 80c25-10 55-10 80 0M70 105c25-10 55-10 80 0M170 80c25-10 55-10 80 0M170 105c25-10 55-10 80 0" '
        'stroke="#d4a73a" stroke-width="5" fill="none" stroke-linecap="round"/>'
        '<g fill="#d4a73a"><circle cx="160" cy="34" r="6"/><circle cx="130" cy="26" r="4"/><circle cx="190" cy="26" r="4"/></g>'),
    "tasbih_kurma": _svg(
        '<g fill="#7a4a24" stroke="#1d2a44" stroke-width="3">'
        + "".join(f'<circle cx="{160 + 80 * math.cos(i / 22 * 6.283):.1f}" cy="{120 + 70 * math.sin(i / 22 * 6.283):.1f}" r="9"/>'
                  for i in range(22)) +
        '</g><path d="M160 190v40" stroke="#7a4a24" stroke-width="6"/><circle cx="160" cy="236" r="12" fill="#d4a73a"/>'
        f'<ellipse cx="80" cy="220" rx="44" ry="18" fill="#fff" stroke="{INK}" stroke-width="5"/>'
        '<g fill="#6b3416"><ellipse cx="66" cy="210" rx="12" ry="7"/><ellipse cx="90" cy="212" rx="12" ry="7"/><ellipse cx="78" cy="202" rx="12" ry="7"/></g>'),
    "ketupat_masjid": _svg(
        f'<g transform="translate(40 30) scale(1.5)">{_isi(ketupat())}</g>'
        f'<g transform="translate(170 50) scale(1.1)">{_isi(ketupat("#2e7d4f", "#f2d06b"))}</g>'
        '<path d="M60 240h220" stroke="#0c4636" stroke-width="6" stroke-linecap="round"/>'),
    "bendera_besar": _svg(
        '<path d="M70 20v230" stroke="#6b3d1e" stroke-width="10" stroke-linecap="round"/><circle cx="70" cy="18" r="10" fill="#f2b33d"/>'
        '<path d="M76 30c60-16 110 16 190 0v60c-80 16-130-16-190 0z" fill="#e53935"/>'
        f'<path d="M76 90c60-16 110 16 190 0v60c-80 16-130-16-190 0z" fill="#fff" stroke="{INK}" stroke-width="3"/>'
        + "".join(f'<g transform="translate({x} {y})">{_isi(bintang("#f2b33d"))}</g>'
                  for x, y in [(240, 190), (200, 220), (276, 220)])),
    "lentera_bulan": _svg(
        f'<g transform="translate(60 10) scale(1.4)">{_isi(lentera())}</g>'
        f'<g transform="translate(170 40) scale(1.3)">{_isi(bulan_sabit())}</g>'
        + "".join(f'<g transform="translate({x} {y}) scale(.9)">{_isi(bintang("#f4c542"))}</g>'
                  for x, y in [(260, 200), (150, 210), (290, 30)])),
}


# ------------------------------------------------------------------ daftar tema
TEMA = {
    "umum": dict(nama="Umum", kata=[],
                 bg="#fff7e8", dot="#f1dcb4", primary="#1565d8", accent="#e8792b", soft=["#ffe2b0", "#d5e6ff", "#ffd6d1", "#dff3e4"],
                 panel="panel-biru", hand="#ffd77a", pill="TIPS ANNAFI",
                 sampul=[("bintang", 96, 186, 70, 0), ("buku", 40, 800, 300, 0), ("pensil", 760, 830, 300, -32), ("bintang2", 930, 1000, 54, 0)],
                 art=["buku_lampu", "kartu_alat", "kertas_cek", "amplop_bunga"],
                 tutup=("Semoga bermanfaat!", "Simpan postingan ini dan bagikan ke teman yang membutuhkan.")),
    "guru": dict(nama="Hari Guru", kata=["guru"],
                 bg="#fff7e8", dot="#f1dcb4", primary="#1565d8", accent="#e8792b", soft=["#ffe2b0", "#ffd6d1", "#d5e6ff", "#dff3e4"],
                 panel="panel-papan", hand="#ffe9a8", pill="HARI GURU NASIONAL", bawah="Terima kasih, Guru!",
                 sampul=[("apel", 800, 170, 190, 0), ("buku", 40, 800, 300, 0), ("pensil", 760, 830, 300, -32),
                         ("bintang", 96, 186, 70, 0), ("bintang2", 930, 1000, 54, 0)],
                 art=["buku_lampu", "amplop_bunga", "kartu_alat", "kertas_cek"],
                 tutup=("Siapa guru favoritmu?", "Tag beliau di kolom komentar dan sampaikan terima kasihmu hari ini.")),
    "maulid": dict(nama="Maulid Nabi", kata=["maulid", "nabi muhammad", "rasulullah", "shalawat", "sholawat"],
                   bg="#fbf6e9", dot="#ead9ad", primary="#0f5a46", accent="#c9962b", soft=["#e3efe2", "#f6e6bd", "#e3efe2", "#f6e6bd"],
                   panel="panel-kubah", hand="#f4d27a", pill="MAULID NABI MUHAMMAD SAW", bawah="Allahumma shalli 'ala Muhammad",
                   sampul=[("lentera", 120, 150, 110, 0), ("lentera", 860, 150, 110, 0), ("bulan", 800, 300, 120, 0),
                           ("masjid", 300, 720, 480, 0), ("bintang_emas", 150, 1000, 60, 0), ("bintang_emas", 900, 1010, 50, 0)],
                   art=["quran_rehal", "tasbih_kurma", "lentera_bulan", "buku_lampu"],
                   tutup=("Perbanyak shalawat", "Semoga kita senantiasa meneladani akhlak Rasulullah SAW dalam keseharian.")),
    "ramadan": dict(nama="Ramadan", kata=["ramadan", "ramadhan", "puasa", "sahur", "buka puasa", "ngabuburit", "tarawih"],
                    bg="#f4f1ff", dot="#d9d2f2", primary="#1b2a5a", accent="#d4a73a", soft=["#e1e6fb", "#f6e6bd", "#e1e6fb", "#f6e6bd"],
                    panel="panel-malam", hand="#f4d27a", pill="RAMADAN", bawah="Marhaban ya Ramadhan",
                    sampul=[("lentera", 110, 150, 110, 0), ("lentera", 870, 150, 110, 0), ("bulan", 480, 100, 120, 0),
                            ("masjid", 300, 720, 480, 0), ("bintang_emas", 150, 1000, 60, 0), ("bintang_emas", 900, 1010, 50, 0)],
                    art=["lentera_bulan", "quran_rehal", "jam_weker", "tasbih_kurma"],
                    tutup=("Selamat menunaikan ibadah puasa", "Semoga Ramadan kali ini penuh berkah untuk kita semua.")),
    "idulfitri": dict(nama="Idul Fitri", kata=["idul fitri", "idulfitri", "lebaran", "syawal", "mudik", "halal bihalal"],
                      bg="#f3faf3", dot="#cfe8d3", primary="#1f7a4d", accent="#d4a73a", soft=["#dff3e4", "#f6e6bd", "#dff3e4", "#f6e6bd"],
                      panel="panel-hijau", hand="#f4d27a", pill="IDUL FITRI", bawah="Mohon maaf lahir dan batin",
                      sampul=[("ketupat", 110, 160, 130, -10), ("ketupat", 860, 160, 120, 12), ("masjid", 300, 720, 480, 0),
                              ("bintang_emas", 150, 1000, 60, 0), ("bintang_emas", 900, 1010, 50, 0)],
                      art=["ketupat_masjid", "amplop_bunga", "tasbih_kurma", "lentera_bulan"],
                      tutup=("Mohon maaf lahir & batin", "Selamat Hari Raya Idul Fitri dari keluarga Annafi ATK.")),
    "kemerdekaan": dict(nama="17 Agustus", kata=["kemerdekaan", "17 agustus", "hut ri", "dirgahayu", "merdeka", "proklamasi", "pahlawan"],
                        bg="#fff6f5", dot="#f4d0cc", primary="#c62828", accent="#1565d8", soft=["#ffd6d1", "#eaf2ff", "#ffd6d1", "#eaf2ff"],
                        panel="panel-merahputih", hand="#ffffff", pill="DIRGAHAYU INDONESIA", bawah="Merdeka!",
                        bawah_top=720, bawah_warna="#c62828", bawah_besar=120,
                        sampul=[("bendera", 70, 150, 160, -6), ("bendera", 860, 170, 150, 8), ("kembang", 860, 1030, 120, 0),
                                ("kembang2", 100, 1040, 100, 0), ("bintang", 960, 940, 50, 0)],
                        art=["bendera_besar", "buku_lampu", "kertas_cek", "amplop_bunga"],
                        tutup=("Dirgahayu Indonesia!", "Mari isi kemerdekaan dengan semangat belajar dan berkarya.")),
    "ujian": dict(nama="Ujian", kata=["ujian", "uas", "uts", "pts", "pas", "asesmen", "tryout", "try out", "belajar", "semester"],
                  bg="#f3f7ff", dot="#d3def5", primary="#1565d8", accent="#2e9d57", soft=["#d5e6ff", "#dff3e4", "#ffe2b0", "#d5e6ff"],
                  panel="panel-kertas", hand="#1565d8", pill="SIAP UJIAN", bawah="Kamu pasti bisa!",
                  sampul=[("bintang", 96, 186, 70, 0), ("pensil", 760, 840, 300, -32), ("buku", 40, 800, 300, 0), ("bintang2", 930, 1000, 54, 0)],
                  art=["kertas_cek", "jam_weker", "buku_lampu", "kartu_alat"],
                  tutup=("Semangat ujiannya!", "Simpan tips ini dan bagikan ke teman sekelasmu.")),
    "sekolah": dict(nama="Masuk Sekolah", kata=["masuk sekolah", "sekolah", "tahun ajaran", "mpls", "back to school", "seragam"],
                    bg="#fffbea", dot="#f3e3a6", primary="#1565d8", accent="#e5483d", soft=["#ffe9a8", "#d5e6ff", "#ffd6d1", "#dff3e4"],
                    panel="panel-kuning", hand="#1565d8", pill="SEMANGAT SEKOLAH", bawah="Siap belajar lagi!",
                    sampul=[("apel", 820, 180, 150, 0), ("buku", 40, 800, 300, 0), ("pensil", 760, 840, 300, -32), ("bintang", 96, 186, 70, 0)],
                    art=["tas_sekolah", "kartu_alat", "buku_lampu", "jam_weker"],
                    tutup=("Semangat sekolah!", "Simpan dan bagikan ke teman yang juga siap belajar.")),
}


def _hiasan(nama, t):
    return {"bintang": bintang("#f2b33d"), "bintang2": bintang(t["primary"]), "bintang_emas": bintang("#d4a73a"),
            "apel": apel(), "buku": buku_tumpuk(t["primary"], "#f2b33d", t["accent"] if t["accent"] != t["primary"] else "#e5483d"),
            "pensil": pensil(), "bulan": bulan_sabit("#f4c542"), "lentera": lentera(), "masjid": masjid("#0c4636" if t["primary"] != "#1b2a5a" else "#121d40"),
            "ketupat": ketupat(), "bendera": bendera(), "kembang": kembang_api("#f2b33d", "#e53935"),
            "kembang2": kembang_api("#1565d8", "#f2b33d")}[nama]


def hiasan_sampul(t):
    """Elemen dekorasi sampul siap ditaruh di HTML (posisi absolut)."""
    out = []
    for nama, x, y, w, rot in t["sampul"]:
        out.append(f'<div class="hias" style="left:{x}px;top:{y}px;width:{w}px;transform:rotate({rot}deg)">{_hiasan(nama, t)}</div>')
    return "".join(out)


def pilih(p: dict) -> str:
    """Tema dari kolom `tema`; kalau kosong, ditebak dari judul/detail/poin. Cadangan: umum."""
    diminta = re.sub(r"[^a-z0-9]", "", (p.get("tema") or "").lower())
    for k, t in TEMA.items():
        if diminta and (diminta == k or diminta == re.sub(r"[^a-z0-9]", "", t["nama"].lower())):
            return k
    teks = " ".join([p.get("nama", ""), p.get("detail", ""), " ".join(p.get("poin", []))]).lower()
    for k, t in TEMA.items():
        if any(re.search(r"\b" + re.escape(kata) + r"\b", teks) for kata in t["kata"]):
            return k
    return "umum"
