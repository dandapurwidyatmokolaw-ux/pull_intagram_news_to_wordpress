# Sistem Otomasi Berita Instagram ke Portal FH UNDIP

Sistem otomasi cerdas berstandar industri untuk mengekstraksi konten dan media visual dari akun Instagram resmi (default: `@law.undip`), menyusun narasi artikel berita jurnalistik dwibahasa (**Bahasa Indonesia & English**) berbasis AI Multimodal (standar 5W+1H), mengirimkan draf kurasi interaktif ke email staf redaksi (`danda@staff.undip.ac.id`), serta mempublikasikan artikel yang disetujui secara otomatis ke portal resmi [https://ilmuhukum.undip.ac.id](https://ilmuhukum.undip.ac.id).

---

## Arsitektur Alur Kerja (Workflow)

```text
[ Instagram Target (.env) ]
             │ (Daily Schedule / Cron 07:00 WIB)
             ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. INGESTION ENGINE (src/scraper.py)                        │
│    - Ekstraksi postingan baru hari ini (WIB / UTC+7)        │
│    - Unduh aset visual resolusi penuh ke data/media/        │
│    - Simpan ke antrean: data/pending_posts.json             │
└─────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. AI BILINGUAL NARRATOR (src/narrator.py)                  │
│    - Analisis Multimodal (Gambar Visual + Caption Asli)     │
│    - Produksi Judul, Lead 5W+1H & Batang Tubuh (ID & EN)    │
│    - Excerpt ringkas, Kategori & Tag SEO                    │
└─────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. CURATOR EMAIL & FEEDBACK GATEWAY (src/mailer.py & server)│
│    - Kirim email draf interaktif ke danda@staff.undip.ac.id │
│    - Tombol Hijau : [✔ SETUJUI & PUBLIKASIKAN]              │
│    - Tombol Kuning: [✎ MINTA PERBAIKAN NARASI]              │
└─────────────────────────────────────────────────────────────┘
             │
      ┌──────┴────────────────────────────────┐
      │                                       │
      ▼                                       ▼
┌───────────────────────────────┐   ┌─────────────────────────────────────────────┐
│ SIKLUS PERBAIKAN (REVISION)   │   │ 4. WORDPRESS PUBLISHER (src/wp_publisher.py)│
│ - Kurator isi form perbaikan  │   │ - Upload Featured Image ke WP Media Library │
│ - AI regenerasi narasi baru   │   │ - Terbitkan Artikel Indonesia (Kategori 143)│
│ - Kirim ulang email konfirmasi│   │ - Terbitkan Artikel English   (Kategori 145)│
│ - Berulang sampai disetujui   │   │ - HAPUS postingan dari pending_posts.json   │
└─────────────┬─────────────────┘   │ - ARSIPKAN riwayat ke history_published.json│
              │ (Saat disetujui)    └─────────────────────────────────────────────┘
              └────────────────────►
```

---

## Fitur Utama

1. **Target Akun Instagram Dinamis**:
   Alamat akun target tidak di-hardcode. Cukup ubah `INSTAGRAM_TARGET_URL` dan `INSTAGRAM_TARGET_USERNAME` di `.env` kapan saja.
2. **Filter Ketat Postingan Harian**:
   Hanya memproses postingan hari ini (WIB / UTC+7). Begitu mendeteksi postingan bertanggal sebelumnya, sistem menghentikan pembacaan postingan lama secara otomatis.
3. **AI Multimodal Bilingual News Engine**:
   Menghasilkan artikel formal dwibahasa (Bahasa Indonesia & English) yang elegan dan memenuhi kaidah jurnalistik 5W+1H serta pedoman penulisan berita Undip.
4. **Email Kurasi & Formulir Revisi Interaktif**:
   Kurator dapat langsung menyetujui artikel atau memberikan instruksi revisi secara online melalui webhook server lokal (port 5000) yang diamankan token HMAC SHA-256.
5. **Otomasi WordPress REST API & Pembersihan Antrean**:
   Begitu artikel disetujui dan terbit di `ilmuhukum.undip.ac.id`, sistem langsung menghapus postingan dari `data/pending_posts.json` dan memindahkannya ke `data/history_published.json` untuk menjamin nol duplikasi konten.
6. **Dukungan CI/CD & Otomasi Repositori**:
   Dilengkapi dengan GitHub Actions (`test.yml` dan `daily_ingest.yml`) serta skrip harian (`scripts/run_daily.sh`).

---

## Struktur Direktori

```text
dev_intagram_fh/
├── .github/
│   └── workflows/
│       ├── test.yml             # CI testing otomatis (Python 3.10 - 3.12)
│       └── daily_ingest.yml     # Jadwal otomasi penarikan harian
├── .gitignore                   # Proteksi ketat kredensial dan file biner
├── .env.example                 # Template referensi konfigurasi aman
├── .env                         # Konfigurasi aktif (rahasia)
├── README.md                    # Dokumentasi lengkap proyek
├── PRD.md                       # Dokumen Spesifikasi Produk (PRD v1.1.0)
├── requirements.txt             # Dependensi Python
│
├── config/
│   ├── __init__.py
│   └── settings.py              # Parser konfigurasi dinamis (.env)
│
├── data/                        # [Diabaikan di Git, dibuat otomatis saat runtime]
│   ├── pending_posts.json       # Antrean postingan aktif yang menunggu kurasi
│   ├── history_published.json   # Riwayat postingan yang sudah terbit di web
│   ├── media/                   # Direktori penyimpanan foto ({post_code}.jpg)
│   ├── email_previews/          # Salinan pratinjau dokumen email HTML
│   └── logs/                    # Berkas log eksekusi harian
│
├── scripts/
│   └── run_daily.sh             # Skrip eksekutor harian (Cron / Task Scheduler)
│
├── src/
│   ├── __init__.py
│   ├── scraper.py               # Penarik data Instagram dinamis
│   ├── narrator.py              # Generator narasi dwibahasa AI Multimodal
│   ├── mailer.py                # Pengirim email kurasi interaktif
│   ├── feedback_server.py       # Gateway web webhook tombol persetujuan
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

## Panduan Instalasi & Penggunaan

### 1. Prasyarat Sistem
- Python 3.10+
- Chromium Browser / Headless Chrome (`sudo apt install chromium-browser`)
- Akses internet aktif

### 2. Instalasi Dependensi
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Lingkungan (`.env`)
Salin file `.env.example` menjadi `.env`, lalu lengkapi kredensial:
```bash
cp .env.example .env
```
Contoh parameter:
```env
# Target Akun Instagram
INSTAGRAM_TARGET_URL=https://www.instagram.com/law.undip/
INSTAGRAM_TARGET_USERNAME=law.undip

# Email Staf Kurator
CURATOR_EMAIL=danda@staff.undip.ac.id
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=danda@staff.undip.ac.id
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# AI Gateway
AI_PROVIDER=9router
AI_API_BASE=http://127.0.0.1:20128/v1
AI_API_KEY=sk-...
AI_MODEL=ag/gemini-3.8-flash-high

# WordPress REST API Target
WP_BASE_URL=https://ilmuhukum.undip.ac.id
WP_USERNAME=admins1
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx
WP_DEFAULT_CATEGORY_ID=143
WP_CATEGORY_ID_EN=145
```

---

## Perintah Operasional

### Menjalankan Pipeline Lengkap Harian:
```bash
PYTHONPATH=. python src/main.py
```

### Menjalankan Server Webhook Feedback Kurator (Background):
```bash
PYTHONPATH=. python src/feedback_server.py --port 5000
```
Tautan Uji Coba: `http://localhost:5000/health`

### Menjalankan Unit Tests:
```bash
PYTHONPATH=. python -m unittest discover tests/ -v
```

---

## Lisensi & Hak Kelola
Dikelola oleh Fakultas Hukum Universitas Diponegoro untuk diseminasi publikasi akademik digital Program Studi S1 Hukum.
