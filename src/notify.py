"""Kirim pesan & pratinjau poster ke Telegram."""
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DRY_RUN

API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def pesan(teks: str):
    if DRY_RUN or not TELEGRAM_BOT_TOKEN:
        print(f"[TELEGRAM] {teks}")
        return
    requests.post(f"{API}/sendMessage", timeout=20, data={
        "chat_id": TELEGRAM_CHAT_ID, "text": teks, "parse_mode": "HTML", "disable_web_page_preview": True})


def foto(path: str, teks: str):
    if DRY_RUN or not TELEGRAM_BOT_TOKEN:
        print(f"[TELEGRAM FOTO {path}] {teks}")
        return
    with open(path, "rb") as f:
        r = requests.post(f"{API}/sendPhoto", timeout=60, files={"photo": f},
                          data={"chat_id": TELEGRAM_CHAT_ID, "caption": teks[:1024], "parse_mode": "HTML"})
    r.raise_for_status()
