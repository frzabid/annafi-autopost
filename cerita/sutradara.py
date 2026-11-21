"""Sutradara AI: naskah satu part (cerita/naskah_musim1.md) -> papan cerita JSON untuk mesin.py, dibuat oleh Gemini.

Hasil disimpan di cerita/papan/partN-<kunci>.json (kunci = isi naskah part + arahan), jadi render ulang memakai papan
yang sama; arahan baru (mis. "buat Raka lebih panik") menghasilkan papan baru.
"""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import mesin as M  # noqa: E402
import tokoh as T  # noqa: E402

DIR = Path(__file__).parent
NASKAH = DIR / "naskah_musim1.md"
PAPAN = DIR / "papan"
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
MODEL = [m for m in (os.environ.get("GEMINI_MODEL"), "gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite") if m]


def naskah():
    teks = NASKAH.read_text(encoding="utf-8")
    kepala = teks.split("## PART")[0].strip()
    part = {int(m[1]): m[0].strip() for m in re.finditer(r"## PART (\d+)[^\n]*\n(?:(?!## PART).*\n?)*", teks)}
    return kepala, part


def daftar_part():
    return sorted(naskah()[1])


def _prompt(n, arahan):
    kepala, part = naskah()
    tokoh = {k: v["nama"] for k, v in T.TOKOH.items()}
    contoh = {"part": 9, "judul": "Contoh Format", "adegan": [
        {"latar": "dalam", "waktu": "sore", "kamera": "zoom_in", "kilas_balik": False,
         "tokoh": [{"id": "dinda_bebas", "ekspresi": "bingung", "posisi": "kiri", "masuk": "kiri"},
                   {"id": "laras", "ekspresi": "senang", "posisi": "kanan", "masuk": ""}],
         "objek": None, "efek": ["bel"],
         "urutan": [{"tokoh": "narator", "ucap": "Sore itu toko sepi.", "emosi": "pelan"},
                    {"tokoh": "dinda_bebas", "ucap": "Mbak, ini punya siapa?", "ekspresi": "bingung", "emosi": "penasaran"},
                    {"jeda": 0.8}]},
        {"latar": "meja", "waktu": "sore", "kamera": "zoom_in", "kilas_balik": False,
         "tokoh": [{"id": "laras", "ekspresi": "kaget", "posisi": "kiri", "masuk": ""}],
         "objek": {"jenis": "surat", "tulisan": "Kita pernah berjanji."}, "efek": ["kertas"],
         "urutan": [{"teks": "Kita pernah berjanji."},
                    {"tokoh": "laras", "ucap": "Tulisan ini...", "ekspresi": "kaget", "emosi": "berbisik, terkejut"}]}]}
    return "\n".join([
        "Kamu sutradara animasi motion comic vertikal (reel Instagram 9:16) untuk cerita misteri bersambung.",
        f"Ubah naskah PART {n} di bawah menjadi PAPAN CERITA JSON untuk mesin animasi. Durasi total 45-60 detik.",
        "",
        "INFO SERI (tokoh, kostum, format):", kepala, "",
        f"NASKAH PART {n}:", part[n], "",
        "ATURAN WAJIB:",
        "- Ikuti urutan adegan & dialog naskah. Setiap baris NARATOR/TOKOH jadi item {tokoh, ucap}. Boleh merapikan kalimat agar enak",
        "  diucapkan, tapi JANGAN menambah fakta/petunjuk baru dan jangan membocorkan misteri part berikutnya.",
        "- TEKS: \"...\" jadi item {teks}. Kalau itu tulisan pada surat/amplop, isi juga objek.tulisan dengan teks yang SAMA PERSIS.",
        "- (terdiam) / jeda dramatis jadi item {jeda: detik 0.6-1.5}. Teks 'Bersambung'/'Part berikutnya' TIDAK perlu (kartu akhir otomatis).",
        "- Tiap adegan maksimal 3 tokoh, 1 objek. Tokoh yang bicara HARUS ada di daftar tokoh adegan itu (pakai id kostum yang sama).",
        "- Pilih kostum sesuai waktu: pagi/jam sekolah = seragam (raka, dinda, bima, hadi); sore pulang sekolah, malam, Minggu = *_bebas;",
        "  kilas balik/foto lama = laras_sma, hadi_sma, rani_sma dengan kilas_balik true.",
        "- emosi: 1-4 kata arahan suara (mis. 'panik, terburu-buru', 'berbisik', 'heran'). ekspresi wajah dari: " + ", ".join(T.EKSPRESI),
        "- Variasikan latar & kamera supaya tidak monoton; adegan pertama harus langsung menarik (hook 3 detik).",
        "",
        "PILIHAN (pakai nilai PERSIS):",
        "latar: " + json.dumps(M.LATAR, ensure_ascii=False),
        "tokoh id: " + json.dumps(tokoh, ensure_ascii=False) + " ; pembicara 'narator' tidak tampil",
        "posisi: kiri, tengah, kanan · masuk: '', 'kiri', 'kanan' (tokoh berjalan masuk ke layar)",
        "objek.jenis: " + json.dumps(M.OBJEK, ensure_ascii=False),
        "kamera: " + ", ".join(M.KAMERA) + " · waktu: " + ", ".join(M.WAKTU) + " · efek suara: " + ", ".join(M.EFEK),
        "",
        ("ARAHAN TAMBAHAN DARI PEMILIK: " + arahan) if arahan else "",
        "CONTOH FORMAT (isi cerita contoh ini fiktif, jangan dipakai): " + json.dumps(contoh, ensure_ascii=False),
        f'Jawab HANYA JSON: {{"part": {n}, "judul": string, "adegan": [...]}}',
    ])


def _gemini(prompt):
    if not GEMINI_KEY:
        raise RuntimeError("GEMINI_API_KEY belum diisi")
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.6, "maxOutputTokens": 12000}}
    err = ""
    for model in MODEL:
        for coba in range(3):
            b = dict(body)
            if "2.5" in model:  # batasi "berpikir" supaya tidak terlalu lama
                b["generationConfig"] = dict(body["generationConfig"], thinkingConfig={"thinkingBudget": 2048})
            try:
                r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                  headers={"x-goog-api-key": GEMINI_KEY}, json=b, timeout=300)
            except requests.RequestException as e:
                err = f"{model}: {e}"
                print("  gemini:", err)
                time.sleep(5)
                continue
            print(f"  gemini {model}: {r.status_code}")
            if r.status_code == 200:
                try:
                    teks = "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"] if not p.get("thought"))
                    return json.loads(re.sub(r"^```(json)?|```$", "", teks.strip()).strip()), model
                except (KeyError, IndexError, ValueError) as e:
                    err = f"{model}: balasan tidak terbaca ({e})"
            else:
                err = f"{model} {r.status_code}: {r.text[:200]}"
                if r.status_code == 404:
                    break
            time.sleep(5 * (coba + 1))
    raise RuntimeError(f"Gemini gagal membuat papan cerita: {err}")


def rapikan(p, n):
    """Validasi & perbaiki papan dari AI supaya mesin tidak pernah gagal karena nilai aneh."""
    hasil = {"part": n, "judul": str(p.get("judul", ""))[:80], "adegan": []}
    for a in p.get("adegan", [])[:14]:
        a = dict(a)
        latar = a.get("latar") if a.get("latar") in M.LATAR else "dalam"
        tokoh, dipakai = [], set()
        for t in (a.get("tokoh") or [])[:3]:
            tid = t.get("id") if t.get("id") in T.TOKOH else None
            if not tid or tid in dipakai:
                continue
            dipakai.add(tid)
            tokoh.append({"id": tid, "ekspresi": t.get("ekspresi") if t.get("ekspresi") in T.EKSPRESI else "senang",
                          "posisi": t.get("posisi") if t.get("posisi") in M.POSISI_LEBAR else "",
                          "masuk": t.get("masuk") if t.get("masuk") in ("kiri", "kanan") else ""})
        urutan = []
        for it in a.get("urutan") or []:
            if it.get("ucap") and str(it["ucap"]).strip():
                sp = str(it.get("tokoh", "narator")).lower().strip()
                if sp != "narator":
                    cocok = [t["id"] for t in tokoh if t["id"] == sp or t["id"].split("_")[0] == sp.split("_")[0]]
                    if cocok:
                        sp = cocok[0]
                    elif sp in T.TOKOH and len(tokoh) < 3:
                        tokoh.append({"id": sp, "ekspresi": "senang", "posisi": "", "masuk": ""})
                    else:
                        sp = "narator"
                urutan.append({"tokoh": sp, "ucap": str(it["ucap"]).strip()[:220], "emosi": str(it.get("emosi", ""))[:40],
                               "ekspresi": it.get("ekspresi") if it.get("ekspresi") in T.EKSPRESI else ""})
            elif it.get("teks") and str(it["teks"]).strip():
                t = str(it["teks"]).strip()
                if re.search(r"bersambung|part\s*\d", t, re.I) and len(t) < 40:
                    continue  # kartu akhir sudah otomatis
                urutan.append({"teks": t[:160]})
            elif it.get("jeda") is not None:
                try:
                    urutan.append({"jeda": max(0.3, min(2.0, float(it["jeda"])))})
                except (TypeError, ValueError):
                    pass
        if not urutan:
            continue
        # posisi otomatis kalau kosong/bentrok
        bebas = ["kiri", "kanan", "tengah"] if len(tokoh) > 1 else ["tengah"]
        terpakai = set()
        for t in tokoh:
            if t["posisi"] in terpakai or not t["posisi"] or (len(tokoh) == 1 and latar not in M.LEBAR):
                t["posisi"] = next((x for x in bebas if x not in terpakai), "tengah")
            terpakai.add(t["posisi"])
        ob = a.get("objek") if isinstance(a.get("objek"), dict) else None
        if ob and ob.get("jenis") in M.OBJEK:
            ob = {"jenis": ob["jenis"], "tulisan": str(ob.get("tulisan") or "")[:140]}
        else:
            ob = None
        hasil["adegan"].append({
            "latar": latar, "waktu": a.get("waktu") if a.get("waktu") in M.WAKTU else "pagi",
            "kamera": a.get("kamera") if a.get("kamera") in M.KAMERA else "zoom_in",
            "kilas_balik": bool(a.get("kilas_balik")), "tokoh": tokoh, "objek": ob,
            "efek": [e for e in (a.get("efek") or []) if e in M.EFEK][:3], "urutan": urutan})
    if not hasil["adegan"]:
        raise RuntimeError("Papan cerita dari AI kosong / tidak valid")
    return hasil


def papan(n, arahan="", baru=False):
    """Ambil papan cerita part n (dari cache, atau minta Gemini membuatnya). Kembalikan (papan, path, dibuat_baru)."""
    _, part = naskah()
    if n not in part:
        raise KeyError(f"Part {n} tidak ada di naskah")
    kunci = hashlib.sha1((part[n] + "|" + arahan.strip()).encode()).hexdigest()[:8]
    path = PAPAN / f"part{n}-{kunci}.json"
    if path.exists() and not baru:
        return json.loads(path.read_text(encoding="utf-8")), path, False
    mentah, model = _gemini(_prompt(n, arahan.strip()))
    hasil = rapikan(mentah, n)
    hasil["_dibuat"] = {"model": model, "arahan": arahan.strip(), "waktu": time.strftime("%Y-%m-%d %H:%M")}
    PAPAN.mkdir(exist_ok=True)
    path.write_text(json.dumps(hasil, ensure_ascii=False, indent=1), encoding="utf-8")
    return hasil, path, True


def ringkas(p):
    """Ringkasan papan untuk pesan Telegram."""
    baris = []
    for i, a in enumerate(p["adegan"], 1):
        siapa = ", ".join(T.TOKOH[t["id"]]["nama"] for t in a["tokoh"]) or "-"
        baris.append(f"{i}. {a['latar']} ({siapa})")
    return "\n".join(baris)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    p, path, baru = papan(n, " ".join(sys.argv[2:]))
    print(path, "baru" if baru else "cache")
    print(ringkas(p))
