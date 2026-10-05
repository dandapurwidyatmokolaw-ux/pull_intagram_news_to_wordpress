"""
tests/test_narrator.py
Unit test untuk generator narasi berita dwibahasa AI Multimodal.
"""

import unittest
from pathlib import Path
from config import settings
from src.narrator import BilingualNarrator

class TestBilingualNarrator(unittest.TestCase):
    def setUp(self):
        self.narrator = BilingualNarrator()

    def test_init_settings(self):
        """Memverifikasi inisialisasi AI model dan endpoint."""
        self.assertTrue(bool(self.narrator.api_base))
        self.assertTrue(bool(self.narrator.api_key))
        self.assertTrue(bool(self.narrator.model))

    def test_encode_image(self):
        """Memverifikasi encoding gambar lokal ke base64 URI."""
        img_path = Path(settings.MEDIA_DIR) / "DeF_pD9JEiX.jpg"
        if img_path.exists():
            encoded = self.narrator._encode_image(str(img_path))
            self.assertIsNotNone(encoded)
            self.assertTrue(encoded.startswith("data:image/jpeg;base64,"))

if __name__ == "__main__":
    unittest.main()
