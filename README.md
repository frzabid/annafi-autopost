# Autopost Konten Annafi ATK

Posting konten otomatis ke **Instagram (Story & Feed) + Facebook** sesuai jadwal di Google Sheet.

| jenis di sheet | tayang di | pratinjau Telegram | perlu disetujui? |
|---|---|---|---|
| `katalog` | Story Instagram (9:16) | 2 jam sebelum tayang | Tidak — tayang otomatis, tahan dengan kolom `tunda` = YA |
| `edukasi` / `promo` / `info` / `momen` | Feed Instagram + Facebook (4:5) | jam 20.00 malam sebelumnya | **Ya** — tombol ✅ Setujui / ❌ Batalkan |

```
Google Sheet ──► GitHub Actions (tiap 15 menit)
                   ├─ pratinjau: poster + caption ke Telegram (siap diteruskan ke Saluran/Status WA)
                   ├─ tombol ✅/❌ diproses di pengecekan berikutnya
                   └─ jam tayang: posting → kabari di Telegram (+ pengingat Sorotan untuk story)
```

- Jam dikosongkan → otomatis jam ramai: story 07.00 / 12.00 / 16.00 / 19.00, feed 19.00 (WIB).
- Gambar katalog: link di kolom `gambar`, atau dicari otomatis (DuckDuckGo, cadangan Serper) lalu latarnya dihapus.
- Kalau isi baris diubah setelah pratinjau → poster dibuat ulang & pratinjau baru dikirim (persetujuan lama gugur).
- Sorotan (Highlights) tidak bisa lewat API Meta → bot mengingatkan untuk menambahkannya manual.
- Jadwal yang terlewat lebih dari 3 jam tidak diposting (diberi tahu di Telegram).

---

## Manajer AI & perencana mingguan (Google Apps Script + Gemini)

File: `apps-script/Code.gs`. Berjalan di dalam Google Sheet, gratis, merespons Telegram dalam hitungan detik.

- **Chat bebas ke bot** → Gemini mengubah jadi aksi di tab Jadwal/Produk (tambah, ubah, tunda — tidak pernah menghapus).
- **Tiap Minggu 17.00** → rencana konten minggu depan (story katalog dari tab Produk + 4–5 feed yang idenya diatur AI) ditulis ke tab Jadwal,
  ringkasannya dikirim ke Telegram. Ketik `/rencana` untuk membuat kapan saja.
- **Tombol ✅/❌** dicatat ke tab `Persetujuan`; sistem GitHub membacanya di pengecekan berikutnya.
- Pengaman: harga hanya dari tab Produk atau angka yang kamu ketik sendiri; orang lain yang chat ke bot diabaikan.

### Pemasangan (sekali, ±10 menit, paling nyaman dari laptop)
1. **API key Gemini**: buka aistudio.google.com → *Get API key* → *Create API key* → salin.
2. Buka Google Sheet jadwal → **Ekstensi → Apps Script**. Hapus isi editor, tempel seluruh `Code.gs`.
3. Isi 3 baris paling atas: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GEMINI_API_KEY` → simpan (Ctrl+S).
4. **Deploy → New deployment** → ikon ⚙️ *Select type* → **Web app**.
   *Execute as*: **Me**, *Who has access*: **Anyone** → **Deploy** → izinkan akses
   (pilih akunmu → *Advanced* → *Go to … (unsafe)* → *Allow*; ini script milikmu sendiri).
5. Di editor pilih fungsi **`setup`** → **Run**. Script membuat tab Produk, Kalender, Persetujuan,
   menambah kolom `jenis`/`poin` ke Jadwal, memasang jadwal Minggu 17.00, dan menghubungkan bot.
   Bot akan mengirim "🤖 Manajer AI Annafi aktif!".
6. Isi tab **Produk** (nama, kategori, harga) dan cek tab **Kalender** (isi tanggal Ramadan/Idul Fitri sendiri).

### Fitur tambahan
- **Foto produk sendiri**: kirim foto ke bot dengan caption nama produk (boleh sebagian, mis. `joyko 6151`), atau unggah ke
  folder Drive **Foto Produk Annafi** dengan nama file = nama produk (dicek tiap jam, atau kirim `/foto`).
  Jalankan `izinkanDrive` sekali dari editor. Kategori rawan foto (mainan, aksesoris, buku islami, dll.) hanya masuk
  rencana story kalau sudah punya foto sendiri.
- **Foto otomatis** hanya dipakai kalau judul/sumbernya cocok dengan nama produk; kalau tidak ketemu, poster dibuat tanpa foto.
- **`MODE_PROMO: false`** (default): feed buatan AI hanya edukasi/info/momen, tanpa harga & kalimat promo.
- **Carousel bertema** (default, `CAROUSEL=1`): feed edukasi/info/momen jadi 3–7 slide: sampul, 1 slide per poin,
  kolase foto produk (kolom `produk`, tanpa harga), penutup + kontak. Tema: umum, guru, maulid, ramadan, idulfitri,
  kemerdekaan, ujian, sekolah — isi kolom `tema` atau biarkan kosong (ditebak dari judul). Tema baru: tambah di `src/tema.py`.
  Tanggal Maulid/Ramadan/Idul Fitri diisi sendiri di tab Kalender tiap tahun.
- **Pengingat foto**: jam 19.00 bot mengirim daftar story katalog besok + status fotonya (foto sendiri / ketemu di internet / tidak ada).
- **Posting feed lewat Make.com** (skenario *Annafi Autopost*): Webhook → filter (gambar harus dari repo ini) → Instagram
  *Create a carousel post* (Files = `files`) → Facebook Pages *Create a Post with Photos* (Photos = `foto`, page ANNAFI PRINTING).
  Alamat webhook disimpan di secret GitHub `MAKE_WEBHOOK_URL`. Kalau izin Facebook kedaluwarsa, buka Make → Credentials → Reauthorize.
- **Contoh poster**: GitHub → Actions → Run workflow → centang *Kirim contoh poster* (tanpa posting).
- Webhook bot harus memakai URL Web app berakhiran **/exec** dengan akses **Anyone** (bukan "Anyone with Google account").

Tab **Jadwal harus tetap paling kiri** (sistem GitHub membaca tab pertama).
Kalau kode diubah: **Deploy → Manage deployments → ✏️ → Version: New version → Deploy**.

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
