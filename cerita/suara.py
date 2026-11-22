"""Tambah suara narator + dialog (TTS bahasa Indonesia) ke video motion comic (uji Gemini TTS).

Suara dibuat dengan ElevenLabs bila secret ELEVENLABS_API_KEY tersedia (model eleven_multilingual_v2,
mendukung bahasa Indonesia); kalau tidak, cadangan edge-tts (gratis, tidak resmi). Butuh internet -> GitHub Actions.
ID suara ElevenLabs bisa diganti lewat variabel ELEVEN_VOICE_NARATOR / ELEVEN_VOICE_NAFI (dari Voice Library).
Pilihan ketiga: Gemini TTS (secret GEMINI_API_KEY) - suara diarahkan dengan instruksi gaya bahasa alami.
Mesin dipilih lewat variabel TTS_MESIN = gemini | eleven | edge (kosong = otomatis: eleven > gemini > edge).
Tiap baris punya waktu mulai; kalau lebih panjang dari slotnya, otomatis dipercepat sedikit.
Pakai:  python cerita/suara.py video_bisu.mp4 out.mp4
"""
import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import base64

import requests

ELEVEN_KEY = os.environ.get("ELEVENLABS_API_KEY", "").strip()
ELEVEN_MODEL = os.environ.get("ELEVEN_MODEL", "eleven_multilingual_v2")
ELEVEN = {
    # default: suara bawaan ElevenLabs; ganti dengan suara berlogat Indonesia dari Voice Library lewat variabel
    "narator": {"voice": os.environ.get("ELEVEN_VOICE_NARATOR") or "JBFqnCBsd6RMkjVDRZzb",
                "settings": {"stability": 0.55, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": True}},
    "laras": {"voice": os.environ.get("ELEVEN_VOICE_LARAS") or "EXAVITQu4vr4xnSDxMaL",
             "settings": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": True}},
}

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_TTS_MODEL = [m for m in (os.environ.get("GEMINI_TTS_MODEL"), "gemini-3.1-flash-tts-preview",
                                "gemini-2.5-flash-preview-tts") if m]
GEMINI = {
    "narator": {"voice": os.environ.get("GEMINI_VOICE_NARATOR") or "Charon",
                "gaya": "Bacakan dalam bahasa Indonesia baku dengan artikulasi sangat jelas dan natural seperti pendongeng radio profesional, "
                        "dekat mikrofon, volume stabil, "
                        "suara hangat dan dalam, intonasi bercerita yang hidup dengan sedikit nuansa misteri, tempo sedang, "
                        "tidak berbisik dan tidak datar, jeda singkat saja pada tanda titik-titik"},
    "laras": {"voice": os.environ.get("GEMINI_VOICE_LARAS") or "Leda",
              "gaya": "Ucapkan dalam bahasa Indonesia sebagai perempuan sekitar 30 tahun yang ramah dan tenang, "
                      "dengan nada kaget dan penasaran"},
}
GEMINI.update({
    "raka": {"voice": "Puck", "gaya": "Ucapkan dalam bahasa Indonesia standar tanpa logat daerah sebagai remaja laki-laki SMA "
                                      "17 tahun yang spontan dan bersemangat. Suaranya jelas laki-laki dengan nada sedang-rendah; "
                                      "walau kaget, panik, atau berteriak tetap tidak melengking dan tidak terdengar seperti perempuan"},
    "dinda": {"voice": "Laomedeia", "gaya": "Ucapkan dalam bahasa Indonesia sebagai anak perempuan 8 tahun yang polos, "
                                            "suara kecil dan riang"},
    "bima": {"voice": "Iapetus", "gaya": "Ucapkan dalam bahasa Indonesia sebagai remaja laki-laki 17 tahun yang pendiam dan pelan"},
    "hadi": {"voice": "Algenib", "gaya": "Ucapkan dalam bahasa Indonesia sebagai laki-laki 32 tahun, guru yang tegas dan berwibawa"},
    "rani": {"voice": "Kore", "gaya": "Ucapkan dalam bahasa Indonesia sebagai perempuan 32 tahun yang lembut dan menahan haru"},
})
PEREMPUAN = {"laras", "dinda", "rani"}
LAKI = {"narator", "raka", "bima", "hadi"}
BATAS_NADA_LAKI = 265  # Hz; di atas ini suara laki-laki terdengar seperti perempuan


def _nada(path: str) -> float:
    """Perkiraan nada dasar (median F0, Hz) klip suara, dengan autokorelasi sederhana."""
    try:
        import numpy as np
    except ImportError:
        return 0.0
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.int16).astype(float)
    sr, n, fs = 16000, 800, []
    lo, hi = sr // 500, sr // 70
    for i in range(0, len(x) - n - hi, n // 2):  # YIN sederhana
        s = x[i:i + n + hi]
        if np.abs(s[:n]).mean() < 300:
            continue
        d = np.array([np.sum((s[:n] - s[t:t + n]) ** 2) for t in range(hi)])
        d[1:] = d[1:] * np.arange(1, hi) / np.maximum(np.cumsum(d[1:]), 1e-9)
        cand = np.where(d[lo:] < 0.15)[0]
        if len(cand):
            t = lo + cand[0]
            while t + 1 < hi and d[t + 1] < d[t]:
                t += 1
            fs.append(sr / t)
    return float(np.median(fs)) if fs else 0.0

MESIN = (os.environ.get("TTS_MESIN") or "").strip().lower() or (
    "eleven" if ELEVEN_KEY else "gemini" if GEMINI_KEY else "edge")

SUARA = {
    "narator": {"voice": "id-ID-ArdiNeural", "rate": "-4%", "pitch": "-6Hz"},
    "laras": {"voice": "id-ID-GadisNeural", "rate": "+6%", "pitch": "+0Hz"},
    "raka": {"voice": "id-ID-ArdiNeural", "rate": "+12%", "pitch": "+14Hz"},
    "bima": {"voice": "id-ID-ArdiNeural", "rate": "-2%", "pitch": "+8Hz"},
    "hadi": {"voice": "id-ID-ArdiNeural", "rate": "+0%", "pitch": "-10Hz"},
    "dinda": {"voice": "id-ID-GadisNeural", "rate": "+8%", "pitch": "+30Hz"},
    "rani": {"voice": "id-ID-GadisNeural", "rate": "-4%", "pitch": "-6Hz"},
}

# (mulai detik, slot maksimal detik, tokoh, teks)
BARIS_PEMBUKA = [
    (0.4, 3.3, "narator", "Jam enam pagi. Seperti biasa, Mbak Laras membuka toko."),
    (3.9, 2.9, "narator", "Tapi pagi ini... ada yang berbeda."),
    (7.2, 1.6, "laras", "Lho? Surat untuk siapa ini?"),
    (8.7, 1.25, "narator", "Misteri Surat Tanpa Nama."),
]


def _durasi(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def _eleven(teks: str, tokoh: str, out: str) -> None:
    c = ELEVEN.get(tokoh) or ELEVEN["laras" if tokoh in PEREMPUAN else "narator"]
    r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{c['voice']}",
                      params={"output_format": "mp3_44100_128"}, timeout=120,
                      headers={"xi-api-key": ELEVEN_KEY, "Content-Type": "application/json"},
                      json={"text": teks, "model_id": ELEVEN_MODEL, "language_code": "id", "voice_settings": c["settings"]})
    if r.status_code == 400 and "language_code" in r.text:  # model yang tidak menerima language_code
        r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{c['voice']}",
                          params={"output_format": "mp3_44100_128"}, timeout=120,
                          headers={"xi-api-key": ELEVEN_KEY, "Content-Type": "application/json"},
                          json={"text": teks, "model_id": ELEVEN_MODEL, "voice_settings": c["settings"]})
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs {r.status_code}: {r.text[:300]}")
    Path(out).write_bytes(r.content)


_MODEL_OK = 0


def _gemini(teks: str, tokoh: str, out: str, emosi: str = "") -> None:
    c = GEMINI.get(tokoh, GEMINI["narator"])
    gaya = c["gaya"] + (f", dengan emosi {emosi}" if emosi else "")
    body = {"contents": [{"parts": [{"text": f"{gaya}: {teks}"}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": c["voice"]}}}}}
    import time
    err = ""
    # model utama dicoba ulang dulu (kadang balasannya kosong / kena batas per menit), baru model cadangan
    global _MODEL_OK
    # mulai dari model yang terakhir berhasil, supaya suara satu episode konsisten
    urutan = [m for m in GEMINI_TTS_MODEL[_MODEL_OK:] for _ in range(3)]
    for i, model in enumerate(urutan):
        if i:
            time.sleep(35 if " 429:" in err else min(20, 4 * i))  # 429 = batas per menit
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                          headers={"x-goog-api-key": GEMINI_KEY}, json=body, timeout=180)
        if r.status_code == 200:
            try:
                part = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
            except (KeyError, IndexError, ValueError):
                err = f"{model} balasan kosong: {r.text[:200]}"
                continue
            pcm = Path(out).with_suffix(".pcm")
            pcm.write_bytes(base64.b64decode(part["data"]))
            rate = 24000
            if "rate=" in part.get("mimeType", ""):
                rate = int(part["mimeType"].split("rate=")[1].split(";")[0])
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(rate), "-ac", "1",
                            "-i", str(pcm), out], check=True)
            _MODEL_OK = GEMINI_TTS_MODEL.index(model)
            print(f"    (gemini {model}, suara {c['voice']})")
            return
        err = f"{model} {r.status_code}: {r.text[:200]}"
    raise RuntimeError(f"Gemini TTS gagal: {err}")


def _rapikan(path: str) -> None:
    """Buang hening di awal & akhir klip suara (Gemini sering menambah jeda panjang)."""
    tmp = path + ".rapi.wav"
    trim = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-af",
                    f"{trim},areverse,{trim},areverse", tmp], check=True)
    Path(tmp).replace(path)


CACHE = Path(__file__).parent / "suara_cache"


def _tts(teks: str, tokoh: str, out: str, emosi: str = "") -> None:
    """Suara satu baris. Hasil disimpan di cerita/suara_cache supaya render ulang tidak memakai kuota TTS lagi.
    Kalau kuota Gemini habis (429), otomatis pakai suara cadangan edge-tts."""
    global MESIN
    import hashlib
    import shutil
    kunci = hashlib.sha1(f"{MESIN}|{tokoh}|{emosi}|{teks}".encode()).hexdigest()[:12]
    simpan = CACHE / f"{tokoh}-{kunci}.wav"
    if simpan.exists() and MESIN != "diam":
        shutil.copy(simpan, out)
        return
    try:
        _tts_mentah(teks, tokoh, out, emosi)
    except RuntimeError as e:
        if MESIN != "gemini" or "429" not in str(e):
            raise
        print("    kuota Gemini TTS habis -> suara cadangan edge-tts untuk sisa episode")
        MESIN = "edge"
        return _tts(teks, tokoh, out, emosi)
    if MESIN == "gemini" and tokoh in LAKI and out.endswith(".wav"):
        # Gemini kadang melengking (terdengar perempuan) saat emosi berteriak/panik -> buat ulang maks 2x, ambil yang paling rendah
        terbaik, f0 = out + ".ok.wav", _nada(out)
        shutil.copy(out, terbaik)
        for _ in range(2):
            if f0 <= BATAS_NADA_LAKI:
                break
            print(f"    nada {tokoh} {f0:.0f} Hz terlalu tinggi, buat ulang")
            _tts_mentah(teks, tokoh, out, "kaget tapi tetap tenang, nada suara laki-laki rendah dan berat, tidak berteriak melengking")
            f1 = _nada(out)
            if f1 < f0:
                f0 = f1
                shutil.copy(out, terbaik)
        Path(terbaik).replace(out)
    if out.endswith(".wav") and MESIN != "diam":
        _rapikan(out)
        CACHE.mkdir(exist_ok=True)
        shutil.copy(out, simpan)


def _tts_mentah(teks: str, tokoh: str, out: str, emosi: str = "") -> None:
    if MESIN == "diam":  # uji tanpa internet: hening sepanjang perkiraan durasi bicara
        d = 0.35 + 0.36 * len(teks.split())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono",
                        "-t", f"{d:.2f}", out], check=True)
        return
    if MESIN == "eleven" and ELEVEN_KEY:
        return _eleven(teks, tokoh, out)
    if MESIN == "gemini" and GEMINI_KEY:
        return _gemini(teks, tokoh, out, emosi)
    import edge_tts
    s = SUARA.get(tokoh, SUARA["narator"])
    asyncio.run(edge_tts.Communicate(teks, s["voice"], rate=s["rate"], pitch=s["pitch"]).save(out))


def tambah_suara(video: str, out: str, baris=BARIS_PEMBUKA, volume_efek: float = 0.55) -> str:
    # mesin diminta tapi kuncinya tidak ada -> pakai cadangan, dan beri tahu
    global MESIN
    if (MESIN == "gemini" and not GEMINI_KEY) or (MESIN == "eleven" and not ELEVEN_KEY):
        print(f"! kunci untuk {MESIN} tidak ada, pakai edge-tts")
        MESIN = "edge"
    with tempfile.TemporaryDirectory() as tmp:
        inputs, filt = ["-i", video], []
        for i, (mulai, slot, tokoh, teks) in enumerate(baris):
            mp3 = str(Path(tmp) / f"b{i}.{'wav' if MESIN == 'gemini' else 'mp3'}")
            _tts(teks, tokoh, mp3)
            d = _durasi(mp3)
            tempo = min(1.35, max(1.0, d / slot))  # percepat bila tidak muat di slotnya
            inputs += ["-i", mp3]
            filt.append(f"[{i + 1}:a]atempo={tempo:.3f},adelay={int(mulai * 1000)}|{int(mulai * 1000)},volume=1.6[s{i}]")
            print(f"  {tokoh:7s} {mulai:4.1f}s  {d:.2f}s -> x{tempo:.2f}  {teks}")
        n = len(baris)
        campur = "".join(f"[s{i}]" for i in range(n))
        filt.append(f"[0:a]volume={volume_efek}[efek]")
        filt.append(f"[efek]{campur}amix=inputs={n + 1}:duration=first:normalize=0,alimiter=limit=0.95[a]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt),
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                        "-movflags", "+faststart", out], check=True)
    return out


if __name__ == "__main__":
    print("Mesin suara:", MESIN)
    print(tambah_suara(sys.argv[1], sys.argv[2]))
