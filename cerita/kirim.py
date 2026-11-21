"""Buat satu part cerita lalu kirim videonya ke Telegram (dipakai workflow cerita.yml).
  python cerita/kirim.py <part> [arahan]
"""
import html
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "cerita"))
import notify  # noqa: E402
import episode  # noqa: E402
import config  # noqa: E402

n = int(sys.argv[1])
arahan = sys.argv[2] if len(sys.argv) > 2 else ""
out = ROOT / "cerita" / "contoh" / f"misteri_part{n}.mp4"
out.parent.mkdir(exist_ok=True)
notify.pesan(f"🎬 Membuat <b>Misteri Surat Tanpa Nama Part {n}</b>: AI menyusun adegan dari naskah, lalu animasi & suara "
             "dirender (±5-8 menit)…")
try:
    info = episode.render(n, str(out), arahan)
except Exception as e:
    traceback.print_exc()
    notify.pesan(f"❌ Part {n} gagal dibuat: {html.escape(str(e))[:400]}")
    sys.exit(1)
p = {"nama": f"Misteri Surat Tanpa Nama Part {n}", "part": n, "jenis": "cerita"}
notify.video(str(out), html.escape(config.caption_cerita(p)))
sampul = out.with_name(out.stem + "-sampul.jpg")
if sampul.exists():
    notify.dokumen(str(sampul), f"🖼️ Sampul Part {n} (kualitas asli). Unduh, lalu saat upload: Edit sampul → Tambahkan dari galeri")
notify.pesan(f"🎬 <b>Part {n}</b> selesai (contoh, belum diposting).\nAdegan:\n<i>{html.escape(info['ringkas'])}</i>"
             + (f"\nArahan: {html.escape(arahan)}" if arahan else "")
             + "\n\nKurang pas? Balas misalnya: <i>ulang part 1, Raka lebih panik</i>. "
               "Sudah oke? Balas: <i>jadwalkan part 1 hari Selasa</i>.")
print(info["path"])
