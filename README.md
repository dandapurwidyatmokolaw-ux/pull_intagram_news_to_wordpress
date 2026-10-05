# Sistem Otomasi Berita Instagram ke Web FH UNDIP

Sistem otomasi cerdas untuk mengekstraksi konten dan media dari akun Instagram resmi (default: `@law.undip`), menyusun narasi artikel berita jurnalistik dwibahasa (**Bahasa Indonesia & English**) berbasis AI (standar 5W+1H), mengirimkan draf kurasi interaktif ke email kurator (`danda@staff.undip.ac.id`), serta mempublikasikan berita yang disetujui secara otomatis ke portal resmi [https://ilmuhukum.undip.ac.id](https://ilmuhukum.undip.ac.id).

---

## Fitur Utama

1. **Target Instagram Dinamis**: Alamat URL dan akun Instagram dapat diubah kapan saja melalui file konfigurasi `.env` (`INSTAGRAM_TARGET_URL` / `INSTAGRAM_TARGET_USERNAME`) tanpa modifikasi kode sumber.
2. **Pencegahan Konten Duplikat**: Otomatis mendeteksi postingan yang sudah ada di antrean (`data/pending_posts.json`) maupun yang sudah terbit (`data/history_published.json`).
3. **Penyimpanan Terstruktur**: Menyimpan aset foto resolusi penuh ke direktori `data/media/` dan metadata ke JSON.
4. **AI Narrative Generator (Bilingual)**: Memproduksi draf berita standar 5W+1H dalam Bahasa Indonesia dan English.
5. **Kurasi Email Interaktif**: Dilengkapi tombol **[Setujui & Terbitkan]** serta **[Minta Perbaikan Narasi]**.
6. **Iterative Revision Loop**: Menghasilkan versi draf baru secara otomatis jika kurator meminta perbaikan sampai disetujui.
7. **Pembersihan Antrean Otomatis**: Menghapus data dari antrean pending setelah berhasil terbit di WordPress untuk menjamin integritas data.

---

## Struktur Direktori

```text
dev_intagram_fh/
├── .gitignore                   # Proteksi kredensial .env dan data runtime
├── .env.example                 # Template konfigurasi aman
├── .env                         # Konfigurasi aktif (rahasia)
├── README.md                    # Dokumentasi utama proyek
├── PRD.md                       # Dokumen Spesifikasi Produk (PRD v1.1.0)
├── requirements.txt             # Dependensi Python
│
├── config/
│   ├── __init__.py
│   └── settings.py              # Parser konfigurasi dinamis (.env)
│
├── data/                        # [Ignored in Git, dibuat otomatis saat runtime]
│   ├── pending_posts.json       # Antrean postingan aktif yang menunggu kurasi
│   ├── history_published.json   # Riwayat postingan yang sudah terbit di web
│   └── media/                   # Direktori unduhan gambar ({post_code}.jpg)
│
├── src/
│   ├── __init__.py
│   ├── scraper.py               # Penarik data Instagram dinamis
│   ├── narrator.py              # Generator narasi dwibahasa AI (Fase 2)
│   ├── mailer.py                # Pengirim email kurasi interaktif (Fase 3)
│   ├── feedback_server.py       # Webhook gateway tombol persetujuan (Fase 3)
│   ├── wp_publisher.py          # Modul publikasi WordPress REST API (Fase 4)
│   └── main.py                  # Entrypoint orkestrasi harian
│
└── tests/
    └── test_scraper.py          # Unit testing scraper
```

---

## Panduan Instalasi & Penggunaan

### 1. Prasyarat Sistem
- Python 3.10+
- Chromium Browser / Headless Chrome (`chromium-browser`)
- Akses internet aktif

### 2. Instalasi Dependensi
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Lingkungan (`.env`)
Salin file template `.env.example` menjadi `.env`, lalu sesuaikan kredensial Anda:
```bash
cp .env.example .env
```
Contoh pengaturan target akun Instagram dinamis:
```env
INSTAGRAM_TARGET_URL=https://www.instagram.com/law.undip/
INSTAGRAM_TARGET_USERNAME=law.undip
```

### 4. Menjalankan Scraper (Fase 1)
Jalankan penarikan postingan terbaru:
```bash
PYTHONPATH=. python src/scraper.py --limit 5
```
Opsi argumen:
- `--limit N`: Menentukan batas maksimal postingan yang ditarik (default: 5).
- `--url <URL>`: Override alamat Instagram sementara tanpa mengubah `.env`.
- `--force`: Memaksa penarikan ulang postingan yang sudah ada di riwayat.

### 5. Menjalankan Pengujian
```bash
PYTHONPATH=. python -m unittest discover tests/
```

---

## Lisensi & Kontribusi
Dikelola oleh Fakultas Hukum Universitas Diponegoro untuk diseminasi publikasi akademik digital.
