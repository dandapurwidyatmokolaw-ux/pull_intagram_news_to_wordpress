"""
src/narrator.py
Modul generator narasi artikel berita jurnalistik dwibahasa (ID & EN) berbasis AI Multimodal.
Menggunakan gambar postingan dan teks caption Instagram untuk menghasilkan draf berita
berstandar 5W+1H sesuai pedoman redaksional WordPress Universitas Diponegoro.
"""

import os
import re
import json
import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests

from config import settings

# Konfigurasi Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("BilingualNarrator")

SYSTEM_PROMPT = """Anda adalah Redaktur Berita Jurnalistik Senior dan Content Strategist resmi untuk Fakultas Hukum Universitas Diponegoro (FH Undip).
Tugas Anda adalah memproduksi artikel berita jurnalistik formal berstandar tinggi dalam FORMAT DWIBAHASA (Bahasa Indonesia dan English) berdasarkan materi publikasi Instagram (gambar visual dan caption asli).

Pedoman Penulisan Berita (Mengacu pada Standar Portal Akademik ilmuhukum.undip.ac.id):
1. JUDUL (Headline):
   - Informatif, bermartabat, menarik, dan mencerminkan esensi peristiwa/informasi.
   - Panjang optimal: 50-70 karakter.
   - Mengandung identitas institusi (FH Undip / Fakultas Hukum Universitas Diponegoro).
2. LEAD PARAGRAPH (Paragraf Pembuka):
   - Wajib memenuhi kaidah 5W+1H (Who, What, When, Where, Why, How) dalam 100 kata pertama.
   - Contoh pembuka: "Semarang — Fakultas Hukum Universitas Diponegoro (FH Undip)..."
3. BATANG TUBUH (Body Content):
   - Terdiri dari 3-4 paragraf yang mengalir rapi dengan gaya bahasa jurnalistik formal, elegan, dan mendalam.
   - Jelaskan konteks peristiwa, relevansi akademis, nilai kemanusiaan/prestasi, serta doa atau harapan yang sesuai.
   - Format isi dalam tag HTML sederhana seperti <p>...</p>. JANGAN gunakan tag <h1> atau <body> di dalam content.
4. KUTIPAN & EXCERPT:
   - Ringkasan 1-2 kalimat (maksimal 150 karakter) untuk cuplikan pengantar / meta description.
5. KATEGORI & TAG SEO:
   - Tentukan minimal 1-2 kategori relevan (contoh: Berita, Duka Cita, Akademik, Prestasi, Kerjasama Internasional).
   - Tentukan 3-5 tag spesifik (contoh: FH Undip, Mahasiswa, Kampus Hukum Progresif, Undip).

FORMAT OUTPUT:
Anda WAJIB menjawab HANYA dalam format JSON murni tanpa pembuka atau penutup markdown (```json ... ```) dengan skema berikut:
{
  "title_id": "Judul Berita Bahasa Indonesia",
  "title_en": "News Title in English",
  "lead_id": "Paragraf pembuka 5W+1H Bahasa Indonesia",
  "lead_en": "Opening 5W+1H paragraph in English",
  "content_id": "<p>Paragraf 1...</p><p>Paragraf 2...</p><p>Paragraf 3...</p>",
  "content_en": "<p>Paragraph 1...</p><p>Paragraph 2...</p><p>Paragraph 3...</p>",
  "excerpt_id": "Ringkasan cuplikan maksimal 150 karakter dalam Bahasa Indonesia",
  "excerpt_en": "Summary excerpt maximum 150 characters in English",
  "categories": ["Berita"],
  "tags": ["FH Undip", "Mahasiswa", "Kampus Hukum Progresif"]
}
"""

class BilingualNarrator:
    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_base = (api_base or settings.AI_API_BASE).rstrip("/")
        self.api_key = api_key or settings.AI_API_KEY
        self.model = model or settings.AI_MODEL
        self.pending_file = settings.PENDING_POSTS_FILE

    def _encode_image(self, image_path: str) -> Optional[str]:
        """Mengonversi file gambar lokal ke format base64 data URI."""
        path = Path(image_path)
        if not path.exists() or path.stat().st_size == 0:
            return None
        try:
            with open(path, "rb") as f:
                data = f.read()
            mime_type = "image/jpeg"
            if path.suffix.lower() == ".png":
                mime_type = "image/png"
            elif path.suffix.lower() == ".webp":
                mime_type = "image/webp"
            b64_str = base64.b64encode(data).decode("utf-8")
            return f"data:{mime_type};base64,{b64_str}"
        except Exception as e:
            logger.warning(f"Gagal membaca gambar {image_path}: {e}")
            return None

    def generate_narrative(
        self,
        post_data: Dict[str, Any],
        feedback_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Menghasilkan draf berita dwibahasa (ID & EN) berdasarkan postingan Instagram.
        Jika feedback_notes disertakan, draf dibuat sebagai versi perbaikan (revisi).
        """
        post_id = post_data.get("post_id", "Unknown")
        caption_raw = post_data.get("caption_raw", "")
        alt_desc = post_data.get("alt_description", "")
        published_at = post_data.get("published_at", "")
        post_url = post_data.get("post_url", "")
        local_img = post_data.get("local_image_path")

        logger.info(f"Memproses narasi untuk post [{post_id}] menggunakan model {self.model}...")

        # Bangun konten pesan user
        user_content: List[Dict[str, Any]] = []

        prompt_text = f"""Silakan susun draf artikel berita dwibahasa (Indonesia & English) dari data postingan Instagram berikut:
- Akun Asal: @{post_data.get('target_username', 'law.undip')} (Fakultas Hukum Universitas Diponegoro)
- Tanggal Publikasi: {published_at}
- URL Post: {post_url}
- Teks Caption Asli Instagram:
\"\"\"{caption_raw}\"\"\"
- Deskripsi Visual Gambar (Alt Text): {alt_desc}
"""

        if feedback_notes:
            previous_draft = post_data.get("draft") or {}
            prompt_text += f"""
CATATAN PERBAIKAN / REVISI DARI KURATOR (PENTING):
Kurator telah meninjau draf sebelumnya dan meminta perubahan berikut:
\"{feedback_notes}\"

Draf Sebelumnya Sebagai Referensi:
- Judul ID Lama: {previous_draft.get('title_id', '')}
- Konten ID Lama: {previous_draft.get('content_id', '')}

Harap lakukan perbaikan dan regenerasi narasi baru secara menyeluruh sesuai instruksi kurator di atas, sambil tetap mematuhi kaidah jurnalistik dwibahasa 5W+1H.
"""

        user_content.append({"type": "text", "text": prompt_text})

        # Sertakan gambar ke prompt multimodal jika tersedia
        if local_img:
            img_b64 = self._encode_image(local_img)
            if img_b64:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": img_b64}
                })
                logger.info(f"Menyertakan gambar lokal {local_img} ke request multimodal AI.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            "stream": False,
            "temperature": 0.3
        }

        endpoint = f"{self.api_base}/chat/completions"
        try:
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            if resp.status_code != 200:
                logger.error(f"AI API HTTP {resp.status_code}: {resp.text[:300]}")
                raise RuntimeError(f"Gagal memanggil AI API: HTTP {resp.status_code}")

            res_json = resp.json()
            raw_answer = res_json["choices"][0]["message"]["content"].strip()

            # Bersihkan markdown formatting jika ada (```json ... ```)
            cleaned = raw_answer
            if "```" in cleaned:
                cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
                cleaned = re.sub(r"\n```$", "", cleaned)
                cleaned = cleaned.strip()

            parsed_draft = json.loads(cleaned)
            logger.info(f"Sukses menghasilkan draf dwibahasa untuk post [{post_id}].")
            return parsed_draft

        except json.JSONDecodeError as je:
            logger.error(f"Gagal mem-parsing output JSON dari AI: {je}\nRaw content:\n{raw_answer[:400]}")
            # Fallback parsing regex jika LLM memberikan teks di luar JSON
            m_json = re.search(r"\{.*\}", raw_answer, re.DOTALL)
            if m_json:
                return json.loads(m_json.group(0))
            raise

    def process_pending_posts(self, force_all: bool = False) -> int:
        """
        Memproses seluruh postingan di pending_posts.json yang belum memiliki draf.
        Menyimpan hasil draf dan menaikkan nomor iterasi.
        """
        if not self.pending_file.exists():
            logger.info(f"File antrean {self.pending_file} tidak ditemukan.")
            return 0

        with open(self.pending_file, "r", encoding="utf-8") as f:
            pending_posts = json.load(f)

        processed_count = 0
        for item in pending_posts:
            if not isinstance(item, dict):
                continue

            # Jika belum ada draf atau force_all=True
            if item.get("draft") is None or force_all:
                post_id = item.get("post_id")
                try:
                    draft = self.generate_narrative(item)
                    item["draft"] = draft
                    item["current_iteration"] = item.get("current_iteration", 0) + 1
                    item["status"] = "pending_approval"
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Error memproses post [{post_id}]: {e}")

        if processed_count > 0:
            with open(self.pending_file, "w", encoding="utf-8") as f:
                json.dump(pending_posts, f, ensure_ascii=False, indent=2)
            logger.info(f"Berhasil memperbarui {processed_count} postingan di {self.pending_file}.")

        return processed_count

    def revise_post(self, post_id: str, feedback_notes: str) -> Optional[Dict[str, Any]]:
        """
        Menjalankan alur revisi untuk satu postingan tertentu berdasarkan catatan kurator.
        """
        if not self.pending_file.exists():
            logger.error(f"File antrean {self.pending_file} tidak ditemukan.")
            return None

        with open(self.pending_file, "r", encoding="utf-8") as f:
            pending_posts = json.load(f)

        target_post = None
        for item in pending_posts:
            if item.get("post_id") == post_id:
                target_post = item
                break

        if not target_post:
            logger.error(f"Post ID [{post_id}] tidak ditemukan di antrean pending.")
            return None

        old_draft = target_post.get("draft")
        current_iter = target_post.get("current_iteration", 1)

        # Rekam ke riwayat revisi
        if old_draft:
            if "revision_history" not in target_post:
                target_post["revision_history"] = []
            target_post["revision_history"].append({
                "iteration": current_iter,
                "notes": feedback_notes,
                "previous_draft": old_draft
            })

        # Generate draf baru
        new_draft = self.generate_narrative(target_post, feedback_notes=feedback_notes)
        target_post["draft"] = new_draft
        target_post["current_iteration"] = current_iter + 1
        target_post["status"] = "pending_approval"

        with open(self.pending_file, "w", encoding="utf-8") as f:
            json.dump(pending_posts, f, ensure_ascii=False, indent=2)

        logger.info(f"Revisi post [{post_id}] iterasi ke-{target_post['current_iteration']} berhasil disimpan.")
        return new_draft

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI Bilingual News Narrator")
    parser.add_argument("--post-id", help="Proses hanya post ID tertentu")
    parser.add_argument("--revise", help="Catatan revisi untuk post ID")
    parser.add_argument("--force", action="store_true", help="Paksa regenerasi draf yang sudah ada")
    args = parser.parse_args()

    narrator = BilingualNarrator()

    if args.post_id and args.revise:
        print(f"Menjalankan revisi untuk Post ID [{args.post_id}]...")
        result = narrator.revise_post(args.post_id, args.revise)
        if result:
            print("\nHASIL REVISI BARU:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Menjalankan pemrosesan draf antrean pending...")
        count = narrator.process_pending_posts(force_all=args.force)
        print(f"\nSelesai: {count} draf berita dwibahasa berhasil dibuat.")
