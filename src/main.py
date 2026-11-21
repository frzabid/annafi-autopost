"""Otomasi konten Annafi ATK.

Jenis konten (kolom `jenis` di sheet):
  katalog                       -> Story Instagram. Pratinjau 2 jam sebelumnya, tayang otomatis
                                   kecuali kolom tunda = YA. Setelah tayang: pengingat Sorotan.
  edukasi / promo / info / momen -> Postingan feed Instagram + Facebook. Pratinjau malam sebelumnya
                                   (20.00) dengan tombol ✅/❌ di Telegram; HANYA tayang kalau disetujui.
  cerita (nama memuat "Part N")  -> Reel cerita bersambung, SEMI-MANUAL: video dirender oleh Claude (workflow cerita.yml).
                                   Bot mengingatkan render (H-2, tombol "Sudah dirender"), lalu di jam tayang mengingatkan
                                   upload + mengirim caption siap salin (tombol "Sudah upload").

  python src/main.py cek       -> cek ringan (tanpa Chrome), apakah ada yang perlu dikerjakan
  python src/main.py prepare   -> proses tombol Telegram, kirim pratinjau, siapkan antrian tayang
  python src/main.py publish   -> posting antrian ke Instagram / Facebook
  python src/main.py tes       -> tes koneksi Telegram & sheet
  python src/main.py contoh    -> kirim contoh poster (1 story + 1 feed terdekat) ke Telegram, tanpa posting
"""
import html, json, os, pathlib, re, sys, traceback
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
    return {"story": "Story Instagram", "reel": "Reels Instagram"}.get(p["format"], "Feed Instagram & Facebook")


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
        if pid[:1] in ("R", "U") and pid[1:] in s["produk"]:  # tombol reel cerita
            st = s["produk"][pid[1:]]
            if st.get("hash") != h or st.get("status") in SELESAI:
                continue
            if aksi == "setuju" and pid[0] == "R" and st.get("status") == "menunggu_render":
                st.update(status="dirender", dirender=True); berubah += 1
                m = re.search(r"part\s*(\d+)", st.get("nama", ""), re.I)
                if m:  # disimpan per part, supaya tetap berlaku kalau jam tayangnya diubah di sheet
                    s.setdefault("reel_dirender", {})[m[1]] = True
            elif aksi == "setuju" and pid[0] == "U":
                st.update(status="terposting", cara="manual", waktu_posting=datetime.now(TZ).isoformat()); berubah += 1
            elif aksi == "batal" and st.get("status") != "dibatalkan":
                st["status"] = "dibatalkan"; berubah += 1
            continue
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
        if pid[:1] in ("R", "U"):
            if terapkan_persetujuan(s, [(pid, h, "setuju" if aksi == "ok" else "batal")]):
                notify.jawab_tombol(cq, "✅ Sudah upload, tercatat." if pid[0] == "U" else
                                    "✅ Video siap. Nanti di jam tayang aku ingatkan upload." if aksi == "ok" else "❌ Dibatalkan.")
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
def pakai_gambar(p):
    """Story katalog selalu mencari foto produk. Feed: hanya kalau kolom gambar berisi link atau "cari: nama produk"
    (judul seperti "Spesial Kado Hari Guru" bukan kata kunci foto yang bisa diandalkan)."""
    g = (p["gambar"] or "").strip().lower()
    return p["format"] == "story" or (bool(g) and g != "cari")


def pakai_carousel(p):
    return p["format"] == "konten" and config.CAROUSEL


def foto_kolase(p, awalan):
    """Foto produk (dari tab Produk) untuk slide kolase carousel, latarnya dihapus. Yang gagal dilewati."""
    import images
    hasil = []
    for k, (nama, link) in enumerate(p.get("foto_produk", [])):
        try:
            path = WORK / f"{awalan}-produk{k}.png"
            images.bersihkan(images.download(link)).save(path)
            hasil.append((nama, str(path)))
        except Exception as e:
            print(f"  foto produk {nama} gagal: {e}")
    return hasil


def buat_carousel(p, st):
    """Feed edukasi/info/momen -> beberapa slide bertema (posters/<id>-<hash>-<n>.jpg)."""
    import carousel
    WORK.mkdir(exist_ok=True); POSTERS.mkdir(exist_ok=True)
    slides = carousel.render(p, str(POSTERS / f"{p['id']}-{p['hash_isi']}"), foto_kolase(p, p["id"]))
    nama = [pathlib.Path(x).name for x in slides]
    for lama in st.get("slides", []) + ([st["poster"]] if st.get("poster") else []):
        if lama not in nama:
            (POSTERS / lama).unlink(missing_ok=True)  # buang versi lama
    st.update(poster=nama[0], slides=nama, sumber_gambar="", hash=p["hash_isi"])
    return POSTERS / nama[0]


def buat_video(p, st):
    """Reel cerita -> posters/<id>-<hash>.mp4 (animasi + suara, dirender dari folder cerita/)."""
    sys.path.insert(0, str(ROOT / "cerita"))
    import episode
    POSTERS.mkdir(exist_ok=True)
    out = POSTERS / f"{p['id']}-{p['hash_isi']}.mp4"
    info = episode.render(p["part"], str(out), arahan=p.get("detail", ""))
    st["adegan"] = info["ringkas"]
    if st.get("poster") and st["poster"] != out.name:
        (POSTERS / st["poster"]).unlink(missing_ok=True)  # buang versi lama
    st.update(poster=out.name, sumber_gambar="", hash=p["hash_isi"])
    st.pop("slides", None)
    return out


def buat_poster(p, st):
    """Siapkan gambar + render poster. Nama file memuat hash isi supaya tidak kena cache lama."""
    if p["format"] == "reel":
        return buat_video(p, st)
    if pakai_carousel(p):
        return buat_carousel(p, st)
    import images, render  # impor berat hanya saat perlu
    WORK.mkdir(exist_ok=True); POSTERS.mkdir(exist_ok=True)
    img, sumber = None, ""
    if pakai_gambar(p):
        img = WORK / f"{p['id']}.png"
        dari_sheet = bool(p["gambar"]) and not p["gambar"].lower().startswith("cari")
        # gambar hasil cari otomatis dipakai ulang (supaya sama dengan pratinjau), kecuali sheet memberi link
        url_simpan = None if dari_sheet or st.get("dari_sheet") else st.get("sumber_gambar")
        try:
            sumber = images.siapkan(p, url_simpan, str(img))
        except images.GambarTidakKetemu as e:  # lebih baik tanpa foto daripada foto yang salah
            print(f"  {e} -> poster tanpa foto")
            img, sumber = None, ""
        st["dari_sheet"] = dari_sheet
    poster = POSTERS / f"{p['id']}-{p['hash_isi']}.jpg"
    render.render(p, str(img) if img else None, str(poster))
    if st.get("poster") and st["poster"] != poster.name:
        (POSTERS / st["poster"]).unlink(missing_ok=True)  # buang versi lama
    st.update(poster=poster.name, sumber_gambar=sumber, hash=p["hash_isi"])
    st.pop("slides", None)
    return poster


def kirim_pratinjau(p, st, poster, diperbarui):
    caption = p["caption"] or config.caption_otomatis(p)
    jam = fmt(p["waktu"]) + (" (jam ramai otomatis)" if p["jam_otomatis"] else "")
    if pakai_gambar(p) and not st.get("sumber_gambar"):
        sumber = ("⚠️ foto yang cocok tidak ketemu, poster dibuat tanpa foto. Mau pakai foto? "
                  "Isi kolom <i>gambar</i> dengan link foto produk.")
    elif pakai_gambar(p) and not st.get("dari_sheet"):
        sumber = f'<a href="{st["sumber_gambar"]}">cari otomatis</a> (salah? isi kolom <i>gambar</i> dengan link foto)'
    elif pakai_gambar(p):
        sumber = "link dari sheet"
    else:
        sumber = "tanpa foto"
    if p["format"] == "reel":
        sumber = (f"video animasi Part {p['part']} (dibuat AI dari naskah)"
                  + (f"\n<i>{html.escape(st.get('adegan', ''))}</i>" if st.get("adegan") else ""))
    if st.get("slides"):
        import tema
        sumber = (f"carousel {len(st['slides'])} slide, tema <b>{tema.TEMA[tema.pilih(p)]['nama']}</b>"
                  + (f", {len(p['foto_produk'])} foto produk" if p.get("foto_produk") else ""))
    # 1) poster + caption persis seperti yang akan tayang -> siap diteruskan ke Saluran/Status WA
    if p["format"] == "reel":
        notify.video(str(poster), html.escape(caption))
    elif st.get("slides"):
        notify.album([str(POSTERS / x) for x in st["slides"]], html.escape(caption))
    else:
        notify.foto(str(poster), html.escape(caption))
    judul = "🔄 Pratinjau diperbarui" if diperbarui else "👀 Pratinjau"
    info = (f"{judul}: <b>{html.escape(p['nama'])}</b>\n"
            f"Tayang di {tempat(p)}: {jam} (baris {p['baris']})\n{'Isi' if p['format'] == 'reel' else 'Gambar'}: {sumber}\n\n")
    if p["butuh_setuju"]:
        info += ("❗ Konten ini <b>hanya tayang kalau kamu setujui</b>. Mau ubah? Edit baris di sheet, "
                 "pratinjau baru akan dikirim.\n📲 Untuk Saluran/Status WA: teruskan "
                 + ("video" if p["format"] == "reel" else "gambar") + " di atas.")
        notify.pesan(info, tombol=[("✅ Setujui", f"ok:{p['id']}:{p['hash_isi']}"),
                                   ("❌ Batalkan", f"no:{p['id']}:{p['hash_isi']}")])
        st["status"] = "menunggu"
        st.pop("setuju_hash", None)
    else:
        info += ("✏️ Salah? Ubah di sheet (isi kolom <i>gambar</i> dengan link lain) atau isi kolom <i>tunda</i> = YA.\n"
                 "📲 Untuk Saluran/Status WA: tekan lama poster di atas → Teruskan/Bagikan → WhatsApp.")
        notify.pesan(info)
        st["status"] = "pratinjau"


def waktu_cek_foto(now):
    """(perlu kirim sekarang?, tanggal besok) — pengingat foto dikirim sekali sehari mulai JAM_CEK_FOTO."""
    h, m = map(int, config.JAM_CEK_FOTO.split(":"))
    besok = (now + timedelta(days=1)).strftime("%d/%m/%Y")
    return now >= now.replace(hour=h, minute=m, second=0, microsecond=0), besok


def cek_foto_besok(s, rows, now, paksa=False):
    """Sehari sebelum tayang: daftar story katalog besok beserta status fotonya, supaya sempat difoto dulu."""
    waktunya, besok = waktu_cek_foto(now)
    if not paksa and (not waktunya or s.get("cek_foto") == besok):
        return
    s["cek_foto"] = besok
    story = [p for p in rows if p["format"] == "story" and p["waktu"].strftime("%d/%m/%Y") == besok
             and aktif(p, s["produk"].get(p["id"], {}))]
    if not story:
        save_state(s)
        return
    import images
    baris, kurang = [], 0
    for p in sorted(story, key=lambda r: r["waktu"]):
        g = (p["gambar"] or "").strip()
        nama = html.escape(p["nama"])
        if g and not g.lower().startswith("cari"):
            baris.append(f"✅ {nama} — foto sendiri")
            continue
        try:  # coba cari foto internet yang cocok (tanpa disimpan) untuk memberi gambaran
            kandidat = [k for k in images.cari_kandidat(p["nama"]) if images.cocok(p["nama"], k["teks"])]
        except Exception as e:
            print(f"  cek foto {p['nama']}: {e}")
            kandidat = []
        kurang += 1
        if kandidat:
            baris.append(f'🔍 {nama} — belum ada foto sendiri; foto internet <a href="{html.escape(kandidat[0]["image"])}">ditemukan</a> (cek benar/tidak)')
        else:
            baris.append(f"⚠️ <b>{nama}</b> — belum ada foto, di internet juga tidak ketemu → poster tanpa foto")
    w = story[0]["waktu"]
    tgl = f"{HARI[w.weekday()]} {w:%d/%m}"
    teks = f"📷 <b>Cek foto story besok ({tgl})</b>\n\n" + "\n".join(baris)
    if kurang:
        teks += ("\n\nSupaya pakai foto asli: kirim foto produknya ke sini dengan <b>caption = nama produk</b> "
                 "(atau unggah ke folder Drive <i>Foto Produk Annafi</i>), paling lambat 2 jam sebelum tayang.")
    else:
        teks += "\n\nSemua sudah punya foto sendiri 👍"
    notify.pesan(teks)
    save_state(s)


def part_siap(p):
    """Reel cerita: apakah animasi part ini sudah dibuat di folder cerita/? (konten lain selalu True)"""
    if p["format"] != "reel":
        return True
    sys.path.insert(0, str(ROOT / "cerita"))
    import episode
    return p["part"] in episode.PART and bool(config.GEMINI_API_KEY)


def langkah_reel(p, st, now):
    """Pengingat reel cerita yang perlu dikirim sekarang (tanpa efek samping): render1/render2/upload1 (2 jam sebelum)/lewat/None."""
    if st.get("hash") != p["hash_isi"]:
        st = {"status": "baru"}
    status = st.get("status", "baru")
    mulai = p["waktu"] - timedelta(days=config.REEL_INGAT_HARI)
    # upload manual: pengingat (+ caption & sampul) dikirim 2 jam sebelum jadwal
    if status in ("baru", "menunggu_render", "dirender") and now >= p["waktu"] - timedelta(hours=config.REEL_INGAT_UPLOAD_JAM):
        return "upload1"
    if status == "menunggu_upload":
        if now - p["waktu"] > timedelta(hours=24):
            return "lewat"
        return None
    if status == "baru" and now >= mulai:
        return "render1"
    if (status == "menunggu_render" and not st.get("ingat_render2") and now >= mulai_pratinjau(p)
            and st.get("ingat_render", "") < mulai_pratinjau(p).isoformat()):
        return "render2"
    return None


s_global = {}


def urus_reel(p, st, now):
    """Reel cerita semi-manual: pengingat render (Claude yang merender) & pengingat upload + caption siap salin."""
    if st.get("hash") != p["hash_isi"]:  # baris baru / isinya berubah -> mulai dari awal
        for k in ("ingat_render", "ingat_render2", "ingat_upload2", "setuju_hash", "poster", "slides", "dirender"):
            st.pop(k, None)
        st.update(hash=p["hash_isi"], status="baru")
    if st.get("status") in ("baru", "menunggu_render") and s_global.get("reel_dirender", {}).get(str(p["part"])):
        st.update(status="dirender", dirender=True)  # video part ini sudah ditandai siap (mis. jamnya baru diubah)
    langkah = langkah_reel(p, st, now)
    nama, jam = html.escape(p["nama"]), fmt(p["waktu"])
    h, pid = p["hash_isi"], p["id"]
    if langkah in ("render1", "render2"):
        ulang = "🔁 Pengingat lagi: " if langkah == "render2" else ""
        notify.pesan(f"🎬 {ulang}<b>{nama}</b> dijadwalkan tayang di Reels Instagram <b>{jam}</b>.\n\n"
                     f"Saatnya render videonya: minta Claude <i>render part {p['part']}</i> (±10 menit, videonya masuk ke sini).\n"
                     "Kalau videonya sudah siap, tekan <b>Sudah dirender</b>.",
                     tombol=[("✅ Sudah dirender", f"ok:R{pid}:{h}"), ("❌ Batalkan", f"no:R{pid}:{h}")])
        st["status"] = "menunggu_render"
        st["ingat_render2" if langkah == "render2" else "ingat_render"] = now.isoformat()
    elif langkah in ("upload1", "upload2"):
        caption = p["caption"] or config.caption_otomatis(p)
        siap = st.get("dirender") or s_global.get("reel_dirender", {}).get(str(p["part"]))
        video = ROOT / "cerita" / "contoh" / f"misteri_part{p['part']}.mp4"
        if langkah == "upload1" and siap and config.MAKE_REEL and config.MAKE_WEBHOOK_URL and video.exists():
            repo, sha = os.getenv("GITHUB_REPOSITORY"), os.getenv("GITHUB_SHA")
            # jsDelivr menyajikan mp4 sebagai video/mp4 (raw GitHub = octet-stream); @sha supaya tidak kena cache lama
            url = (f"https://cdn.jsdelivr.net/gh/{repo}@{sha}/cerita/contoh/{video.name}" if repo and sha
                   else f"{config.PUBLIC_BASE_URL.rstrip('/')}/cerita/contoh/{video.name}")
            try:
                meta.post_make_reel(url, caption)
                st.update(status="terposting", cara="make", waktu_posting=now.isoformat())
                notify.pesan(f"✅ Reel <b>{nama}</b> dikirim ke Instagram lewat Make (video diproses IG, tayang beberapa menit lagi).\n"
                             "📲 Bagikan juga ke Story/Status WA supaya pengikut tahu part baru sudah keluar.")
                return
            except Exception as e:
                traceback.print_exc()
                notify.pesan(f"⚠️ Upload otomatis <b>{nama}</b> lewat Make gagal: {html.escape(str(e))[:200]}\nUpload manual ya 👇")
        belum = "" if siap else "\n⚠️ Video belum ditandai <i>sudah dirender</i>."
        if langkah == "upload1":
            sampul = video.with_name(video.stem + "-sampul.jpg")
            if sampul.exists():
                notify.foto(str(sampul), "🖼️ Sampul reel: saat upload pilih <b>Edit sampul → Tambahkan dari galeri</b>")
            notify.pesan(f"<pre>{html.escape(caption)}</pre>")
        belum = ("\n⚠️ <b>Video belum ditandai sudah dirender</b> — minta Claude <i>render part "
                 f"{p['part']}</i> sekarang (±10 menit).") if not siap else "\n✅ Video sudah dirender."
        notify.pesan(f"⏰ <b>2 jam lagi</b> jadwal upload <b>{nama}</b> ke Reels Instagram ({jam}).{belum}\n\n"
                     "Saat upload: Instagram → + → Reel → pilih videonya → <b>Edit sampul → Tambahkan dari galeri</b> (gambar di atas) "
                     "→ salin caption di atas (ketuk kotaknya) → Bagikan. Bagikan juga ke Story/Status WA.\n"
                     "Sudah? Tekan <b>Sudah upload</b>.",
                     tombol=[("✅ Sudah upload", f"ok:U{pid}:{h}")])
        if langkah == "upload1":
            st["status"] = "menunggu_upload"
        else:
            st["ingat_upload2"] = now.isoformat()
    elif langkah == "lewat":
        st["status"] = "terlewat"
        notify.pesan(f"⏭️ <b>{nama}</b> ({jam}) belum ditandai sudah upload setelah 24 jam, pengingat dihentikan. "
                     "Ubah tanggal di sheet kalau mau dijadwalkan ulang.")


HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def proses_permintaan(s):
    """Contoh poster yang diminta lewat chat bot (tab Permintaan) -> render -> kirim ke Telegram. Tidak memposting."""
    if not config.SHEET_CSV_URL:
        return
    selesai = s.setdefault("permintaan", [])
    for pid, data in sheet.load_permintaan(config.SHEET_CSV_URL):
        if pid in selesai:
            continue
        selesai.append(pid)
        del selesai[:-200]
        save_state(s)  # tandai dulu supaya tidak diulang kalau render gagal
        p, err = sheet.baris_dari_dict(data, config.SHEET_CSV_URL)
        if not p:
            notify.pesan(f"⚠️ Contoh <b>{html.escape(data.get('nama', '?'))}</b> tidak bisa dibuat: {html.escape('; '.join(err))[:300]}")
            continue
        try:
            kirim_contoh(p, judul="🎨 <b>CONTOH SESUAI PERMINTAAN</b> (tidak diposting)",
                         penutup="Mau dijadwalkan? Balas misalnya: <i>jadwalkan yang tadi hari Sabtu jam 7 malam</i>.")
        except Exception as e:
            traceback.print_exc()
            notify.pesan(f"⚠️ Contoh <b>{html.escape(p['nama'])}</b> gagal dibuat: {html.escape(str(e))[:300]}")


def kirim_contoh(p, judul, penutup=""):
    """Render poster/carousel ke folder kerja dan kirim ke Telegram (tanpa mengubah status jadwal)."""
    WORK.mkdir(exist_ok=True)
    caption = p["caption"] or config.caption_otomatis(p)
    if p["format"] == "reel":
        sys.path.insert(0, str(ROOT / "cerita"))
        import episode
        out = WORK / f"contoh-{p['id']}.mp4"
        notify.pesan(f"🎬 Mulai membuat <b>{html.escape(p['nama'])}</b>: AI menyusun adegan dari naskah, lalu animasi & suara "
                     "dirender (±5-8 menit)…")
        info = episode.render(p["part"], str(out), arahan=p.get("detail", ""))
        notify.video(str(out), html.escape(caption))
        notify.pesan(f"{judul}: {html.escape(p['nama'])}\nAdegan:\n<i>{html.escape(info['ringkas'])}</i>"
                     + (f"\nArahan: {html.escape(p['detail'])}" if p.get("detail") else "")
                     + "\n\nKurang pas? Balas misalnya: <i>ulang part 1, Raka lebih panik dan adegan surat lebih lama</i>."
                     + (f"\n{penutup}" if penutup else ""))
        return
    import images, render
    if pakai_carousel(p):
        import carousel, tema
        slides = carousel.render(p, str(WORK / f"contoh-{p['id']}"), foto_kolase(p, f"contoh-{p['id']}"))
        notify.album(slides, html.escape(caption))
        info = (f"{len(slides)} slide · tema <b>{tema.TEMA[tema.pilih(p)]['nama']}</b>"
                + (f" · {len(p['foto_produk'])} foto produk" if p.get("foto_produk") else ""))
    else:
        img, info = None, ""
        if pakai_gambar(p):
            img = WORK / f"contoh-{p['id']}.png"
            try:
                info = "Foto: " + html.escape(images.siapkan(p, None, str(img))[:150])
            except images.GambarTidakKetemu as e:
                img, info = None, f"⚠️ {html.escape(str(e))} Poster dibuat tanpa foto."
        out = WORK / f"contoh-{p['id']}.jpg"
        render.render(p, str(img) if img else None, str(out))
        notify.foto(str(out), html.escape(caption))
    notify.pesan(f"{judul}: {html.escape(p['nama'])}\n{info}" + (f"\n{penutup}" if penutup else ""))


def prepare(now=None):
    now = now or datetime.now(TZ)
    s = load_state()
    proses_tombol(s)
    proses_permintaan(s)
    rows, errors = baca_sheet()
    try:
        cek_foto_besok(s, rows, now)
    except Exception:
        traceback.print_exc()
    for e in errors:
        if e not in s["error_terkirim"]:
            notify.pesan(f"⚠️ Cek sheet: {e}")
            s["error_terkirim"].append(e)
    antrian = []
    s_global.clear(); s_global.update(reel_dirender=s.setdefault("reel_dirender", {}))
    cerita = {r["part"]: r for r in rows if r["format"] == "reel" and not r["tunda"]}
    for r in cerita.values():  # untuk caption: kapan part berikutnya tayang / part terakhir
        nxt = cerita.get(r["part"] + 1)
        r["berikut"] = nxt["waktu"] if nxt and nxt["waktu"] > r["waktu"] else None
        r["terakhir"] = r["part"] == 8
    for p in sorted(rows, key=lambda r: r["waktu"]):
        st = s["produk"].setdefault(p["id"], {"nama": p["nama"], "status": "baru", "gagal": 0})
        st["waktu_tayang"] = fmt(p["waktu"])
        if p["format"] == "reel":
            if not p["tunda"] and (st.get("hash") != p["hash_isi"] or st.get("status") not in SELESAI + ("dibatalkan",)):
                urus_reel(p, st, now)
            continue
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
                            "slides": st.get("slides") or [st["poster"]],
                            "format": p["format"], "kategori": p["kategori"]})
    save_state(s)
    QUEUE.write_text(json.dumps(antrian, indent=1, ensure_ascii=False))
    print(f"{len(rows)} baris dibaca, {len(antrian)} siap diposting")
    return antrian


# ---------------------------------------------------------------- posting
def url_slides(item, st):
    """URL publik semua slide (mode GitHub). Mode laptop: carousel belum didukung, pakai slide pertama."""
    if config.PUBLIC_BASE_URL:
        return [f"{config.PUBLIC_BASE_URL.rstrip('/')}/posters/{x}" for x in item.get("slides") or [item["poster"]]]
    return [url_publik(item, st)]


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
            if item["format"] == "reel" and make_siap and config.MAKE_REEL:
                meta.post_make_reel(url_publik(item, st), item["caption"])
                st.update(status="terposting", cara="make", waktu_posting=datetime.now(TZ).isoformat())
                notify.pesan(f"✅ Reel <b>{nama}</b> dikirim ke Instagram (video diproses IG, tayang beberapa menit lagi).\n\n"
                             f"📲 Bagikan juga ke Story/Status WA supaya pengikut tahu part baru sudah keluar.")
            elif item["format"] == "reel":
                # posting Reel lewat Make belum dinyalakan -> kirim videonya, kamu yang mengunggah
                notify.video(str(POSTERS / item["poster"]),
                             f"⏰ <b>Saatnya posting reel: {nama}</b>\n\n1. Tekan lama video ini → Simpan\n"
                             f"2. Instagram → + → Reel → pilih video ini\n3. Tempel caption di bawah → Bagikan")
                notify.pesan(html.escape(item["caption"]))
                st.update(status="terposting", cara="manual", waktu_posting=datetime.now(TZ).isoformat())
            elif item["format"] == "story" and not (meta_siap or config.DRY_RUN):
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
                urls = url_slides(item, st)
                ig = st.get("link_ig") or meta.post_instagram_carousel(urls, item["caption"])
                st["link_ig"] = ig  # simpan dulu supaya tidak dobel kalau FB gagal
                save_state(s)
                fb = meta.post_facebook_album(urls, item["caption"])
                st.update(status="terposting", link_fb=fb, waktu_posting=datetime.now(TZ).isoformat())
                notify.pesan(f"✅ <b>{nama}</b> sudah tayang.\nIG: {ig}\nFB: {fb}")
            elif make_siap:
                urls = url_slides(item, st)
                hasil = meta.post_make(urls[0], item["caption"], urls)
                st.update(status="terposting", cara="make", waktu_posting=datetime.now(TZ).isoformat())
                link_ig = f"https://www.instagram.com/{config.TOKO['ig'].lstrip('@')}/"
                notify.pesan(f"✅ <b>{nama}</b> dikirim ke Instagram (tayang ±1 menit lagi).\n\n"
                             f"📲 <b>Bagikan ke Facebook</b> (profil Annafi Atk Menganti tidak bisa otomatis):\n"
                             f"buka postingannya di {link_ig} → ketuk <b>Bagikan ke Facebook</b> di bawah foto.")
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
    waktunya, besok = waktu_cek_foto(now)
    perlu = perlu or (waktunya and s.get("cek_foto") != besok)  # pengingat foto story besok
    if config.SHEET_CSV_URL:  # contoh poster yang diminta lewat chat bot
        perlu = perlu or any(pid not in s.get("permintaan", []) for pid, _ in sheet.load_permintaan(config.SHEET_CSV_URL))
    for p in rows:
        st = s["produk"].get(p["id"], {})
        if p["format"] == "reel":
            if not p["tunda"] and (st.get("hash") != p["hash_isi"] or st.get("status") not in SELESAI + ("dibatalkan",)):
                perlu = perlu or bool(langkah_reel(p, st, now))
            continue
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
        if pakai_carousel(p):
            try:
                import carousel, tema
                slides = carousel.render(p, str(WORK / f"contoh-{p['id']}"), foto_kolase(p, f"contoh-{p['id']}"))
                notify.album(slides, html.escape(p["caption"] or config.caption_otomatis(p)))
                notify.pesan(f"🧪 <b>CONTOH CAROUSEL</b> (tidak diposting): {html.escape(p['nama'])}\n"
                             f"{len(slides)} slide · tema <b>{tema.TEMA[tema.pilih(p)]['nama']}</b>"
                             + (f" · {len(p['foto_produk'])} foto produk" if p.get("foto_produk") else "")
                             + f"\nRencana tayang di {tempat(p)}: {fmt(p['waktu'])} (baris {p['baris']})\n"
                             "Tema bisa diganti lewat kolom <i>tema</i> di sheet.")
            except Exception as e:
                traceback.print_exc()
                notify.pesan(f"⚠️ Contoh carousel <b>{html.escape(p['nama'])}</b> gagal dibuat: {html.escape(str(e))[:300]}")
            continue
        try:
            img, catatan = None, ""
            if pakai_gambar(p):
                img = WORK / f"contoh-{p['id']}.png"
                try:
                    catatan = "Foto: " + images.siapkan(p, None, str(img))[:150]
                except images.GambarTidakKetemu as e:
                    img, catatan = None, f"⚠️ {e} Poster dibuat tanpa foto."
            out = WORK / f"contoh-{p['id']}.jpg"
            render.render(p, str(img) if img else None, str(out))
            caption = p["caption"] or config.caption_otomatis(p)
            notify.foto(str(out), html.escape(caption))
            notify.pesan(f"🧪 <b>CONTOH</b> (tidak diposting): {html.escape(p['nama'])}\n"
                         f"Rencana tayang di {tempat(p)}: {fmt(p['waktu'])} (baris {p['baris']})\n{html.escape(catatan)}")
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
