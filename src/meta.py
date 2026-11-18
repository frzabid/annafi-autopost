"""Posting ke Instagram (Graph API, alur container -> publish) dan Facebook Page."""
import time
import requests
from config import GRAPH_VERSION, META_IG_USER_ID, META_PAGE_ID, META_PAGE_TOKEN, DRY_RUN

G = f"https://graph.facebook.com/{GRAPH_VERSION}"


def _cek(r):
    data = r.json()
    if r.status_code >= 400 or "error" in data:
        raise RuntimeError(f"Meta API error: {data.get('error', data)}")
    return data


def post_instagram(image_url: str, caption: str) -> str:
    if DRY_RUN:
        print(f"[IG] {image_url}")
        return "https://instagram.com/p/DRYRUN"
    c = _cek(requests.post(f"{G}/{META_IG_USER_ID}/media", timeout=60, data={
        "image_url": image_url, "caption": caption, "access_token": META_PAGE_TOKEN}))
    cid = c["id"]
    for _ in range(20):  # tunggu Instagram selesai memproses gambar
        s = _cek(requests.get(f"{G}/{cid}", timeout=30, params={"fields": "status_code", "access_token": META_PAGE_TOKEN}))
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            raise RuntimeError("Instagram gagal memproses gambar")
        time.sleep(3)
    pub = _cek(requests.post(f"{G}/{META_IG_USER_ID}/media_publish", timeout=60, data={
        "creation_id": cid, "access_token": META_PAGE_TOKEN}))
    link = _cek(requests.get(f"{G}/{pub['id']}", timeout=30, params={"fields": "permalink", "access_token": META_PAGE_TOKEN}))
    return link.get("permalink", "")


def post_facebook(image_url: str, caption: str) -> str:
    if DRY_RUN:
        print(f"[FB] {image_url}")
        return "https://facebook.com/DRYRUN"
    d = _cek(requests.post(f"{G}/{META_PAGE_ID}/photos", timeout=60, data={
        "url": image_url, "caption": caption, "access_token": META_PAGE_TOKEN}))
    return f"https://facebook.com/{d.get('post_id', d.get('id'))}"
