"""Bantu ambil META_PAGE_ID, META_PAGE_TOKEN (tidak kedaluwarsa) dan META_IG_USER_ID.

Cara pakai (sekali saja, di laptop):
  python tools/token_meta.py APP_ID APP_SECRET TOKEN_DARI_GRAPH_API_EXPLORER

Token dari Graph API Explorer harus punya izin:
  pages_show_list, pages_read_engagement, pages_manage_posts,
  instagram_basic, instagram_content_publish, business_management
"""
import sys
import requests

G = "https://graph.facebook.com/v25.0"


def main(app_id, app_secret, short_token):
    r = requests.get(f"{G}/oauth/access_token", params={
        "grant_type": "fb_exchange_token", "client_id": app_id,
        "client_secret": app_secret, "fb_exchange_token": short_token}).json()
    if "access_token" not in r:
        sys.exit(f"Gagal tukar token: {r}")
    long_user = r["access_token"]
    pages = requests.get(f"{G}/me/accounts", params={
        "access_token": long_user, "fields": "id,name,access_token,instagram_business_account"}).json()
    for p in pages.get("data", []):
        ig = (p.get("instagram_business_account") or {}).get("id", "(IG belum ditautkan ke Page ini)")
        print(f"\nPage: {p['name']}")
        print(f"  META_PAGE_ID     = {p['id']}")
        print(f"  META_IG_USER_ID  = {ig}")
        print(f"  META_PAGE_TOKEN  = {p['access_token']}")
    if not pages.get("data"):
        print("Tidak ada Page. Pastikan izin pages_show_list dicentang & kamu admin Page.", pages)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
