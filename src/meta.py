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


def post_instagram(image_url: str, caption: str, story: bool = False) -> str:
    """Feed (dengan caption) atau Story (media_type=STORIES, story tidak memakai caption)."""
    if DRY_RUN:
        print(f"[IG {'STORY' if story else 'FEED'}] {image_url}")
        return "https://instagram.com/stories/DRYRUN" if story else "https://instagram.com/p/DRYRUN"
    data = {"image_url": image_url, "access_token": META_PAGE_TOKEN}
    data.update({"media_type": "STORIES"} if story else {"caption": caption})
    c = _cek(requests.post(f"{G}/{META_IG_USER_ID}/media", timeout=60, data=data))
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


def _tunggu(cid):
    for _ in range(20):  # tunggu Instagram selesai memproses gambar
        s = _cek(requests.get(f"{G}/{cid}", timeout=30, params={"fields": "status_code", "access_token": META_PAGE_TOKEN}))
        if s.get("status_code") == "FINISHED":
            return
        if s.get("status_code") == "ERROR":
            raise RuntimeError("Instagram gagal memproses gambar")
        time.sleep(3)


def post_instagram_carousel(image_urls: list[str], caption: str) -> str:
    """Carousel feed Instagram (2-10 gambar): container per gambar -> container CAROUSEL -> publish."""
    if len(image_urls) == 1:
        return post_instagram(image_urls[0], caption)
    if DRY_RUN:
        print(f"[IG CAROUSEL {len(image_urls)}] {image_urls[0]}")
        return "https://instagram.com/p/DRYRUN"
    anak = []
    for url in image_urls[:10]:
        c = _cek(requests.post(f"{G}/{META_IG_USER_ID}/media", timeout=60, data={
            "image_url": url, "is_carousel_item": "true", "access_token": META_PAGE_TOKEN}))
        _tunggu(c["id"])
        anak.append(c["id"])
    c = _cek(requests.post(f"{G}/{META_IG_USER_ID}/media", timeout=60, data={
        "media_type": "CAROUSEL", "children": ",".join(anak), "caption": caption, "access_token": META_PAGE_TOKEN}))
    _tunggu(c["id"])
    pub = _cek(requests.post(f"{G}/{META_IG_USER_ID}/media_publish", timeout=60, data={
        "creation_id": c["id"], "access_token": META_PAGE_TOKEN}))
    link = _cek(requests.get(f"{G}/{pub['id']}", timeout=30, params={"fields": "permalink", "access_token": META_PAGE_TOKEN}))
    return link.get("permalink", "")


def post_facebook_album(image_urls: list[str], caption: str) -> str:
    """Postingan Facebook Page berisi beberapa foto (unggah tanpa terbit dulu, lalu satukan di satu post)."""
    if len(image_urls) == 1:
        return post_facebook(image_urls[0], caption)
    if DRY_RUN:
        print(f"[FB ALBUM {len(image_urls)}] {image_urls[0]}")
        return "https://facebook.com/DRYRUN"
    ids = [_cek(requests.post(f"{G}/{META_PAGE_ID}/photos", timeout=60, data={
        "url": u, "published": "false", "access_token": META_PAGE_TOKEN}))["id"] for u in image_urls[:10]]
    import json
    data = {"message": caption, "access_token": META_PAGE_TOKEN}
    for i, pid in enumerate(ids):
        data[f"attached_media[{i}]"] = json.dumps({"media_fbid": pid})
    d = _cek(requests.post(f"{G}/{META_PAGE_ID}/feed", timeout=60, data=data))
    return f"https://facebook.com/{d.get('id')}"


def post_facebook(image_url: str, caption: str) -> str:
    if DRY_RUN:
        print(f"[FB] {image_url}")
        return "https://facebook.com/DRYRUN"
    d = _cek(requests.post(f"{G}/{META_PAGE_ID}/photos", timeout=60, data={
        "url": image_url, "caption": caption, "access_token": META_PAGE_TOKEN}))
    return f"https://facebook.com/{d.get('post_id', d.get('id'))}"


def post_facebook_file(path: str, caption: str, published: bool = True):
    """Mode laptop: unggah poster ke Page (published=False -> hanya untuk dapat URL publik, tidak tampil).
    Kembalikan (link post, URL gambar publik untuk IG)."""
    if DRY_RUN:
        print(f"[FB upload published={published}] {path}")
        return "https://facebook.com/DRYRUN", "https://example.com/poster.jpg"
    with open(path, "rb") as f:
        d = _cek(requests.post(f"{G}/{META_PAGE_ID}/photos", timeout=120, files={"source": f},
                               data={"caption": caption, "published": str(published).lower(),
                                     "access_token": META_PAGE_TOKEN}))
    img = _cek(requests.get(f"{G}/{d['id']}", timeout=30, params={"fields": "images", "access_token": META_PAGE_TOKEN}))
    url = max(img["images"], key=lambda i: i["width"])["source"]
    return f"https://facebook.com/{d.get('post_id', d['id'])}", url


def post_make(image_url: str, caption: str, semua: list[str] | None = None) -> str:
    """Kirim poster ke skenario Make.com yang memposting ke Feed Instagram + Facebook Page.
    `semua` = semua slide carousel (gambar = slide pertama, untuk skenario 1 gambar)."""
    from config import MAKE_WEBHOOK_URL, MAKE_KUNCI
    if DRY_RUN:
        print(f"[MAKE] {image_url}")
        return "dikirim ke Make (DRY RUN)"
    r = requests.post(MAKE_WEBHOOK_URL, timeout=90, json={"kunci": MAKE_KUNCI, "gambar": image_url, "caption": caption,
                                                                 "gambar_semua": semua or [image_url],
                                                                 "jumlah": len(semua or [image_url])})
    if r.status_code >= 400:
        raise RuntimeError(f"Make menolak ({r.status_code}): {r.text[:200]}")
    return r.text.strip()[:300] or "diterima Make"
