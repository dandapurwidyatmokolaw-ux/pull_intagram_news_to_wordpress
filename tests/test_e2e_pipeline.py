"""
tests/test_e2e_pipeline.py
Unit test integrasi end-to-end untuk seluruh alur kerja sistem.
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from config import settings
from src.scraper import InstagramScraper
from src.narrator import BilingualNarrator
from src.mailer import CuratorMailer, generate_feedback_token, verify_feedback_token
from src.wp_publisher import WordPressPublisher

class TestEndToEndPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.pending_file = Path(self.test_dir) / "pending_posts.json"
        self.history_file = Path(self.test_dir) / "history_published.json"
        self.media_dir = Path(self.test_dir) / "media"
        self.media_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_complete_queue_lifecycle(self):
        """Memverifikasi siklus hidup postingan dari antrean pending hingga pembersihan."""
        post_id = "TEST_E2E_001"
        sample_post = {
            "post_id": post_id,
            "target_username": "law.undip",
            "post_url": f"https://www.instagram.com/law.undip/p/{post_id}/",
            "published_at": "2026-10-05T08:00:00+07:00",
            "media_type": "feed",
            "local_image_path": str(self.media_dir / f"{post_id}.jpg"),
            "caption_raw": "Dies Natalis Fakultas Hukum Undip",
            "alt_description": "Banner dies natalis",
            "status": "pending_review",
            "current_iteration": 0,
            "draft": None,
            "revision_history": []
        }

        # Simpan ke pending
        with open(self.pending_file, "w", encoding="utf-8") as f:
            json.dump([sample_post], f)

        # 1. Verifikasi pending tersimpan
        with open(self.pending_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["post_id"], post_id)

        # 2. Token feedback aman
        token = generate_feedback_token(post_id)
        self.assertTrue(verify_feedback_token(post_id, token))

        # 3. Simulasi penerbitan dan pembersihan antrean
        publisher = WordPressPublisher()
        publisher.pending_file = self.pending_file
        publisher.history_file = self.history_file

        published_info = {
            "post_id": post_id,
            "wp_id_post_id": 99999,
            "wp_id_url": "https://ilmuhukum.undip.ac.id/2026/10/05/test/",
            "published_at": "2026-10-05T10:00:00+07:00"
        }
        publisher.cleanup_queue_and_archive(post_id, published_info)

        # 4. Verifikasi antrean kosong
        with open(self.pending_file, "r", encoding="utf-8") as f:
            pending_after = json.load(f)
        self.assertEqual(len(pending_after), 0)

        # 5. Verifikasi tercatat di history
        with open(self.history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["post_id"], post_id)
        self.assertEqual(history[0]["wp_id_post_id"], 99999)

if __name__ == "__main__":
    unittest.main()
