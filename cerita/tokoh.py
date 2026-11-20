"""Tokoh 'Misteri Surat Tanpa Nama' sebagai SVG datar (dipakai ulang di semua part supaya wajah konsisten)."""

KULIT = "#E7B48C"
KULIT_GELAP = "#D49A70"
HIJAB = "#24539C"
HIJAB_TERANG = "#3B6FC4"
BAJU = "#F6EFE1"
APRON = "#2F6FD1"
ROK = "#26365E"


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


def kepala_nafi(ekspresi: str = "senang") -> str:
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


def nafi_badan(ekspresi: str = "senang") -> str:
    """Kak Nafi seluruh badan, viewBox 0 0 400 900."""
    return f'''<svg viewBox="0 0 400 900" xmlns="http://www.w3.org/2000/svg">
    <ellipse cx="200" cy="872" rx="120" ry="16" fill="#000" opacity=".12"/>
    <path d="M120 520 L280 520 L318 850 L82 850Z" fill="{ROK}"/>
    <rect x="110" y="846" width="78" height="22" rx="10" fill="#3b2b25"/><rect x="212" y="846" width="78" height="22" rx="10" fill="#3b2b25"/>
    <g class="lengan-kiri"><path d="M118 330 C88 380 80 460 92 540" stroke="{BAJU}" stroke-width="46" fill="none" stroke-linecap="round"/>
      <circle cx="94" cy="550" r="22" fill="{KULIT}"/></g>
    <g class="lengan-kanan"><path d="M282 330 C312 380 320 460 308 540" stroke="{BAJU}" stroke-width="46" fill="none" stroke-linecap="round"/>
      <circle cx="306" cy="550" r="22" fill="{KULIT}"/></g>
    <path d="M110 330 C110 300 150 290 200 290 C250 290 290 300 290 330 L296 540 L104 540Z" fill="{BAJU}"/>
    <path d="M140 360 L260 360 L270 600 L130 600Z" fill="{APRON}"/>
    <rect x="165" y="470" width="70" height="52" rx="8" fill="#2558b4"/>
    <text x="200" y="430" font-family="Poppins" font-weight="700" font-size="34" fill="#fff" text-anchor="middle">A</text>
    <g class="kepala">{kepala_nafi(ekspresi)}</g>
    </svg>'''


def nafi_dada(ekspresi: str = "kaget") -> str:
    """Kak Nafi setengah badan (untuk close-up), viewBox 0 0 400 520."""
    return f'''<svg viewBox="0 0 400 520" xmlns="http://www.w3.org/2000/svg">
    <path d="M60 520 C60 400 120 360 200 360 C280 360 340 400 340 520Z" fill="{BAJU}"/>
    <path d="M140 400 L260 400 L268 520 L132 520Z" fill="{APRON}"/>
    <g class="kepala">{kepala_nafi(ekspresi)}</g>
    </svg>'''


def amplop(lebar: int = 360, tua: bool = False, depan: bool = False) -> str:
    """depan=True: sisi depan (tanpa lipatan) dengan bintang di pojok, untuk close-up tulisan."""
    kertas = "#E9D7A6" if tua else "#F4E7C8"
    garis = "#CDB47A" if tua else "#E2CFA4"
    if depan:
        isi = (f'<rect x="18" y="18" width="324" height="204" rx="6" fill="none" stroke="{garis}" stroke-width="2" stroke-dasharray="8 6"/>'
               '<path d="M318 30 l6 13 14 2 -10 10 3 14 -13 -7 -13 7 3 -14 -10 -10 14 -2z" fill="#1E3A6B"/>')
    else:
        isi = (f'<path d="M8 10 L180 132 L352 10" stroke="{garis}" stroke-width="5" fill="none"/>'
               '<path d="M180 150 l9 19 21 3 -15 15 4 21 -19 -10 -19 10 4 -21 -15 -15 21 -3z" fill="#1E3A6B"/>')
    return f'''<svg viewBox="0 0 360 240" width="{lebar}" xmlns="http://www.w3.org/2000/svg">
    <rect x="4" y="4" width="352" height="232" rx="10" fill="{kertas}" stroke="{garis}" stroke-width="4"/>
    {isi}
    </svg>'''
