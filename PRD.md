# PRODUCT REQUIREMENT DOCUMENT (PRD)
# SISTEM OTOMASI PENARIKAN KONTEN INSTAGRAM (DINAMIS), KURASI NARASI BILINGUAL, DAN PUBLIKASI KE ILMUHUKUM.UNDIP.AC.ID

- **Dokumen Versi**: 1.1.0
- **Tanggal Efektif**: 5 Oktober 2026
- **Status Dokumen**: Final Draft (Approved for Development)
- **Penyusun**: AI Agent Solution Architect
- **Target Penerima Review/Notifikasi**: `danda@staff.undip.ac.id`
- **Direktori Proyek**: `D:\dev_intagram_fh` (`/mnt/d/dev_intagram_fh`)
- **Hosting Repositori**: GitHub (`https://github.com/dandapurwidyatmokolaw-ux/dev_intagram_fh`)
- **Target Portal Web**: https://ilmuhukum.undip.ac.id (WordPress REST API)

---

## 1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)

### 1.1 Latar Belakang
Kanal media sosial Instagram fakultas dan unit akademik Universitas Diponegoro memproduksi berbagai publikasi visual kegiatan, seperti perkuliahan internasional (*Undip Global Classroom*), kunjungan studi siswa SMA, capaian prestasi mahasiswa tingkat nasional/internasional, dan agenda institusional. Selama ini, materi media sosial tersebut belum terkonversi secara otomatis menjadi artikel berita jurnalistik formal di portal web resmi Program Studi S1 Hukum (`ilmuhukum.undip.ac.id`), sehingga terjadi potensi kehilangan jejak dokumentasi akademik dan visibilitas SEO universitas.

Sistem ini dirancang sebagai aplikasi modular berstandar industri, **dikelola dalam repositori GitHub**, serta memiliki **fleksibilitas alamat target Instagram yang dinamis dan dapat diubah sewaktu-waktu melalui file konfigurasi `.env`** (default: `@law.undip`).

### 1.2 Tujuan Sistem
Membangun sistem pipeline otomatis end-to-end yang:
1. **Penarikan Fleksibel & Dinamis**: Menarik data dan foto postingan terbaru dari akun Instagram target yang ditentukan melalui variabel `.env` (`INSTAGRAM_TARGET_URL` / `INSTAGRAM_TARGET_USERNAME`) secara harian (*daily cron*).
2. **Penyimpanan Terstruktur**: Menyimpan data hasil ekstraksi dan file media ke dalam struktur JSON lokal (`data/pending_posts.json`) dan direktori aset media.
3. **AI Narrative Generator (Bilingual)**: Menghasilkan narasi artikel berita jurnalistik (standar 5W+1H) dalam format dwibahasa (**Bahasa Indonesia** dan **English**) berbasis analisis gambar dan caption Instagram.
4. **Approval & Feedback Gateway**: Mengirimkan draf berita ke email kurator `danda@staff.undip.ac.id` yang dilengkapi antarmuka umpan balik interaktif (Tombol Setujui / Minta Revisi Narasi).
5. **Iterative Revision Loop**: Menjalankan siklus revisi otomatis jika kurator meminta perbaikan narasi hingga draf disetujui.
6. **Publikasi Otomatis**: Mempublikasikan berita yang disetujui secara langsung ke situs `ilmuhukum.undip.ac.id` via WordPress REST API lengkap dengan gambar unggulan (*Featured Image*), tata letak bilingual, kategori, dan tag SEO.
7. **Pembersihan Antrean (Queue Cleanup)**: Menghapus data postingan dari antrean pending setelah berhasil dipublikasikan untuk mencegah redudansi dan duplikasi konten.
8. **Pengelolaan di GitHub**: Seluruh kode sumber, dokumentasi, pipeline deployment/CI, dan panduan penggunaan dikelola secara rapi dan versioned di GitHub, dengan proteksi ketat agar kredensial `.env` dan aset privat tidak bocor ke publik.

---

## 2. ARSITEKTUR & ALUR KERJA SISTEM (SYSTEM WORKFLOW)

```
┌─────────────────────────────────────────────────────────────┐
│ 0. KONFIGURASI LINGKUNGAN (.env)                            │
│    - INSTAGRAM_TARGET_URL / USERNAME (Dapat Diubah)         │
│    - Kredensial Email SMTP, WP REST API, AI Gateway         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. INGESTION ENGINE                                         │
│    - Baca Target Akun dari .env                             │
│    - Ekstraksi Postingan Harian (H-0 s.d H-1)               │
│    - Unduh Foto High-Res / Media ke data/media/             │
│    - Simpan ke antrean mentah: data/pending_posts.json      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. AI NARRATIVE GENERATOR (VISION & BILINGUAL ENGINE)       │
│    - Analisis Konten Visual + Teks Caption Instagram        │
│    - Pembuatan Judul & Berita 5W+1H (Bahasa Indonesia)      │
│    - Terjemahan & Lokalisasi Formal (English Version)       │
│    - Penyusunan Rekomendasi Kategori & Tag SEO              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. EMAIL APPROVAL & FEEDBACK GATEWAY                        │
│    - Kirim Email Interaktif ke danda@staff.undip.ac.id      │
│    - Menampilkan Gambar, Caption Asli, Narasi ID, Narasi EN │
│    - Tombol Aksi: [SETUJUI & PUBLISH] / [MINTA REVISI]      │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          │                                       │
          ▼                                       ▼
┌───────────────────────────────┐     ┌─────────────────────────────────────────────┐
│ 4. REVISION LOOP              │     │ 5. WORDPRESS REST API PUBLISHING ENGINE     │
│    (Jika Kurator Minta Revisi)│     │    (Jika Kurator Setuju / Approved)         │
│ - Terima catatan revisi       │     │ - Upload Featured Image ke WP Media         │
│ - AI regenerasi narasi baru   │     │ - Format Konten Dwibahasa (Bilingual Layout)│
│ - Kirim ulang email draf baru │     │ - Set Kategori, Tag, Slug, Excerpt          │
│ - Berulang sampai disetujui   │     │ - Status: 'publish' ke ilmuhukum.undip.ac.id│
└──────────────┬────────────────┘     │ - Hapus data dari data/pending_posts.json   │
               │ (Setelah disetujui)  │ - Arsipkan riwayat ke history_published.json│
               └─────────────────────►└─────────────────────────────────────────────┘
```

---

## 3. SPESIFIKASI DETAIL MODUL SISTEM

### Modul 1: Ingestion & Extraction Engine (Dynamic Instagram Scraper)
1. **Konfigurasi Sumber Dinamis**:
   - URL atau username akun target **tidak di-hardcode** di dalam kode program, melainkan dibaca dinamis dari `.env`:
     ```env
     INSTAGRAM_TARGET_URL=https://www.instagram.com/law.undip/
     INSTAGRAM_TARGET_USERNAME=law.undip
     ```
   - Administrator dapat mengganti target akun kapan saja (misal ke akun program studi lain, unit laboratorium, himpunan mahasiswa, atau fakultas lain) cukup dengan mengubah nilai konfigurasi tersebut tanpa perlu memodifikasi kode sumber.
2. **Jadwal Eksekusi**:
   - Berjalan 1 kali per hari (Cronjob Linux WSL / Windows Task Scheduler / GitHub Actions) pada pukul 07.00 WIB.
3. **Filter Waktu & Pencegahan Duplikasi**:
   - Mengambil postingan baru dalam rentang 24 jam terakhir (H-1).
   - Memeriksa `data/history_published.json` dan `data/pending_posts.json` untuk memastikan tidak ada `post_id` yang ditarik berulang.
4. **Ekstraksi Data & Media**:
   - `post_code` (Unique slug/code, contoh: `DeF_pD9JEiX`).
   - `post_url` (Tautan permanen postingan).
   - `published_at` (Timestamp publikasi ISO-8601).
   - `media_type` (Feed Image, Video Reels, atau Carousel).
   - `caption_raw` (Teks caption asli lengkap).
   - `display_uri` (URL aset gambar utama beresolusi penuh).
   - `alt_description` (Deskripsi aksesibilitas gambar).
5. **Penyimpanan Lokal**:
   - Gambar diunduh dan disimpan ke `data/media/{post_code}.jpg`.
   - Metadata lengkap disimpan ke `data/pending_posts.json`.

---

### Modul 2: AI Bilingual Narrative Generator
1. **Engine**: Multimodal LLM (OpenAI GPT-4o / Claude 3.5 Sonnet / Hermes 9Router Gateway).
2. **Pedoman Redaksional (Sesuai Aturan Berita WP Undip)**:
   - **Judul**: Menarik, informatif, mengandung kata kunci utama institusi, panjang 50-70 karakter.
   - **Lead Paragraph**: Menguraikan unsur 5W+1H (Siapa, Apa, Kapan, Di mana, Mengapa, dan Bagaimana) pada paragraf pembuka.
   - **Batang Tubuh**: Minimal 3-4 paragraf yang menjabarkan konteks akademis/hukum, narasumber yang hadir, serta relevansi bagi sivitas akademika.
   - **Struktur Dwibahasa**:
     - Bagian 1: Versi Bahasa Indonesia baku dan elegan.
     - Bagian 2: Versi Bahasa Inggris resmi (*formal academic news standard*).
   - **Kutipan & Excerpt**: Ringkasan 1-2 kalimat (maksimal 150 karakter).
   - **Kategori & Tag**: Menentukan kategori yang relevan di portal `ilmuhukum.undip.ac.id` (misal: Berita, Kerjasama Internasional, Prestasi Mahasiswa, Akademik) dan 3-5 tag kata kunci.

---

### Modul 3: Email Notification & Interactive Feedback Gateway
1. **Penerima**: `danda@staff.undip.ac.id`
2. **Protokol**: SMTP (Port 587 / 465) dikonfigurasi melalui `.env`.
3. **Komponen Email HTML**:
   - Header identitas bot redaksi resmi.
   - Metadata Postingan: Tanggal posting, tipe media, tautan asli Instagram.
   - Gambar Unggulan (Embedded inline image).
   - Caption Asli Instagram (sebagai referensi konteks).
   - Draf Berita Bahasa Indonesia (Judul, Excerpt, Konten Lengkap).
   - Draf Berita English (Title, Excerpt, Full Content).
   - Rekomendasi Kategori dan Tag.
4. **Mekanisme Umpan Balik (Feedback Mechanism)**:
   - **Tombol Hijau**: **[Setujui & Publikasikan ke Web]**
     Tautan langsung ke webhook: `http://host:port/api/feedback?action=approve&id={post_id}&token={hash}`
   - **Tombol Kuning**: **[Minta Perbaikan Narasi]**
     Tautan ke formulir web minimalis: `http://host:port/api/feedback?action=revise&id={post_id}&token={hash}`
     Kurator dapat mengisikan catatan perbaikan (contoh: *"Tolong tambahkan nama Dekan FH Undip"* atau *"Fokuskan pada peran mahasiswa"*).

---

### Modul 4: Iterative Revision Engine (Perbaikan Berulang)
1. Jika kurator mengirimkan feedback/catatan revisi:
   - Sistem mencatat riwayat versi narasi (`iteration_count`).
   - Sistem mengirimkan prompt baru ke AI yang memuat: narasi lama, caption Instagram, dan poin-poin revisi kurator.
   - AI memproduksi narasi baru yang telah disempurnakan (tetap dwibahasa).
   - Sistem mengirimkan email notifikasi baru dengan label `[REVISI #{n}] Draf Berita Siap Dikurasi`.
2. Alur ini terus berulang hingga kurator mengklik tombol **Setujui**.

---

### Modul 5: WordPress REST API Publishing Engine
1. **Endpoint Target**: `https://ilmuhukum.undip.ac.id/wp-json/wp/v2/`
2. **Autentikasi**: WordPress Application Password (dikonfigurasi di `.env`).
3. **Tahap Publikasi**:
   - **Unggah Media**: File gambar lokal diunggah ke `/wp/v2/media` lengkap dengan Alt Text dan Title SEO. Mendapatkan `featured_media_id`.
   - **Format Tata Letak Bilingual**:
     ```html
     <!-- Versi Bahasa Indonesia -->
     <div class="news-content-id">
         <h2>{Judul_ID}</h2>
         <p class="lead">{Lead_ID}</p>
         {Isi_Lengkap_ID}
     </div>
     <hr class="wp-block-separator" />
     <!-- English Version -->
     <div class="news-content-en">
         <h2><em>{Judul_EN}</em></h2>
         <p class="lead"><em>{Lead_EN}</em></p>
         <em>{Isi_Lengkap_EN}</em>
     </div>
     ```
   - **Posting Konten**: Membuat postingan baru di `/wp/v2/posts` dengan status `publish`.
4. **Pembersihan Antrean (Delete from Queue)**:
   - Setelah status HTTP 201 (Created) diterima dari WordPress, data postingan **otomatis dihapus dari `pending_posts.json`**.
   - Record postingan dipindahkan ke `history_published.json` lengkap dengan tanggal tayang, URL artikel WordPress baru, dan kode Instagram aslinya.
   - File gambar sementara yang sudah tayang dibersihkan dari penyimpanan lokal antrean aktif.

---

### Modul 6: GitHub Repository & Version Control Strategy
1. **Hosting & Struktur Repositori**:
   - Repositori dimuat di GitHub (misal: `dandapurwidyatmokolaw-ux/dev_intagram_fh`).
   - Dilengkapi dengan dokumentasi teknis lengkap di `README.md`, panduan instalasi, dan panduan konfigurasi.
2. **Proteksi Kredensial & Sensitivitas Data (`.gitignore`)**:
   - File `.env` **WAJIB** masuk ke dalam `.gitignore` agar password email, token AI, dan WordPress Application Password tidak pernah terunggah ke repositori publik.
   - Folder `data/media/` dan file data `pending_posts.json` masuk ke dalam `.gitignore` untuk mencegah penumpukan aset biner dan data sementara di Git history.
   - Template `.env.example` disediakan sebagai acuan konfigurasi aman.
3. **Automasi & CI/CD**:
   - Repositori mendukung GitHub Actions (`.github/workflows/daily_ingest.yml`) untuk linting kode (flake8/black) dan eksekusi skrip otomatis (atau integrasi dengan server/WSL runner lokal).

---

## 4. STRUKTUR DIREKTORI REPOSITORI GITHUB

```
dev_intagram_fh/ (Git Repository Root)
│
├── .github/
│   └── workflows/
│       ├── test.yml             # CI testing & syntax validation
│       └── daily_ingest.yml     # (Opsional) GitHub Actions scheduler
│
├── .gitignore                   # Mengabaikan .env, data/media/, data/*.json, venv/
├── .env.example                 # Template referensi konfigurasi aman
├── README.md                    # Dokumentasi lengkap proyek & panduan setup
├── PRD.md                       # Dokumen Spesifikasi Produk (file ini)
├── requirements.txt             # Dependensi Python (requests, python-docx, jinja2, dll)
├── setup.py / pyproject.toml    # Metadata package Python
│
├── config/
│   ├── __init__.py
│   └── settings.py              # Parser konfigurasi dinamis (.env)
│
├── data/                        # [Ignored in Git, dibuat otomatis saat runtime]
│   ├── pending_posts.json       # Antrean postingan aktif yang menunggu kurasi/upload
│   ├── history_published.json   # Riwayat postingan yang sudah tayang di web
│   └── media/                   # Direktori unduhan gambar lokal ({code}.jpg)
│
├── src/
│   ├── __init__.py
│   ├── scraper.py               # Penarik data Instagram dinamis (baca target dari .env)
│   ├── narrator.py              # Generator narasi berita dwibahasa (AI Multimodal)
│   ├── mailer.py                # Pengirim email HTML draf kurasi ke staf
│   ├── feedback_server.py       # Gateway web lokal penerima klik Approve/Revise
│   ├── wp_publisher.py          # Modul publikasi ke WordPress REST API
│   └── main.py                  # Orkestrator alur kerja harian (CLI/Cron entrypoint)
│
└── tests/                       # Unit testing modul
    ├── test_scraper.py
    ├── test_narrator.py
    └── test_publisher.py
```

---

## 5. SKEMA DATA JSON (DATA CONTRACTS)

### 5.1 Skema Antrean Postingan (`data/pending_posts.json`)
```json
[
  {
    "post_id": "DeF_pD9JEiX",
    "target_username": "law.undip",
    "post_url": "https://www.instagram.com/law.undip/p/DeF_pD9JEiX/",
    "published_at": "2026-10-04T18:08:52Z",
    "media_type": "image",
    "local_image_path": "data/media/DeF_pD9JEiX.jpg",
    "caption_raw": "Innalillahi wa inna ilaihi raji'un...",
    "status": "pending_review",
    "current_iteration": 1,
    "draft": {
      "title_id": "Duka Cita Mendalam FH Undip atas Berpulangnya Mahasiswa Angkatan 2023",
      "title_en": "Deep Condolences: Diponegoro University Faculty of Law Mourns the Passing of Class of 2023 Student",
      "content_id": "<p>Semarang — Keluarga besar Fakultas Hukum...</p>",
      "content_en": "<p>Semarang — The academic community of Faculty of Law...</p>",
      "excerpt_id": "Keluarga besar FH Undip berduka cita atas berpulangnya Adyatma Maulana Lutfi...",
      "excerpt_en": "The academic community of FH Undip expresses deepest condolences...",
      "categories": ["Berita", "Duka Cita"],
      "tags": ["FH Undip", "Mahasiswa", "Duka Cita", "Kampus Hukum Progresif"]
    },
    "revision_history": []
  }
]
```

### 5.2 Skema Arsip Riwayat Publikasi (`data/history_published.json`)
```json
[
  {
    "post_id": "DeF_pD9JEiX",
    "target_username": "law.undip",
    "wp_post_id": 36890,
    "wp_post_url": "https://ilmuhukum.undip.ac.id/duka-cita-mahasiswa-2023/",
    "published_at": "2026-10-05T09:30:00Z",
    "approver": "danda@staff.undip.ac.id",
    "iteration_count": 1
  }
]
```

---

## 6. SPESIFIKASI KONFIGURASI LINGKUNGAN DINAMIS (`.env`)

Seluruh kredensial sensitif dan parameter dinamis disimpan secara aman di file `.env`:

```env
# ================================================================
# [1] KONFIGURASI TARGET INSTAGRAM (DINAMIS DAPAT DIUBAH)
# ================================================================
# Target akun dapat diganti kapan saja tanpa mengubah kode program
INSTAGRAM_TARGET_URL=https://www.instagram.com/law.undip/
INSTAGRAM_TARGET_USERNAME=law.undip

# ================================================================
# [2] REPOSITORY GITHUB & APLIKASI
# ================================================================
GITHUB_REPOSITORY=dandapurwidyatmokolaw-ux/dev_intagram_fh
APP_ENV=production
APP_PORT=5000
APP_BASE_URL=http://localhost:5000
DATA_DIR=/mnt/d/dev_intagram_fh/data

# ================================================================
# [3] KONFIGURASI EMAIL KURATOR & NOTIFIKASI
# ================================================================
CURATOR_EMAIL=danda@staff.undip.ac.id
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=danda@staff.undip.ac.id
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx
SMTP_FROM_NAME="Redaksi Berita FH Undip Bot"

# ================================================================
# [4] AI GENERATOR (9ROUTER / OPENAI / CLAUDE / LOCAL LLM)
# ================================================================
AI_PROVIDER=9router
AI_API_BASE=http://127.0.0.1:20128/v1
AI_API_KEY=sk-your-token-here
AI_MODEL=gpt-4o

# ================================================================
# [5] WORDPRESS REST API (ILMUHUKUM.UNDIP.AC.ID)
# ================================================================
WP_BASE_URL=https://ilmuhukum.undip.ac.id
WP_USERNAME=your_wp_username
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx
WP_DEFAULT_STATUS=publish
WP_DEFAULT_CATEGORY_ID=1

# ================================================================
# [6] KEAMANAN TOKEN WEBHOOK FEEDBACK
# ================================================================
FEEDBACK_SECRET_KEY=b9c47e8293d01fa56e82a
```

---

## 7. RENCANA IMPLEMENTASI & JADWAL KERJA

| Fase | Durasi | Deskripsi Aktivitas | Deliverable |
| :--- | :---: | :--- | :--- |
| **Fase 1: Repositori & Scraper Dinamis** | Hari 1 | Inisialisasi GitHub repo, `.gitignore`, parser `.env`, penarik data Instagram dinamis | `src/scraper.py`, `config/settings.py` |
| **Fase 2: AI Bilingual Narrator** | Hari 2 | Implementasi prompt generator berita jurnalistik dwibahasa (ID & EN) standar 5W+1H | `src/narrator.py` |
| **Fase 3: Email & Feedback Loop** | Hari 3 | Template email interaktif, integrasi SMTP, server mini webhook Approve/Revise | `src/mailer.py`, `src/feedback_server.py` |
| **Fase 4: WordPress Publisher & Cleanup** | Hari 4 | Integrasi REST API WP (Media upload, posting dwibahasa, hapus antrean setelah tayang) | `src/wp_publisher.py` |
| **Fase 5: Pengujian, CI/CD & Deploy** | Hari 5 | Pengujian end-to-end, setup cronjob harian, dorong commit ke GitHub | Repositori GitHub Live & Terdokumentasi |

---

## 8. KRITERIA KEBERHASILAN (ACCEPTANCE CRITERIA)

1. [x] **Dukungan GitHub**: Seluruh struktur proyek, kode sumber, dan dokumentasi tersusun rapi dalam repositori Git dengan proteksi `.gitignore` yang ketat.
2. [x] **Target Dinamis**: Alamat Instagram yang ditarik sepenuhnya fleksibel dan dapat diubah melalui `INSTAGRAM_TARGET_URL` / `INSTAGRAM_TARGET_USERNAME` di `.env` tanpa modifikasi kode.
3. [x] **Penarikan & Media**: Sistem berhasil mengunduh gambar dan data metadata postingan ke format JSON terstruktur.
4. [x] **Kualitas Narasi Bilingual**: Narasi berita mencerminkan konteks gambar dan caption dalam Bahasa Indonesia dan English standar jurnalistik 5W+1H.
5. [x] **Email & Siklus Revisi**: Draf terkirim ke `danda@staff.undip.ac.id` dengan tombol aksi. Jika kurator meminta perbaikan, sistem meregenerasi narasi baru sampai disetujui.
6. [x] **Publikasi WordPress**: Artikel yang disetujui langsung terbit di `ilmuhukum.undip.ac.id` dengan Featured Image dan tata letak dwibahasa.
7. [x] **Pembersihan Antrean**: Postingan yang telah dipublikasikan otomatis dihapus dari antrean `pending_posts.json` untuk menjamin nol duplikasi.
