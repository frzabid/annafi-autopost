"""Otomasi konten Annafi ATK.

Jenis konten (kolom `jenis` di sheet):
  katalog                       -> Story Instagram. Pratinjau 2 jam sebelumnya, tayang otomatis
                                   kecuali kolom tunda = YA. Setelah tayang: pengingat Sorotan.
  edukasi / promo / info / momen -> Postingan feed Instagram + Facebook. Pratinjau malam sebelumnya
                                   (20.00) dengan tombol ✅/❌ di Telegram; HANYA tayang kalau disetujui.

  python src/main.py cek       -> cek ringan (tanpa Chrome), apakah ada yang perlu dikerjakan
  python src/main.py prepare   -> proses tombol Telegram, kirim pratinjau, siapkan antrian tayang
  python src/main.py publish   -> posting antrian ke Instagram / Facebook
  python src/main.py tes       -> tes koneksi Telegram & sheet
  python src/main.py contoh    -> kirim contoh poster (1 story + 1 feed terdekat) ke Telegram, tanpa posting
"""
import html, json, os, pathlib, sys, traceback
from datetime import datetime, timedelta
import config, meta, notify, sheet
from config import TZ

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "state.json"
QUEUE = ROOT / "state" / "queue.json"
POSTERS = ROOT / "posters"
WORK = ROOT / ".work"
SELESAI = ("terposting", "terlewat")


def load_state():
    s = json.loads(STATE.read_text()) if STATE.exists() else {}
    s.setdefault("produk", {}); s.setdefault("error_terkirim", []); s.setdefault("tg_offset", 0)
    return s


def save_state(s):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1, ensure_ascii=False, default=str))


def baca_sheet():
    if not config.SHEET_CSV_URL:
        if not config.DRY_RUN:
            sys.exit("SHEET_CSV_URL belum diisi di GitHub Secrets.")
        return sheet.load(str(ROOT / "contoh_jadwal.csv"))  # contoh hanya untuk uji coba
    return sheet.load(config.SHEET_CSV_URL)


def fmt(dt):
    hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][dt.weekday()]
    return f"{hari} {dt:%d/%m %H:%M}"


def mulai_pratinjau(p):
    if p["format"] == "story":
        return p["waktu"] - timedelta(hours=config.PREVIEW_JAM)
    hh, mm = map(int, config.JAM_PRATINJAU_FEED.split(":"))
    return (p["waktu"] - timedelta(days=1)).replace(hour=hh, minute=mm, second=0)


def tempat(p):
    return "Story Instagram" if p["format"] == "story" else "Feed Instagram & Facebook"


def aktif(p, st):
    """Masih perlu diurus? (belum selesai; batal hanya berlaku untuk isi yang sama)"""
    if p["tunda"] or st.get("status") in SELESAI:
        return False
    return not (st.get("status") == "dibatalkan" and st.get("hash") == p["hash_isi"])


# ---------------------------------------------------------------- tombol Telegram
def terapkan_persetujuan(s, daftar):
    """Terapkan keputusan dari tab Persetujuan (Manajer AI). Kembalikan jumlah perubahan."""
    berubah = 0
    for pid, h, aksi in daftar:
        st = s["produk"].get(pid)
        if not st or st.get("hash") != h or st.get("status") in SELESAI:
            continue  # pratinjau lama (isi sudah berubah) atau sudah selesai
        if aksi == "setuju" and st.get("setuju_hash") != h:
            st.update(setuju_hash=h, status="disetujui"); berubah += 1
        elif aksi == "batal" and st.get("status") != "dibatalkan":
            st.update(status="dibatalkan"); st.pop("setuju_hash", None); berubah += 1
    return berubah


def proses_tombol(s):
    terapkan_persetujuan(s, sheet.load_persetujuan(config.SHEET_CSV_URL))
    hasil, s["tg_offset"] = notify.ambil_tombol(s.get("tg_offset", 0))
    for data, cq in hasil:
        try:
            aksi, pid, h = data.split(":")
        except ValueError:
            continue
        st = s["produk"].get(pid)
        if not st:
            continue
        if st.get("hash") != h or st.get("status") in SELESAI:
            notify.jawab_tombol(cq, "⚠️ Pratinjau ini sudah kedaluwarsa (isinya berubah atau sudah selesai).")
        elif aksi == "ok":
            st.update(setuju_hash=h, status="disetujui")
            notify.jawab_tombol(cq, f"✅ Disetujui — tayang {st.get('waktu_tayang', '')}")
        elif aksi == "no":
            st.update(status="dibatalkan"); st.pop("setuju_hash", None)
            notify.jawab_tombol(cq, "❌ Dibatalkan — tidak akan diposting. Ubah isinya di sheet kalau mau dijadwalkan ulang.")


# ---------------------------------------------------------------- poster & pratinjau
def buat_poster(p, st):
    """Siapkan gambar + render poster. Nama file memuat hash isi supaya tidak kena cache lama."""
    import images, render  # impor berat hanya saat perlu
    WORK.mkdir(exist_ok=True); POSTERS.mkdir(exist_ok=True)
    pakai_gambar = p["format"] == "story" or bool(p["gambar"])  # konten feed: gambar opsional
    img, sumber = None, ""
    if pakai_gambar:
        img = WORK / f"{p['id']}.png"
        dari_sheet = bool(p["gambar"]) and p["gambar"].lower() != "cari"
        # gambar hasil cari otomatis dipakai ulang (supaya sama dengan pratinjau), kecuali sheet memberi link
        url_simpan = None if dari_sheet or st.get("dari_sheet") else st.get("sumber_gambar")
        sumber = images.siapkan(p, url_simpan, str(img))
        st["dari_sheet"] = dari_sheet
    poster = POSTERS / f"{p['id']}-{p['hash_isi']}.jpg"
    render.render(p, str(img) if img else None, str(poster))
    if st.get("poster") and st["poster"] != poster.name:
        (POSTERS / st["poster"]).unlink(missing_ok=True)  # buang versi lama
    st.update(poster=poster.name, sumber_gambar=sumber, hash=p["hash_isi"])
    return poster


def kirim_pratinjau(p, st, poster, diperbarui):
    caption = p["caption"] or config.caption_otomatis(p)
    jam = fmt(p["waktu"]) + (" (jam ramai otomatis)" if p["jam_otomatis"] else "")
    if not p["gambar"] and p["format"] == "story":
        sumber = f'<a href="{st["sumber_gambar"]}">cari otomatis</a>'
    elif p["gambar"]:
        sumber = "cari otomatis" if p["gambar"].lower() == "cari" else "link dari sheet"
    else:
        sumber = "tanpa gambar"
    # 1) poster + caption persis seperti yang akan tayang -> siap diteruskan ke Saluran/Status WA
    notify.foto(str(poster), html.escape(caption))
    judul = "🔄 Pratinjau diperbarui" if diperbarui else "👀 Pratinjau"
    info = (f"{judul}: <b>{html.escape(p['nama'])}</b>\n"
            f"Tayang di {tempat(p)}: {jam} (baris {p['baris']})\nGambar: {sumber}\n\n")
    if p["butuh_setuju"]:
        info += ("❗ Konten ini <b>hanya tayang kalau kamu setujui</b>. Mau ubah? Edit baris di sheet, "
                 "pratinjau baru akan dikirim.\n📲 Untuk Saluran/Status WA: teruskan poster di atas.")
        notify.pesan(info, tombol=[("✅ Setujui", f"ok:{p['id']}:{p['hash_isi']}"),
                                   ("❌ Batalkan", f"no:{p['id']}:{p['hash_isi']}")])
        st["status"] = "menunggu"
        st.pop("setuju_hash", None)
    else:
        info += ("✏️ Salah? Ubah di sheet (isi kolom <i>gambar</i> dengan link lain) atau isi kolom <i>tunda</i> = YA.\n"
                 "📲 Untuk Saluran/Status WA: tekan lama poster di atas → Teruskan/Bagikan → WhatsApp.")
        notify.pesan(info)
        st["status"] = "pratinjau"


def prepare(now=None):
    now = now or datetime.now(TZ)
    s = load_state()
    proses_tombol(s)
    rows, errors = baca_sheet()
    for e in errors:
        if e not in s["error_terkirim"]:
            notify.pesan(f"⚠️ Cek sheet: {e}")
            s["error_terkirim"].append(e)
    antrian = []
    for p in sorted(rows, key=lambda r: r["waktu"]):
        st = s["produk"].setdefault(p["id"], {"nama": p["nama"], "status": "baru", "gagal": 0})
        st["waktu_tayang"] = fmt(p["waktu"])
        if not aktif(p, st) or now < mulai_pratinjau(p):
            continue
        if now - p["waktu"] > timedelta(hours=config.BATAS_TELAT_JAM):
            st["status"] = "terlewat"
            notify.pesan(f"⏭️ <b>{html.escape(p['nama'])}</b> ({fmt(p['waktu'])}) terlewat lebih dari "
                         f"{config.BATAS_TELAT_JAM:g} jam, tidak diposting. Ubah tanggal/jam di sheet kalau mau dijadwalkan ulang.")
            continue
        if st.get("hash") != p["hash_isi"] or not st.get("poster") or not (POSTERS / st["poster"]).exists():
            diperbarui = st["status"] in ("pratinjau", "menunggu", "disetujui", "dibatalkan")
            try:
                poster = buat_poster(p, st)
            except Exception as e:
                traceback.print_exc()
                if st.get("error") != str(e):
                    notify.pesan(f"❌ Poster <b>{html.escape(p['nama'])}</b> gagal dibuat: {html.escape(str(e))}")
                st["error"] = str(e)
                continue
            st.pop("error", None)
            kirim_pratinjau(p, st, poster, diperbarui)
        if now >= p["waktu"]:
            if p["butuh_setuju"] and st.get("setuju_hash") != p["hash_isi"]:
                st["status"] = "terlewat"
                notify.pesan(f"⏹️ <b>{html.escape(p['nama'])}</b> tidak diposting karena belum disetujui sampai jam tayang "
                             f"({fmt(p['waktu'])}). Ubah tanggal/jam di sheet untuk menjadwalkan ulang.")
                continue
            caption = p["caption"] or config.caption_otomatis(p)
            antrian.append({"id": p["id"], "nama": p["nama"], "poster": st["poster"], "caption": caption,
                            "format": p["format"], "kategori": p["kategori"]})
    save_state(s)
    QUEUE.write_text(json.dumps(antrian, indent=1, ensure_ascii=False))
    print(f"{len(rows)} baris dibaca, {len(antrian)} siap diposting")
    return antrian


# ---------------------------------------------------------------- posting
def url_publik(item, st):
    if config.PUBLIC_BASE_URL:  # mode GitHub: poster sudah punya URL publik di repo
        return f"{config.PUBLIC_BASE_URL.rstrip('/')}/posters/{item['poster']}"
    if not st.get("url_gambar_fb"):  # mode laptop: titip foto di Facebook (tidak dipublikasikan)
        _, st["url_gambar_fb"] = meta.post_facebook_file(str(POSTERS / item["poster"]), "", published=False)
    return st["url_gambar_fb"]


def publish():
    s = load_state()
    antrian = json.loads(QUEUE.read_text()) if QUEUE.exists() else []
    meta_siap = all([config.META_PAGE_ID, config.META_PAGE_TOKEN, config.META_IG_USER_ID])
    make_siap = bool(config.MAKE_WEBHOOK_URL)
    for item in antrian:
        st = s["produk"][item["id"]]
        nama = html.escape(item["nama"])
        sorotan = item.get("kategori", "").title() or "Katalog"
        try:
            if item["format"] == "story" and not (meta_siap or config.DRY_RUN):
                # semi-otomatis: kirim poster ke Telegram, kamu yang memposting ke Story IG
                notify.foto(str(POSTERS / item["poster"]),
                            f"⏰ <b>Saatnya posting story: {nama}</b>\n\n1. Tekan lama foto ini → Simpan\n"
                            f"2. Instagram → Story → pilih foto ini → Bagikan\n"
                            f"3. Ketuk <i>Sorot</i> → Sorotan \"{html.escape(sorotan)}\"\n"
                            f"4. Teruskan juga ke Saluran/Status WA")
                st.update(status="terposting", cara="manual", waktu_posting=datetime.now(TZ).isoformat())
            elif item["format"] == "story":
                ig = meta.post_instagram(url_publik(item, st), "", story=True)
                st.update(status="terposting", link_ig=ig, waktu_posting=datetime.now(TZ).isoformat())
                notify.pesan(f"✅ Story <b>{nama}</b> sudah tayang di Instagram.\n\n"
                             f"📌 Jangan lupa masukkan ke Sorotan <b>{html.escape(sorotan)}</b>: buka profil IG → ketuk foto "
                             f"profil (story) → ketuk <i>Sorot</i> → pilih/buat Sorotan \"{html.escape(sorotan)}\".")
            elif meta_siap or (config.DRY_RUN and not make_siap):
                url = url_publik(item, st)
                ig = st.get("link_ig") or meta.post_instagram(url, item["caption"])
                st["link_ig"] = ig  # simpan dulu supaya tidak dobel kalau FB gagal
                save_state(s)
                fb = meta.post_facebook(url, item["caption"])
                st.update(status="terposting", link_fb=fb, waktu_posting=datetime.now(TZ).isoformat())
                notify.pesan(f"✅ <b>{nama}</b> sudah tayang.\nIG: {ig}\nFB: {fb}")
            elif make_siap:
                hasil = meta.post_make(url_publik(item, st), item["caption"])
                st.update(status="terposting", cara="make", waktu_posting=datetime.now(TZ).isoformat())
                notify.pesan(f"✅ <b>{nama}</b> dikirim ke Instagram & Facebook lewat Make.\n{html.escape(hasil)}")
            else:  # belum ada jalur posting feed: beri tahu sekali, jangan dihitung gagal
                if not st.get("info_meta"):
                    notify.pesan(f"ℹ️ <b>{nama}</b> sudah waktunya tayang, tapi jalur posting feed belum diatur "
                                 f"(secret MAKE_WEBHOOK_URL atau META_* kosong). Belum diposting.")
                    st["info_meta"] = True
                    save_state(s)
                continue
        except Exception as e:
            traceback.print_exc()
            st["gagal"] = st.get("gagal", 0) + 1
            if st["gagal"] >= 3:
                st["status"] = "terlewat"
                notify.pesan(f"❌ <b>{nama}</b> gagal diposting 3x, dihentikan.\n{html.escape(str(e))}")
            else:
                notify.pesan(f"⚠️ <b>{nama}</b> gagal diposting (dicoba lagi 15 menit lagi).\n{html.escape(str(e))}")
        save_state(s)
    QUEUE.write_text("[]")


# ---------------------------------------------------------------- cek ringan & tes
def _tulis_output(perlu):
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"perlu={'1' if perlu else '0'}\n")


def cek(now=None):
    """Cek ringan (tanpa Chrome): apakah ada yang perlu dikerjakan? Hasil ditulis ke GITHUB_OUTPUT."""
    now = now or datetime.now(TZ)
    if not config.SHEET_CSV_URL and not config.DRY_RUN:
        print("Belum dikonfigurasi: isi secret SHEET_CSV_URL dulu. Tidak ada yang dikerjakan.")
        _tulis_output(False)
        return False
    s = load_state()
    rows, errors = baca_sheet()
    perlu = any(e not in s["error_terkirim"] for e in errors)
    tombol, _ = notify.ambil_tombol(s.get("tg_offset", 0))  # hanya mengintip, belum dikonfirmasi
    perlu = perlu or bool(tombol)
    salinan = json.loads(json.dumps(s))
    perlu = perlu or terapkan_persetujuan(salinan, sheet.load_persetujuan(config.SHEET_CSV_URL)) > 0
    for p in rows:
        st = s["produk"].get(p["id"], {})
        if not aktif(p, st) or now < mulai_pratinjau(p):
            continue
        if st.get("hash") != p["hash_isi"] or now >= p["waktu"] or st.get("error"):
            perlu = True
    print("perlu kerja:", perlu)
    _tulis_output(perlu)
    return perlu


def tes():
    """Kirim pesan uji ke Telegram dan laporkan secret mana yang sudah/belum diisi."""
    cek_isi = {k: bool(getattr(config, k)) for k in
               ["SHEET_CSV_URL", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "MAKE_WEBHOOK_URL", "MAKE_KUNCI",
                "META_PAGE_ID", "META_PAGE_TOKEN", "META_IG_USER_ID"]}
    daftar = "\n".join(f"{'✅' if v else '⬜'} {k}" for k, v in cek_isi.items())
    if config.SHEET_CSV_URL:
        try:
            rows, errors = sheet.load(config.SHEET_CSV_URL)
            daftar += f"\n\n📄 Sheet terbaca: {len(rows)} jadwal valid"
            daftar += "".join(f"\n⚠️ {e}" for e in errors[:5])
            daftar += "".join(f"\n• {fmt(r['waktu'])} — {r['nama']} ({r['jenis']})"
                              for r in sorted(rows, key=lambda r: r['waktu'])[:8])
        except Exception as e:
            daftar += f"\n\n❌ Sheet gagal dibaca: {e}"
    print(daftar)
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        import requests
        r = requests.post(f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage", timeout=20,
                          data={"chat_id": config.TELEGRAM_CHAT_ID, "text": f"🤖 Bot Annafi Autopost terhubung!\n\nStatus pengaturan:\n{daftar}"})
        print("Telegram:", r.status_code, r.text[:120])
        r.raise_for_status()


def contoh():
    """Kirim contoh poster ke Telegram: story katalog & feed terdekat. Tidak mengubah status, tidak memposting."""
    import images, render
    rows, _ = baca_sheet()
    now = datetime.now(TZ)
    nanti = sorted([r for r in rows if r["waktu"] >= now and not r["tunda"]], key=lambda r: r["waktu"])
    pilih = []
    for f in ("story", "konten"):
        r = next((r for r in nanti if r["format"] == f), None)
        if r: pilih.append(r)
    if not pilih:
        notify.pesan("🧪 Belum ada jadwal mendatang untuk dibuatkan contoh poster."); return
    WORK.mkdir(exist_ok=True)
    for p in pilih:
        try:
            img = None
            if p["format"] == "story" or p["gambar"]:
                img = WORK / f"contoh-{p['id']}.png"
                images.siapkan(p, None, str(img))
            out = WORK / f"contoh-{p['id']}.jpg"
            render.render(p, str(img) if img else None, str(out))
            caption = p["caption"] or config.caption_otomatis(p)
            notify.foto(str(out), html.escape(caption))
            notify.pesan(f"🧪 <b>CONTOH</b> (tidak diposting): {html.escape(p['nama'])}\n"
                         f"Rencana tayang di {tempat(p)}: {fmt(p['waktu'])} (baris {p['baris']})")
        except Exception as e:
            traceback.print_exc()
            notify.pesan(f"⚠️ Contoh poster <b>{html.escape(p['nama'])}</b> gagal dibuat: {html.escape(str(e))[:300]}")


def jalan():
    """Mode laptop (Task Scheduler): cek, lalu kerjakan kalau perlu."""
    if cek():
        prepare()
        publish()


if __name__ == "__main__":
    {"cek": cek, "prepare": prepare, "publish": publish, "jalan": jalan, "tes": tes, "contoh": contoh}[sys.argv[1]]()
