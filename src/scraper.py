"""
src/scraper.py
Modul penarik data dan media Instagram dinamis berdasarkan konfigurasi .env.
Mendukung filter ketat postingan hari ini (WIB / UTC+7), ekstraksi media, dan anti-duplikasi.
"""

import os
import re
import json
import logging
import subprocess
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import settings

# Konfigurasi Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("InstagramScraper")

# Timezone Indonesia Barat (WIB = UTC+7)
TIMEZONE_WIB = timezone(timedelta(hours=7))

class InstagramScraper:
    def __init__(self, target_url: Optional[str] = None, target_username: Optional[str] = None):
        self.target_url = target_url or settings.INSTAGRAM_TARGET_URL
        self.target_username = target_username or settings.INSTAGRAM_TARGET_USERNAME
        self.pending_file = settings.PENDING_POSTS_FILE
        self.history_file = settings.HISTORY_FILE
        self.media_dir = settings.MEDIA_DIR

        # Pastikan direktori media dan data siap
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.pending_file.parent.mkdir(parents=True, exist_ok=True)

    def load_processed_ids(self) -> set:
        """Memuat daftar ID postingan yang sudah ada di antrean pending atau sudah dipublikasikan."""
        processed = set()

        # Baca dari history_published.json
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    for item in history:
                        if isinstance(item, dict) and "post_id" in item:
                            processed.add(item["post_id"])
            except Exception as e:
                logger.warning(f"Gagal membaca history_file: {e}")

        # Baca dari pending_posts.json
        if self.pending_file.exists():
            try:
                with open(self.pending_file, 'r', encoding='utf-8') as f:
                    pending = json.load(f)
                    for item in pending:
                        if isinstance(item, dict) and "post_id" in item:
                            processed.add(item["post_id"])
            except Exception as e:
                logger.warning(f"Gagal membaca pending_file: {e}")

        return processed

    def fetch_page_dom(self, url: str) -> str:
        """Mengambil DOM halaman Instagram menggunakan Headless Chromium."""
        logger.info(f"Mengambil data halaman Instagram via Chromium: {url}")
        cmd = [
            "chromium-browser",
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--dump-dom",
            url
        ]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=45)
            if result.returncode != 0:
                logger.warning(f"Chromium exit code {result.returncode}: {result.stderr[:200]}")
            return result.stdout
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout saat mengambil halaman Instagram: {url}")
            return ""
        except Exception as e:
            logger.error(f"Gagal menjalankan Chromium: {e}")
            return ""

    def extract_nodes_from_dom(self, dom_text: str) -> List[Dict[str, Any]]:
        """Mengekstrak node postingan dari JSON Relay cache yang tersemat dalam tag script."""
        nodes = []
        if not dom_text:
            return nodes

        matches = re.findall(r'<script[^>]*>(.*?)</script>', dom_text, re.DOTALL)
        for content in matches:
            if "polaris_ordered_timeline_connection" not in content:
                continue
            try:
                data = json.loads(content)
                def search_connection(obj):
                    if not isinstance(obj, (dict, list)):
                        return
                    if isinstance(obj, dict):
                        if "polaris_ordered_timeline_connection" in obj:
                            conn = obj["polaris_ordered_timeline_connection"]
                            if isinstance(conn, dict) and "edges" in conn:
                                for edge in conn["edges"]:
                                    node = edge.get("node")
                                    if node and isinstance(node, dict):
                                        nodes.append(node)
                        for k, v in obj.items():
                            search_connection(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            search_connection(item)

                search_connection(data)
            except Exception:
                continue

        logger.info(f"Berhasil menemukan {len(nodes)} node postingan dari profil.")
        return nodes

    def get_post_exact_date(self, post_code: str) -> Optional[datetime]:
        """
        Mengambil tanggal publikasi eksak postingan dari halaman detail post.
        Mengembalikan datetime dalam timezone WIB (Asia/Jakarta, UTC+7).
        """
        post_url = f"https://www.instagram.com/{self.target_username}/p/{post_code}/"
        dom = self.fetch_page_dom(post_url)
        if not dom:
            return None

        # 1. Cek nilai JSON taken_at (timestamp unix detik)
        m_taken = re.search(r'"taken_at":\s*(\d+)', dom)
        if m_taken:
            ts = int(m_taken.group(1))
            dt_wib = datetime.fromtimestamp(ts, tz=TIMEZONE_WIB)
            return dt_wib

        # 2. Cek tag <time datetime="...">
        time_match = re.search(r'<time[^>]*datetime=["\']([^"\']+)["\']', dom)
        if time_match:
            iso_str = time_match.group(1).replace('Z', '+00:00')
            try:
                dt_utc = datetime.fromisoformat(iso_str)
                dt_wib = dt_utc.astimezone(TIMEZONE_WIB)
                return dt_wib
            except Exception as e:
                logger.warning(f"Gagal parse iso date {iso_str}: {e}")

        return None

    def download_media(self, uri: str, post_code: str) -> Optional[str]:
        """Mengunduh gambar media postingan ke data/media/{post_code}.jpg."""
        if not uri:
            return None
        target_path = self.media_dir / f"{post_code}.jpg"
        if target_path.exists() and target_path.stat().st_size > 0:
            return str(target_path)

        try:
            req = urllib.request.Request(
                uri,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
                with open(target_path, "wb") as f_out:
                    f_out.write(data)
            logger.info(f"Berhasil mengunduh media {post_code}.jpg ({len(data)} bytes).")
            return str(target_path)
        except Exception as e:
            logger.warning(f"Gagal mengunduh media {post_code}: {e}")
            return None

    def scrape(self, today_only: bool = True, force: bool = False) -> List[Dict[str, Any]]:
        """
        Menjalankan penarikan postingan dari target akun.
        Jika today_only=True, HANYA mengambil postingan yang dipublikasikan pada hari ini (WIB).
        Menyimpan postingan baru ke data/pending_posts.json jika belum pernah diproses.
        """
        processed_ids = set() if force else self.load_processed_ids()
        dom = self.fetch_page_dom(self.target_url)
        raw_nodes = self.extract_nodes_from_dom(dom)

        today_date_wib = datetime.now(TIMEZONE_WIB).date()
        logger.info(f"Tanggal Hari Ini (WIB): {today_date_wib}. Filter today_only: {today_only}")

        new_posts = []
        for i, node in enumerate(raw_nodes):
            code = node.get("code")
            if not code:
                continue

            if code in processed_ids:
                logger.info(f"Post [{code}] sudah pernah diproses di antrean/riwayat, lewati.")
                continue

            # Periksa tanggal eksak postingan
            exact_dt_wib = self.get_post_exact_date(code)
            if not exact_dt_wib:
                logger.warning(f"Tidak dapat menentukan tanggal untuk post [{code}], lewati.")
                continue

            post_date_wib = exact_dt_wib.date()
            logger.info(f"Post [{code}] tanggal terbit WIB: {exact_dt_wib.strftime('%Y-%m-%d %H:%M:%S %Z')}")

            if today_only:
                if post_date_wib < today_date_wib:
                    logger.info(f"Post [{code}] berasal dari tanggal sebelumnya ({post_date_wib} < {today_date_wib}). Menghentikan pencarian postingan lama.")
                    # Karena postingan terurut kronologis mundur, jika ketemu yang lebih lama, hentikan loop
                    break
                elif post_date_wib > today_date_wib:
                    # Tanggal masa depan (jika ada anomali timezone), lewati
                    continue

            # Postingan lolos filter (Hari Ini)
            caption = (node.get("caption") or {}).get("text", "")
            display_uri = node.get("display_uri")
            alt_desc = node.get("accessibility_caption", "")
            product_type = node.get("product_type", "feed")

            # Unduh file media
            local_media_path = self.download_media(display_uri, code)

            post_record = {
                "post_id": code,
                "target_username": self.target_username,
                "post_url": f"https://www.instagram.com/{self.target_username}/p/{code}/",
                "published_at": exact_dt_wib.isoformat(),
                "media_type": product_type,
                "local_image_path": local_media_path,
                "caption_raw": caption,
                "alt_description": alt_desc,
                "status": "pending_review",
                "current_iteration": 0,
                "draft": None,
                "revision_history": []
            }
            new_posts.append(post_record)
            processed_ids.add(code)

        if new_posts:
            # Muat antrean lama jika ada dan belum tayang
            existing_queue = []
            if self.pending_file.exists():
                try:
                    with open(self.pending_file, "r", encoding="utf-8") as f:
                        existing_queue = json.load(f)
                except Exception:
                    existing_queue = []

            # Gabungkan dengan postingan baru
            combined_queue = new_posts + existing_queue
            with open(self.pending_file, "w", encoding="utf-8") as f:
                json.dump(combined_queue, f, ensure_ascii=False, indent=2)
            logger.info(f"Tersimpan {len(new_posts)} postingan hari ini ke {self.pending_file}.")
        else:
            logger.info("Tidak ada postingan hari ini yang perlu ditambahkan ke antrean.")

        return new_posts

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Instagram Content Scraper (Harian)")
    parser.add_argument("--url", help="Target Instagram URL override")
    parser.add_argument("--user", help="Target Instagram username override")
    parser.add_argument("--all", action="store_true", help="Ambil semua postingan tanpa filter hari ini")
    parser.add_argument("--force", action="store_true", help="Paksa tarik ulang meskipun sudah ada di riwayat")
    args = parser.parse_args()

    scraper = InstagramScraper(target_url=args.url, target_username=args.user)
    posts = scraper.scrape(today_only=not args.all, force=args.force)
    print(f"\nHasil Eksekusi Scraper: {len(posts)} postingan hari ini.")
    for p in posts:
        print(f"- [{p['post_id']}] Waktu: {p['published_at']}")
        print(f"  URL: {p['post_url']}")
        print(f"  Media: {p['local_image_path']}")
        print(f"  Caption: {p['caption_raw'][:100]}...\n")
