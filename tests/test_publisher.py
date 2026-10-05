"""
tests/test_publisher.py
Unit test untuk modul WordPress Publisher dan antrean publikasi.
"""

import unittest
from config import settings
from src.wp_publisher import WordPressPublisher

class TestWordPressPublisher(unittest.TestCase):
    def setUp(self):
        self.publisher = WordPressPublisher()

    def test_init_config(self):
        """Memverifikasi konfigurasi URL dan kredensial WP."""
        self.assertTrue(bool(self.publisher.base_url))
        self.assertTrue(bool(self.publisher.username))
        self.assertTrue(bool(self.publisher.app_password))
        self.assertEqual(self.publisher.cat_id_id, 143)
        self.assertEqual(self.publisher.cat_id_en, 145)

    def test_auth_headers(self):
        """Memverifikasi pembuatan Authorization header."""
        self.assertIn("Authorization", self.publisher.headers)
        self.assertTrue(self.publisher.headers["Authorization"].startswith("Basic "))

    def test_connection_live(self):
        """Memverifikasi koneksi live REST API ke portal ilmuhukum.undip.ac.id."""
        is_connected = self.publisher.check_connection()
        self.assertTrue(is_connected, "WP REST API ilmuhukum.undip.ac.id harus berhasil diautentikasi.")

if __name__ == "__main__":
    unittest.main()
