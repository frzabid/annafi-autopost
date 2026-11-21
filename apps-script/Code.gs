/**
 * Annafi Autopost — Manajer AI (Telegram + Gemini) & Perencana Konten Mingguan
 *
 * Dipasang di Google Sheet jadwal: Ekstensi → Apps Script → tempel seluruh file ini.
 * Panduan lengkap: README.md bagian "Manajer AI".
 *
 *  - Chat bebas ke bot Telegram  → Gemini menerjemahkan jadi perubahan di tab Jadwal
 *  - Tombol ✅ / ❌ pratinjau     → dicatat di tab Persetujuan (dibaca sistem GitHub)
 *  - Tiap Minggu 17.00           → rencana konten minggu depan ditulis ke tab Jadwal
 *
 * Batas keamanan: AI tidak bisa memposting apa pun. Harga hanya dari tab Produk
 * atau angka yang kamu ketik sendiri. Baris tidak pernah dihapus (hanya ditunda).
 */

// ============================== PENGATURAN — ISI 3 BARIS PERTAMA ==============================
const CONFIG = {
  TELEGRAM_BOT_TOKEN: 'ISI_TOKEN_BOT_TELEGRAM',
  TELEGRAM_CHAT_ID: 'ISI_CHAT_ID_TELEGRAM',
  GEMINI_API_KEY: 'ISI_API_KEY_GEMINI',
  WEB_APP_URL: '',   // opsional: alamat Web app berakhiran /exec (Deploy → Manage deployments → salin URL)
  GITHUB_TOKEN: '',  // opsional: token GitHub (izin Actions) supaya contoh poster jadi ±3 menit; kosong = ±15 menit
  GITHUB_REPO: 'frzabid/annafi-autopost',

  GEMINI_MODEL: 'gemini-flash-lite-latest',       // cepat (±1-5 detik); ganti kalau Google mengubah nama model
  GEMINI_MODEL_CADANGAN: 'gemini-flash-latest',    // lebih pintar tapi sering sibuk (503) & lambat
  STORY_PER_HARI: 2,                               // jumlah story katalog per hari
  HARI_FEED: [1, 2, 3, 5, 6],                      // hari favorit feed (1=Senin … 7=Minggu); AI memilih 4-5 di antaranya
  FEED_PER_MINGGU: '4-5',                          // jumlah feed seminggu; idenya diatur AI, tiap feed tetap menunggu ✅ darimu
  JAM_FEED: '19:00',
  // cerita bersambung (reel animasi). Naskahnya di GitHub (cerita/naskah_musim1.md); tiap part dibuatkan animasinya
  // oleh AI (sutradara Gemini + mesin animasi). Part berikutnya otomatis masuk rencana mingguan di HARI_CERITA.
  JUDUL_CERITA: 'Misteri Surat Tanpa Nama',
  HARI_CERITA: [2, 5],                             // Selasa & Jumat
  JAM_CERITA: '20:00',
  NASKAH_URL: 'https://raw.githubusercontent.com/frzabid/annafi-autopost/main/cerita/naskah_musim1.md',
  // kategori yang fotonya jarang ada di internet: hanya masuk rencana story kalau sudah ada foto sendiri
  KATEGORI_WAJIB_FOTO: ['AKSESORIS & FASHION', 'MAINAN', 'BUKU BACAAN & ISLAMI', 'KOSMETIK & PERAWATAN',
    'PESTA & ULANG TAHUN', 'SERAGAM SEKOLAH', 'RUMAH TANGGA & LAINNYA', 'MINUMAN & JAJANAN', 'PRAMUKA'],
  FOLDER_FOTO: 'Foto Produk Annafi',               // folder Google Drive untuk foto kiriman lewat bot
  MODE_PROMO: false,   // false = postingan feed umum (edukasi/info/momen) tanpa kalimat promo & tanpa harga
  JAM_RENCANA: 17,                                 // Minggu jam 17.00 rencana minggu depan dibuat
  ZONA: 'Asia/Jakarta',
  NAMA_TOKO: 'Annafi Atk Menganti',
  WA: '0895-1208-5529',
};
// ==============================================================================================

const TAB_JADWAL = 'Jadwal', TAB_PRODUK = 'Produk', TAB_KALENDER = 'Kalender', TAB_SETUJU = 'Persetujuan';
const TAB_MINTA = 'Permintaan';  // permintaan contoh poster dari chat, dikerjakan sistem GitHub
const KOLOM_MINTA = ['waktu', 'id', 'data', 'status'];
const KOLOM_JADWAL = ['tanggal', 'jam', 'jenis', 'nama', 'kategori', 'detail', 'poin', 'label_harga_1', 'harga_1',
  'label_harga_2', 'harga_2', 'gambar', 'caption', 'tunda', 'tema', 'produk'];
// tema carousel feed (lihat src/tema.py di GitHub); kosong = ditebak otomatis dari judul
const TEMA = ['umum', 'guru', 'maulid', 'ramadan', 'idulfitri', 'kemerdekaan', 'ujian', 'sekolah'];
const KOLOM_PRODUK = ['nama', 'kategori', 'detail', 'label_harga_1', 'harga_1', 'label_harga_2', 'harga_2', 'gambar', 'aktif'];
const JENIS = ['katalog', 'edukasi', 'promo', 'info', 'momen', 'cerita'];
const KOLOM_HARGA = ['harga_1', 'harga_2'];

// ============================== PEMASANGAN ==============================
/** Jalankan SEKALI dari editor (pilih fungsi `setup` → Run) setelah Deploy sebagai Web app. */
function setup() {
  const ss = SpreadsheetApp.getActive();
  siapkanTab_(ss, TAB_JADWAL, KOLOM_JADWAL, []);
  siapkanTab_(ss, TAB_PRODUK, KOLOM_PRODUK, [
    ['Pensil Joyko 6151 HB', 'PENSIL', 'Pensil HB dengan penghapus · isi 12 pcs', 'Per Pack (12 pcs)', '12000', 'Satuan', '2000', '', 'YA'],
  ]);
  siapkanTab_(ss, TAB_KALENDER, ['tanggal', 'acara', 'catatan'], KALENDER_AWAL);
  siapkanTab_(ss, TAB_SETUJU, ['waktu', 'id', 'hash', 'aksi'], []);
  siapkanTab_(ss, TAB_MINTA, KOLOM_MINTA, []);
  // tab Jadwal harus paling kiri (sistem GitHub membaca tab pertama)
  ss.setActiveSheet(ss.getSheetByName(TAB_JADWAL));
  ss.moveActiveSheet(1);

  ScriptApp.getProjectTriggers().filter(t => t.getHandlerFunction() === 'rencanaOtomatis')
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('rencanaOtomatis').timeBased().onWeekDay(ScriptApp.WeekDay.SUNDAY)
    .atHour(CONFIG.JAM_RENCANA).inTimezone(CONFIG.ZONA).create();

  let url = CONFIG.WEB_APP_URL || ScriptApp.getService().getUrl();
  const lama = (tg_('getWebhookInfo', {}).result || {}).url || '';
  if (!/\/exec$/.test(url || '') && /\/exec$/.test(lama)) url = lama;  // pertahankan webhook /exec yang sudah benar
  if (!url) throw new Error('Deploy dulu sebagai Web app (Deploy → New deployment → Web app), lalu jalankan setup lagi.');
  // alamat /dev hanya bisa dibuka pemilik → Telegram ditolak 401. Wajib alamat /exec.
  if (!/\/exec$/.test(url)) throw new Error('Alamat Web app harus berakhiran /exec. Salin dari Deploy → Manage deployments, isi di CONFIG.WEB_APP_URL, lalu jalankan setup lagi.');
  const r = tg_('setWebhook', { url: url, allowed_updates: JSON.stringify(['message', 'callback_query']) });
  kirim_('🤖 <b>Manajer AI Annafi aktif!</b>\n\n' + BANTUAN + '\n\nWebhook: ' + (r.ok ? '✅' : '❌ ' + r.description));
}

function siapkanTab_(ss, nama, kolom, isiAwal) {
  let sh = ss.getSheetByName(nama);
  if (!sh) {
    sh = ss.insertSheet(nama, ss.getNumSheets());
    sh.getRange(1, 1, 1, kolom.length).setValues([kolom]).setFontWeight('bold');
    sh.setFrozenRows(1);
    if (isiAwal.length) sh.getRange(2, 1, isiAwal.length, kolom.length).setNumberFormat('@').setValues(isiAwal);
    return sh;
  }
  // tab sudah ada: tambahkan kolom yang belum ada di ujung kanan (data lama tidak diubah)
  const header = sh.getRange(1, 1, 1, Math.max(sh.getLastColumn(), 1)).getValues()[0].map(h => String(h).trim().toLowerCase());
  const kurang = kolom.filter(k => header.indexOf(k) < 0);
  if (kurang.length) sh.getRange(1, header.filter(String).length + 1, 1, kurang.length).setValues([kurang]).setFontWeight('bold');
  return sh;
}

const KALENDER_AWAL = [
  ['01/01', 'Tahun Baru', 'agenda & kalender baru'], ['21/04', 'Hari Kartini', ''],
  ['02/05', 'Hari Pendidikan Nasional', ''], ['01/06', 'Persiapan ujian kenaikan kelas (perkiraan)', 'sesuaikan jadwal sekolah sekitar'],
  ['13/07', 'Tahun ajaran baru (perkiraan)', 'musim belanja perlengkapan sekolah; sesuaikan'],
  ['23/07', 'Hari Anak Nasional', ''], ['17/08', 'HUT Kemerdekaan RI', 'lomba, bendera, hiasan'],
  ['22/10', 'Hari Santri', ''], ['28/10', 'Sumpah Pemuda', ''], ['10/11', 'Hari Pahlawan', ''],
  ['25/11', 'Hari Guru Nasional', 'kado & kartu ucapan untuk guru'],
  ['01/12', 'Ujian akhir semester ganjil (perkiraan)', 'pensil 2B, papan ujian; sesuaikan'],
  ['22/12', 'Hari Ibu', 'kartu ucapan, kado'], ['25/12', 'Natal', ''],
  ['', 'Ramadan & Idul Fitri', 'ISI TANGGALNYA SENDIRI tiap tahun (amplop lebaran, kartu ucapan)'],
];

const BANTUAN = 'Ketik perintah biasa, contoh:\n' +
  '• <i>jadwalkan story Pensil Joyko 6151 HB besok jam 12</i>\n' +
  '• <i>buat konten edukasi hari Jumat tentang cara memilih kertas</i>\n' +
  '• <i>undur post Hari Guru ke Senin jam 7 malam</i>\n' +
  '• <i>ganti harga satuan Joyko 6151 jadi 2500</i>\n' +
  '• <i>tunda semua story hari Sabtu</i>\n' +
  '• <i>buatkan contoh poster tips merawat pulpen</i> (contoh dikirim ke sini, tidak diposting)\n' +
  '• atau ngobrol biasa: minta ide konten, caption, saran\n\n' +
  '📷 Kirim <b>foto produk</b> dengan caption = nama produk, atau unggah ke folder Drive "Foto Produk Annafi" dengan nama file = nama produk lalu kirim /foto.\n\n' +
  'Perintah cepat: /jadwal (7 hari ke depan) · /rencana (buat rencana minggu depan) · /bantuan';

// ============================== TELEGRAM WEBHOOK ==============================
function doPost(e) {
  try {
    const u = JSON.parse(e.postData.contents);
    const cache = CacheService.getScriptCache();
    if (cache.get('u' + u.update_id)) return HtmlService.createHtmlOutput('ok');  // cegah proses ganda
    cache.put('u' + u.update_id, '1', 21600);
    if (u.callback_query) tanganiTombol_(u.callback_query);
    else if (u.message && (u.message.photo || /^image\//.test((u.message.document || {}).mime_type || ''))) tanganiFoto_(u.message);
    else if (u.message && u.message.text) tanganiPesan_(u.message);
  } catch (err) {
    console.error(err);
    try { kirim_('⚠️ ' + esc_(String(err && err.message || err))); } catch (e2) {}
  }
  // HtmlService (bukan ContentService): ContentService membalas redirect 302 yang ditolak webhook Telegram
  return HtmlService.createHtmlOutput('ok');
}

function doGet() { return HtmlService.createHtmlOutput('Manajer AI Annafi aktif.'); }

function bolehAkses_(chatId) { return String(chatId) === String(CONFIG.TELEGRAM_CHAT_ID); }

function tanganiTombol_(cq) {
  const msg = cq.message || {};
  if (!bolehAkses_(msg.chat && msg.chat.id)) return;
  const bagian = String(cq.data || '').split(':');  // ok:<id>:<hash> / no:<id>:<hash>
  if (bagian.length !== 3 || ['ok', 'no'].indexOf(bagian[0]) < 0) return;
  const aksi = bagian[0] === 'ok' ? 'setuju' : 'batal';
  sheet_(TAB_SETUJU).appendRow([sekarang_(), bagian[1], bagian[2], aksi]);
  const jenis = bagian[1].charAt(0);  // R<id> = reel sudah dirender, U<id> = reel sudah diupload
  const status = jenis === 'U' && aksi === 'setuju' ? '✅ Sudah upload, tercatat. Terima kasih!'
    : jenis === 'R' && aksi === 'setuju' ? '✅ Video siap. Di jam tayang aku ingatkan upload + kirim captionnya.'
    : aksi === 'setuju' ? '✅ Disetujui — akan tayang sesuai jadwal.'
    : '❌ Dibatalkan — tidak akan diposting. Ubah isinya di sheet kalau mau dijadwalkan ulang.';
  tg_('answerCallbackQuery', { callback_query_id: cq.id, text: status });
  tg_('editMessageText', { chat_id: msg.chat.id, message_id: msg.message_id,
    text: (msg.text || '') + '\n\n' + status, disable_web_page_preview: true });
}

function tanganiPesan_(m) {
  if (!bolehAkses_(m.chat.id)) return;  // abaikan orang lain yang menemukan bot ini
  const teks = m.text.trim();
  const perintah = teks.split(/\s+/)[0].toLowerCase().replace(/@.*$/, '');
  if (perintah === '/start' || perintah === '/bantuan' || perintah === '/help') return kirim_(BANTUAN);
  if (perintah === '/jadwal') return kirim_(ringkasJadwal_(7));
  if (perintah === '/rencana') return kirim_(buatRencanaMingguan_(true));
  if (perintah === '/foto') return sinkronFoto(true);
  tg_('sendChatAction', { chat_id: m.chat.id, action: 'typing' });
  kirim_(manajer_(teks));
}

// ============================== FOTO PRODUK (TELEGRAM & FOLDER DRIVE) ==============================
/** Cari produk dari teks bebas: sama persis, atau semua kata/kode teks ada di nama produk
 *  (urutan, huruf besar-kecil, tanda - dan spasi diabaikan). Hasil {p} kalau pasti, {mirip} kalau ragu. */
function cocokProduk_(semua, teks) {
  const n = String(teks).toLowerCase().trim();
  const persis = semua.filter(x => x.nama.toLowerCase() === n)[0];
  if (persis) return { p: persis, mirip: [] };
  const rapat = t => String(t).toLowerCase().replace(/[^a-z0-9]/g, '');
  const kata = n.match(/[a-z0-9]+/g) || [];
  const mirip = kata.length ? semua.filter(x => { const r = rapat(x.nama); return kata.every(k => r.indexOf(k) >= 0); }) : [];
  return mirip.length === 1 ? { p: mirip[0], mirip: [] } : { p: null, mirip: mirip };
}

function folderFoto_() {
  const it = DriveApp.getFoldersByName(CONFIG.FOLDER_FOTO);
  return it.hasNext() ? it.next() : DriveApp.createFolder(CONFIG.FOLDER_FOTO);
}

/** Bagikan file (lihat saja) supaya bisa dibaca sistem poster, isi kolom gambar di Produk & jadwal story mendatang. */
function pasangFoto_(tabel, p, file) {
  file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  const link = 'https://drive.google.com/file/d/' + file.getId() + '/view';
  ubahBaris_(TAB_PRODUK, tabel.header, p._row, { gambar: link });
  p.gambar = link;
  const jt = bacaTabel_(TAB_JADWAL), hariIni = keDate_(fmtTgl_(new Date()));
  let n = 0;
  jt.rows.forEach(r => {
    const d = keDate_(r.tanggal);
    if (d && d >= hariIni && (r.jenis || 'katalog').toLowerCase() === 'katalog' && r.nama.toLowerCase() === p.nama.toLowerCase()) {
      ubahBaris_(TAB_JADWAL, jt.header, r._row, { gambar: link }); n++;
    }
  });
  return n;
}

function saranProduk_(semua, teks, mirip) {
  const saran = (mirip.length ? mirip : produkRelevan_(semua, teks, 6)).slice(0, 6);
  return saran.length ? '\nMaksudnya salah satu ini? (tekan untuk salin)\n' + saran.map(x => '• <code>' + esc_(x.nama) + '</code>').join('\n') : '';
}

/** Foto dikirim ke bot dengan caption nama produk. */
function tanganiFoto_(m) {
  if (!bolehAkses_(m.chat.id)) return;
  const nama = String(m.caption || '').trim();
  if (!nama) return kirim_('📷 Fotonya belum ada keterangan. Kirim ulang dengan <b>caption = nama produk</b>, mis. <i>Al-Quran Khot Besar</i>.');
  const tabel = bacaTabel_(TAB_PRODUK);
  const semua = tabel.rows.filter(p => p.nama);
  const c = cocokProduk_(semua, nama);
  if (!c.p) return kirim_('❓ Produk "<b>' + esc_(nama) + '</b>" ' + (c.mirip.length ? 'cocok dengan beberapa produk.' : 'tidak ketemu di tab Produk.') +
    saranProduk_(semua, nama, c.mirip) + '\n\nKirim ulang fotonya dengan caption nama yang persis.');
  const fileId = m.photo ? m.photo[m.photo.length - 1].file_id : m.document.file_id;  // foto terbesar
  const f = tg_('getFile', { file_id: fileId });
  if (!f.ok) throw new Error('Foto gagal diambil dari Telegram: ' + f.description);
  const blob = UrlFetchApp.fetch('https://api.telegram.org/file/bot' + CONFIG.TELEGRAM_BOT_TOKEN + '/' + f.result.file_path)
    .getBlob().setName(c.p.nama + '.jpg');
  const n = pasangFoto_(tabel, c.p, folderFoto_().createFile(blob));
  kirim_('✅ Foto disimpan untuk <b>' + esc_(c.p.nama) + '</b> (baris ' + c.p._row + ' tab Produk).' +
    (n ? '\n' + n + ' jadwal story produk ini ikut diperbarui.' : ''));
}

/** Foto yang diunggah langsung ke folder Drive "Foto Produk Annafi" dengan NAMA FILE = nama produk.
 *  Jalan otomatis tiap jam, atau kirim /foto ke bot untuk menjalankan sekarang. */
function sinkronFoto(laporSelalu) {
  laporSelalu = laporSelalu === true;  // pemicu jam mengirim objek event, bukan true
  const tabel = bacaTabel_(TAB_PRODUK);
  const semua = tabel.rows.filter(p => p.nama);
  const terpakai = semua.map(p => p.gambar).join(' ');
  const props = PropertiesService.getScriptProperties();
  const dilapor = JSON.parse(props.getProperty('fotoDilapor') || '[]');
  const ok = [], gagal = [];
  const files = folderFoto_().getFiles();
  while (files.hasNext()) {
    const f = files.next();
    if (!/^image\//.test(f.getMimeType()) || terpakai.indexOf(f.getId()) >= 0) continue;
    const nama = f.getName().replace(/\.[a-z0-9]+$/i, '');
    const c = cocokProduk_(semua, nama);
    if (c.p) { const n = pasangFoto_(tabel, c.p, f); ok.push('• ' + esc_(c.p.nama) + (n ? ' (+' + n + ' jadwal)' : '')); }
    else if (laporSelalu || dilapor.indexOf(f.getId()) < 0) {
      gagal.push('• <b>' + esc_(f.getName()) + '</b>: ' + (c.mirip.length ? 'cocok ke ' + c.mirip.length + ' produk, perjelas namanya'
        : 'tidak ada produk dengan nama itu') + saranProduk_(semua, nama, c.mirip).replace(/\n/g, '\n   '));
      dilapor.push(f.getId());
    }
  }
  props.setProperty('fotoDilapor', JSON.stringify(dilapor.slice(-300)));
  if (ok.length || gagal.length || laporSelalu) kirim_('📁 <b>Foto dari folder Drive</b>\n' +
    (ok.length ? '✅ Terpasang:\n' + ok.join('\n') + '\n' : '') +
    (gagal.length ? '⚠️ Belum terpasang (ganti nama filenya jadi nama produk):\n' + gagal.join('\n') : '') +
    (!ok.length && !gagal.length ? 'Tidak ada foto baru.' : ''));
}

/** Jalankan sekali dari editor: izin Google Drive + pemicu sinkron foto tiap jam. */
function izinkanDrive() {
  const folder = folderFoto_();
  ScriptApp.getProjectTriggers().filter(t => t.getHandlerFunction() === 'sinkronFoto').forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('sinkronFoto').timeBased().everyHours(1).create();
  kirim_('📁 Folder foto siap: <b>' + esc_(folder.getName()) + '</b>.\nCara 1: kirim foto ke bot dengan caption nama produk.\n' +
    'Cara 2: unggah ke folder itu dengan <b>nama file = nama produk</b> (dicek tiap jam, atau kirim /foto).');
  sinkronFoto(true);
}

// ============================== MANAJER AI ==============================
function manajer_(instruksi) {
  const semuaProduk = bacaTabel_(TAB_PRODUK).rows.filter(p => p.nama);
  const produk = produkRelevan_(semuaProduk, instruksi, 60);
  const jadwal = bacaTabel_(TAB_JADWAL).rows;
  const hariIni = new Date();
  const dekat = jadwal.filter(r => {
    const d = keDate_(r.tanggal);
    return d && d >= tambahHari_(hariIni, -7) && d <= tambahHari_(hariIni, 21);
  });
  const prompt = [
    'Kamu asisten AI sekaligus manajer konten Instagram/Facebook untuk toko alat tulis "' + CONFIG.NAMA_TOKO + '" (Menganti, Gresik).',
    'Hari ini ' + fmtHari_(hariIni) + ' (' + fmtTgl_(hariIni) + '), zona WIB.',
    'Kamu mengobrol dengan pemilik toko lewat Telegram. Kalau ia bertanya, minta ide, caption, saran, atau sekadar ngobrol,',
    'jawab langsung di "balasan" tanpa aksi (boleh topik umum juga). Kalau ia meminta perubahan jadwal/produk, buat aksi.',
    'Kalau ia minta CONTOH poster/desain/story, buat aksi "contoh" lengkap dengan isi yang kamu tulis sendiri (tidak diposting).',
    'Kalau ia ingin contoh terakhir dijadwalkan ("jadwalkan yang tadi", "pakai ini hari Sabtu"), buat aksi "jadwalkan_contoh".',
    'CONTOH TERAKHIR: ' + (PropertiesService.getScriptProperties().getProperty('contohTerakhir') || 'belum ada'),
    '',
    'ATURAN:',
    (CONFIG.MODE_PROMO ? '- jenis hanya: katalog (story produk), edukasi, promo, info, momen (postingan feed).'
      : '- jenis hanya: katalog (story produk), edukasi, info, momen (postingan feed). Konten promo SEDANG DIMATIKAN: ' +
        'feed harus informatif/umum, tanpa harga dan tanpa kata promo/diskon/murah/beli sekarang. Kalau diminta promo, jelaskan di balasan.'),
    '- jenis "cerita" = reel animasi cerita bersambung "' + CONFIG.JUDUL_CERITA + '" (bukan feed). nama WAJIB "' + CONFIG.JUDUL_CERITA +
      ' Part N", jam ' + CONFIG.JAM_CERITA + ', tanpa poin/gambar; "detail" = arahan untuk sutradara AI (opsional). Part di naskah: ' +
      partSiap_().join(', ') + '.',
    '- Pemilik bisa brainstorm cerita denganmu (ide part, dialog, tokoh, twist): jawab di "balasan" berdasarkan NASKAH CERITA di bawah.',
    '  Minta video part dibuat/dibuat ulang ("buat part 1", "ulang part 2, Raka lebih panik") = aksi "contoh" dengan data',
    '  {format:"cerita", jenis:"cerita", nama:"' + CONFIG.JUDUL_CERITA + ' Part N", detail: arahan}. Untuk "ulang", detail WAJIB diisi',
    '  (rangkum arahannya; kalau tidak ada, tulis "versi baru, variasikan adegan & kamera"). Hasil video masuk ±5-10 menit.',
    '  Menjadwalkan part = aksi "tambah" jenis cerita. Ide perubahan naskah: tulis jadi arahan (naskah aslinya diubah di GitHub).',
    '- Untuk katalog, "nama" HARUS persis salah satu nama di PRODUK; harga diisi sistem, jangan tulis harga.',
    '- Jangan mengarang harga. Ubah harga hanya kalau pemilik menyebut angkanya di instruksi.',
    '- tanggal format dd/MM/yyyy, jam format HH:mm. Sebaiknya jam DIKOSONGKAN: sistem otomatis menyebar story di jam ramai',
    '  (07.00, 12.00, 16.00, 19.00) dan feed di 19.00. Kalau mengisi jam, jangan beri jam yang sama untuk 2 story di hari yang sama.',
    '- poin dipisah titik koma ;, maksimal 5 poin singkat. Judul (nama) maksimal ~6 kata.',
    '- "baris" hanya boleh nomor baris yang ada di JADWAL atau PRODUK di bawah.',
    '- Feed tampil sebagai carousel bertema. Kolom "tema" (opsional) salah satu: ' + TEMA.join(', ') + '. Kolom "produk" (opsional) = nama produk dipisah ; untuk slide foto produk.',
    '- Tidak ada aksi hapus; untuk membatalkan pakai aksi "tunda".',
    '- Kalau instruksi kurang jelas atau tidak bisa dilakukan, jangan buat aksi; tanyakan di "balasan".',
    '- "balasan": bahasa Indonesia santai dan ramah. Kalau ada aksi, jelaskan singkat apa yang kamu lakukan. Jawaban obrolan boleh',
    '  lebih panjang bila perlu, tapi tetap ringkas (maks ~12 kalimat). Jangan pakai format Markdown (*, #); boleh emoji secukupnya.',
    '- Aksi "contoh": data.format "feed" (carousel: jenis, nama judul maks 6 kata, detail 1 kalimat, poin 3-4 "Judul: isi",',
    '  tema, produk opsional) atau "story" (nama PERSIS dari PRODUK; harga diisi sistem).',
    '',
    'NASKAH CERITA (tokoh, kostum, isi tiap part): ' + naskahCerita_(),
    '',
    'KATEGORI PRODUK: ' + JSON.stringify(uniq_(semuaProduk.map(p => p.kategori))),
    'PRODUK yang relevan dengan instruksi (sebagian dari ' + semuaProduk.length + '): ' + JSON.stringify(produk.map(p => ({ baris: p._row, nama: p.nama, kategori: p.kategori,
      harga: [p.label_harga_1, p.harga_1, p.label_harga_2, p.harga_2].filter(String).join(' ') }))),
    'JADWAL (7 hari lalu s/d 3 minggu ke depan): ' + JSON.stringify(dekat.map(r => ({ baris: r._row,
      tanggal: r.tanggal, jam: r.jam, jenis: r.jenis || 'katalog', nama: r.nama, tunda: r.tunda }))),
    '',
    'PERCAKAPAN SEBELUMNYA (lama → baru): ' + JSON.stringify(riwayatChat_()),
    '',
    'PESAN PEMILIK SEKARANG: """' + instruksi + '"""',
    '',
    'Jawab HANYA JSON: {"balasan": string, "aksi": [ ' +
      '{"tipe":"tambah","data":{tanggal,jam,jenis,nama,kategori,detail,poin,gambar,caption,tema,produk,produk_harga}} | ' +
      '{"tipe":"ubah","baris":n,"data":{kolom: nilai}} | {"tipe":"tunda","baris":n} | ' +
      '{"tipe":"ubah_produk","baris":n,"data":{kolom: nilai}} | {"tipe":"rencana"} | ' +
      '{"tipe":"contoh","data":{format,jenis,nama,detail,poin,tema,produk}} | {"tipe":"jadwalkan_contoh","tanggal","jam"} ]}',
    '(produk_harga opsional: nama produk dari PRODUK yang harganya ditampilkan di poster promo; gambar: kosong, "cari", atau link)',
  ].join('\n');

  const hasil = gemini_(prompt);
  const laporan = [];
  (hasil.aksi || []).slice(0, 40).forEach(a => {
    try { laporan.push(jalankanAksi_(a, instruksi, semuaProduk)); }
    catch (err) { laporan.push('⚠️ ' + esc_(err.message)); }
  });
  const jawab = esc_(hasil.balasan || 'Oke.') + (laporan.length ? '\n\n' + laporan.join('\n') : '');
  simpanChat_(instruksi, hasil.balasan || '');
  return jawab;
}

/** Ingatan obrolan singkat (8 pesan terakhir, 6 jam) supaya Gemini paham konteks "yang tadi". */
function riwayatChat_() {
  return JSON.parse(CacheService.getScriptCache().get('riwayatChat') || '[]');
}
function simpanChat_(pesan, balasan) {
  const r = riwayatChat_();
  r.push({ pemilik: String(pesan).slice(0, 500), kamu: String(balasan).slice(0, 700) });
  CacheService.getScriptCache().put('riwayatChat', JSON.stringify(r.slice(-8)), 21600);
}

/** Permintaan contoh poster → tab Permintaan; sistem GitHub merender dan mengirimnya ke Telegram. */
function mintaContoh_(baris) {
  const sh = siapkanTab_(SpreadsheetApp.getActive(), TAB_MINTA, KOLOM_MINTA, []);
  const id = 'c' + Utilities.getUuid().replace(/-/g, '').slice(0, 7); // huruf di depan: supaya Sheets tidak mengubahnya jadi angka
  sh.appendRow([sekarang_(), id, JSON.stringify(baris), 'baru']);
  PropertiesService.getScriptProperties().setProperty('contohTerakhir', JSON.stringify(baris));
  let cepat = false;
  if (CONFIG.GITHUB_TOKEN) {
    const r = UrlFetchApp.fetch('https://api.github.com/repos/' + CONFIG.GITHUB_REPO + '/actions/workflows/autopost.yml/dispatches', {
      method: 'post', contentType: 'application/json', muteHttpExceptions: true, payload: JSON.stringify({ ref: 'main' }),
      headers: { Authorization: 'Bearer ' + CONFIG.GITHUB_TOKEN, Accept: 'application/vnd.github+json' } });
    cepat = r.getResponseCode() === 204;
  }
  if (baris.jenis === 'cerita')
    return '🎬 <b>' + esc_(baris.nama) + '</b> sedang dibuat AI (adegan → animasi → suara). Videonya masuk ke sini ' +
      (cepat ? '±8 menit lagi.' : 'dalam ±15-25 menit.') + '\nSudah oke? Balas: <i>jadwalkan yang tadi hari Selasa</i>.';
  return '🎨 Contoh <b>' + esc_(baris.nama) + '</b> sedang dibuat, masuk ke sini ' + (cepat ? '±3 menit lagi.' : 'dalam ±15 menit.') +
    '\nMau dijadwalkan? Balas misalnya: <i>jadwalkan yang tadi hari Sabtu</i>.';
}

/** Pilih produk yang kata-katanya muncul di instruksi (hemat kuota Gemini untuk daftar produk yang panjang). */
function produkRelevan_(produk, instruksi, maks) {
  // Cocokkan per KATA (bukan potongan huruf: "per" tidak lagi cocok ke "paper"), kata yang terlalu umum diabaikan,
  // dan kata langka diberi bobot lebih besar supaya "krayon" mengalahkan kata yang muncul di ratusan produk.
  const SINONIM = { crayon: 'krayon', pulpen: 'bolpen', pena: 'bolpen', pen: 'bolpen', stabilo: 'highlighter',
    tipex: 'tip', notebook: 'buku', binder: 'binder', cat: 'cat', lem: 'lem' };
  const BUANG = ['yang', 'dan', 'untuk', 'jam', 'besok', 'hari', 'story', 'buat', 'buatkan', 'jadwalkan', 'jadwal', 'ganti', 'harga',
    'tolong', 'dengan', 'ubah', 'kedepan', 'depan', 'dalam', 'satu', 'minggu', 'seluruh', 'semua', 'katalog', 'fokus', 'sudah',
    'kamu', 'bebas', 'mengatur', 'sehari', 'atau', 'per', 'merk', 'barang', 'produk', 'postingan', 'poster', 'contoh', 'ini',
    'itu', 'saja', 'juga', 'bisa', 'mau', 'ingin', 'aku', 'saya', 'tiap', 'setiap', 'kali', 'pagi', 'siang', 'sore', 'malam'];
  const kata = uniq_((String(instruksi).toLowerCase().match(/[a-z0-9]{3,}/g) || []).map(k => SINONIM[k] || k))
    .filter(k => BUANG.indexOf(k) < 0);
  const token = produk.map(p => (p.nama + ' ' + (p.kategori || '')).toLowerCase().match(/[a-z0-9]+/g) || []);
  const cocok = (tok, k) => tok.some(t => t === k || (k.length >= 4 && t.indexOf(k) === 0));
  const bobot = {};
  kata.forEach(k => {
    const df = token.filter(tok => cocok(tok, k)).length;
    if (df && df <= produk.length * 0.15) bobot[k] = (/\d/.test(k) ? 3 : 1) / Math.log(2 + df);  // terlalu umum = diabaikan
  });
  return produk.map((p, i) => ({ p: p, skor: Object.keys(bobot).reduce((s, k) => s + (cocok(token[i], k) ? bobot[k] : 0), 0) }))
    .filter(x => x.skor > 0).sort((a, b) => b.skor - a.skor).slice(0, maks).map(x => x.p);
}

/** Produk di kategori "wajib foto" baru boleh dipilih untuk story kalau kolom gambar sudah terisi. */
function bisaStory_(p) {
  return !!p.gambar || CONFIG.KATEGORI_WAJIB_FOTO.indexOf(String(p.kategori || '').toUpperCase()) < 0;
}

function uniq_(arr) { return arr.filter((x, i) => x && arr.indexOf(x) === i); }

/** Ambil sampel produk aktif per kategori supaya prompt perencana tetap ringkas. */
function sampelProduk_(produk, perKategori, hindari) {
  const grup = {};
  produk.forEach(p => { (grup[p.kategori || 'LAINNYA'] = grup[p.kategori || 'LAINNYA'] || []).push(p); });
  const out = [];
  Object.keys(grup).forEach(k => {
    const segar = grup[k].filter(p => hindari.indexOf(p.nama) < 0);
    const pool = (segar.length ? segar : grup[k]).slice();
    for (let i = pool.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); const t = pool[i]; pool[i] = pool[j]; pool[j] = t; }
    out.push.apply(out, pool.slice(0, perKategori));
  });
  return out;
}

function jalankanAksi_(a, instruksi, produk) {
  const angkaDiInstruksi = (instruksi.replace(/[.,]/g, '').match(/\d+/g) || []);
  const cekHarga = data => KOLOM_HARGA.forEach(k => {
    if (data[k] === undefined || data[k] === '') return;
    const n = String(data[k]).replace(/\D/g, '');
    if (angkaDiInstruksi.indexOf(n) < 0) throw new Error('Perubahan harga ' + n + ' ditolak: angkanya tidak ada di pesanmu.');
    data[k] = n;
  });
  if (a.tipe === 'rencana') return buatRencanaMingguan_(true);
  if (a.tipe === 'contoh') {
    const d = Object.assign({}, a.data || {});
    const story = String(d.format || '').toLowerCase() === 'story' || String(d.jenis || '').toLowerCase() === 'katalog';
    const cerita = String(d.format || '').toLowerCase() === 'cerita' || String(d.jenis || '').toLowerCase() === 'cerita';
    d.jenis = cerita ? 'cerita' : story ? 'katalog' : (d.jenis && d.jenis !== 'katalog' ? d.jenis : 'edukasi');
    d.tanggal = fmtTgl_(new Date());
    return mintaContoh_(barisKonten_(d, produk));
  }
  if (a.tipe === 'jadwalkan_contoh') {
    const lama = PropertiesService.getScriptProperties().getProperty('contohTerakhir');
    if (!lama) throw new Error('Belum ada contoh yang bisa dijadwalkan.');
    const baris = barisKonten_(Object.assign(JSON.parse(lama), { tanggal: a.tanggal, jam: a.jam || '' }), produk);
    tambahBaris_(TAB_JADWAL, KOLOM_JADWAL, baris);
    return '📅 Dijadwalkan: <b>' + esc_(baris.nama) + '</b> — ' + esc_(baris.tanggal) + ' ' + esc_(baris.jam || '(jam ramai)');
  }
  if (a.tipe === 'tambah') {
    const baris = barisKonten_(a.data || {}, produk);
    tambahBaris_(TAB_JADWAL, KOLOM_JADWAL, baris);
    return '➕ ' + esc_(baris.jenis) + ': <b>' + esc_(baris.nama) + '</b> — ' + esc_(baris.tanggal) + ' ' + esc_(baris.jam || '(jam ramai)');
  }
  if (a.tipe === 'ubah' || a.tipe === 'tunda') {
    const tab = bacaTabel_(TAB_JADWAL);
    const r = tab.rows.filter(x => x._row === Number(a.baris))[0];
    if (!r) throw new Error('Baris ' + a.baris + ' tidak ditemukan di Jadwal.');
    const data = a.tipe === 'tunda' ? { tunda: 'YA' } : bersihkanData_(a.data || {}, KOLOM_JADWAL);
    if (data.jenis && JENIS.indexOf(data.jenis) < 0) throw new Error('Jenis "' + data.jenis + '" tidak dikenal.');
    cekHarga(data);
    ubahBaris_(TAB_JADWAL, tab.header, r._row, data);
    return (a.tipe === 'tunda' ? '⏸️ Ditunda: ' : '✏️ Diubah: ') + '<b>' + esc_(r.nama) + '</b> (baris ' + r._row + ')' +
      (a.tipe === 'ubah' ? ' → ' + esc_(Object.keys(data).map(k => k + '=' + data[k]).join(', ')) : '');
  }
  if (a.tipe === 'ubah_produk') {
    const tab = bacaTabel_(TAB_PRODUK);
    const r = tab.rows.filter(x => x._row === Number(a.baris))[0];
    if (!r) throw new Error('Baris produk ' + a.baris + ' tidak ditemukan.');
    const data = bersihkanData_(a.data || {}, KOLOM_PRODUK);
    cekHarga(data);
    ubahBaris_(TAB_PRODUK, tab.header, r._row, data);
    return '🏷️ Produk diubah: <b>' + esc_(r.nama) + '</b> → ' + esc_(Object.keys(data).map(k => k + '=' + data[k]).join(', ')) +
      '\n(jadwal story yang sudah ada tidak ikut berubah; minta aku ubah juga kalau perlu)';
  }
  throw new Error('Aksi "' + a.tipe + '" tidak dikenal.');
}

/** Rapikan satu baris konten dari AI; harga katalog/promo SELALU diambil dari tab Produk. */
function barisKonten_(d, produk) {
  const jenis = String(d.jenis || 'katalog').toLowerCase();
  if (JENIS.indexOf(jenis) < 0) throw new Error('Jenis "' + jenis + '" tidak dikenal.');
  if (!keDate_(d.tanggal)) throw new Error('Tanggal "' + d.tanggal + '" tidak terbaca.');
  if (jenis === 'cerita') {
    const m = String(d.nama || '').match(/part\s*(\d+)/i);
    if (!m) throw new Error('Cerita harus menyebut nomor part, misal "' + CONFIG.JUDUL_CERITA + ' Part 1".');
    return { tanggal: fmtTgl_(keDate_(d.tanggal)), jam: rapikanJam_(d.jam || CONFIG.JAM_CERITA), jenis: 'cerita',
      nama: CONFIG.JUDUL_CERITA + ' Part ' + (+m[1]), kategori: '', detail: String(d.detail || '').slice(0, 300), poin: '',
      gambar: '', caption: d.caption || '',
      tunda: '', tema: '', produk: '' };
  }
  const poin = Array.isArray(d.poin) ? d.poin.join('; ') : String(d.poin || '');
  const baris = { tanggal: fmtTgl_(keDate_(d.tanggal)), jam: rapikanJam_(d.jam), jenis: jenis, nama: String(d.nama || '').trim(),
    kategori: String(d.kategori || '').toUpperCase(), detail: d.detail || '', poin: poin, gambar: d.gambar || '',
    caption: d.caption || '', tunda: '', tema: TEMA.indexOf(String(d.tema || '').toLowerCase()) >= 0 ? String(d.tema).toLowerCase() : '',
    produk: '' };
  if (jenis !== 'katalog' && d.produk) {  // foto produk untuk slide kolase carousel: hanya produk yang SUDAH punya foto
    const daftar = (Array.isArray(d.produk) ? d.produk : String(d.produk).split(/;|\n/)).map(x => String(x).trim()).filter(String);
    baris.produk = daftar.map(n => cariProduk_(produk, n)).filter(p => p && p.gambar).slice(0, 4).map(p => p.nama).join('; ');
  }
  if (!CONFIG.MODE_PROMO && jenis === 'promo') throw new Error('konten promo sedang dimatikan (MODE_PROMO: false)');
  const cari = jenis === 'katalog' ? baris.nama : (CONFIG.MODE_PROMO ? d.produk_harga || '' : '');
  if (cari) {
    const p = cariProduk_(produk, cari);
    if (!p) throw new Error('Produk "' + cari + '" tidak ada di tab Produk.');
    if (!p.harga_1) throw new Error('Produk "' + p.nama + '" belum punya harga di tab Produk.');
    ['label_harga_1', 'harga_1', 'label_harga_2', 'harga_2'].forEach(k => baris[k] = p[k] || '');
    if (jenis === 'katalog') {
      baris.nama = p.nama; baris.kategori = (p.kategori || baris.kategori).toUpperCase();
      baris.detail = p.detail || baris.detail; baris.gambar = p.gambar || '';
    } else {
      // feed: harga harus jelas milik produk apa, dan fotonya foto produk itu
      const lbl = String(p.label_harga_1 || '').trim();
      baris.label_harga_1 = p.nama + (lbl && !/^harga$/i.test(lbl) ? ' · ' + lbl : '');
      baris.gambar = p.gambar || ('cari: ' + p.nama);
    }
  } else if (jenis !== 'katalog' && /^cari$/i.test(String(baris.gambar).trim())) {
    baris.gambar = '';  // judul feed bukan kata kunci foto yang bisa diandalkan
  }
  if (!baris.nama) throw new Error('Judul/nama kosong.');
  if (jenis !== 'katalog' && !baris.poin && !baris.harga_1) throw new Error('Konten "' + baris.nama + '" belum punya poin.');
  return baris;
}

function cariProduk_(produk, nama) {
  const n = String(nama).toLowerCase().trim();
  return produk.filter(p => p.nama.toLowerCase() === n)[0] ||
    produk.filter(p => p.nama.toLowerCase().indexOf(n) >= 0 || n.indexOf(p.nama.toLowerCase()) >= 0)[0];
}

function bersihkanData_(data, kolom) {
  const out = {};
  Object.keys(data).forEach(k => {
    const kk = String(k).toLowerCase();
    if (kolom.indexOf(kk) < 0) return;
    let v = data[k];
    if (Array.isArray(v)) v = v.join('; ');
    if (kk === 'tanggal') { const d = keDate_(v); if (!d) throw new Error('Tanggal "' + v + '" tidak terbaca.'); v = fmtTgl_(d); }
    if (kk === 'jam') v = rapikanJam_(v);
    if (kk === 'jenis') v = String(v).toLowerCase();
    out[kk] = v === null || v === undefined ? '' : String(v);
  });
  return out;
}

// ============================== PERENCANA MINGGUAN ==============================
function rencanaOtomatis() { kirim_(buatRencanaMingguan_(false)); }

function buatRencanaMingguan_(paksa) {
  const produk = bacaTabel_(TAB_PRODUK).rows.filter(p => p.nama && p.harga_1 && !/^(tidak|no|0)$/i.test(p.aktif || ''));
  if (!produk.length) return '⚠️ Tab <b>Produk</b> masih kosong. Isi dulu daftar produk & harga, lalu ketik /rencana.';
  const senin = seninBerikut_(new Date());
  const kunci = 'rencana_' + fmtKunci_(senin);
  const props = PropertiesService.getScriptProperties();
  if (!paksa && props.getProperty(kunci)) return 'ℹ️ Rencana minggu ' + fmtTgl_(senin) + ' sudah pernah dibuat.';

  const jadwal = bacaTabel_(TAB_JADWAL).rows;
  const riwayat = jadwal.filter(r => { const d = keDate_(r.tanggal); return d && d >= tambahHari_(senin, -28) && d < senin; });
  const sudahAda = jadwal.filter(r => { const d = keDate_(r.tanggal); return d && d >= senin && d < tambahHari_(senin, 7); });
  const hari = [];
  for (let i = 0; i < 7; i++) hari.push(fmtHari_(tambahHari_(senin, i)) + ' ' + fmtTgl_(tambahHari_(senin, i)));
  const kalender = bacaTabel_(TAB_KALENDER).rows.filter(k => k.acara).map(k => k.tanggal + ' — ' + k.acara + (k.catatan ? ' (' + k.catatan + ')' : ''));
  const hariFeed = CONFIG.HARI_FEED.map(i => hari[(i + 6) % 7]);

  const prompt = [
    'Kamu manajer konten Instagram/Facebook toko alat tulis "' + CONFIG.NAMA_TOKO + '" (pembeli: pelajar, orang tua, guru, kantor).',
    'Buat rencana konten untuk minggu: ' + hari.join(', ') + '.',
    '',
    'BUTUHKAN:',
    '1. "story": tepat ' + CONFIG.STORY_PER_HARI + ' produk per hari (7 hari), nama PERSIS dari PRODUK. Gilir produk,',
    '   hindari produk yang muncul di RIWAYAT 2 minggu terakhir kalau masih ada pilihan lain, dahulukan yang relevan dengan momen.',
    '2. "feed": ' + CONFIG.FEED_PER_MINGGU + ' postingan seminggu, ide & harinya KAMU yang atur. Utamakan hari: ' + hariFeed.join(', ') +
      ' (boleh geser kalau ada momen di KALENDER). Maksimal 1 feed per hari. Kalau SUDAH TERJADWAL sudah berisi feed, cukup lengkapi sampai total ' + CONFIG.FEED_PER_MINGGU + '.',
    '   Variasikan: jangan dua feed berturut-turut dengan jenis/topik yang sama.',
    (CONFIG.MODE_PROMO
      ? '   Campuran: 1 edukasi, 1 promo, 1 info atau momen. Momen dijadwalkan SEBELUM/TEPAT di harinya, promo momen 2-3 hari sebelumnya.'
      : '   Campuran: edukasi, info, dan momen (TANPA promo). Isinya umum & bermanfaat: tips, pengetahuan, ucapan hari besar.\n' +
        '   DILARANG: harga, kata promo/diskon/murah/hemat/spesial/beli sekarang, ajakan belanja. produk_harga selalu "".'),
    '   Tiap feed: jenis, tanggal (dd/MM/yyyy), nama (judul maks 6 kata), detail (1 kalimat), poin (3-4 poin singkat,',
    '   boleh format "Judul: isi" — tiap poin jadi 1 slide carousel, jadi isi 6-14 kata yang bermakna), gambar (selalu ""),',
    '   tema (salah satu: ' + TEMA.join(', ') + '; pilih yang paling cocok dengan topik/momen, "umum" untuk tips biasa),',
    '   produk (opsional, maks 4 nama PERSIS dari PRODUK_BERFOTO yang relevan dengan topik; untuk slide foto produk TANPA harga),',
    '   produk_harga (opsional: nama PERSIS dari PRODUK kalau promo menampilkan harga; JANGAN mengarang harga atau harga paket).',
    '   Jangan ulang tema yang ada di RIWAYAT. Bahasa Indonesia santai, cocok untuk toko ATK lokal.',
    '3. "ringkasan": 1-2 kalimat strategi minggu ini.',
    '',
    'PRODUK (pilihan acak per kategori): ' + JSON.stringify(sampelProduk_(produk.filter(bisaStory_), 8, riwayat.map(r => r.nama)).map(p => ({ nama: p.nama, kategori: p.kategori }))),
    'PRODUK_BERFOTO (boleh dipakai di kolom produk): ' + JSON.stringify(produk.filter(p => p.gambar).slice(0, 80).map(p => p.nama)),
    'KALENDER (dd/MM tiap tahun): ' + JSON.stringify(kalender),
    'RIWAYAT 4 minggu: ' + JSON.stringify(riwayat.map(r => [r.tanggal, r.jenis || 'katalog', r.nama])),
    'SUDAH TERJADWAL minggu ini (jangan duplikat, cukup lengkapi): ' + JSON.stringify(sudahAda.map(r => [r.tanggal, r.jenis || 'katalog', r.nama])),
    '',
    'Jawab HANYA JSON: {"ringkasan": string, "story": [{"tanggal": "dd/MM/yyyy", "produk": string}], ' +
      '"feed": [{"jenis","tanggal","nama","detail","poin":[string],"gambar","tema","produk":[string],"produk_harga"}]}',
  ].join('\n');

  const hasil = gemini_(prompt);
  const ditambah = [], gagal = [];
  (hasil.story || []).slice(0, 7 * CONFIG.STORY_PER_HARI + 3).forEach(s => {
    try {
      const b = barisKonten_({ tanggal: s.tanggal, jam: '', jenis: 'katalog', nama: s.produk }, produk);
      if (!dalamMinggu_(b.tanggal, senin)) throw new Error('tanggal di luar minggu');
      tambahBaris_(TAB_JADWAL, KOLOM_JADWAL, b); ditambah.push(b);
    } catch (e) { gagal.push('story ' + s.produk + ': ' + e.message); }
  });
  (hasil.feed || []).slice(0, 5).forEach(f => {
    try {
      const b = barisKonten_(Object.assign({}, f, { jam: CONFIG.JAM_FEED }), produk);
      if (b.jenis === 'katalog') throw new Error('feed tidak boleh berjenis katalog');
      if (!dalamMinggu_(b.tanggal, senin)) throw new Error('tanggal di luar minggu');
      tambahBaris_(TAB_JADWAL, KOLOM_JADWAL, b); ditambah.push(b);
    } catch (e) { gagal.push('feed ' + (f.nama || '?') + ': ' + e.message); }
  });
  // cerita bersambung: part berikutnya di hari cerita (diatur sistem, bukan AI), hanya part yang animasinya sudah jadi
  try {
    const nomor = r => { const m = String(r.nama).match(/part\s*(\d+)/i); return m ? +m[1] : 0; };
    const cerita = jadwal.filter(r => String(r.jenis).toLowerCase() === 'cerita');
    const siap = partSiap_();
    let part = cerita.reduce((m, r) => Math.max(m, nomor(r)), 0);
    const terisi = sudahAda.filter(r => String(r.jenis).toLowerCase() === 'cerita').map(r => r.tanggal);
    CONFIG.HARI_CERITA.forEach(i => {
      const tgl = fmtTgl_(tambahHari_(senin, i - 1));
      if (terisi.indexOf(tgl) >= 0 || siap.indexOf(part + 1) < 0) return;
      part++;
      const b = barisKonten_({ tanggal: tgl, jenis: 'cerita', nama: CONFIG.JUDUL_CERITA + ' Part ' + part }, produk);
      tambahBaris_(TAB_JADWAL, KOLOM_JADWAL, b); ditambah.push(b);
    });
    if (siap.indexOf(part + 1) < 0 && cerita.length)
      gagal.push('cerita: Part ' + (part + 1) + ' belum dianimasikan, jadi belum dijadwalkan');
  } catch (e) { gagal.push('cerita: ' + e.message); }
  props.setProperty(kunci, sekarang_());

  const urut = ditambah.slice().sort((a, b) => fmtKunci_(keDate_(a.tanggal)).localeCompare(fmtKunci_(keDate_(b.tanggal))));
  let teks = '🗓️ <b>Rencana konten ' + fmtTgl_(senin) + ' – ' + fmtTgl_(tambahHari_(senin, 6)) + '</b>\n' +
    (hasil.ringkasan ? '<i>' + esc_(hasil.ringkasan) + '</i>\n' : '') + '\n';
  hari.forEach((h, i) => {
    const tgl = fmtTgl_(tambahHari_(senin, i));
    const isi = urut.filter(b => b.tanggal === tgl);
    if (!isi.length) return;
    teks += '<b>' + esc_(h) + '</b>\n' + isi.map(b => (b.jenis === 'katalog' ? '  📱 story: ' : b.jenis === 'cerita' ? '  🎬 reel: ' : '  🖼️ ' + b.jenis + ': ') + esc_(b.nama)).join('\n') + '\n';
  });
  teks += '\nSemua sudah masuk tab Jadwal. Mau ubah? Edit sheet atau ketik perintah ke sini ' +
    '(mis. <i>ganti story Selasa dengan pulpen</i>). Feed tetap menunggu ✅ darimu sebelum tayang.';
  if (gagal.length) teks += '\n\n⚠️ Dilewati: ' + esc_(gagal.join('; '));
  return teks;
}

/** Isi naskah cerita dari GitHub (disimpan 1 jam). */
function naskahCerita_() {
  const cache = CacheService.getScriptCache();
  const simpan = cache.get('naskah');
  if (simpan) return simpan;
  let teks = '';
  try {
    const r = UrlFetchApp.fetch(CONFIG.NASKAH_URL, { muteHttpExceptions: true });
    if (r.getResponseCode() === 200) teks = r.getContentText().slice(0, 9000);
  } catch (e) { /* GitHub tidak terjangkau */ }
  if (teks) cache.put('naskah', teks, 3600);
  return teks || '(naskah tidak terbaca)';
}

/** Nomor part yang ada di naskah (judul "## PART n"). */
function partSiap_() {
  return (naskahCerita_().match(/^## PART (\d+)/gm) || []).map(x => parseInt(x.replace(/\D/g, ''), 10));
}

function ringkasJadwal_(nHari) {
  const mulai = keDate_(fmtTgl_(new Date()));
  const rows = bacaTabel_(TAB_JADWAL).rows.filter(r => { const d = keDate_(r.tanggal); return d && d >= mulai && d < tambahHari_(mulai, nHari); })
    .sort((a, b) => (fmtKunci_(keDate_(a.tanggal)) + (a.jam || '99')).localeCompare(fmtKunci_(keDate_(b.tanggal)) + (b.jam || '99')));
  if (!rows.length) return '📭 Belum ada jadwal ' + nHari + ' hari ke depan. Ketik /rencana untuk membuat rencana minggu depan.';
  return '📅 <b>Jadwal ' + nHari + ' hari ke depan</b>\n' + rows.map(r =>
    (/^ya$/i.test(r.tunda || '') ? '⏸️ ' : '') + esc_(r.tanggal) + ' ' + esc_(r.jam || 'auto') + ' · ' +
    esc_(r.jenis || 'katalog') + ' · ' + esc_(r.nama) + ' <i>(baris ' + r._row + ')</i>').join('\n');
}

// ============================== GEMINI ==============================
function gemini_(prompt) {
  // Model utama → cadangan → model stabil; tiap model dicoba ulang singkat kalau sedang sibuk (503) / kena batas (429)
  const model = uniq_([CONFIG.GEMINI_MODEL, CONFIG.GEMINI_MODEL_CADANGAN, 'gemini-2.5-flash-lite', 'gemini-2.5-flash']);
  const body = JSON.stringify({ contents: [{ role: 'user', parts: [{ text: prompt }] }],
    generationConfig: { responseMimeType: 'application/json', temperature: 0.7 } });
  let terakhir = '', sibuk = false;
  for (let i = 0; i < model.length; i++) {
    const url = 'https://generativelanguage.googleapis.com/v1beta/models/' + model[i] + ':generateContent';
    for (let coba = 0; coba < 2; coba++) {
      // Key format baru "AQ." maupun lama "AIza": kirim lewat header; kalau ditolak (401/403) coba lewat parameter ?key=
      let r = UrlFetchApp.fetch(url, { method: 'post', contentType: 'application/json', muteHttpExceptions: true,
        headers: { 'x-goog-api-key': CONFIG.GEMINI_API_KEY }, payload: body });
      if (r.getResponseCode() === 401 || r.getResponseCode() === 403) {
        r = UrlFetchApp.fetch(url + '?key=' + encodeURIComponent(CONFIG.GEMINI_API_KEY),
          { method: 'post', contentType: 'application/json', muteHttpExceptions: true, payload: body });
      }
      const kode = r.getResponseCode();
      if (kode === 200) {
        const j = JSON.parse(r.getContentText());
        const teks = j.candidates && j.candidates[0] && j.candidates[0].content.parts
          .filter(p => !p.thought).map(p => p.text || '').join('');
        return JSON.parse(String(teks).replace(/^```(json)?|```$/g, '').trim());
      }
      terakhir = kode + ' ' + model[i];
      if (kode === 404) break;                         // model tidak ada → langsung ke model berikutnya
      if (kode !== 429 && kode < 500) throw new Error('Gemini menolak permintaan (' + kode + '): ' +
        r.getContentText().replace(/\s+/g, ' ').slice(0, 160));
      sibuk = true;
      Utilities.sleep(1500 * (coba + 1));              // sibuk sebentar → tunggu lalu coba lagi
    }
  }
  throw new Error(sibuk ? 'Server Gemini sedang sibuk (semua model penuh). Coba kirim ulang pesanmu 1-2 menit lagi ya.'
    : 'Gemini gagal (' + terakhir + ')');
}

/** Jalankan dari editor untuk mengetes API key Gemini (hasilnya dikirim ke Telegram). */
function tesGemini() {
  try {
    const h = gemini_('Balas JSON {"pesan": "halo"} dalam bahasa Indonesia, sapa pemilik toko ATK.');
    kirim_('✅ Gemini terhubung: ' + esc_(h.pesan || JSON.stringify(h)));
  } catch (e) { kirim_('❌ ' + esc_(e.message)); throw e; }
}

// ============================== SHEET ==============================
function sheet_(nama) {
  const sh = SpreadsheetApp.getActive().getSheetByName(nama);
  if (!sh) throw new Error('Tab "' + nama + '" tidak ada. Jalankan setup dulu.');
  return sh;
}

function bacaTabel_(nama) {
  const nilai = sheet_(nama).getDataRange().getValues();
  const header = (nilai.shift() || []).map(h => String(h).trim().toLowerCase().replace(/\s+/g, '_'));
  const rows = nilai.map((baris, i) => {
    const o = { _row: i + 2 };
    header.forEach((h, j) => { if (h) o[h] = baris[j] instanceof Date ? fmtTgl_(baris[j]) : String(baris[j]).trim(); });
    return o;
  }).filter(o => o.nama || o.acara || o.id);
  return { header: header, rows: rows };
}

function tambahBaris_(nama, kolomUrut, obj) {
  const sh = sheet_(nama);
  const header = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0].map(h => String(h).trim().toLowerCase());
  const baris = header.map(h => obj[h] !== undefined ? String(obj[h]) : '');
  const r = sh.getLastRow() + 1;
  sh.getRange(r, 1, 1, header.length).setNumberFormat('@').setValues([baris]);
}

function ubahBaris_(nama, header, nomor, data) {
  const sh = sheet_(nama);
  Object.keys(data).forEach(k => {
    const c = header.indexOf(k);
    if (c >= 0) sh.getRange(nomor, c + 1).setNumberFormat('@').setValue(data[k]);
  });
}

// ============================== TELEGRAM ==============================
function tg_(method, payload) {
  const r = UrlFetchApp.fetch('https://api.telegram.org/bot' + CONFIG.TELEGRAM_BOT_TOKEN + '/' + method,
    { method: 'post', payload: payload, muteHttpExceptions: true });
  return JSON.parse(r.getContentText());
}

function kirim_(teks) {
  // Telegram membatasi 4096 karakter per pesan
  for (let i = 0; i < teks.length; i += 3900) {
    const r = tg_('sendMessage', { chat_id: CONFIG.TELEGRAM_CHAT_ID, text: teks.slice(i, i + 3900),
      parse_mode: 'HTML', disable_web_page_preview: true });
    if (!r.ok) tg_('sendMessage', { chat_id: CONFIG.TELEGRAM_CHAT_ID, text: teks.slice(i, i + 3900).replace(/<[^>]+>/g, '') });
  }
}

// ============================== TANGGAL & TEKS ==============================
function esc_(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function sekarang_() { return Utilities.formatDate(new Date(), CONFIG.ZONA, 'dd/MM/yyyy HH:mm'); }
function fmtTgl_(d) { return Utilities.formatDate(d, CONFIG.ZONA, 'dd/MM/yyyy'); }
function fmtKunci_(d) { return Utilities.formatDate(d, CONFIG.ZONA, 'yyyy-MM-dd'); }
function fmtHari_(d) {
  return ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'][Number(Utilities.formatDate(d, CONFIG.ZONA, 'u')) % 7];
}
function tambahHari_(d, n) { return new Date(d.getTime() + n * 86400000); }
function keDate_(s) {
  if (s instanceof Date) return s;
  const m = String(s || '').trim().match(/^(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{2,4})$/);
  if (!m) return null;
  const th = m[3].length === 2 ? '20' + m[3] : m[3];
  const d = Utilities.parseDate(('0' + m[1]).slice(-2) + '/' + ('0' + m[2]).slice(-2) + '/' + th + ' 12:00', CONFIG.ZONA, 'dd/MM/yyyy HH:mm');
  return isNaN(d.getTime()) ? null : d;
}
function rapikanJam_(j) {
  const m = String(j || '').trim().replace('.', ':').match(/^(\d{1,2}):(\d{2})/);
  return m && Number(m[1]) < 24 && Number(m[2]) < 60 ? ('0' + m[1]).slice(-2) + ':' + m[2] : '';
}
function seninBerikut_(d) {
  const hariKe = Number(Utilities.formatDate(d, CONFIG.ZONA, 'u'));  // 1=Senin ... 7=Minggu
  return keDate_(fmtTgl_(tambahHari_(d, 8 - hariKe)));
}
function dalamMinggu_(tgl, senin) {
  const d = keDate_(tgl);
  return d && d >= tambahHari_(senin, -0.6) && d < tambahHari_(senin, 7);
}

/** Diagnosa: kirim status webhook Telegram (alamat & error terakhir) ke chat. Jalankan dari editor. */
function cekWebhook() {
  const r = tg_('getWebhookInfo', {}).result || {};
  const err = r.last_error_message
    ? r.last_error_message + ' (' + Utilities.formatDate(new Date(r.last_error_date * 1000), CONFIG.ZONA, 'dd/MM HH:mm') + ')'
    : 'tidak ada';
  kirim_('🔎 <b>Cek webhook</b>\nURL: ' + esc_(r.url || '(kosong)') +
    '\nPesan tertahan: ' + (r.pending_update_count || 0) +
    '\nError terakhir: ' + esc_(err) +
    '\nURL Web app: ' + esc_(ScriptApp.getService().getUrl() || '-'));
}
