"""Tokoh 'Misteri Surat Tanpa Nama' sebagai SVG datar (dipakai ulang di semua part supaya wajah konsisten)."""

KULIT = "#E7B48C"
KULIT_GELAP = "#D49A70"
HIJAB = "#8E5B6E"        # mauve, warna hijab sehari-hari (bukan warna brand)
HIJAB_TERANG = "#A9758A"
BAJU = "#7FA38A"         # tunik hijau sage
BAJU_GELAP = "#6B8E76"
ROK = "#4A4A58"          # celana/rok abu tua


def _mata(ekspresi: str) -> str:
    if ekspresi == "kaget":
        alis = ('<path d="M156 168 q20 -16 38 -4" stroke="#3a2a22" stroke-width="7" fill="none" stroke-linecap="round"/>'
                '<path d="M206 164 q18 -12 38 4" stroke="#3a2a22" stroke-width="7" fill="none" stroke-linecap="round"/>')
        mata = ('<g class="kedip"><ellipse cx="175" cy="203" rx="11" ry="14" fill="#2b2220"/>'
                '<ellipse cx="225" cy="203" rx="11" ry="14" fill="#2b2220"/>'
                '<circle cx="179" cy="198" r="4" fill="#fff"/><circle cx="229" cy="198" r="4" fill="#fff"/></g>')
        mulut = '<ellipse cx="200" cy="252" rx="11" ry="14" fill="#7a2e2e"/><ellipse cx="200" cy="258" rx="6" ry="5" fill="#e07a7a"/>'
    else:  # senang
        alis = ('<path d="M158 178 q18 -9 34 0" stroke="#3a2a22" stroke-width="6" fill="none" stroke-linecap="round"/>'
                '<path d="M208 178 q16 -9 34 0" stroke="#3a2a22" stroke-width="6" fill="none" stroke-linecap="round"/>')
        mata = ('<g class="kedip"><ellipse cx="175" cy="205" rx="9" ry="11" fill="#2b2220"/>'
                '<ellipse cx="225" cy="205" rx="9" ry="11" fill="#2b2220"/>'
                '<circle cx="178" cy="201" r="3.5" fill="#fff"/><circle cx="228" cy="201" r="3.5" fill="#fff"/></g>')
        mulut = '<path d="M182 245 q18 18 36 0" stroke="#7a2e2e" stroke-width="6" fill="none" stroke-linecap="round"/>'
    return alis + mata + mulut


def kepala_laras(ekspresi: str = "senang") -> str:
    """Kepala + hijab dalam koordinat 0..400 (pusat wajah 200,210)."""
    return f'''
    <path d="M200 70 C120 70 82 130 82 205 C82 260 100 300 70 380 L330 380 C300 300 318 260 318 205 C318 130 280 70 200 70Z" fill="{HIJAB}"/>
    <path d="M118 160 C130 110 170 92 200 92 C230 92 270 110 282 160" stroke="{HIJAB_TERANG}" stroke-width="10" fill="none"/>
    <ellipse cx="200" cy="215" rx="72" ry="84" fill="{KULIT}"/>
    <path d="M130 170 C140 118 170 104 200 104 C230 104 260 118 270 170 C250 150 230 142 200 142 C170 142 150 150 130 170Z" fill="{HIJAB}"/>
    <circle cx="160" cy="236" r="13" fill="#f08a8a" opacity=".35"/><circle cx="240" cy="236" r="13" fill="#f08a8a" opacity=".35"/>
    <path d="M197 218 q5 10 -2 14" stroke="{KULIT_GELAP}" stroke-width="4" fill="none" stroke-linecap="round"/>
    {_mata(ekspresi)}
    '''


def laras_badan(ekspresi: str = "senang") -> str:
    """Mbak Laras (±32 th, pemilik/penjaga toko) seluruh badan, viewBox 0 0 400 900. Pakaian biasa, tanpa logo."""
    return f'''<svg viewBox="0 0 400 900" xmlns="http://www.w3.org/2000/svg">
    <ellipse cx="200" cy="872" rx="120" ry="16" fill="#000" opacity=".12"/>
    <path d="M120 520 L280 520 L318 850 L82 850Z" fill="{ROK}"/>
    <rect x="110" y="846" width="78" height="22" rx="10" fill="#3b2b25"/><rect x="212" y="846" width="78" height="22" rx="10" fill="#3b2b25"/>
    <g class="lengan-kiri"><path d="M118 330 C88 380 80 460 92 540" stroke="{BAJU}" stroke-width="46" fill="none" stroke-linecap="round"/>
      <circle cx="94" cy="550" r="22" fill="{KULIT}"/></g>
    <g class="lengan-kanan"><path d="M282 330 C312 380 320 460 308 540" stroke="{BAJU}" stroke-width="46" fill="none" stroke-linecap="round"/>
      <circle cx="306" cy="550" r="22" fill="{KULIT}"/></g>
    <path d="M110 330 C110 300 150 290 200 290 C250 290 290 300 290 330 L296 540 L104 540Z" fill="{BAJU}"/>
    <path d="M104 520 L296 520 L304 640 L96 640Z" fill="{BAJU}"/>
    <path d="M200 300 L200 630" stroke="{BAJU_GELAP}" stroke-width="4"/>
    <circle cx="200" cy="380" r="5" fill="{BAJU_GELAP}"/><circle cx="200" cy="450" r="5" fill="{BAJU_GELAP}"/><circle cx="200" cy="520" r="5" fill="{BAJU_GELAP}"/>
    <g class="kepala">{kepala_laras(ekspresi)}</g>
    </svg>'''


def laras_dada(ekspresi: str = "kaget") -> str:
    """Mbak Laras setengah badan (untuk close-up), viewBox 0 0 400 520."""
    return f'''<svg viewBox="0 0 400 520" xmlns="http://www.w3.org/2000/svg">
    <path d="M60 520 C60 400 120 360 200 360 C280 360 340 400 340 520Z" fill="{BAJU}"/>
    <path d="M200 370 L200 520" stroke="{BAJU_GELAP}" stroke-width="4"/><circle cx="200" cy="440" r="5" fill="{BAJU_GELAP}"/>
    <g class="kepala">{kepala_laras(ekspresi)}</g>
    </svg>'''


def amplop(lebar: int = 360, tua: bool = False, depan: bool = False) -> str:
    """depan=True: sisi depan (tanpa lipatan) dengan bintang di pojok, untuk close-up tulisan."""
    kertas = "#D6BC82" if tua else "#F4E7C8"
    garis = "#A88A4E" if tua else "#E2CFA4"
    noda = ('<circle cx="70" cy="190" r="34" fill="#a07a3a" opacity=".18"/><circle cx="300" cy="60" r="22" fill="#a07a3a" opacity=".15"/>'
            '<path d="M4 120 L30 112 L22 140Z" fill="#00000014"/>') if tua else ""
    if depan:
        isi = (f'<rect x="18" y="18" width="324" height="204" rx="6" fill="none" stroke="{garis}" stroke-width="2" stroke-dasharray="8 6"/>'
               '<path d="M318 30 l6 13 14 2 -10 10 3 14 -13 -7 -13 7 3 -14 -10 -10 14 -2z" fill="#1E3A6B"/>')
    else:
        isi = (f'<path d="M8 10 L180 132 L352 10" stroke="{garis}" stroke-width="5" fill="none"/>'
               '<path d="M180 150 l9 19 21 3 -15 15 4 21 -19 -10 -19 10 4 -21 -15 -15 21 -3z" fill="#1E3A6B"/>')
    return f'''<svg viewBox="0 0 360 240" width="{lebar}" xmlns="http://www.w3.org/2000/svg">
    <rect x="4" y="4" width="352" height="232" rx="10" fill="{kertas}" stroke="{garis}" stroke-width="4"/>
    {noda}{isi}
    </svg>'''


# nama lama (kompatibilitas)
nafi_badan, nafi_dada, kepala_nafi = laras_badan, laras_dada, kepala_laras


# =============================================================================== semua tokoh (dipakai mesin.py)
# jk: p/l · hijab (warna) atau rambut + gaya_rambut · bawah_jenis: rok / celana / rok_pendek · skala tinggi badan
_SMA_L = dict(baju="#f6f6f4", baju2="#d6d6d2", kerah=True, osis=True, bawah="#7d7f86", bawah_jenis="celana", sepatu="#1b1b1d")
_SMA_P = dict(baju="#f6f6f4", baju2="#d6d6d2", kerah=True, osis=True, bawah="#7d7f86", bawah_jenis="rok", sepatu="#1b1b1d")
_KERUDUNG_SEKOLAH = dict(hijab="#fbfbfb", hijab2="#e4e4e4")
TOKOH = {
    "laras": dict(nama="Mbak Laras", jk="p", hijab=HIJAB, hijab2=HIJAB_TERANG, baju=BAJU, baju2=BAJU_GELAP,
                  bawah=ROK, bawah_jenis="rok", kulit=KULIT, skala=1.0, kancing=True, tunik=True),
    "raka": dict(nama="Raka", jk="l", rambut="#1d1716", gaya_rambut="klimis", kulit="#D9A47A", skala=1.0, **_SMA_L),
    "dinda": dict(nama="Dinda", jk="p", rambut="#2a1d18", gaya_rambut="bob", kulit="#EDBE98", skala=0.95, **_SMA_P),
    "bima": dict(nama="Bima", jk="l", rambut="#151212", gaya_rambut="poni", kulit="#C98E64", skala=1.0, **_SMA_L),
    # Bima memakai jaket gelap di luar seragam (petunjuk palsu di Part 2-3)
    "bima_jaket": dict(nama="Bima", jk="l", rambut="#151212", gaya_rambut="poni", kulit="#C98E64", skala=1.0,
                       **dict(_SMA_L, baju="#2b2d33", baju2="#17181c", kerah=False, osis=False, jaket=True)),
    "hadi": dict(nama="Pak Hadi", jk="l", rambut="#1d1716", gaya_rambut="rapi", batik=True, baju="#2f7a4f", baju2="#1f5a37",
                 kerah=True, kerah_warna="#2f7a4f", bawah="#18181b", bawah_jenis="celana", sepatu="#0d0d0f", pantofel=True,
                 kulit="#D49A70", kacamata=True, kumis=True, skala=1.03),
    "rani": dict(nama="Rani", jk="p", rambut="#231815", gaya_rambut="panjang", baju="#1f2024", baju2="#0e0e10", jaket=True,
                 bawah="#2b2b33", bawah_jenis="celana", sepatu="#141414", kulit="#E2AD86", skala=1.0),
    # baju bebas (pulang sekolah, malam, hari Minggu)
    "raka_bebas": dict(nama="Raka (bebas)", jk="l", rambut="#1d1716", gaya_rambut="klimis", kulit="#D9A47A", skala=1.0,
                       baju="#d9622b", baju2="#b24c1e", kaos=True, lengan_pendek=True,
                       sablon='<rect x="-90" y="-22" width="180" height="14" fill="#f3e3c8"/><rect x="-90" y="2" width="180" height="14" fill="#1E3A6B"/>',
                       bawah="#35557f", bawah_jenis="celana", sneakers=True),
    "dinda_bebas": dict(nama="Dinda (bebas)", jk="p", rambut="#2a1d18", gaya_rambut="bob", kulit="#EDBE98", skala=0.95,
                        baju="#e9b949", baju2="#c99a2e", kaos=True,
                        sablon='<path d="M0 -28 l8 17 19 3 -14 13 3 19 -16 -9 -16 9 3 -19 -14 -13 19 -3z" fill="#fff"/>',
                        bawah="#e8dcc4", bawah_jenis="rok", sneakers=True),
    "bima_bebas": dict(nama="Bima (bebas)", jk="l", rambut="#151212", gaya_rambut="poni", kulit="#C98E64", skala=1.0,
                       baju="#8a9097", baju2="#6c7279", hoodie=True, bawah="#24262b", bawah_jenis="celana", sneakers=True),
    "hadi_bebas": dict(nama="Hadi (bebas)", jk="l", rambut="#1d1716", gaya_rambut="rapi", kulit="#D49A70", kacamata=True, kumis=True,
                       skala=1.03, baju="#d8c7a3", baju2="#b9a67e", kerah=True, kerah_warna="#d8c7a3", lengan_pendek=True,
                       bawah="#5a4a3a", bawah_jenis="celana", sepatu="#3b2b25"),
    # kilas balik / foto lama (SMA, ±2011)
    "laras_sma": dict(nama="Laras (SMA)", jk="p", kulit=KULIT, skala=0.97, **_KERUDUNG_SEKOLAH, **_SMA_P),
    "hadi_sma": dict(nama="Hadi (SMA)", jk="l", rambut="#1d1716", gaya_rambut="rapi", kulit="#D49A70", kacamata=True,
                     skala=1.0, **_SMA_L),
    "rani_sma": dict(nama="Rani (SMA)", jk="p", rambut="#231815", gaya_rambut="panjang", kulit="#E2AD86", skala=0.97, **_SMA_P),
}
EKSPRESI = ["senang", "kaget", "bingung", "sedih", "serius", "takut"]


def _wajah(ekspresi: str) -> str:
    """Alis, mata, mulut (+ mulut terbuka .mb untuk animasi bicara) di koordinat kepala 0..400."""
    garis = 'stroke="#3a2a22" fill="none" stroke-linecap="round"'
    mata_biasa = ('<g class="kedip"><ellipse cx="175" cy="205" rx="9" ry="11" fill="#2b2220"/>'
                  '<ellipse cx="225" cy="205" rx="9" ry="11" fill="#2b2220"/>'
                  '<circle cx="178" cy="201" r="3.5" fill="#fff"/><circle cx="228" cy="201" r="3.5" fill="#fff"/></g>')
    if ekspresi in ("kaget", "takut"):
        return _mata("kaget") + '<ellipse class="mb" cx="200" cy="254" rx="13" ry="15" fill="#7a2e2e" opacity="0"/>'
    if ekspresi == "bingung":
        alis = f'<path d="M156 176 q20 -6 36 2" {garis} stroke-width="6"/><path d="M208 166 q18 -12 36 -2" {garis} stroke-width="6"/>'
        mulut = f'<path d="M184 252 q8 -6 16 0 t16 0" {garis} stroke="#7a2e2e" stroke-width="6"/>'
    elif ekspresi == "sedih":
        alis = f'<path d="M158 176 q16 -2 32 -12" {garis} stroke-width="6"/><path d="M210 164 q16 10 32 12" {garis} stroke-width="6"/>'
        mulut = f'<path d="M184 258 q16 -12 32 0" {garis} stroke="#7a2e2e" stroke-width="6"/>'
    elif ekspresi == "serius":
        alis = f'<path d="M156 180 l36 6" {garis} stroke-width="7"/><path d="M244 180 l-36 6" {garis} stroke-width="7"/>'
        mulut = f'<path d="M186 252 h28" {garis} stroke="#7a2e2e" stroke-width="6"/>'
    else:
        return _mata("senang") + '<ellipse class="mb" cx="200" cy="252" rx="14" ry="12" fill="#7a2e2e" opacity="0"/>'
    return alis + mata_biasa + mulut + '<ellipse class="mb" cx="200" cy="252" rx="13" ry="12" fill="#7a2e2e" opacity="0"/>'


_RAMBUT = {
    "jabrik": ('<path d="M124 210 C110 150 118 112 140 100 L136 62 L166 86 L178 48 L202 80 L222 46 L236 84 L266 60 L262 100 '
               'C284 116 292 150 276 210 C272 178 266 160 258 150 L246 166 L236 144 L222 162 L210 140 L196 160 L182 140 '
               'L168 162 L156 146 L146 168 C136 176 128 190 124 210Z" fill="{r}"/>'),
    "poni": ('<path d="M124 215 C104 112 156 80 202 80 C250 80 296 112 276 215 C270 170 254 140 210 136 C180 132 150 160 124 215Z" fill="{r}"/>'
             '<path d="M126 198 C128 128 170 108 216 112 C256 118 280 150 274 200 C262 172 240 152 212 150 C188 172 160 188 126 198Z" fill="{r}"/>'),
    "rapi": ('<path d="M126 196 C114 112 160 88 204 88 C250 88 288 116 274 196 C264 152 238 136 198 140 L182 128 '
             'C162 140 140 160 126 196Z" fill="{r}"/>'),
    "klimis": ('<path d="M126 200 C116 118 158 86 204 86 C252 86 288 116 274 200 C268 160 252 140 222 136 '
               'C206 128 186 126 168 134 C150 142 134 166 126 200Z" fill="{r}"/>'
               '<path d="M160 104 C178 74 236 70 258 98 C236 90 208 92 186 106 C178 100 168 100 160 104Z" fill="{r}"/>'),
    "bob": ('<path d="M128 204 C118 128 160 90 202 90 C246 90 286 128 276 204 C270 172 262 158 250 150 '
            'C222 162 180 162 152 150 C140 160 132 180 128 204Z" fill="{r}"/>'),
    "panjang": ('<path d="M128 214 C112 120 156 82 202 82 C250 82 292 118 274 214 C268 170 246 140 214 134 '
                'C196 156 160 176 128 214Z" fill="{r}"/>'),
    "kuncir": ('<circle cx="104" cy="196" r="34" fill="{r}"/><circle cx="296" cy="196" r="34" fill="{r}"/>'
               '<rect x="122" y="182" width="14" height="26" rx="5" fill="#e74c3c"/><rect x="264" y="182" width="14" height="26" rx="5" fill="#e74c3c"/>'
               '<path d="M126 210 C110 112 158 84 200 84 C242 84 290 112 274 210 C270 170 250 150 200 150 C150 150 130 170 126 210Z" fill="{r}"/>'
               '<path d="M134 176 C150 136 250 136 266 176 L262 156 C240 140 160 140 138 156Z" fill="{r}"/>'),
}


def kepala(t: dict, ekspresi: str = "senang") -> str:
    k = t["kulit"]
    if t.get("hijab"):
        h, h2 = t["hijab"], t["hijab2"]
        return f'''
    <path d="M200 70 C120 70 82 130 82 205 C82 260 100 300 70 380 L330 380 C300 300 318 260 318 205 C318 130 280 70 200 70Z" fill="{h}"/>
    <path d="M118 160 C130 110 170 92 200 92 C230 92 270 110 282 160" stroke="{h2}" stroke-width="10" fill="none"/>
    <ellipse cx="200" cy="215" rx="72" ry="84" fill="{k}"/>
    <path d="M130 170 C140 118 170 104 200 104 C230 104 260 118 270 170 C250 150 230 142 200 142 C170 142 150 150 130 170Z" fill="{h}"/>
    <circle cx="160" cy="236" r="13" fill="#f08a8a" opacity=".35"/><circle cx="240" cy="236" r="13" fill="#f08a8a" opacity=".35"/>
    <path d="M197 218 q5 10 -2 14" stroke="#00000033" stroke-width="4" fill="none" stroke-linecap="round"/>
    {_wajah(ekspresi)}'''
    kaca = ('<g fill="none" stroke="#2b2b2b" stroke-width="5"><rect x="152" y="186" width="46" height="36" rx="12"/>'
            '<rect x="202" y="186" width="46" height="36" rx="12"/><path d="M198 200 h4"/></g>') if t.get("kacamata") else ""
    kumis = '<path d="M180 238 q20 -8 40 0" stroke="#2b1d18" stroke-width="7" fill="none" stroke-linecap="round"/>' if t.get("kumis") else ""
    leher = f'<rect x="172" y="270" width="56" height="34" fill="{k}"/><rect x="172" y="284" width="56" height="12" fill="#00000018"/>'
    return f'''{leher}
    <circle cx="128" cy="222" r="17" fill="{k}"/><circle cx="272" cy="222" r="17" fill="{k}"/>
    <ellipse cx="200" cy="215" rx="72" ry="84" fill="{k}"/>
    {_RAMBUT[t["gaya_rambut"]].format(r=t["rambut"])}
    <circle cx="160" cy="236" r="12" fill="#f08a8a" opacity=".3"/><circle cx="240" cy="236" r="12" fill="#f08a8a" opacity=".3"/>
    <path d="M197 218 q5 10 -2 14" stroke="#00000033" stroke-width="4" fill="none" stroke-linecap="round"/>
    {_wajah(ekspresi)}{kaca}{kumis}'''


RAMBUT_BELAKANG = {
    "bob": '<path d="M112 210 C98 120 150 78 202 78 C256 78 306 120 292 210 L298 300 C276 314 250 312 238 300 L160 300 C150 312 124 314 106 300Z" fill="{r}"/>',
    "panjang": '<path d="M112 200 C96 120 150 76 202 76 C256 76 306 120 290 200 L306 430 C260 450 140 450 96 430Z" fill="{r}"/>',
}

_BATIK = ('<defs><pattern id="batik" width="56" height="56" patternUnits="userSpaceOnUse">'
          '<rect width="56" height="56" fill="#2f7a4f"/>'
          '<g fill="#e9d79a" opacity=".85"><ellipse cx="28" cy="14" rx="7" ry="12"/><ellipse cx="28" cy="42" rx="7" ry="12"/>'
          '<ellipse cx="14" cy="28" rx="12" ry="7"/><ellipse cx="42" cy="28" rx="12" ry="7"/></g>'
          '<circle cx="28" cy="28" r="4" fill="#1f5a37"/><circle cx="0" cy="0" r="5" fill="#a5c98f"/>'
          '<circle cx="56" cy="0" r="5" fill="#a5c98f"/><circle cx="0" cy="56" r="5" fill="#a5c98f"/><circle cx="56" cy="56" r="5" fill="#a5c98f"/>'
          '</pattern></defs>')


def _osis(x: int = 236, y: int = 380) -> str:
    """Badge OSIS di saku kiri seragam."""
    return (f'<rect x="{x - 6}" y="{y - 8}" width="56" height="44" rx="4" fill="none" stroke="#d6d6d2" stroke-width="3"/>'
            f'<path d="M{x + 22} {y} l14 6 v12 c0 10 -8 16 -14 18 c-6 -2 -14 -8 -14 -18 v-12z" fill="#c9a227" stroke="#8a6d12" stroke-width="2"/>')


def _atasan(t: dict, y1: int = 290) -> str:
    b, b2 = t["baju"], t["baju2"]
    isi = "url(#batik)" if t.get("batik") else b
    out = (_BATIK if t.get("batik") else "") + \
        f'<path d="M110 330 C110 300 150 {y1} 200 {y1} C250 {y1} 290 300 290 330 L296 540 L104 540Z" fill="{isi}"/>'
    if t.get("jaket"):
        out += (f'<path d="M200 {y1 + 6} L200 640" stroke="{b2}" stroke-width="6"/>'
                f'<path d="M150 {y1 + 4} C160 330 180 350 200 360 C220 350 240 330 250 {y1 + 4}" stroke="{b2}" stroke-width="16" fill="none"/>'
                f'<rect x="136" y="460" width="40" height="8" rx="4" fill="{b2}"/><rect x="224" y="460" width="40" height="8" rx="4" fill="{b2}"/>')
    elif t.get("kerah"):
        kw = t.get("kerah_warna", "#ffffff")
        out += (f'<path d="M160 {y1 + 2} L200 345 L184 365Z M240 {y1 + 2} L200 345 L216 365Z" fill="{kw}" stroke="{b2}" stroke-width="3"/>'
                f'<path d="M200 345 L200 540" stroke="{b2}" stroke-width="3"/>'
                f'<circle cx="200" cy="400" r="4" fill="{b2}"/><circle cx="200" cy="460" r="4" fill="{b2}"/>')
        if t.get("osis"):
            out += _osis(236, 420 if t.get("hijab") else 380)
    elif t.get("kaos"):
        out += (f'<path d="M168 {y1 + 2} C176 312 224 312 232 {y1 + 2}" stroke="{b2}" stroke-width="8" fill="none"/>'
                + (f'<g transform="translate(200 420)">{t["sablon"]}</g>' if t.get("sablon") else ""))
    elif t.get("hoodie"):
        out += (f'<path d="M140 {y1 + 6} C150 340 250 340 260 {y1 + 6} C250 316 150 316 140 {y1 + 6}Z" fill="{b2}"/>'
                f'<path d="M184 330 L180 400 M216 330 L220 400" stroke="#ddd" stroke-width="5" stroke-linecap="round"/>'
                f'<path d="M140 470 L260 470 L250 530 L150 530Z" fill="{b2}" opacity=".6"/>')
    elif t.get("kancing"):
        out += (f'<path d="M200 300 L200 630" stroke="{b2}" stroke-width="4"/>'
                f'<circle cx="200" cy="380" r="5" fill="{b2}"/><circle cx="200" cy="450" r="5" fill="{b2}"/><circle cx="200" cy="520" r="5" fill="{b2}"/>')
    return out


def badan(id_: str, ekspresi: str = "senang") -> str:
    """Tokoh seluruh badan, viewBox 0 0 400 900 (kaki di y=868)."""
    t = TOKOH[id_]
    b, k, bw = t["baju"], t["kulit"], t["bawah"]
    if t["bawah_jenis"] == "rok":
        bawah = f'<path d="M120 520 L280 520 L318 850 L82 850Z" fill="{bw}"/>'
        ujung = 540
    elif t["bawah_jenis"] == "celana":
        bawah = (f'<path d="M112 520 L288 520 L284 850 L210 850 L200 640 L190 850 L116 850Z" fill="{bw}"/>')
        ujung = 560
    else:  # rok pendek anak + kaki
        bawah = (f'<rect x="140" y="640" width="40" height="190" fill="{k}"/><rect x="220" y="640" width="40" height="190" fill="{k}"/>'
                 '<rect x="138" y="770" width="44" height="70" fill="#fff"/><rect x="218" y="770" width="44" height="70" fill="#fff"/>'
                 f'<path d="M108 520 L292 520 L316 680 L84 680Z" fill="{bw}"/>')
        ujung = 520
    tunik = f'<path d="M104 520 L296 520 L304 640 L96 640Z" fill="{b}"/>' if t.get("tunik") else ""
    if t.get("osis"):  # seragam dimasukkan + ikat pinggang hitam
        tunik = '<rect x="108" y="518" width="184" height="16" fill="#1b1b1d"/><rect x="190" y="516" width="22" height="20" fill="#9aa"/>'
    lengan = "url(#batik)" if t.get("batik") else b
    sp = t.get("sepatu", "#3b2b25")
    pendek = t.get("lengan_pendek", False)
    if t.get("sneakers"):
        sp = "#f4f4f4"
    kilap = ('<path d="M124 852 h40" stroke="#ffffff66" stroke-width="4" stroke-linecap="round"/>'
             '<path d="M226 852 h40" stroke="#ffffff66" stroke-width="4" stroke-linecap="round"/>') if t.get("pantofel") else ""
    rb = RAMBUT_BELAKANG.get(t.get("gaya_rambut", ""), "").format(r=t.get("rambut", ""))
    return f'''<svg viewBox="0 0 400 900" xmlns="http://www.w3.org/2000/svg">
    <ellipse cx="200" cy="872" rx="120" ry="16" fill="#000" opacity=".12"/>
    {bawah}
    <rect x="110" y="846" width="78" height="22" rx="10" fill="{sp}"/><rect x="212" y="846" width="78" height="22" rx="10" fill="{sp}"/>{kilap}{'<rect x="110" y="862" width="78" height="8" rx="4" fill="#9aa"/><rect x="212" y="862" width="78" height="8" rx="4" fill="#9aa"/>' if t.get("sneakers") else ""}
    {rb}
    <g class="lengan-kiri"><path d="M118 330 C88 380 80 460 92 {ujung}" stroke="{k if pendek else lengan}" stroke-width="{38 if pendek else 46}" fill="none" stroke-linecap="round"/>
      {f'<path d="M118 330 C104 352 98 380 97 404" stroke="{lengan}" stroke-width="52" fill="none" stroke-linecap="round"/>' if pendek else ""}
      <circle cx="94" cy="{ujung + 10}" r="22" fill="{k}"/></g>
    <g class="lengan-kanan"><path d="M282 330 C312 380 320 460 308 {ujung}" stroke="{k if pendek else lengan}" stroke-width="{38 if pendek else 46}" fill="none" stroke-linecap="round"/>
      {f'<path d="M282 330 C296 352 302 380 303 404" stroke="{lengan}" stroke-width="52" fill="none" stroke-linecap="round"/>' if pendek else ""}
      <circle cx="306" cy="{ujung + 10}" r="22" fill="{k}"/></g>
    {_atasan(t)}{tunik}
    <g class="kepala">{kepala(t, ekspresi)}</g>
    </svg>'''


def dada(id_: str, ekspresi: str = "senang") -> str:
    """Tokoh setengah badan untuk close-up, viewBox 0 0 400 520."""
    t = TOKOH[id_]
    b, b2 = t["baju"], t["baju2"]
    if t.get("batik"):
        b = "url(#batik)"
    hiasan = _BATIK if t.get("batik") else ""
    if t.get("jaket"):
        hiasan += f'<path d="M200 372 L200 520" stroke="{b2}" stroke-width="6"/><path d="M150 364 C170 400 190 410 200 414 C210 410 230 400 250 364" stroke="{b2}" stroke-width="14" fill="none"/>'
    elif t.get("kerah"):
        hiasan += (f'<path d="M160 362 L200 410 L184 430Z M240 362 L200 410 L216 430Z" fill="{t.get("kerah_warna", "#fff")}" '
                   f'stroke="{b2}" stroke-width="3"/>' + (_osis(236, 470 if t.get("hijab") else 450) if t.get("osis") else ""))
    elif t.get("kancing"):
        hiasan += f'<path d="M200 370 L200 520" stroke="{b2}" stroke-width="4"/><circle cx="200" cy="440" r="5" fill="{b2}"/>'
    return f'''<svg viewBox="0 0 400 520" xmlns="http://www.w3.org/2000/svg">
    {RAMBUT_BELAKANG.get(t.get("gaya_rambut", ""), "").format(r=t.get("rambut", "")).replace('<path', '<path transform="translate(0,58)"', 1)}
    <path d="M60 520 C60 400 120 360 200 360 C280 360 340 400 340 520Z" fill="{b}"/>{hiasan}
    <g class="kepala" transform="translate(0,{0 if t.get("hijab") else 58})">{kepala(t, ekspresi)}</g>
    </svg>'''
