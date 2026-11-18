# Autopost Katalog Annafi ATK

Posting katalog produk otomatis ke **Instagram + Facebook** sesuai jadwal di Google Sheet.

```
Google Sheet ──► GitHub Actions (tiap 15 menit)
                   ├─ 2 jam sebelum jadwal: buat poster → kirim pratinjau ke Telegram
                   └─ saat jadwal: posting ke Instagram + Facebook → kabari di Telegram
```

- Gambar: link di kolom `gambar`, atau dicari otomatis (DuckDuckGo, cadangan Serper) lalu latarnya dihapus.
- Kalau pratinjau salah: ubah baris di sheet (misal tempel link gambar lain) → poster dibuat ulang.
- Kalau tidak sempat cek: tetap diposting. Isi kolom `tunda` = `YA` untuk menahan.
- Jadwal yang terlewat lebih dari 3 jam tidak diposting (diberi tahu di Telegram).

---

## Mode laptop (Windows) — tanpa GitHub

Jalan lewat Task Scheduler tiap 15 menit. **Laptop harus menyala, tidak sleep, dan terhubung internet**
saat jam pratinjau & jam posting. Poster diunggah ke Facebook dulu, lalu URL fotonya dipakai Instagram
(jadi tidak perlu repo publik).

1. Pasang **Python 3.12** dari python.org (centang *Add python.exe to PATH*).
2. Double-click **setup.bat** (sekali saja; pasang paket, Chromium, dan jadwal "Annafi Autopost").
3. Buka file **.env** dengan Notepad, isi nilai-nilainya (langkah 1–3 di bawah). Biarkan `DRY_RUN=1` dulu.
4. Double-click **jalan.bat** untuk tes, lalu lihat **log.txt**. Kalau aman, ubah `DRY_RUN=0`.
5. Mau berhenti: double-click **hapus_jadwal.bat**.

Tips: Pengaturan Windows → Sistem → Daya → set *Sleep* ke "Never" saat dicolok.

## Setup (sekali saja)

### 1. Google Sheet
1. Buka Google Drive → **Baru → Upload file** → `Template_Jadwal_Annafi.xlsx` → buka dengan Google Sheets
   (atau **File → Simpan sebagai Google Spreadsheet**).
2. **File → Bagikan → Publikasikan ke web** → pilih sheet **Jadwal** dan format **CSV** → Publikasikan.
3. Salin link yang muncul → ini `SHEET_CSV_URL`.

> Perubahan di sheet butuh ±5 menit sampai terbaca sistem.

### 2. Bot Telegram
1. Di Telegram cari **@BotFather** → `/newbot` → beri nama → salin **token** (`TELEGRAM_BOT_TOKEN`).
2. Buka bot barumu, kirim pesan apa saja (misal `halo`).
3. Buka di browser: `https://api.telegram.org/bot<TOKEN>/getUpdates` → cari `"chat":{"id":123456789` → angka itu `TELEGRAM_CHAT_ID`.

### 3. Meta (Instagram + Facebook)
1. Instagram @annafi_atk_menganti → jadikan **akun Bisnis/Profesional**, lalu tautkan ke Page **Annafi Atk Menganti**.
2. Buka **developers.facebook.com** → **Buat Aplikasi** → tipe **Bisnis**.
3. Di app, buka **Graph API Explorer**: pilih app-mu → **Get User Access Token** → centang izin:
   `pages_show_list, pages_read_engagement, pages_manage_posts, instagram_basic, instagram_content_publish, business_management`
   → Generate → salin token.
4. Di laptop: `pip install requests` lalu
   ```
   python tools/token_meta.py APP_ID APP_SECRET TOKEN_TADI
   ```
   (APP_ID & APP_SECRET ada di **Pengaturan Aplikasi → Dasar**). Hasilnya: `META_PAGE_ID`, `META_IG_USER_ID`, `META_PAGE_TOKEN` (token Page ini tidak kedaluwarsa).

App boleh tetap mode *Development* karena hanya dipakai untuk akunmu sendiri (kamu admin app).

### 4. GitHub (hanya untuk mode GitHub)
1. Repo ini harus **Public** (supaya Instagram bisa mengambil gambar poster & menit Actions gratis tanpa batas).
2. **Settings → Secrets and variables → Actions → New repository secret**, isi:
   `SHEET_CSV_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `META_PAGE_ID`, `META_PAGE_TOKEN`, `META_IG_USER_ID`
   (opsional: `SERPER_API_KEY` dari serper.dev sebagai cadangan pencarian gambar).
3. Tab **Variables** (opsional): `PREVIEW_JAM` (default 2), `DRY_RUN` = `1` untuk uji coba tanpa posting sungguhan.
4. Tab **Actions** → aktifkan workflow → **Autopost katalog Annafi → Run workflow** untuk tes.

## Uji coba aman
Set variable `DRY_RUN` = `1`, isi satu baris jadwal 1 jam dari sekarang, lalu **Run workflow**.
Lihat log di tab Actions (pratinjau & posting hanya dicetak, tidak dikirim). Kalau sudah oke, hapus `DRY_RUN`.

## Struktur
```
src/main.py      alur utama (cek / prepare / publish)
src/sheet.py     baca jadwal CSV
src/images.py    cari & bersihkan gambar
src/render.py    poster 1080x1350 JPEG dari src/template.html
src/notify.py    Telegram
src/meta.py      Instagram + Facebook Graph API
src/config.py    data toko, caption, hashtag, pengaturan
state/           status tiap postingan (otomatis)
posters/         poster jadi (otomatis, URL publik untuk Instagram)
```

## Catatan
- Gambar hasil pencarian otomatis bisa milik toko/orang lain atau salah produk — itulah gunanya pratinjau.
- GitHub bisa menonaktifkan jadwal kalau repo tidak ada aktivitas 60 hari; tinggal aktifkan lagi di tab Actions.
- Batas Instagram: 100 postingan API per 24 jam — jauh di atas kebutuhan toko.
