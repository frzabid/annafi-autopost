"""Pengaturan toko & sistem. Ubah di sini kalau ada yang berganti."""
import os
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Jakarta")

TOKO = {
    "wa": "0895-1208-5529",
    "ig": "@annafi_atk_menganti",
    "tiktok": "@annafiatkmenganti",
    "fb": "Annafi Atk Menganti",
}

# Pratinjau dikirim ke Telegram sekian jam sebelum jadwal posting
PREVIEW_JAM = float(os.getenv("PREVIEW_JAM", "2"))
# Kalau jadwal sudah lewat lebih dari ini (misal GitHub sempat mati), jangan diposting, cukup diberi tahu
BATAS_TELAT_JAM = float(os.getenv("BATAS_TELAT_JAM", "3"))

# Caption otomatis kalau kolom caption di sheet kosong
HASHTAG = "#annafiatk #atkmenganti #alattulis #atkmurah #perlengkapansekolah"


def caption_otomatis(p) -> str:
    baris_harga = "\n".join(f"• {h['label']}: {rupiah(h['nilai'])}" for h in p["harga"])
    kat = "".join(ch for ch in p.get("kategori", "").lower() if ch.isalnum())
    tag = HASHTAG + (f" #{kat}" if kat else "")
    detail = f"\n{p['detail']}" if p.get("detail") else ""
    return (f"{p['nama']}{detail}\n\n{baris_harga}\n\n"
            f"Pesan langsung via WhatsApp {TOKO['wa']} 📲\n"
            f"📍 {TOKO['fb']}\n\n{tag}")


def rupiah(n: int) -> str:
    return "Rp" + f"{int(n):,}".replace(",", ".")


# Rahasia (diisi di GitHub → Settings → Secrets and variables → Actions)
SHEET_CSV_URL = os.getenv("SHEET_CSV_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
META_PAGE_ID = os.getenv("META_PAGE_ID", "")
META_PAGE_TOKEN = os.getenv("META_PAGE_TOKEN", "")
META_IG_USER_ID = os.getenv("META_IG_USER_ID", "")
GRAPH_VERSION = os.getenv("GRAPH_VERSION", "v25.0")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")  # opsional, cadangan pencarian gambar

# URL publik folder posters/ (repo publik GitHub), diisi otomatis oleh workflow
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "")

DRY_RUN = os.getenv("DRY_RUN", "") == "1"  # 1 = tidak benar-benar kirim/posting
