# pull_intagram_news_to_wordpress

[![CI Testing & Code Quality](https://github.com/dandapurwidyatmokolaw-ux/pull_intagram_news_to_wordpress/actions/workflows/test.yml/badge.svg)](https://github.com/dandapurwidyatmokolaw-ux/pull_intagram_news_to_wordpress/actions/workflows/test.yml)
[![Daily Automation Ingest](https://github.com/dandapurwidyatmokolaw-ux/pull_intagram_news_to_wordpress/actions/workflows/daily_ingest.yml/badge.svg)](https://github.com/dandapurwidyatmokolaw-ux/pull_intagram_news_to_wordpress/actions/workflows/daily_ingest.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)

Sistem pipeline otomasi cerdas dan modular untuk mengekstraksi konten dan aset visual postingan dari akun Instagram (default: `@law.undip`), menyusun artikel berita jurnalistik formal berstandar **5W+1H** dalam format dwibahasa (**Bahasa Indonesia & English**) berbasis AI Multimodal, mengirimkan draf kurasi interaktif ke email staf kurator (`danda@staff.undip.ac.id`), serta mempublikasikan artikel yang disetujui secara otomatis ke portal resmi [https://ilmuhukum.undip.ac.id](https://ilmuhukum.undip.ac.id) via WordPress REST API lengkap dengan pembersihan antrean otomatis.

---

## Daftar Isi
- [Arsitektur Alur Kerja](#arsitektur-alur-kerja)
- [Fitur Utama](#fitur-utama)
- [Struktur Repositori](#struktur-repositori)
- [Panduan Instalasi](#panduan-instalasi)
- [Konfigurasi Lingkungan (.env)](#konfigurasi-lingkungan-env)
- [Petunjuk Penggunaan & Operasional](#petunjuk-penggunaan--operasional)
  - [1. Menjalankan Pipeline Harian](#1-menjalankan-pipeline-harian)
  - [2. Alur Kurasi & Revisi Interaktif](#2-alur-kurasi--revisi-interaktif)
  - [3. Publikasi Otomatis ke WordPress](#3-publikasi-otomatis-ke-wordpress)
- [Penjadwalan Otomatis (Cron / Task Scheduler)](#penjadwalan-otomatis-cron--task-scheduler)
- [Pengujian (Unit & E2E Testing)](#pengujian-unit--e2e-testing)
- [Keamanan & Perlindungan Kredensial](#keamanan--perlindungan-kredensial)

---

## Arsitektur Alur Kerja

```text
[ Target Akun Instagram (.env) ]
                │ (Daily Cron / Manual Trigger)
                ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. INGESTION ENGINE (src/scraper.py)                        │
│    - Ekstraksi postingan baru hari ini (WIB / UTC+7)        │
│    - Filter ketat: Berhenti otomatis saat mendeteksi post lama│
│    - Unduh foto resolusi penuh ke data/media/{code}.jpg     │
│    - Simpan ke antrean aktif: data/pending_posts.json       │
└─────────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. AI BILINGUAL NARRATOR (src/narrator.py)                  │
│    - Multimodal LLM (Gemini 3.8 / GPT-4o / 9Router)         │
│    - Membaca foto postingan dan caption asli Instagram      │
│    - Menghasilkan draf 5W+1H: Bahasa Indonesia & English    │
│    - Menentukan Excerpt, Kategori & Tag SEO                 │
└─────────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. CURATOR EMAIL & FEEDBACK GATEWAY (src/mailer.py & server)│
│    - Kirim email draf interaktif ke danda@staff.undip.ac.id │
│    - Dilengkapi token keamanan HMAC SHA-256                 │
│    - Tombol Hijau : [✔ SETUJUI & PUBLIKASIKAN]              │
│    - Tombol Kuning: [✎ MINTA PERBAIKAN NARASI]              │
└─────────────────────────────────────────────────────────────┘
                │
        ┌───────┴───────────────────────────────┐
        │                                       │
        ▼                                       ▼
┌───────────────────────────────┐   ┌─────────────────────────────────────────────┐
│ SIKLUS PERBAIKAN (REVISION)   │   │ 4. WORDPRESS PUBLISHER (src/wp_publisher.py)│
│ - Kurator mengisi form revisi │   │ - Unggah Featured Image ke WP Media Library │
│ - AI meregenerasi draf baru   │   │ - Terbitkan Artikel ID (Kategori Berita 143)│
│ - Kirim ulang email konfirmasi│   │ - Terbitkan Artikel EN (Kategori news 145)  │
│ - Berulang sampai disetujui   │   │ - HAPUS postingan dari pending_posts.json   │
└───────────────┬───────────────┘   │ - ARSIPKAN riwayat ke history_published.json│
                │ (Saat disetujui)  └─────────────────────────────────────────────┘
                └──────────────────►
```

---

## Fitur Utama

- **Target Akun Instagram Dinamis**: Alamat akun tidak di-hardcode di kode program. Cukup ubah `INSTAGRAM_TARGET_URL` dan `INSTAGRAM_TARGET_USERNAME` di file `.env`.
- **Anti-Duplikasi & Filter Tanggal Akurat**: Menganalisis metadata timestamp eksak postingan (`taken_at` / `<time datetime>`) dalam zona waktu Indonesia Barat (WIB). Mengabaikan postingan bertanggal sebelumnya untuk efisiensi eksekusi.
- **AI Multimodal Jurnalistik**: Mengolah gambar dan caption Instagram menjadi artikel berita bermutu tinggi sesuai pedoman penulisan berita web Undip.
- **Dukungan Dwibahasa (Bilingual Polylang)**: Menghasilkan versi Bahasa Indonesia dan versi English resmi yang siap dihubungkan di sistem WordPress.
- **Gateway Umpan Balik Tanpa Login Rumit**: Kurator cukup mengklik tombol di dalam email untuk langsung menerbitkan berita atau membuka formulir perbaikan narasi.
- **Pembersihan Antrean Otomatis**: Postingan yang telah berhasil dipublikasikan langsung dihapus dari antrean pending lokal untuk menjamin integritas data dan mencegah posting ganda di masa mendatang.
- **CI/CD Terintegrasi**: Pengujian otomatis pada Python 3.10, 3.11, dan 3.12 via GitHub Actions.

---

## Struktur Repositori

```text
pull_intagram_news_to_wordpress/
├── .github/
│   └── workflows/
│       ├── test.yml             # Workflow CI testing & linting otomatis
│       └── daily_ingest.yml     # Workflow scheduler harian GitHub Actions
├── .gitignore                   # Proteksi kredensial .env dan data runtime
├── .env.example                 # Template referensi konfigurasi aman
├── README.md                    # Dokumentasi lengkap proyek
├── PRD.md                       # Dokumen Spesifikasi Produk (PRD v1.1.0)
├── requirements.txt             # Daftar dependensi Python
│
├── config/
│   ├── __init__.py
│   └── settings.py              # Parser konfigurasi dinamis (.env)
│
├── data/                        # [Diabaikan di Git, dibuat saat runtime]
│   ├── pending_posts.json       # Antrean postingan aktif yang menunggu kurasi
│   ├── history_published.json   # Riwayat postingan yang sudah terbit di web
│   ├── media/                   # Direktori penyimpanan foto ({post_code}.jpg)
│   ├── email_previews/          # Salinan pratinjau dokumen email HTML
│   └── logs/                    # Berkas catatan log eksekusi harian
│
├── scripts/
│   └── run_daily.sh             # Skrip eksekutor harian (Cron / Task Scheduler)
│
├── src/
│   ├── __init__.py
│   ├── scraper.py               # Penarik data Instagram dinamis
│   ├── narrator.py              # Generator narasi dwibahasa AI Multimodal
│   ├── mailer.py                # Pengirim email kurasi interaktif
│   ├── feedback_server.py       # Webhook gateway tombol persetujuan (port 5000)
│   ├── wp_publisher.py          # Modul publikasi WordPress REST API
│   └── main.py                  # Orkestrator utama pipeline
│
└── tests/
    ├── __init__.py
    ├── test_scraper.py          # Unit test penarikan Instagram
    ├── test_narrator.py         # Unit test AI bilingual
    ├── test_mailer_feedback.py  # Unit test notifikasi & token feedback
    ├── test_publisher.py        # Unit test publikasi WordPress
    └── test_e2e_pipeline.py     # Unit test integrasi pipeline end-to-end
```

---

## Panduan Instalasi

### 1. Kloning Repositori
```bash
git clone git@github.com:dandapurwidyatmokolaw-ux/pull_intagram_news_to_wordpress.git
cd pull_intagram_news_to_wordpress
```

### 2. Prasyarat Sistem
Pastikan Python 3.10+ dan Chromium Headless terpasang di sistem operasi Anda:
```bash
# Ubuntu / Debian / WSL
sudo apt-get update
sudo apt-get install -y python3 python3-pip chromium-browser
```

### 3. Pasang Dependensi Python
```bash
pip install -r requirements.txt
```

---

## Konfigurasi Lingkungan (.env)

Salin template `.env.example` menjadi `.env`:
```bash
cp .env.example .env
```

Sesuaikan variabel konfigurasi berikut:

| Variabel | Contoh Nilai | Keterangan |
| :--- | :--- | :--- |
| `INSTAGRAM_TARGET_URL` | `https://www.instagram.com/law.undip/` | URL profil Instagram sumber |
| `INSTAGRAM_TARGET_USERNAME` | `law.undip` | Username target Instagram |
| `CURATOR_EMAIL` | `danda@staff.undip.ac.id` | Alamat email staf penerima kurasi |
| `SMTP_HOST` | `smtp.gmail.com` | Host SMTP pengiriman email |
| `SMTP_PORT` | `587` | Port SMTP (STARTTLS) |
| `SMTP_USER` | `danda@staff.undip.ac.id` | Akun email pengirim SMTP |
| `SMTP_PASSWORD` | `xxxx-xxxx-xxxx-xxxx` | App Password email pengirim |
| `AI_PROVIDER` | `9router` / `openai` | Gateway AI LLM |
| `AI_API_BASE` | `http://127.0.0.1:20128/v1` | Endpoint API AI |
| `AI_API_KEY` | `sk-...` | Token autentikasi API AI |
| `AI_MODEL` | `ag/gemini-3.8-flash-high` | Model multimodal yang digunakan |
| `WP_BASE_URL` | `https://ilmuhukum.undip.ac.id` | URL portal WordPress target |
| `WP_USERNAME` | `admins1` | Username administrator WordPress |
| `WP_APP_PASSWORD` | `ItnB 1Zrh fMbx kQAo 4WJU 2Nvo` | Application Password WordPress |
| `WP_DEFAULT_CATEGORY_ID` | `143` | ID Kategori Bahasa Indonesia (*Berita*) |
| `WP_CATEGORY_ID_EN` | `145` | ID Kategori English (*news*) |
| `APP_PORT` | `5000` | Port server webhook feedback lokal |
| `FEEDBACK_SECRET_KEY` | `rahasia_token_hmac` | Kunci enkripsi token verifikasi |

---

## Petunjuk Penggunaan & Operasional

### 1. Penggunaan Cepat via Windows (`start.bat` & `stop.bat`)
Bagi pengguna Windows, sistem dapat dijalankan langsung tanpa membuka terminal WSL:
- **`start.bat`**: Cukup klik dua kali (double click) file `start.bat` di folder `D:\dev_intagram_fh`:
  * Otomatis menyalakan Feedback Webhook Server di background (Port 5000).
  * Menjalankan penarikan postingan Instagram hari ini & menyusun narasi berita dwibahasa AI.
  * Mengirim email kurasi interaktif ke `danda@staff.undip.ac.id`.
  * Menampilkan menu interaktif untuk cek status, pratinjau browser, atau buka folder data.
- **`stop.bat`**: Klik dua kali file `stop.bat` untuk menghentikan seluruh layanan server background di port 5000 dengan aman.

---

### 2. Menjalankan Pipeline Harian Manual (CLI WSL)
Eksekusi pipeline lengkap (Scrape -> Narrate -> Send Email -> Publish Approved):
```bash
PYTHONPATH=. python src/main.py
```
Opsi argumen:
- `--all`: Mengambil seluruh postingan tanpa batasan hanya hari ini.
- `--force`: Memaksa scrape ulang postingan yang sudah ada di antrean.
- `--auto-approve`: Langsung mempublikasikan draf baru ke web tanpa menunggu persetujuan kurator.
- `--url <URL>`: Override URL Instagram sementara tanpa mengubah `.env`.

### 3. Alur Kurasi & Revisi Interaktif
1. Jalankan server webhook feedback di latar belakang:
   ```bash
   PYTHONPATH=. python src/feedback_server.py --port 5000 &
   ```
2. Saat draf baru selesai dibuat, staf redaksi menerima email interaktif yang memuat foto postingan, caption asli, serta draf narasi dwibahasa.
3. Di dalam email terdapat dua tombol:
   - **Tombol Hijau [SETUJUI & PUBLIKASIKAN]**: Mengubah status menjadi `approved` dan langsung memicu modul publisher untuk menerbitkan artikel ke web secara otomatis.
   - **Tombol Kuning [MINTA PERBAIKAN NARASI]**: Membuka antarmuka formulir web di mana staf dapat mengetikkan instruksi perubahan (misal: penambahan nama narasumber atau penyesuaian gaya bahasa). AI akan meregenerasi draf baru dan mengirimkan email konfirmasi baru secara berulang hingga disetujui.

### 4. Publikasi Otomatis ke WordPress
Anda juga dapat menerbitkan draf yang berstatus disetujui secara manual melalui CLI:
```bash
PYTHONPATH=. python src/wp_publisher.py
```
Uji koneksi ke WordPress REST API:
```bash
PYTHONPATH=. python src/wp_publisher.py --check-auth
```

---

## Penjadwalan Otomatis (Cron / Task Scheduler)

### Linux / WSL (Crontab)
Jalankan `crontab -e` dan tambahkan baris berikut untuk mengeksekusi otomatis setiap hari pukul 07.00 WIB:
```bash
0 7 * * * /bin/bash /mnt/d/dev_intagram_fh/scripts/run_daily.sh
```

### Windows Task Scheduler
Buat Basic Task di Windows Task Scheduler:
- **Trigger**: Daily at 07:00 AM
- **Action**: Start a program
- **Program**: `wsl.exe`
- **Arguments**: `-d Ubuntu -e /bin/bash /mnt/d/dev_intagram_fh/scripts/run_daily.sh`

---

## Pengujian (Unit & E2E Testing)

Jalankan seluruh test suite otomatis:
```bash
PYTHONPATH=. python -m unittest discover tests/ -v
```

Hasil pengujian mencakup:
- `test_scraper.py`: Validasi penarikan Instagram, parsing relay DOM, dan unduh media.
- `test_narrator.py`: Validasi inisialisasi AI, payload multimodal, dan encoding gambar base64.
- `test_mailer_feedback.py`: Validasi token keamanan HMAC SHA-256 dan pembentukan template email.
- `test_publisher.py`: Validasi autentikasi REST API ke portal `ilmuhukum.undip.ac.id`.
- `test_e2e_pipeline.py`: Validasi integrasi menyeluruh dan pembersihan antrean otomatis.

---

## Keamanan & Perlindungan Kredensial

1. Berkas `.env` **TIDAK PERNAH** dikomit ke repositori publik (terlindungi oleh `.gitignore`).
2. Tautan aksi umpan balik pada email diproteksi dengan tanda tangan digital HMAC SHA-256 berbasis `FEEDBACK_SECRET_KEY` sehingga tidak dapat dimanipulasi oleh pihak ketiga.
3. Seluruh komunikasi WordPress menggunakan jalur terenkripsi HTTPS dan WordPress Application Password khusus.

---

## Lisensi & Kontribusi
Repositori ini dikembangkan dan dikelola oleh Fakultas Hukum Universitas Diponegoro untuk diseminasi publikasi akademik digital Program Studi S1 Hukum. Dilindungi di bawah lisensi MIT.
