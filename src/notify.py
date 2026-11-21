"""Telegram: kirim pesan/pratinjau, tombol setuju/batal, dan baca jawaban tombol."""
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DRY_RUN

API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
_AKTIF = bool(TELEGRAM_BOT_TOKEN) and not DRY_RUN


def _tombol(tombol):
    import json
    return json.dumps({"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in tombol]]})


def pesan(teks: str, tombol=None):
    if not _AKTIF:
        print(f"[TELEGRAM] {teks}" + (f"  [tombol: {', '.join(t for t, _ in tombol)}]" if tombol else ""))
        return
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": teks, "parse_mode": "HTML", "disable_web_page_preview": True}
    if tombol:
        data["reply_markup"] = _tombol(tombol)
    requests.post(f"{API}/sendMessage", timeout=20, data=data).raise_for_status()


def foto(path: str, teks: str):
    if not _AKTIF:
        print(f"[TELEGRAM FOTO {path}] {teks}")
        return
    with open(path, "rb") as f:
        r = requests.post(f"{API}/sendPhoto", timeout=60, files={"photo": f},
                          data={"chat_id": TELEGRAM_CHAT_ID, "caption": teks[:1024], "parse_mode": "HTML"})
    r.raise_for_status()


def video(path: str, teks: str):
    if not _AKTIF:
        print(f"[TELEGRAM VIDEO {path}] {teks}")
        return
    with open(path, "rb") as f:
        r = requests.post(f"{API}/sendVideo", timeout=180, files={"video": f},
                          data={"chat_id": TELEGRAM_CHAT_ID, "caption": teks[:1024], "parse_mode": "HTML",
                                "supports_streaming": "true", "width": 1080, "height": 1920})
    r.raise_for_status()


def album(paths: list[str], teks: str):
    """Kirim beberapa gambar sebagai satu album (pratinjau carousel). Caption di gambar pertama."""
    if len(paths) == 1:
        return foto(paths[0], teks)
    if not _AKTIF:
        print(f"[TELEGRAM ALBUM {len(paths)} slide] {teks}")
        return
    import json
    media, files = [], {}
    for i, path in enumerate(paths[:10]):
        m = {"type": "photo", "media": f"attach://f{i}"}
        if i == 0:
            m.update(caption=teks[:1024], parse_mode="HTML")
        media.append(m)
        files[f"f{i}"] = open(path, "rb")
    try:
        r = requests.post(f"{API}/sendMediaGroup", timeout=120, files=files,
                          data={"chat_id": TELEGRAM_CHAT_ID, "media": json.dumps(media)})
        r.raise_for_status()
    finally:
        for f in files.values():
            f.close()


def ambil_tombol(offset: int):
    """Ambil tombol yang ditekan sejak offset. Kembalikan (daftar (data, callback), offset_baru)."""
    if not _AKTIF:
        return [], offset
    r = requests.get(f"{API}/getUpdates", timeout=30,
                     params={"offset": offset, "timeout": 0, "allowed_updates": '["callback_query"]'})
    if r.status_code == 409:  # webhook Manajer AI aktif -> persetujuan dibaca dari tab Persetujuan
        return [], offset
    r.raise_for_status()
    hasil, baru = [], offset
    for u in r.json().get("result", []):
        baru = max(baru, u["update_id"] + 1)
        cq = u.get("callback_query")
        if cq and str(cq.get("message", {}).get("chat", {}).get("id")) == str(TELEGRAM_CHAT_ID):
            hasil.append((cq.get("data", ""), cq))
    return hasil, baru


def jawab_tombol(cq: dict, status: str):
    """Tandai pesan pratinjau (hapus tombol, tambah status di bawahnya)."""
    if not _AKTIF:
        print(f"[TELEGRAM jawab] {status}")
        return
    try:
        requests.post(f"{API}/answerCallbackQuery", timeout=15, data={"callback_query_id": cq["id"], "text": status})
    except Exception:
        pass  # tombol yang ditekan lama sebelumnya tidak bisa dijawab lagi; tidak masalah
    msg = cq.get("message", {})
    try:
        requests.post(f"{API}/editMessageText", timeout=15, data={
            "chat_id": msg["chat"]["id"], "message_id": msg["message_id"],
            "text": f"{msg.get('text', '')}\n\n{status}", "disable_web_page_preview": True})
    except Exception:
        pass
