"""Otomasi posting katalog Annafi ATK.

  python src/main.py prepare   -> baca sheet, kirim pratinjau ke Telegram, siapkan poster yang jatuh tempo
  python src/main.py publish   -> posting poster yang jatuh tempo ke Instagram + Facebook

Workflow GitHub Actions menjalankan keduanya tiap 15 menit (commit poster di antaranya
supaya poster punya URL publik yang bisa diambil Instagram).
"""
import json, pathlib, sys, traceback
from datetime import datetime, timedelta
import config, meta, notify, sheet
from config import TZ

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "state.json"
QUEUE = ROOT / "state" / "queue.json"
POSTERS = ROOT / "posters"
WORK = ROOT / ".work"


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"produk": {}, "error_terkirim": []}


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


def buat_poster(p, st):
    """Siapkan gambar + render poster. Nama file memuat hash isi supaya tidak kena cache lama."""
    import images, render  # impor berat hanya saat perlu
    WORK.mkdir(exist_ok=True); POSTERS.mkdir(exist_ok=True)
    img = WORK / f"{p['id']}.png"
    # gambar hasil cari otomatis dipakai ulang (supaya sama dengan pratinjau), kecuali sheet memberi link
    url_simpan = None if p["gambar"] or st.get("dari_sheet") else st.get("sumber_gambar")
    sumber = images.siapkan(p, url_simpan, str(img))
    st["dari_sheet"] = bool(p["gambar"])
    poster = POSTERS / f"{p['id']}-{p['hash_isi']}.jpg"
    render.render(p, str(img), str(poster))
    if st.get("poster") and st["poster"] != poster.name:
        (POSTERS / st["poster"]).unlink(missing_ok=True)  # buang versi lama
    st.update(poster=poster.name, sumber_gambar=sumber, hash=p["hash_isi"])
    return poster


def prepare(now=None):
    now = now or datetime.now(TZ)
    s = load_state()
    rows, errors = baca_sheet()
    for e in errors:
        if e not in s["error_terkirim"]:
            notify.pesan(f"⚠️ Cek sheet: {e}")
            s["error_terkirim"].append(e)
    antrian = []
    for p in sorted(rows, key=lambda r: r["waktu"]):
        st = s["produk"].setdefault(p["id"], {"nama": p["nama"], "status": "baru", "gagal": 0})
        if st["status"] in ("terposting", "terlewat") or p["tunda"]:
            continue
        if now < p["waktu"] - timedelta(hours=config.PREVIEW_JAM):
            continue
        if now - p["waktu"] > timedelta(hours=config.BATAS_TELAT_JAM):
            st["status"] = "terlewat"
            notify.pesan(f"⏭️ <b>{p['nama']}</b> ({fmt(p['waktu'])}) terlewat lebih dari "
                         f"{config.BATAS_TELAT_JAM:g} jam, tidak diposting. Ubah tanggal/jam di sheet kalau mau dijadwalkan ulang.")
            continue
        perlu_render = st.get("hash") != p["hash_isi"] or not st.get("poster") \
            or not (POSTERS / st["poster"]).exists()
        if perlu_render:
            try:
                poster = buat_poster(p, st)
            except Exception as e:
                if st.get("error") != str(e):
                    notify.pesan(f"❌ Poster <b>{p['nama']}</b> gagal dibuat: {e}")
                st["error"] = str(e)
                continue
            st.pop("error", None)
            judul = "🔄 Pratinjau diperbarui" if st["status"] == "pratinjau" else "👀 Pratinjau"
            sumber = "link dari sheet" if p["gambar"] else f'<a href="{st["sumber_gambar"]}">cari otomatis</a>'
            notify.foto(str(poster),
                        f"{judul}: <b>{p['nama']}</b>\nTayang: {fmt(p['waktu'])} (baris {p['baris']})\n"
                        f"Gambar: {sumber}\n\nSalah? Ubah di sheet (isi kolom <i>gambar</i> dengan link lain), "
                        f"atau isi kolom <i>tunda</i> dengan YA.")
            st["status"] = "pratinjau"
        if now >= p["waktu"]:
            caption = p["caption"] or config.caption_otomatis(p)
            antrian.append({"id": p["id"], "nama": p["nama"], "poster": st["poster"], "caption": caption})
    save_state(s)
    QUEUE.write_text(json.dumps(antrian, indent=1, ensure_ascii=False))
    print(f"{len(rows)} baris dibaca, {len(antrian)} siap diposting")
    return antrian


def publish():
    s = load_state()
    antrian = json.loads(QUEUE.read_text()) if QUEUE.exists() else []
    meta_siap = all([config.META_PAGE_ID, config.META_PAGE_TOKEN, config.META_IG_USER_ID]) or config.DRY_RUN
    for item in antrian:
        st = s["produk"][item["id"]]
        if not meta_siap:  # belum diatur: jangan hitung sebagai gagal, cukup beri tahu sekali
            if not st.get("info_meta"):
                notify.pesan(f"ℹ️ <b>{item['nama']}</b> sudah waktunya tayang, tapi akun Instagram/Facebook "
                             f"belum dihubungkan (secret META_* kosong). Belum diposting.")
                st["info_meta"] = True
                save_state(s)
            continue
        try:
            if config.PUBLIC_BASE_URL:  # mode GitHub: poster sudah punya URL publik di repo
                url = f"{config.PUBLIC_BASE_URL.rstrip('/')}/posters/{item['poster']}"
                ig = st.get("link_ig") or meta.post_instagram(url, item["caption"])
                st["link_ig"] = ig  # simpan dulu supaya tidak dobel kalau FB gagal
                fb = st.get("link_fb") or meta.post_facebook(url, item["caption"])
            else:  # mode laptop: unggah ke Facebook dulu, URL fotonya dipakai Instagram
                if not st.get("url_gambar_fb"):
                    st["link_fb"], st["url_gambar_fb"] = meta.post_facebook_file(str(POSTERS / item["poster"]), item["caption"])
                    save_state(s)
                fb = st["link_fb"]
                ig = meta.post_instagram(st["url_gambar_fb"], item["caption"])
                st["link_ig"] = ig
            st.update(status="terposting", link_fb=fb, waktu_posting=datetime.now(TZ).isoformat())
            notify.pesan(f"✅ <b>{item['nama']}</b> sudah tayang.\nIG: {ig}\nFB: {fb}")
        except Exception as e:
            traceback.print_exc()
            st["gagal"] = st.get("gagal", 0) + 1
            if st["gagal"] >= 3:
                st["status"] = "terlewat"
                notify.pesan(f"❌ <b>{item['nama']}</b> gagal diposting 3x, dihentikan.\n{e}")
            else:
                notify.pesan(f"⚠️ <b>{item['nama']}</b> gagal diposting (dicoba lagi 15 menit lagi).\n{e}")
        save_state(s)
    QUEUE.write_text("[]")


def cek(now=None):
    """Cek ringan (tanpa Chrome): apakah ada yang perlu dikerjakan? Hasil ditulis ke GITHUB_OUTPUT."""
    import os
    now = now or datetime.now(TZ)
    if not config.SHEET_CSV_URL and not config.DRY_RUN:
        print("Belum dikonfigurasi: isi secret SHEET_CSV_URL dulu. Tidak ada yang dikerjakan.")
        perlu = False
        if os.getenv("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write("perlu=0\n")
        return perlu
    s = load_state()
    rows, errors = baca_sheet()
    perlu = any(e not in s["error_terkirim"] for e in errors)
    for p in rows:
        st = s["produk"].get(p["id"], {})
        if p["tunda"] or st.get("status") in ("terposting", "terlewat"):
            continue
        if now >= p["waktu"] - timedelta(hours=config.PREVIEW_JAM) and (
                st.get("hash") != p["hash_isi"] or now >= p["waktu"] or st.get("error")):
            perlu = True
    print("perlu kerja:", perlu)
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"perlu={'1' if perlu else '0'}\n")
    return perlu


def tes():
    """Kirim pesan uji ke Telegram dan laporkan secret mana yang sudah/belum diisi."""
    cek_isi = {k: bool(getattr(config, k)) for k in
               ["SHEET_CSV_URL", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "META_PAGE_ID", "META_PAGE_TOKEN", "META_IG_USER_ID"]}
    daftar = "\n".join(f"{'✅' if v else '⬜'} {k}" for k, v in cek_isi.items())
    if config.SHEET_CSV_URL:
        try:
            rows, errors = sheet.load(config.SHEET_CSV_URL)
            daftar += f"\n\n📄 Sheet terbaca: {len(rows)} jadwal valid"
            daftar += "".join(f"\n⚠️ {e}" for e in errors[:5])
            daftar += "".join(f"\n• {fmt(r['waktu'])} — {r['nama']}" for r in sorted(rows, key=lambda r: r['waktu'])[:5])
        except Exception as e:
            daftar += f"\n\n❌ Sheet gagal dibaca: {e}"
    print(daftar)
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        import requests
        r = requests.post(f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage", timeout=20,
                          data={"chat_id": config.TELEGRAM_CHAT_ID, "text": f"🤖 Bot Annafi Autopost terhubung!\n\nStatus pengaturan:\n{daftar}"})
        print("Telegram:", r.status_code, r.text[:300])
        r.raise_for_status()


def jalan():
    """Mode laptop (Task Scheduler): cek, lalu kerjakan kalau perlu."""
    if cek():
        prepare()
        publish()


if __name__ == "__main__":
    {"cek": cek, "prepare": prepare, "publish": publish, "jalan": jalan, "tes": tes}[sys.argv[1]]()
