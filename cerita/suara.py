"""Tambah suara narator + dialog (TTS bahasa Indonesia) ke video motion comic.

Suara dibuat dengan ElevenLabs bila secret ELEVENLABS_API_KEY tersedia (model eleven_multilingual_v2,
mendukung bahasa Indonesia); kalau tidak, cadangan edge-tts (gratis, tidak resmi). Butuh internet -> GitHub Actions.
ID suara ElevenLabs bisa diganti lewat variabel ELEVEN_VOICE_NARATOR / ELEVEN_VOICE_NAFI (dari Voice Library).
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

import requests

ELEVEN_KEY = os.environ.get("ELEVENLABS_API_KEY", "").strip()
ELEVEN_MODEL = os.environ.get("ELEVEN_MODEL", "eleven_multilingual_v2")
ELEVEN = {
    # default: suara bawaan ElevenLabs; ganti dengan suara berlogat Indonesia dari Voice Library lewat variabel
    "narator": {"voice": os.environ.get("ELEVEN_VOICE_NARATOR") or "JBFqnCBsd6RMkjVDRZzb",
                "settings": {"stability": 0.55, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": True}},
    "nafi": {"voice": os.environ.get("ELEVEN_VOICE_NAFI") or "EXAVITQu4vr4xnSDxMaL",
             "settings": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": True}},
}

SUARA = {
    "narator": {"voice": "id-ID-ArdiNeural", "rate": "-4%", "pitch": "-6Hz"},
    "nafi": {"voice": "id-ID-GadisNeural", "rate": "+6%", "pitch": "+0Hz"},
}

# (mulai detik, slot maksimal detik, tokoh, teks)
BARIS_PEMBUKA = [
    (0.4, 3.3, "narator", "Jam enam pagi. Seperti biasa, Kak Nafi membuka toko."),
    (3.9, 2.9, "narator", "Tapi pagi ini... ada yang berbeda."),
    (7.2, 1.6, "nafi", "Lho? Surat untuk siapa ini?"),
    (8.7, 1.25, "narator", "Misteri Surat Tanpa Nama."),
]


def _durasi(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def _eleven(teks: str, tokoh: str, out: str) -> None:
    c = ELEVEN[tokoh]
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


def _tts(teks: str, tokoh: str, out: str) -> None:
    if ELEVEN_KEY:
        return _eleven(teks, tokoh, out)
    import edge_tts
    s = SUARA[tokoh]
    asyncio.run(edge_tts.Communicate(teks, s["voice"], rate=s["rate"], pitch=s["pitch"]).save(out))


def tambah_suara(video: str, out: str, baris=BARIS_PEMBUKA, volume_efek: float = 0.55) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        inputs, filt = ["-i", video], []
        for i, (mulai, slot, tokoh, teks) in enumerate(baris):
            mp3 = str(Path(tmp) / f"b{i}.mp3")
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
    print("Mesin suara:", f"ElevenLabs ({ELEVEN_MODEL})" if ELEVEN_KEY else "edge-tts (cadangan)")
    print(tambah_suara(sys.argv[1], sys.argv[2]))
