"""
src/feedback_server.py
Gateway server lokal penerima callback umpan balik kurator (Persetujuan / Perbaikan Narasi).
Mendukung verifikasi token HMAC SHA-256, form input revisi interaktif, regenerasi narasi AI (Fase 2),
dan pengiriman ulang email konfirmasi revisi ke danda@staff.undip.ac.id.
"""

import os
import json
import logging
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, Optional

from config import settings
from src.mailer import verify_feedback_token, CuratorMailer
from src.narrator import BilingualNarrator
from src.wp_publisher import WordPressPublisher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("FeedbackServer")

def get_pending_post(post_id: str) -> Optional[Dict[str, Any]]:
    """Mencari data postingan dari file data/pending_posts.json."""
    if not settings.PENDING_POSTS_FILE.exists():
        return None
    try:
        with open(settings.PENDING_POSTS_FILE, "r", encoding="utf-8") as f:
            posts = json.load(f)
            for p in posts:
                if p.get("post_id") == post_id:
                    return p
    except Exception as e:
        logger.error(f"Gagal membaca pending_posts.json: {e}")
    return None

def update_post_status(post_id: str, new_status: str) -> bool:
    """Memperbarui status postingan di data/pending_posts.json."""
    if not settings.PENDING_POSTS_FILE.exists():
        return False
    try:
        with open(settings.PENDING_POSTS_FILE, "r", encoding="utf-8") as f:
            posts = json.load(f)
        found = False
        for p in posts:
            if p.get("post_id") == post_id:
                p["status"] = new_status
                found = True
                break
        if found:
            with open(settings.PENDING_POSTS_FILE, "w", encoding="utf-8") as f:
                json.dump(posts, f, ensure_ascii=False, indent=2)
            return True
    except Exception as e:
        logger.error(f"Gagal update status post: {e}")
    return False

def render_html_page(title: str, content: str) -> str:
    """Template pembungkus halaman respons feedback dengan estetika resmi FH Undip."""
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Redaksi FH Undip</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #F8FAFC; color: #1E293B; margin: 0; padding: 20px; }}
  .box {{ max-width: 640px; margin: 30px auto; background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); overflow: hidden; }}
  .top-banner {{ background-color: #0B2545; color: #FFFFFF; padding: 20px 28px; }}
  .top-banner h1 {{ margin: 0; font-size: 18px; text-transform: uppercase; letter-spacing: 0.5px; }}
  .top-banner p {{ margin: 4px 0 0; font-size: 12.5px; color: #94A3B8; }}
  .inner {{ padding: 28px; }}
  .btn {{ display: inline-block; font-size: 14px; font-weight: 700; text-decoration: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; border: none; }}
  .btn-green {{ background-color: #059669; color: #FFFFFF; }}
  .btn-blue {{ background-color: #134074; color: #FFFFFF; }}
  .btn-outline {{ background-color: #FFFFFF; color: #475569; border: 1px solid #CBD5E1; }}
  textarea {{ width: 100%; box-sizing: border-box; border-radius: 8px; border: 1px solid #CBD5E1; padding: 12px; font-family: inherit; font-size: 14px; min-height: 120px; resize: vertical; }}
  textarea:focus {{ outline: none; border-color: #0B2545; box-shadow: 0 0 0 3px rgba(11,37,69,0.1); }}
</style>
</head>
<body>
<div class="box">
  <div class="top-banner">
    <h1>Portal Redaksi Berita FH Undip</h1>
    <p>Sistem Kurasi Media Sosial &rarr; ilmuhukum.undip.ac.id</p>
  </div>
  <div class="inner">
    {content}
  </div>
</div>
</body>
</html>"""

class FeedbackHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.do_GET()

    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "app": "FH Undip Feedback Gateway"}).encode())
            return

        if path == "/api/feedback":
            action = params.get("action", [""])[0]
            post_id = params.get("id", [""])[0]
            token = params.get("token", [""])[0]

            if not post_id or not token or not verify_feedback_token(post_id, token):
                self.send_response(403)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                content = """
                <div style="text-align:center;padding:20px 0;">
                  <h2 style="color:#DC2626;">Akses Ditolak (Token Tidak Valid)</h2>
                  <p style="color:#64748B;">Tautan umpan balik ini tidak valid atau telah kedaluwarsa demi keamanan sistem.</p>
                </div>
                """
                self.wfile.write(render_html_page("Akses Ditolak", content).encode())
                return

            post = get_pending_post(post_id)
            if not post:
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                content = f"""
                <div style="text-align:center;padding:20px 0;">
                  <h2 style="color:#DC2626;">Postingan Tidak Ditemukan</h2>
                  <p style="color:#64748B;">Data postingan ID <strong>[{post_id}]</strong> sudah tidak berada di antrean pending.</p>
                </div>
                """
                self.wfile.write(render_html_page("Post Tidak Ditemukan", content).encode())
                return

            draft = post.get("draft") or {}

            # [A] ACTION: APPROVE
            if action == "approve":
                update_post_status(post_id, "approved")
                
                # Memicu publikasi langsung ke WordPress REST API ilmuhukum.undip.ac.id
                logger.info(f"Persetujuan diterima untuk post [{post_id}], memulai publikasi WordPress...")
                publisher = WordPressPublisher()
                pub_result = publisher.publish(post)

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()

                if pub_result.get("success"):
                    link_id = pub_result.get("id_post", {}).get("link", "#")
                    link_en = pub_result.get("en_post", {}).get("link", "#")
                    content = f"""
                    <div style="text-align:center;padding:10px 0 20px;">
                      <div style="font-size:48px;color:#059669;margin-bottom:10px;">&check;</div>
                      <h2 style="color:#059669;margin:0 0 10px;">Berita Berhasil Diterbitkan!</h2>
                      <p style="color:#475569;font-size:14px;line-height:1.6;">
                        Draf berita dwibahasa untuk postingan Instagram <strong>[{post_id}]</strong> 
                        telah resmi dipublikasikan ke portal <strong>ilmuhukum.undip.ac.id</strong> 
                        dan antrean pending telah dibersihkan.
                      </p>
                    </div>
                    <div style="background-color:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:16px;margin:16px 0;text-align:left;">
                      <div style="font-size:12px;font-weight:700;color:#64748B;text-transform:uppercase;">Tautan Artikel Terbit (Live):</div>
                      <div style="margin-top:8px;">
                        <a href="{link_id}" target="_blank" style="color:#0B2545;font-weight:700;text-decoration:none;display:block;margin-bottom:6px;">
                          &#127470;&#127465; Versi Bahasa Indonesia: {draft.get('title_id')} &rarr;
                        </a>
                        <a href="{link_en}" target="_blank" style="color:#134074;font-style:italic;text-decoration:none;display:block;">
                          &#127468;&#127463; English Version: {draft.get('title_en')} &rarr;
                        </a>
                      </div>
                    </div>
                    <div style="text-align:center;margin-top:20px;">
                      <a href="{link_id}" target="_blank" class="btn btn-green">Buka Berita di Web &rarr;</a>
                    </div>
                    """
                else:
                    err_msg = pub_result.get("message", "Gagal menghubungi WordPress REST API")
                    content = f"""
                    <div style="text-align:center;padding:10px 0 20px;">
                      <div style="font-size:48px;color:#DC2626;margin-bottom:10px;">&cross;</div>
                      <h2 style="color:#DC2626;margin:0 0 10px;">Publikasi Mengalami Kendala</h2>
                      <p style="color:#475569;font-size:14px;line-height:1.6;">
                        Persetujuan dicatat, namun terjadi kendala saat pengiriman ke WordPress: {err_msg}
                      </p>
                    </div>
                    """
                self.wfile.write(render_html_page("Status Publikasi", content).encode())
                return

            # [B] ACTION: REVISE (FORM INPUT CATATAN)
            elif action == "revise":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                content = f"""
                <h2 style="color:#0B2545;margin:0 0 8px;">Permintaan Perbaikan Narasi</h2>
                <p style="font-size:13.5px;color:#64748B;margin-bottom:20px;">
                  Masukkan instruksi atau poin perbaikan di bawah ini. AI Multimodal akan meregenerasi narasi berita dwibahasa baru dan mengirimkan konfirmasinya kembali ke email Anda.
                </p>
                <div style="background-color:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:14px;margin-bottom:20px;font-size:13px;">
                  <strong>Draf Saat Ini (Iterasi #{post.get('current_iteration', 1)}):</strong><br>
                  <span style="font-weight:600;color:#0B2545;">{draft.get('title_id')}</span>
                </div>
                <form action="/api/feedback/submit_revision" method="POST">
                  <input type="hidden" name="post_id" value="{post_id}">
                  <input type="hidden" name="token" value="{token}">
                  <label style="font-size:13px;font-weight:700;color:#334155;display:block;margin-bottom:8px;">
                    Catatan / Arahan Perbaikan Narasi:
                  </label>
                  <textarea name="revision_notes" required placeholder="Contoh: Tolong sebutkan nama Dekan FH Undip, tambahkan penekanan pada aspek solidaritas mahasiswa angkatan 2023, dan buat kalimat penutup lebih khidmat..."></textarea>
                  <div style="margin-top:20px;text-align:right;">
                    <button type="submit" class="btn btn-blue">&#9998; Regenerasi Narasi &amp; Kirim Email Baru</button>
                  </div>
                </form>
                """
                self.wfile.write(render_html_page("Minta Perbaikan Narasi", content).encode())
                return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/feedback/submit_revision":
            content_length = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_length).decode("utf-8")
            params = urllib.parse.parse_qs(post_body)

            post_id = params.get("post_id", [""])[0]
            token = params.get("token", [""])[0]
            revision_notes = params.get("revision_notes", [""])[0].strip()

            if not post_id or not token or not verify_feedback_token(post_id, token):
                self.send_response(403)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(render_html_page("Akses Ditolak", "<p>Token autentikasi tidak valid.</p>").encode())
                return

            logger.info(f"Menerima instruksi revisi untuk post [{post_id}]: {revision_notes}")

            # 1. Jalankan regenerasi narasi AI
            narrator = BilingualNarrator()
            new_draft = narrator.revise_post(post_id, feedback_notes=revision_notes)

            if not new_draft:
                self.send_response(500)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(render_html_page("Gagal Memproses", "<p>Terjadi kendala saat regenerasi narasi oleh AI.</p>").encode())
                return

            # 2. Ambil data post yang sudah diperbarui
            updated_post = get_pending_post(post_id)

            # 3. Kirimkan email kurasi baru
            mailer = CuratorMailer()
            mailer.send_review_email(updated_post)

            approve_url, revise_url = mailer.build_feedback_urls(post_id)

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            content = f"""
            <div style="text-align:center;padding:10px 0 16px;">
              <div style="font-size:44px;color:#059669;margin-bottom:8px;">&check;</div>
              <h2 style="color:#059669;margin:0 0 10px;">Perbaikan Narasi Selesai!</h2>
              <p style="color:#475569;font-size:14px;line-height:1.6;">
                AI telah meregenerasi draf berita dwibahasa baru <strong>(Iterasi #{updated_post.get('current_iteration')})</strong> 
                berdasarkan catatan revisi Anda. Email konfirmasi baru telah dikirimkan ke <strong>{settings.CURATOR_EMAIL}</strong>.
              </p>
            </div>
            <div style="background-color:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:16px;margin:16px 0;text-align:left;">
              <div style="font-size:12px;font-weight:700;color:#64748B;">JUDUL BARU (INDONESIA):</div>
              <div style="font-size:15px;font-weight:700;color:#0B2545;margin:4px 0 12px;">{new_draft.get('title_id')}</div>
              <div style="font-size:12px;font-weight:700;color:#64748B;">NEW TITLE (ENGLISH):</div>
              <div style="font-size:14px;font-style:italic;color:#334155;margin-top:4px;">{new_draft.get('title_en')}</div>
            </div>
            <div style="text-align:center;margin-top:24px;">
              <a href="{approve_url}" class="btn btn-green" style="margin-right:8px;">&check; SETUJUI VERSI INI SEKARANG</a>
              <a href="{revise_url}" class="btn btn-outline">&#9998; Perbaiki Lagi</a>
            </div>
            """
            self.wfile.write(render_html_page("Revisi Sukses", content).encode())
            return

        self.send_response(404)
        self.end_headers()

def run_server(port: int = settings.APP_PORT):
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, FeedbackHandler)
    logger.info(f"Feedback Webhook Server aktif dan berjalan di http://0.0.0.0:{port} (mendukung akses localhost)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Feedback Webhook Server dihentikan.")
        httpd.server_close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Curator Feedback Webhook Server")
    parser.add_argument("--port", type=int, default=settings.APP_PORT, help="Port server HTTP")
    args = parser.parse_args()
    run_server(args.port)
