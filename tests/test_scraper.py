"""
tests/test_scraper.py
Unit test untuk konfigurasi dan scraper Instagram dinamis.
"""

import unittest
from pathlib import Path
from config import settings
from src.scraper import InstagramScraper

class TestInstagramScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = InstagramScraper()

    def test_settings_loaded(self):
        """Memverifikasi bahwa konfigurasi dari settings terbaca dengan baik."""
        self.assertTrue(bool(settings.INSTAGRAM_TARGET_URL))
        self.assertTrue(bool(settings.INSTAGRAM_TARGET_USERNAME))
        self.assertTrue(Path(settings.DATA_DIR).exists())
        self.assertTrue(Path(settings.MEDIA_DIR).exists())

    def test_override_target(self):
        """Memverifikasi bahwa target dapat di-override secara dinamis."""
        custom_scraper = InstagramScraper(
            target_url="https://www.instagram.com/undip.official/",
            target_username="undip.official"
        )
        self.assertEqual(custom_scraper.target_username, "undip.official")
        self.assertEqual(custom_scraper.target_url, "https://www.instagram.com/undip.official/")

    def test_load_processed_ids(self):
        """Memverifikasi pemuatan ID yang sudah diproses."""
        processed = self.scraper.load_processed_ids()
        self.assertIsInstance(processed, set)

if __name__ == "__main__":
    unittest.main()
