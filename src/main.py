"""
src/main.py
Orkestrator utama pipeline penarikan konten Instagram, pembuatan narasi berita dwibahasa,
pengiriman email kurasi, serta otomasi publikasi ke portal resmi ilmuhukum.undip.ac.id.
Dapat dijalankan secara mandiri atau dijadwalkan via Cron / Task Scheduler.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

from config import settings
from src.scraper import InstagramScraper
from src.narrator import BilingualNarrator
from src.mailer import CuratorMailer
from src.wp_publisher import WordPressPublisher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("MainPipeline")

def run_pipeline(
    today_only: bool = True,
    force_scrape: bool = False,
    auto_approve: bool = False,
    target_url: str = None
):
    logger.info("==================================================================")
    logger.info("MEMULAI PIPELINE OTOMASI INSTAGRAM KE BERITA ILMUHUKUM.UNDIP.AC.ID")
    logger.info("==================================================================")
    logger.info(f"Target Instagram: {target_url or settings.INSTAGRAM_TARGET_URL}")
    logger.info(f"Email Kurator   : {settings.CURATOR_EMAIL}")
    logger.info(f"Portal Target   : {settings.WP_BASE_URL}")
    logger.info(f"Filter Hari Ini : {today_only}")
    logger.info("------------------------------------------------------------------")

    # 1. TAHAP 1: PENARIKAN KONTEN & MEDIA INSTAGRAM
    logger.info("[LANGKAH 1] Menjalankan Scraper Instagram...")
    scraper = InstagramScraper(target_url=target_url)
    new_posts = scraper.scrape(today_only=today_only, force=force_scrape)
    logger.info(f"[LANGKAH 1 SELESAI] Diperoleh {len(new_posts)} postingan baru.")

    # 2. TAHAP 2: GENERASI NARASI BERITA DWIBAHASA (AI MULTIMODAL)
    logger.info("[LANGKAH 2] Menjalankan AI Bilingual Narrator...")
    narrator = BilingualNarrator()
    narrated_count = narrator.process_pending_posts(force_all=False)
    logger.info(f"[LANGKAH 2 SELESAI] Berhasil memproduksi {narrated_count} draf berita dwibahasa.")

    # 3. TAHAP 3: PENGIRIMAN EMAIL DRAF KURASI KE STAF
    if not settings.PENDING_POSTS_FILE.exists():
        logger.info("Tidak ada file antrean pending. Pipeline selesai.")
        return

    with open(settings.PENDING_POSTS_FILE, "r", encoding="utf-8") as f:
        pending_posts = json.load(f)

    if not pending_posts:
        logger.info("Antrean pending_posts.json kosong. Semua postingan telah terbit.")
        return

    mailer = CuratorMailer()
    publisher = WordPressPublisher()

    for post in pending_posts:
        post_id = post.get("post_id")
        status = post.get("status")

        if auto_approve or status == "approved":
            # 4. TAHAP 4: PUBLIKASI KE WORDPRESS (JIKA AUTO-APPROVE ATAU SUDAH APPROVED)
            logger.info(f"[LANGKAH 4] Mempublikasikan post [{post_id}] ke WordPress REST API...")
            pub_result = publisher.publish(post)
            if pub_result.get("success"):
                logger.info(f"[SUKSES PUBLIKASI] Post [{post_id}] terbit di ilmuhukum.undip.ac.id!")
                logger.info(f"- Link ID: {pub_result.get('id_post', {}).get('link')}")
                logger.info(f"- Link EN: {pub_result.get('en_post', {}).get('link')}")
            else:
                logger.error(f"[GAGAL PUBLIKASI] Post [{post_id}]: {pub_result.get('message')}")
        else:
            # Kirim email review ke kurator
            logger.info(f"[LANGKAH 3] Mengirimkan draf email kurasi untuk post [{post_id}]...")
            mailer.send_review_email(post)

    logger.info("==================================================================")
    logger.info("PIPELINE HARIAN SELESAI DIJALANKAN DENGAN SUKSES.")
    logger.info("==================================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instagram to WP Daily Automation Pipeline")
    parser.add_argument("--all", action="store_true", help="Nonaktifkan filter hari ini (ambil semua postingan)")
    parser.add_argument("--force", action="store_true", help="Paksa scrape ulang")
    parser.add_argument("--auto-approve", action="store_true", help="Langsung publikasikan ke web tanpa menunggu klik kurator")
    parser.add_argument("--url", help="Target Instagram URL override")
    args = parser.parse_args()

    run_pipeline(
        today_only=not args.all,
        force_scrape=args.force,
        auto_approve=args.auto_approve,
        target_url=args.url
    )
