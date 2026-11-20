"""Tambah suara narator + dialog (TTS bahasa Indonesia) ke video motion comic.

Suara dibuat dengan edge-tts (suara neural Microsoft Edge, gratis; butuh internet -> dijalankan di GitHub Actions).
Tiap baris punya waktu mulai; kalau lebih panjang dari slotnya, otomatis dipercepat sedikit.
Pakai:  python cerita/suara.py video_bisu.mp4 out.mp4
"""
import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import edge_tts

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


async def _tts(teks: str, tokoh: str, out: str) -> None:
    s = SUARA[tokoh]
    await edge_tts.Communicate(teks, s["voice"], rate=s["rate"], pitch=s["pitch"]).save(out)


def tambah_suara(video: str, out: str, baris=BARIS_PEMBUKA, volume_efek: float = 0.55) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        inputs, filt = ["-i", video], []
        for i, (mulai, slot, tokoh, teks) in enumerate(baris):
            mp3 = str(Path(tmp) / f"b{i}.mp3")
            asyncio.run(_tts(teks, tokoh, mp3))
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
    print(tambah_suara(sys.argv[1], sys.argv[2]))
