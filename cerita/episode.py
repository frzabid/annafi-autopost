"""Render satu part cerita: naskah -> papan cerita (Gemini, sutradara.py) -> video (mesin.py).

Dipakai autopost (jadwal & permintaan dari bot Telegram) dan workflow cerita.yml.
  python cerita/episode.py <part> <out.mp4> [arahan...]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sutradara  # noqa: E402

PART = {n: "naskah" for n in sutradara.daftar_part()}  # part yang bisa dibuat (ada di naskah)


class BelumDibuat(Exception):
    pass


def render(part: int, out_mp4: str, arahan: str = "", baru: bool = False) -> dict:
    """Kembalikan info: papan (dict), path papan, apakah papan baru dibuat AI."""
    if part not in PART:
        raise BelumDibuat(f"Part {part} belum ada di naskah (ada: Part {', '.join(map(str, sorted(PART)))}).")
    import mesin
    papan, path, dibuat = sutradara.papan(part, arahan, baru)
    mesin.render(papan, out_mp4, terakhir=part == max(PART))
    return {"papan": papan, "path": str(path), "baru": dibuat, "ringkas": sutradara.ringkas(papan)}


if __name__ == "__main__":
    n = int(sys.argv[1])
    out = sys.argv[2]
    info = render(n, out, " ".join(sys.argv[3:]))
    print(info["path"], "(papan baru dari AI)" if info["baru"] else "(papan lama)")
    print(info["ringkas"])
