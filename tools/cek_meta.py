"""Cek sambungan Meta API tanpa memposting apa pun. Hanya menampilkan nama & ID, tidak pernah token."""
import sys, requests
sys.path.insert(0, "src")
import config
g = f"https://graph.facebook.com/{config.GRAPH_VERSION}"
t = config.META_USER_TOKEN
if not t:
    sys.exit("META_USER_TOKEN kosong")
dbg = requests.get(f"{g}/me", params={"fields": "id,name", "access_token": t}, timeout=30).json()
print("Pengguna:", dbg.get("name"), dbg.get("error", ""))
perm = requests.get(f"{g}/me/permissions", params={"access_token": t}, timeout=30).json().get("data", [])
print("Izin:", ", ".join(p["permission"] for p in perm if p.get("status") == "granted"))
hal = requests.get(f"{g}/me/accounts", params={"fields": "id,name,instagram_business_account{id,username}", "access_token": t}, timeout=30).json()
for h in hal.get("data", []):
    ig = h.get("instagram_business_account") or {}
    print(f"Halaman: {h['name']} (id {h['id']}) -> Instagram: @{ig.get('username','-')} (id {ig.get('id','-')})")
if "error" in hal:
    print("Error halaman:", hal["error"].get("message"))
print("Siap posting:", bool(config.META_PAGE_TOKEN and config.META_IG_USER_ID))
if config.META_IG_USER_ID and config.META_PAGE_TOKEN:
    lim = requests.get(f"{g}/{config.META_IG_USER_ID}/content_publishing_limit", params={"fields": "quota_usage,config", "access_token": config.META_PAGE_TOKEN}, timeout=30).json()
    print("Kuota posting IG:", lim.get("data", lim))
