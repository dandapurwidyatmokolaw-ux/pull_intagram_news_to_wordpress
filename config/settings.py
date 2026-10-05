"""
config/settings.py
Modul konfigurasi terpusat untuk memuat variabel lingkungan (.env).
Mendukung target akun Instagram dinamis, email SMTP, AI API, dan WordPress REST API.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Path basis proyek
BASE_DIR = Path(__file__).resolve().parent.parent

# Muat file .env jika ada
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# [1] Target Instagram Dinamis
INSTAGRAM_TARGET_URL = os.getenv("INSTAGRAM_TARGET_URL", "https://www.instagram.com/law.undip/").strip()
INSTAGRAM_TARGET_USERNAME = os.getenv("INSTAGRAM_TARGET_USERNAME", "").strip()

if not INSTAGRAM_TARGET_USERNAME:
    # Auto-extract username dari URL jika kosong
    trimmed = INSTAGRAM_TARGET_URL.rstrip("/")
    INSTAGRAM_TARGET_USERNAME = trimmed.split("/")[-1]

# [2] Direktori & File Penyimpanan Data
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
MEDIA_DIR = DATA_DIR / "media"
PENDING_POSTS_FILE = DATA_DIR / "pending_posts.json"
HISTORY_FILE = DATA_DIR / "history_published.json"

# Pastikan folder data dan media selalu ada
DATA_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# [3] Kredensial Email & Kurator
CURATOR_EMAIL = os.getenv("CURATOR_EMAIL", "danda@staff.undip.ac.id")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Redaksi Berita FH Undip Bot")

# [4] AI Generator Gateway
AI_PROVIDER = os.getenv("AI_PROVIDER", "9router")
AI_API_BASE = os.getenv("AI_API_BASE", "http://127.0.0.1:20128/v1")
AI_API_KEY = os.getenv("AI_API_KEY", "") or os.getenv("HERMES_CUSTOM_172_17_68_249_20128_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "ag/gemini-3.8-flash-high")

# [5] WordPress REST API
WP_BASE_URL = os.getenv("WP_BASE_URL", "https://ilmuhukum.undip.ac.id").rstrip("/")
WP_USERNAME = os.getenv("WP_USERNAME", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")
WP_DEFAULT_STATUS = os.getenv("WP_DEFAULT_STATUS", "publish")
WP_DEFAULT_CATEGORY_ID = int(os.getenv("WP_DEFAULT_CATEGORY_ID", "143"))
WP_CATEGORY_ID_EN = int(os.getenv("WP_CATEGORY_ID_EN", "145"))

# [6] Webhook & Server
APP_ENV = os.getenv("APP_ENV", "production")
APP_PORT = int(os.getenv("APP_PORT", "5000"))
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5000").rstrip("/")
FEEDBACK_SECRET_KEY = os.getenv("FEEDBACK_SECRET_KEY", "default_secret_key")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "dandapurwidyatmokolaw-ux/pull_intagram_news_to_wordpress")

def get_summary():
    """Mengembalikan ringkasan konfigurasi aktif tanpa membocorkan password."""
    return {
        "instagram_target_username": INSTAGRAM_TARGET_USERNAME,
        "instagram_target_url": INSTAGRAM_TARGET_URL,
        "curator_email": CURATOR_EMAIL,
        "wp_base_url": WP_BASE_URL,
        "data_dir": str(DATA_DIR),
        "media_dir": str(MEDIA_DIR),
        "ai_provider": AI_PROVIDER,
        "ai_model": AI_MODEL,
        "github_repo": GITHUB_REPOSITORY
    }

if __name__ == "__main__":
    import json
    print("Konfigurasi Sistem Aktif:")
    print(json.dumps(get_summary(), indent=2))
