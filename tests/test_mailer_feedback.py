"""
tests/test_mailer_feedback.py
Unit test untuk mailer kurasi dan verifikasi token feedback gateway.
"""

import unittest
from src.mailer import generate_feedback_token, verify_feedback_token, CuratorMailer

class TestMailerAndFeedback(unittest.TestCase):
    def setUp(self):
        self.mailer = CuratorMailer()
        self.post_id = "test_post_123"

    def test_token_generation_and_verification(self):
        """Memverifikasi keamanan HMAC SHA-256 token."""
        token = generate_feedback_token(self.post_id)
        self.assertTrue(bool(token))
        self.assertEqual(len(token), 64)  # SHA-256 hex length
        self.assertTrue(verify_feedback_token(self.post_id, token))
        self.assertFalse(verify_feedback_token("wrong_id", token))
        self.assertFalse(verify_feedback_token(self.post_id, "invalid_token"))

    def test_build_feedback_urls(self):
        """Memverifikasi pembuatan URL approve dan revise."""
        approve_url, revise_url = self.mailer.build_feedback_urls(self.post_id)
        self.assertIn("action=approve", approve_url)
        self.assertIn(f"id={self.post_id}", approve_url)
        self.assertIn("token=", approve_url)

        self.assertIn("action=revise", revise_url)
        self.assertIn(f"id={self.post_id}", revise_url)
        self.assertIn("token=", revise_url)

    def test_html_content_builder(self):
        """Memverifikasi penyusunan dokumen email HTML."""
        sample_post = {
            "post_id": self.post_id,
            "target_username": "law.undip",
            "post_url": "https://www.instagram.com/law.undip/p/test/",
            "published_at": "2026-10-05T08:00:00Z",
            "caption_raw": "Uji coba caption instagram",
            "current_iteration": 1,
            "draft": {
                "title_id": "Judul Berita Uji Coba",
                "title_en": "Test News Title",
                "lead_id": "Lead uji coba",
                "lead_en": "Test lead",
                "content_id": "<p>Isi uji coba</p>",
                "content_en": "<p>Test content</p>",
                "excerpt_id": "Excerpt uji coba",
                "excerpt_en": "Test excerpt",
                "categories": ["Berita"],
                "tags": ["FH Undip"]
            }
        }
        approve_url, revise_url = self.mailer.build_feedback_urls(self.post_id)
        html = self.mailer.build_html_content(sample_post, approve_url, revise_url)

        self.assertIn("Judul Berita Uji Coba", html)
        self.assertIn("Test News Title", html)
        self.assertIn(approve_url, html)
        self.assertIn(revise_url, html)

if __name__ == "__main__":
    unittest.main()
