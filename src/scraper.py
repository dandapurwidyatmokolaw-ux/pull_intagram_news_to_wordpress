"""
src/scraper.py
Modul penarik data dan media Instagram dinamis berdasarkan konfigurasi .env.
Mendukung ekstraksi otomatis melalui Headless Chromium, unduh media, dan anti-duplikasi.
"""

import os
import re
import json
import logging
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import settings

# Konfigurasi Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("InstagramScraper")

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
            logger.error("Timeout saat mengambil halaman Instagram via Chromium.")
            return ""
        except Exception as e:
            logger.error(f"Gagal menjalankan Chromium: {e}")
            return ""

    def extract_nodes_from_dom(self, dom_text: str) -> List[Dict[str, Any]]:
        """Mengekstrak node postingan dari JSON Relay cache yang tersemat dalam tag script."""
        nodes = []
        if not dom_text:
            return nodes

        # Cari pola script JSON yang memuat timeline connection
        # Regex mencari string polaris_ordered_timeline_connection
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

        logger.info(f"Berhasil menemukan {len(nodes)} node postingan dari DOM Relay cache.")
        return nodes

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

    def scrape(self, max_posts: int = 10, force: bool = False) -> List[Dict[str, Any]]:
        """
        Menjalankan penarikan postingan baru dari target akun.
        Menyimpan postingan baru ke data/pending_posts.json jika belum pernah diproses.
        """
        processed_ids = set() if force else self.load_processed_ids()
        dom = self.fetch_page_dom(self.target_url)
        raw_nodes = self.extract_nodes_from_dom(dom)

        new_posts = []
        for node in raw_nodes[:max_posts]:
            code = node.get("code")
            if not code:
                continue

            if code in processed_ids:
                logger.debug(f"Post {code} sudah pernah diproses, lewati.")
                continue

            # Parse timestamp jika ada
            taken_at = node.get("taken_at")
            if taken_at:
                published_at = datetime.fromtimestamp(taken_at, tz=timezone.utc).isoformat()
            else:
                published_at = datetime.now(timezone.utc).isoformat()

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
                "published_at": published_at,
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
            # Muat antrean lama dan gabungkan
            existing_queue = []
            if self.pending_file.exists():
                try:
                    with open(self.pending_file, "r", encoding="utf-8") as f:
                        existing_queue = json.load(f)
                except Exception:
                    existing_queue = []

            # Gabungkan dengan prioritas data baru di depan
            combined_queue = new_posts + existing_queue
            with open(self.pending_file, "w", encoding="utf-8") as f:
                json.dump(combined_queue, f, ensure_ascii=False, indent=2)
            logger.info(f"Tersimpan {len(new_posts)} postingan baru ke {self.pending_file}.")
        else:
            logger.info("Tidak ada postingan baru yang perlu ditambahkan ke antrean.")

        return new_posts

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Instagram Content Scraper")
    parser.add_argument("--url", help="Target Instagram URL override")
    parser.add_argument("--user", help="Target Instagram username override")
    parser.add_argument("--limit", type=int, default=5, help="Jumlah maksimal postingan yang ditarik")
    parser.add_argument("--force", action="store_true", help="Paksa tarik ulang meskipun sudah ada di riwayat")
    args = parser.parse_args()

    scraper = InstagramScraper(target_url=args.url, target_username=args.user)
    posts = scraper.scrape(max_posts=args.limit, force=args.force)
    print(f"\nHasil Eksekusi Scraper: {len(posts)} postingan baru.")
    for p in posts:
        print(f"- [{p['post_id']}] {p['post_url']} | Media: {p['local_image_path']}")
