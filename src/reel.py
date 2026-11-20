"""Reel slideshow: ubah slide carousel (1080x1350) jadi video tegak 9:16 (1080x1920) dengan gerakan halus.

Dipakai:  python src/reel.py out.mp4 slide1.jpg slide2.jpg ...
Tanpa musik: musik Instagram tidak bisa ditambahkan lewat API, jadi ditempel manual kalau mau.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageFilter, ImageEnhance

W, H = 1080, 1920
FPS = 30
DURASI = 3.0       # detik per slide
TRANSISI = 0.5     # detik crossfade antar slide


def _bingkai(slide: Path, out: Path) -> None:
    """Slide di tengah, latar belakang = slide yang sama diperbesar, diburamkan dan digelapkan sedikit."""
    im = Image.open(slide).convert("RGB")
    latar = im.resize((int(H * im.width / im.height), H)).crop((0, 0, W, H))
    latar = latar.filter(ImageFilter.GaussianBlur(40))
    latar = ImageEnhance.Brightness(latar).enhance(0.85)
    lebar = W
    tinggi = int(im.height * lebar / im.width)
    depan = im.resize((lebar, tinggi), Image.LANCZOS)
    latar.paste(depan, (0, (H - tinggi) // 2))
    latar.save(out, quality=95)


def buat(slides: list, out_mp4: str) -> str:
    slides = [Path(s) for s in slides]
    if not slides:
        raise ValueError("tidak ada slide")
    with tempfile.TemporaryDirectory() as tmp:
        frames = []
        for i, s in enumerate(slides):
            f = Path(tmp) / f"f{i}.jpg"
            _bingkai(s, f)
            frames.append(f)

        n_frame = int(DURASI * FPS)
        args = ["ffmpeg", "-y", "-loglevel", "error"]
        for f in frames:
            args += ["-i", str(f)]  # 1 frame; zoompan yang memperpanjang jadi DURASI detik
        filt = []
        for i in range(len(frames)):
            # zoom pelan 1.00 -> 1.06, bergantian masuk/keluar supaya tidak monoton
            z = "min(zoom+0.0007,1.06)" if i % 2 == 0 else "if(eq(on,0),1.06,max(zoom-0.0007,1.0))"
            filt.append(
                f"[{i}:v]scale={W*2}:{H*2},zoompan=z='{z}':d={n_frame}:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},setsar=1,format=yuv420p[v{i}]"
            )
        last = "v0"
        offset = DURASI - TRANSISI
        for i in range(1, len(frames)):
            nama = f"x{i}"
            filt.append(f"[{last}][v{i}]xfade=transition=fade:duration={TRANSISI}:offset={offset:.2f}[{nama}]")
            last = nama
            offset += DURASI - TRANSISI
        args += ["-filter_complex", ";".join(filt), "-map", f"[{last}]",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                 "-r", str(FPS), "-movflags", "+faststart", out_mp4]
        subprocess.run(args, check=True)
    return out_mp4


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("pakai: python src/reel.py out.mp4 slide1.jpg slide2.jpg ...")
    print(buat(sys.argv[2:], sys.argv[1]))
