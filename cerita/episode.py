"""Daftar part cerita yang animasinya sudah dibuat. Dipakai autopost (src/main.py) untuk merender reel.

Tambah part baru: buat cerita/partN.py yang punya fungsi render(out_mp4) -> path, lalu daftarkan di PART.
"""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# nomor part -> nama modul di folder cerita/
PART = {
    1: "part1_pembuka",  # sementara: pembuka ±16 detik (versi lengkap menyusul)
}


class BelumDibuat(Exception):
    pass


def render(part: int, out_mp4: str) -> str:
    if part not in PART:
        raise BelumDibuat(f"Animasi Part {part} belum dibuat (yang sudah ada: Part {', '.join(map(str, sorted(PART)))}).")
    return importlib.import_module(PART[part]).render(out_mp4)
