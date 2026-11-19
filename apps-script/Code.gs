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

  GEMINI_MODEL: 'gemini-flash-latest',            // ganti kalau Google mengubah nama model
  GEMINI_MODEL_CADANGAN: 'gemini-flash-lite-latest',
  STORY_PER_HARI: 2,                               // jumlah story katalog per hari
  HARI_FEED: [1, 3, 5],                            // hari postingan feed: 1=Senin 3=Rabu 5=Jumat
  JAM_FEED: '19:00',
  JAM_RENCANA: 17,                                 // Minggu jam 17.00 rencana minggu depan dibuat
  ZONA: 'Asia/Jakarta',
  NAMA_TOKO: 'Annafi Atk Menganti',
  WA: '0895-1208-5529',
};
// ==============================================================================================

const TAB_JADWAL = 'Jadwal', TAB_PRODUK = 'Produk', TAB_KALENDER = 'Kalender', TAB_SETUJU = 'Persetujuan';
const KOLOM_JADWAL = ['tanggal', 'jam', 'jenis', 'nama', 'kategori', 'detail', 'poin', 'label_harga_1', 'harga_1',
  'label_harga_2', 'harga_2', 'gambar', 'caption', 'tunda'];
const KOLOM_PRODUK = ['nama', 'kategori', 'detail', 'label_harga_1', 'harga_1', 'label_harga_2', 'harga_2', 'gambar', 'aktif'];
const JENIS = ['katalog', 'edukasi', 'promo', 'info', 'momen'];
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
  // tab Jadwal harus paling kiri (sistem GitHub membaca tab pertama)
  ss.setActiveSheet(ss.getSheetByName(TAB_JADWAL));
  ss.moveActiveSheet(1);

  ScriptApp.getProjectTriggers().filter(t => t.getHandlerFunction() === 'rencanaOtomatis')
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('rencanaOtomatis').timeBased().onWeekDay(ScriptApp.WeekDay.SUNDAY)
    .atHour(CONFIG.JAM_RENCANA).inTimezone(CONFIG.ZONA).create();

  const url = ScriptApp.getService().getUrl();
  if (!url) throw new Error('Deploy dulu sebagai Web app (Deploy → New deployment → Web app), lalu jalankan setup lagi.');
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
  '• <i>undur promo paket ujian ke Senin jam 7 malam</i>\n' +
  '• <i>ganti harga satuan Joyko 6151 jadi 2500</i>\n' +
  '• <i>tunda semua story hari Sabtu</i>\n\n' +
  'Perintah cepat: /jadwal (7 hari ke depan) · /rencana (buat rencana minggu depan) · /bantuan';

// ============================== TELEGRAM WEBHOOK ==============================
function doPost(e) {
  try {
    const u = JSON.parse(e.postData.contents);
    const cache = CacheService.getScriptCache();
    if (cache.get('u' + u.update_id)) return HtmlService.createHtmlOutput('ok');  // cegah proses ganda
    cache.put('u' + u.update_id, '1', 21600);
    if (u.callback_query) tanganiTombol_(u.callback_query);
    else if (u.message && u.message.text) tanganiPesan_(u.message);
  } catch (err) {
    console.error(err);
    try { kirim_('⚠️ Terjadi kesalahan: ' + esc_(String(err && err.message || err))); } catch (e2) {}
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
  const status = aksi === 'setuju'
    ? '✅ Disetujui — akan tayang sesuai jadwal.'
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
  tg_('sendChatAction', { chat_id: m.chat.id, action: 'typing' });
  kirim_(manajer_(teks));
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
    'Kamu adalah manajer konten Instagram/Facebook untuk toko alat tulis "' + CONFIG.NAMA_TOKO + '".',
    'Hari ini ' + fmtHari_(hariIni) + ' (' + fmtTgl_(hariIni) + '), zona WIB.',
    'Tugasmu: terjemahkan instruksi pemilik toko menjadi aksi terhadap tab Jadwal / Produk.',
    '',
    'ATURAN:',
    '- jenis hanya: katalog (story produk), edukasi, promo, info, momen (postingan feed).',
    '- Untuk katalog, "nama" HARUS persis salah satu nama di PRODUK; harga diisi sistem, jangan tulis harga.',
    '- Jangan mengarang harga. Ubah harga hanya kalau pemilik menyebut angkanya di instruksi.',
    '- tanggal format dd/MM/yyyy, jam format HH:mm (boleh kosong = jam ramai otomatis).',
    '- poin dipisah titik koma ;, maksimal 5 poin singkat. Judul (nama) maksimal ~6 kata.',
    '- "baris" hanya boleh nomor baris yang ada di JADWAL atau PRODUK di bawah.',
    '- Tidak ada aksi hapus; untuk membatalkan pakai aksi "tunda".',
    '- Kalau instruksi kurang jelas atau tidak bisa dilakukan, jangan buat aksi; tanyakan di "balasan".',
    '- "balasan": bahasa Indonesia santai, singkat, jelaskan apa yang kamu lakukan.',
    '',
    'KATEGORI PRODUK: ' + JSON.stringify(uniq_(semuaProduk.map(p => p.kategori))),
    'PRODUK yang relevan dengan instruksi (sebagian dari ' + semuaProduk.length + '): ' + JSON.stringify(produk.map(p => ({ baris: p._row, nama: p.nama, kategori: p.kategori,
      harga: [p.label_harga_1, p.harga_1, p.label_harga_2, p.harga_2].filter(String).join(' ') }))),
    'JADWAL (7 hari lalu s/d 3 minggu ke depan): ' + JSON.stringify(dekat.map(r => ({ baris: r._row,
      tanggal: r.tanggal, jam: r.jam, jenis: r.jenis || 'katalog', nama: r.nama, tunda: r.tunda }))),
    '',
    'INSTRUKSI PEMILIK: """' + instruksi + '"""',
    '',
    'Jawab HANYA JSON: {"balasan": string, "aksi": [ ' +
      '{"tipe":"tambah","data":{tanggal,jam,jenis,nama,kategori,detail,poin,gambar,caption,produk_harga}} | ' +
      '{"tipe":"ubah","baris":n,"data":{kolom: nilai}} | {"tipe":"tunda","baris":n} | ' +
      '{"tipe":"ubah_produk","baris":n,"data":{kolom: nilai}} | {"tipe":"rencana"} ]}',
    '(produk_harga opsional: nama produk dari PRODUK yang harganya ditampilkan di poster promo; gambar: kosong, "cari", atau link)',
  ].join('\n');

  const hasil = gemini_(prompt);
  const laporan = [];
  (hasil.aksi || []).slice(0, 15).forEach(a => {
    try { laporan.push(jalankanAksi_(a, instruksi, semuaProduk)); }
    catch (err) { laporan.push('⚠️ ' + esc_(err.message)); }
  });
  return esc_(hasil.balasan || 'Oke.') + (laporan.length ? '\n\n' + laporan.join('\n') : '');
}

/** Pilih produk yang kata-katanya muncul di instruksi (hemat kuota Gemini untuk daftar produk yang panjang). */
function produkRelevan_(produk, instruksi, maks) {
  const kata = uniq_(String(instruksi).toLowerCase().match(/[a-z0-9]{3,}/g) || [])
    .filter(k => ['yang', 'dan', 'untuk', 'jam', 'besok', 'hari', 'story', 'buat', 'jadwalkan', 'ganti', 'harga', 'tolong', 'dengan'].indexOf(k) < 0);
  return produk.map(p => {
    const n = (p.nama + ' ' + (p.kategori || '')).toLowerCase();
    return { p: p, skor: kata.reduce((s, k) => s + (n.indexOf(k) >= 0 ? (/\d/.test(k) ? 3 : 1) : 0), 0) };
  }).filter(x => x.skor > 0).sort((a, b) => b.skor - a.skor).slice(0, maks).map(x => x.p);
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
  const poin = Array.isArray(d.poin) ? d.poin.join('; ') : String(d.poin || '');
  const baris = { tanggal: fmtTgl_(keDate_(d.tanggal)), jam: rapikanJam_(d.jam), jenis: jenis, nama: String(d.nama || '').trim(),
    kategori: String(d.kategori || '').toUpperCase(), detail: d.detail || '', poin: poin, gambar: d.gambar || '',
    caption: d.caption || '', tunda: '' };
  const cari = jenis === 'katalog' ? baris.nama : (d.produk_harga || '');
  if (cari) {
    const p = cariProduk_(produk, cari);
    if (!p) throw new Error('Produk "' + cari + '" tidak ada di tab Produk.');
    if (!p.harga_1) throw new Error('Produk "' + p.nama + '" belum punya harga di tab Produk.');
    ['label_harga_1', 'harga_1', 'label_harga_2', 'harga_2'].forEach(k => baris[k] = p[k] || '');
    if (jenis === 'katalog') {
      baris.nama = p.nama; baris.kategori = (p.kategori || baris.kategori).toUpperCase();
      baris.detail = p.detail || baris.detail; baris.gambar = p.gambar || '';
    }
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
    '2. "feed": 3 postingan pada ' + hariFeed.join(', ') + ' (boleh geser 1 hari kalau ada momen di KALENDER).',
    '   Campuran: 1 edukasi, 1 promo, 1 info atau momen. Momen dijadwalkan SEBELUM/TEPAT di harinya, promo momen 2-3 hari sebelumnya.',
    '   Tiap feed: jenis, tanggal (dd/MM/yyyy), nama (judul maks 6 kata), detail (1 kalimat), poin (3-4 poin singkat,',
    '   boleh format "Judul: isi"), gambar ("" atau "cari"), produk_harga (opsional: nama PERSIS dari PRODUK kalau promo',
    '   menampilkan harga produk itu; JANGAN mengarang harga atau harga paket).',
    '   Jangan ulang tema yang ada di RIWAYAT. Bahasa Indonesia santai, cocok untuk toko ATK lokal.',
    '3. "ringkasan": 1-2 kalimat strategi minggu ini.',
    '',
    'PRODUK (pilihan acak per kategori): ' + JSON.stringify(sampelProduk_(produk, 8, riwayat.map(r => r.nama)).map(p => ({ nama: p.nama, kategori: p.kategori }))),
    'KALENDER (dd/MM tiap tahun): ' + JSON.stringify(kalender),
    'RIWAYAT 4 minggu: ' + JSON.stringify(riwayat.map(r => [r.tanggal, r.jenis || 'katalog', r.nama])),
    'SUDAH TERJADWAL minggu ini (jangan duplikat, cukup lengkapi): ' + JSON.stringify(sudahAda.map(r => [r.tanggal, r.jenis || 'katalog', r.nama])),
    '',
    'Jawab HANYA JSON: {"ringkasan": string, "story": [{"tanggal": "dd/MM/yyyy", "produk": string}], ' +
      '"feed": [{"jenis","tanggal","nama","detail","poin":[string],"gambar","produk_harga"}]}',
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
  props.setProperty(kunci, sekarang_());

  const urut = ditambah.slice().sort((a, b) => fmtKunci_(keDate_(a.tanggal)).localeCompare(fmtKunci_(keDate_(b.tanggal))));
  let teks = '🗓️ <b>Rencana konten ' + fmtTgl_(senin) + ' – ' + fmtTgl_(tambahHari_(senin, 6)) + '</b>\n' +
    (hasil.ringkasan ? '<i>' + esc_(hasil.ringkasan) + '</i>\n' : '') + '\n';
  hari.forEach((h, i) => {
    const tgl = fmtTgl_(tambahHari_(senin, i));
    const isi = urut.filter(b => b.tanggal === tgl);
    if (!isi.length) return;
    teks += '<b>' + esc_(h) + '</b>\n' + isi.map(b => (b.jenis === 'katalog' ? '  📱 story: ' : '  🖼️ ' + b.jenis + ': ') + esc_(b.nama)).join('\n') + '\n';
  });
  teks += '\nSemua sudah masuk tab Jadwal. Mau ubah? Edit sheet atau ketik perintah ke sini ' +
    '(mis. <i>ganti story Selasa dengan pulpen</i>). Feed tetap menunggu ✅ darimu sebelum tayang.';
  if (gagal.length) teks += '\n\n⚠️ Dilewati: ' + esc_(gagal.join('; '));
  return teks;
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
  const model = [CONFIG.GEMINI_MODEL, CONFIG.GEMINI_MODEL_CADANGAN];
  const body = JSON.stringify({ contents: [{ role: 'user', parts: [{ text: prompt }] }],
    generationConfig: { responseMimeType: 'application/json', temperature: 0.7 } });
  let terakhir = '';
  for (let i = 0; i < model.length; i++) {
    const url = 'https://generativelanguage.googleapis.com/v1beta/models/' + model[i] + ':generateContent';
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
    terakhir = kode + ' ' + r.getContentText().slice(0, 200);
    if (kode !== 429 && kode !== 404 && kode < 500) break;  // kuota habis / model tidak ada → coba cadangan
  }
  throw new Error('Gemini gagal (' + terakhir + ')');
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
