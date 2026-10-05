"""
src/wp_publisher.py
Modul publikasi artikel berita dwibahasa ke portal resmi WordPress (https://ilmuhukum.undip.ac.id).
Mendukung upload media unggulan (Featured Image), pembuatan/pencarian tag otomatis,
penerbitan artikel dwibahasa (ID & EN), serta pembersihan antrean pending (Queue Cleanup)
ke riwayat publikasi (history_published.json).
"""

import os
import json
import base64
import logging
import mimetypes
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import requests

from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("WordPressPublisher")

TIMEZONE_WIB = timezone(timedelta(hours=7))

class WordPressPublisher:
    def __init__(self):
        self.base_url = settings.WP_BASE_URL.rstrip("/")
        self.username = settings.WP_USERNAME
        self.app_password = settings.WP_APP_PASSWORD
        self.default_status = settings.WP_DEFAULT_STATUS
        self.cat_id_id = settings.WP_DEFAULT_CATEGORY_ID   # 143 (Berita)
        self.cat_id_en = settings.WP_CATEGORY_ID_EN        # 145 (news)
        self.pending_file = settings.PENDING_POSTS_FILE
        self.history_file = settings.HISTORY_FILE

        # Inisialisasi Basic Auth Header
        auth_token = base64.b64encode(f"{self.username}:{self.app_password}".encode("utf-8")).decode("utf-8")
        self.headers = {
            "Authorization": f"Basic {auth_token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FHUndip-NewsBot/1.0"
        }

    def check_connection(self) -> bool:
        """Memverifikasi kredensial dan hak akses ke WordPress REST API."""
        endpoint = f"{self.base_url}/wp-json/wp/v2/users/me"
        try:
            r = requests.get(endpoint, headers=self.headers, timeout=15)
            if r.status_code == 200:
                user_info = r.json()
                logger.info(f"Koneksi WP REST API terverifikasi: User '{user_info.get('name')}' (ID: {user_info.get('id')})")
                return True
            else:
                logger.error(f"Gagal verifikasi WP REST API: HTTP {r.status_code} - {r.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"Koneksi ke WP REST API gagal: {e}")
            return False

    def check_duplicate(self, title: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """Mengecek apakah artikel dengan judul yang sama persis sudah pernah terbit di WP."""
        endpoint = f"{self.base_url}/wp-json/wp/v2/posts"
        clean_title = title.strip()
        params = {"search": clean_title, "per_page": 5}
        try:
            r = requests.get(endpoint, headers=self.headers, params=params, timeout=15)
            if r.status_code == 200:
                posts = r.json()
                for p in posts:
                    p_title = p.get("title", {}).get("rendered", "").strip()
                    if clean_title.lower() == p_title.lower():
                        return True, p.get("id"), p.get("link")
        except Exception as e:
            logger.warning(f"Gagal memeriksa duplikasi online: {e}")
        return False, None, None

    def get_or_create_tag(self, tag_name: str) -> Optional[int]:
        """Mencari tag berdasarkan nama atau membuatnya baru jika belum ada."""
        clean_name = tag_name.strip().lstrip("#")
        if not clean_name:
            return None

        endpoint = f"{self.base_url}/wp-json/wp/v2/tags"
        try:
            # 1. Cari tag yang sudah ada
            r = requests.get(endpoint, headers=self.headers, params={"search": clean_name}, timeout=15)
            if r.status_code == 200:
                tags = r.json()
                for t in tags:
                    if t.get("name", "").lower() == clean_name.lower():
                        return t.get("id")

            # 2. Buat tag baru jika belum ada
            create_r = requests.post(endpoint, headers=self.headers, json={"name": clean_name}, timeout=15)
            if create_r.status_code in (200, 201):
                new_tag = create_r.json()
                return new_tag.get("id")
        except Exception as e:
            logger.warning(f"Gagal memproses tag '{clean_name}': {e}")
        return None

    def upload_featured_media(self, image_path: str, alt_text: str = "", title: str = "") -> Tuple[Optional[int], Optional[str]]:
        """Mengunggah gambar ke WordPress Media Library dan mengembalikan (media_id, media_url)."""
        path = Path(image_path)
        if not path.exists():
            logger.error(f"File gambar {image_path} tidak ditemukan!")
            return None, None

        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            mime_type = "image/jpeg"

        filename = path.name
        endpoint = f"{self.base_url}/wp-json/wp/v2/media"
        headers = self.headers.copy()
        headers["Content-Type"] = mime_type
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'

        logger.info(f"Mengunggah gambar unggulan: {filename} ({path.stat().st_size} bytes)...")
        try:
            with open(path, "rb") as f:
                img_data = f.read()

            r = requests.post(endpoint, headers=headers, data=img_data, timeout=40)
            if r.status_code in (200, 201):
                res = r.json()
                media_id = res.get("id")
                media_url = res.get("source_url")
                logger.info(f"Gambar berhasil diunggah! Media ID: {media_id} | URL: {media_url}")

                # Update metadata Alt Text dan Title gambar
                update_endpoint = f"{endpoint}/{media_id}"
                update_payload = {
                    "alt_text": alt_text or title or filename,
                    "title": title or filename
                }
                requests.post(update_endpoint, headers=self.headers, json=update_payload, timeout=15)

                return media_id, media_url
            else:
                logger.error(f"Gagal upload media: HTTP {r.status_code} - {r.text[:250]}")
                return None, None
        except Exception as e:
            logger.error(f"Terjadi kesalahan saat upload media: {e}")
            return None, None

    def post_article(
        self,
        title: str,
        content: str,
        excerpt: str,
        category_id: int,
        lang: str,
        tag_names: List[str],
        featured_media_id: Optional[int] = None,
        post_date_iso: Optional[str] = None
    ) -> Dict[str, Any]:
        """Menerbitkan satu artikel ke WordPress."""
        tag_ids = []
        for tn in tag_names:
            tid = self.get_or_create_tag(tn)
            if tid:
                tag_ids.append(tid)

        payload = {
            "title": title,
            "content": content,
            "excerpt": excerpt,
            "status": self.default_status,
            "lang": lang,
            "categories": [category_id] if category_id else [],
            "tags": tag_ids
        }
        if featured_media_id:
            payload["featured_media"] = featured_media_id
        if post_date_iso:
            payload["date"] = post_date_iso

        endpoint = f"{self.base_url}/wp-json/wp/v2/posts"
        logger.info(f"Menerbitkan artikel ({lang.upper()}): '{title}'...")
        try:
            r = requests.post(endpoint, headers=self.headers, json=payload, timeout=30)
            if r.status_code in (200, 201):
                res = r.json()
                post_id = res.get("id")
                link = res.get("link")
                logger.info(f"Artikel ({lang.upper()}) berhasil terbit! ID: {post_id} | Link: {link}")
                return {"success": True, "id": post_id, "link": link, "lang": lang}
            else:
                logger.error(f"Gagal terbit artikel ({lang.upper()}): HTTP {r.status_code} - {r.text[:250]}")
                return {"success": False, "error": r.text, "lang": lang}
        except Exception as e:
            logger.error(f"Kesalahan koneksi saat memposting artikel: {e}")
            return {"success": False, "error": str(e), "lang": lang}

    def cleanup_queue_and_archive(self, post_id: str, published_info: Dict[str, Any]):
        """
        Menghapus postingan dari pending_posts.json dan mencatatnya ke history_published.json.
        """
        # 1. Hapus dari pending_posts.json
        if self.pending_file.exists():
            try:
                with open(self.pending_file, "r", encoding="utf-8") as f:
                    pending_posts = json.load(f)
                updated_pending = [p for p in pending_posts if p.get("post_id") != post_id]
                with open(self.pending_file, "w", encoding="utf-8") as f:
                    json.dump(updated_pending, f, ensure_ascii=False, indent=2)
                logger.info(f"Post [{post_id}] berhasil dihapus dari antrean pending ({self.pending_file}).")
            except Exception as e:
                logger.error(f"Gagal membersihkan antrean pending: {e}")

        # 2. Catat ke history_published.json
        history = []
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

        history.insert(0, published_info)
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            logger.info(f"Post [{post_id}] berhasil diarsipkan ke riwayat publikasi ({self.history_file}).")
        except Exception as e:
            logger.error(f"Gagal menyimpan ke history_published: {e}")

    def publish(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Eksekusi menyeluruh publikasi postingan Instagram yang telah disetujui:
        1. Cek duplikasi online
        2. Upload Featured Image
        3. Terbitkan artikel Bahasa Indonesia (Kategori Berita ID: 143)
        4. Terbitkan artikel English (Kategori news ID: 145)
        5. Bersihkan dari antrean dan catat ke riwayat
        """
        post_id = post_data.get("post_id")
        draft = post_data.get("draft")
        if not draft:
            return {"success": False, "message": "Postingan belum memiliki draf narasi."}

        title_id = draft.get("title_id", "")
        title_en = draft.get("title_en", "")
        content_id = draft.get("content_id", "")
        content_en = draft.get("content_en", "")
        excerpt_id = draft.get("excerpt_id", "")
        excerpt_en = draft.get("excerpt_en", "")
        tags = draft.get("tags", ["FH Undip", "Kampus Hukum Progresif"])
        local_img = post_data.get("local_image_path")
        post_date = post_data.get("published_at")

        logger.info(f"=== MEMULAI PUBLIKASI WORDPRESS POST [{post_id}] ===")

        # 1. Cek Duplikasi Online
        is_dup, dup_id, dup_link = self.check_duplicate(title_id)
        if is_dup:
            logger.warning(f"Postingan dengan judul '{title_id}' sudah ada di WordPress (ID: {dup_id}, Link: {dup_link}).")
            # Tetap bersihkan dari antrean agar tidak menumpuk
            self.cleanup_queue_and_archive(post_id, {
                "post_id": post_id,
                "status": "duplicate_skipped",
                "wp_id_post_id": dup_id,
                "wp_id_url": dup_link,
                "published_at": datetime.now(TIMEZONE_WIB).isoformat()
            })
            return {"success": True, "duplicate": True, "link": dup_link}

        # 2. Upload Gambar Unggulan
        featured_media_id = None
        media_url = None
        if local_img and Path(local_img).exists():
            featured_media_id, media_url = self.upload_featured_media(
                image_path=local_img,
                alt_text=f"Dokumentasi {title_id} - FH Undip",
                title=title_id
            )

        # 3. Terbitkan Artikel Bahasa Indonesia
        res_id = self.post_article(
            title=title_id,
            content=content_id,
            excerpt=excerpt_id,
            category_id=self.cat_id_id,
            lang="id",
            tag_names=tags,
            featured_media_id=featured_media_id,
            post_date_iso=post_date
        )

        # 4. Terbitkan Artikel English
        res_en = self.post_article(
            title=title_en,
            content=content_en,
            excerpt=excerpt_en,
            category_id=self.cat_id_en,
            lang="en",
            tag_names=tags,
            featured_media_id=featured_media_id,
            post_date_iso=post_date
        )

        is_success = res_id.get("success") or res_en.get("success")
        published_record = {
            "post_id": post_id,
            "target_username": post_data.get("target_username", "law.undip"),
            "published_at": datetime.now(TIMEZONE_WIB).isoformat(),
            "source_published_at": post_date,
            "current_iteration": post_data.get("current_iteration", 1),
            "featured_media_id": featured_media_id,
            "featured_media_url": media_url,
            "wp_id_post_id": res_id.get("id"),
            "wp_id_url": res_id.get("link"),
            "wp_en_post_id": res_en.get("id"),
            "wp_en_url": res_en.get("link")
        }

        if is_success:
            # 5. Pembersihan Antrean Otomatis
            self.cleanup_queue_and_archive(post_id, published_record)

        return {
            "success": is_success,
            "id_post": res_id,
            "en_post": res_en,
            "record": published_record
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WordPress REST API Publisher")
    parser.add_argument("--post-id", help="Publikasikan postingan tertentu dari pending_posts.json")
    parser.add_argument("--check-auth", action="store_true", help="Uji koneksi dan otentikasi WP REST API")
    args = parser.parse_args()

    publisher = WordPressPublisher()

    if args.check_auth:
        ok = publisher.check_connection()
        print(f"Status Koneksi WP: {'OK (Terhubung)' if ok else 'GAGAL'}")
        exit(0 if ok else 1)

    if not settings.PENDING_POSTS_FILE.exists():
        print(f"File antrean {settings.PENDING_POSTS_FILE} tidak ditemukan.")
        exit(0)

    with open(settings.PENDING_POSTS_FILE, "r", encoding="utf-8") as f:
        posts = json.load(f)

    if not posts:
        print("Tidak ada postingan di antrean pending.")
        exit(0)

    target = posts[0]
    if args.post_id:
        for p in posts:
            if p.get("post_id") == args.post_id:
                target = p
                break

    print(f"Mempublikasikan postingan [{target.get('post_id')}]...")
    result = publisher.publish(target)
    print("\nHasil Publikasi:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
