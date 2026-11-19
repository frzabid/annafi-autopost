"""Pengaturan toko & sistem. Ubah di sini kalau ada yang berganti."""
import os, pathlib
from zoneinfo import ZoneInfo

# Mode laptop: rahasia disimpan di file .env (di GitHub Actions pakai Secrets)
_env = pathlib.Path(__file__).resolve().parent.parent / ".env"
if _env.exists():
    for _l in _env.read_text(encoding="utf-8").splitlines():
        if "=" in _l and not _l.strip().startswith("#"):
            _k, _v = _l.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"'))

TZ = ZoneInfo("Asia/Jakarta")


def _env(nama: str, default: str = "") -> str:
    """Ambil pengaturan; spasi/Enter yang ikut tertempel di secret dibuang."""
    return (os.getenv(nama) or default).strip()

TOKO = {
    "wa": "0895-1208-5529",
    "ig": "@annafi_atk_menganti",
    "tiktok": "@annafiatkmenganti",
    "fb": "Annafi Atk Menganti",
}

# Pratinjau dikirim ke Telegram sekian jam sebelum jadwal posting
PREVIEW_JAM = float(_env("PREVIEW_JAM", "2"))
# Jam ramai (WIB) dipakai kalau kolom jam di sheet dikosongkan
JAM_STORY = ["07:00", "12:00", "16:00", "19:00"]  # story katalog disebar sepanjang hari
JAM_FEED = ["19:00"]                               # postingan feed: malam hari
# Pratinjau konten feed (edukasi/promo/...) dikirim malam sebelumnya jam segini, dengan tombol setuju
JAM_PRATINJAU_FEED = _env("JAM_PRATINJAU_FEED", "20:00")
# Kalau jadwal sudah lewat lebih dari ini (misal GitHub sempat mati), jangan diposting, cukup diberi tahu
BATAS_TELAT_JAM = float(_env("BATAS_TELAT_JAM", "3"))

# Caption otomatis kalau kolom caption di sheet kosong
HASHTAG = "#annafiatk #atkmenganti #alattulis #atkmurah #perlengkapansekolah"


def caption_otomatis(p) -> str:
    kat = "".join(ch for ch in p.get("kategori", "").lower() if ch.isalnum())
    tag = HASHTAG if MODE_PROMO else HASHTAG.replace(" #atkmurah", "")  # tanpa kesan promo saat mode promo mati
    tag += f" #{kat}" if kat else ""
    bagian = [p["nama"] + (f"\n{p['detail']}" if p.get("detail") else "")]
    if p.get("poin"):
        bagian.append("\n".join(f"✅ {x}" for x in p["poin"]))
    if p.get("harga"):
        bagian.append("\n".join(f"• {h['label']}: {rupiah(h['nilai'])}" for h in p["harga"]))
    bagian.append(f"Pesan langsung via WhatsApp {TOKO['wa']} 📲\n📍 {TOKO['fb']}")
    bagian.append(tag)
    return "\n\n".join(bagian)


def rupiah(n: int) -> str:
    return "Rp" + f"{int(n):,}".replace(",", ".")


# Rahasia (diisi di GitHub → Settings → Secrets and variables → Actions)
SHEET_CSV_URL = _env("SHEET_CSV_URL", "")
TELEGRAM_BOT_TOKEN = _env("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = _env("TELEGRAM_CHAT_ID", "")
META_PAGE_ID = _env("META_PAGE_ID", "")
META_PAGE_TOKEN = _env("META_PAGE_TOKEN", "")
META_IG_USER_ID = _env("META_IG_USER_ID", "")
GRAPH_VERSION = _env("GRAPH_VERSION", "v25.0")
SERPER_API_KEY = _env("SERPER_API_KEY", "")
# Make.com (posting feed IG+FB tanpa akun developer Meta)
MAKE_WEBHOOK_URL = _env("MAKE_WEBHOOK_URL", "")
MAKE_KUNCI = _env("MAKE_KUNCI", "")  # kode rahasia, dicek oleh filter di skenario Make  # opsional, cadangan pencarian gambar

# URL publik folder posters/ (mode GitHub). Kosong = mode laptop: gambar di-host lewat foto Facebook
PUBLIC_BASE_URL = _env("PUBLIC_BASE_URL", "")

CAROUSEL = _env("CAROUSEL", "1") == "1"  # 1 = feed edukasi/info/momen jadi carousel beberapa slide bertema
MODE_PROMO = _env("MODE_PROMO", "0") == "1"  # 0 = feed tanpa harga, baris berjenis promo tidak diproses
DRY_RUN = _env("DRY_RUN", "") == "1"  # 1 = tidak benar-benar kirim/posting
