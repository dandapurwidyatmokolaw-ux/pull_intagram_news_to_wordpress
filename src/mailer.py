"""
src/mailer.py
Modul pengirim email notifikasi draf kurasi berita Instagram ke staf redaksi (danda@staff.undip.ac.id).
Menyediakan antarmuka interaktif dalam format HTML dengan tombol [Setujui & Publikasikan] dan [Minta Perbaikan Narasi].
"""

import os
import hmac
import hashlib
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path
from typing import Dict, Any, Optional

from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("CuratorMailer")

def generate_feedback_token(post_id: str) -> str:
    """Membuat token HMAC SHA-256 aman untuk verifikasi callback feedback."""
    secret = settings.FEEDBACK_SECRET_KEY.encode("utf-8")
    return hmac.new(secret, post_id.encode("utf-8"), hashlib.sha256).hexdigest()

def verify_feedback_token(post_id: str, token: str) -> bool:
    """Memverifikasi kecocokan token HMAC."""
    expected = generate_feedback_token(post_id)
    return hmac.compare_digest(expected, token)

class CuratorMailer:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_name = settings.SMTP_FROM_NAME
        self.curator_email = settings.CURATOR_EMAIL
        self.base_url = settings.APP_BASE_URL
        self.previews_dir = settings.DATA_DIR / "email_previews"
        self.previews_dir.mkdir(parents=True, exist_ok=True)

    def build_feedback_urls(self, post_id: str) -> tuple[str, str]:
        """Menghasilkan URL approval dan revision callback."""
        token = generate_feedback_token(post_id)
        approve_url = f"{self.base_url}/api/feedback?action=approve&id={post_id}&token={token}"
        revise_url = f"{self.base_url}/api/feedback?action=revise&id={post_id}&token={token}"
        return approve_url, revise_url

    def build_html_content(self, post: Dict[str, Any], approve_url: str, revise_url: str) -> str:
        """Menyusun dokumen email responsif berdesain modern elegan untuk kurasi berita FH Undip."""
        post_id = post.get("post_id", "")
        published_at = post.get("published_at", "")
        post_url = post.get("post_url", "")
        caption_raw = post.get("caption_raw", "")
        current_iter = post.get("current_iteration", 1)
        draft = post.get("draft") or {}

        title_id = draft.get("title_id", "Draf Berita Tanpa Judul")
        title_en = draft.get("title_en", "Untitled News Draft")
        lead_id = draft.get("lead_id", "")
        lead_en = draft.get("lead_en", "")
        content_id = draft.get("content_id", "")
        content_en = draft.get("content_en", "")
        excerpt_id = draft.get("excerpt_id", "")
        excerpt_en = draft.get("excerpt_en", "")
        categories = draft.get("categories", ["Berita"])
        tags = draft.get("tags", ["FH Undip", "Undip"])

        cat_badges = "".join([f'<span style="background-color:#EBF3FB;color:#0B2545;padding:4px 10px;border-radius:12px;font-size:12px;font-weight:600;margin-right:6px;">{c}</span>' for c in categories])
        tag_badges = "".join([f'<span style="background-color:#F1F5F9;color:#475569;padding:4px 10px;border-radius:12px;font-size:12px;margin-right:6px;">#{t}</span>' for t in tags])

        iter_label = f"DRAF AWAL (Iterasi #1)" if current_iter <= 1 else f"REVISI (Iterasi #{current_iter})"
        iter_badge_color = "#10B981" if current_iter <= 1 else "#F59E0B"

        html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kurasi Berita Instagram FH Undip</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 0; background-color: #F8FAFC; color: #1E293B; }}
  .container {{ max-width: 680px; margin: 24px auto; background-color: #FFFFFF; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 14px rgba(0,0,0,0.06); border: 1px solid #E2E8F0; }}
  .header {{ background-color: #0B2545; color: #FFFFFF; padding: 24px 32px; text-align: center; }}
  .header h1 {{ margin: 0; font-size: 20px; letter-spacing: 0.5px; text-transform: uppercase; }}
  .header p {{ margin: 6px 0 0; font-size: 13px; color: #94A3B8; }}
  .status-bar {{ background-color: #F1F5F9; padding: 12px 32px; font-size: 13px; display: flex; justify-content: space-between; border-bottom: 1px solid #E2E8F0; }}
  .content {{ padding: 32px; }}
  .section-title {{ font-size: 15px; font-weight: 700; color: #0B2545; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 24px; margin-bottom: 12px; border-bottom: 2px solid #E2E8F0; padding-bottom: 6px; }}
  .caption-box {{ background-color: #F8FAFC; border-left: 4px solid #CBD5E1; padding: 14px 18px; font-size: 13px; color: #475569; font-style: italic; white-space: pre-wrap; line-height: 1.6; border-radius: 0 8px 8px 0; }}
  .draft-card {{ background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 20px; margin-top: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }}
  .draft-headline {{ font-size: 18px; font-weight: 700; color: #0F172A; margin: 0 0 12px; line-height: 1.4; }}
  .draft-lead {{ font-size: 14px; font-weight: 600; color: #334155; line-height: 1.6; margin-bottom: 14px; background-color: #F8FAFC; padding: 10px 14px; border-radius: 6px; border-left: 3px solid #134074; }}
  .draft-body {{ font-size: 14px; color: #334155; line-height: 1.7; }}
  .draft-body p {{ margin-bottom: 12px; }}
  .excerpt-text {{ font-size: 13px; color: #64748B; font-style: italic; margin-top: 8px; }}
  .button-container {{ text-align: center; margin: 32px 0 16px; padding: 24px; background-color: #F8FAFC; border-radius: 10px; border: 1px dashed #CBD5E1; }}
  .btn {{ display: inline-block; font-size: 15px; font-weight: 700; text-decoration: none; padding: 14px 28px; border-radius: 8px; margin: 8px 10px; transition: background-color 0.2s; }}
  .btn-approve {{ background-color: #059669; color: #FFFFFF !important; box-shadow: 0 4px 8px rgba(5,150,105,0.25); }}
  .btn-revise {{ background-color: #D97706; color: #FFFFFF !important; box-shadow: 0 4px 8px rgba(217,119,6,0.25); }}
  .footer {{ background-color: #F1F5F9; color: #64748B; text-align: center; padding: 20px; font-size: 12px; line-height: 1.6; border-top: 1px solid #E2E8F0; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Redaksi Berita Fakultas Hukum UNDIP</h1>
    <p>Sistem Otomasi Publikasi Instagram &rarr; ilmuhukum.undip.ac.id</p>
  </div>
  
  <div class="status-bar">
    <div><strong>ID Post:</strong> <a href="{post_url}" target="_blank" style="color:#0B2545;">{post_id}</a></div>
    <div><span style="background-color:{iter_badge_color};color:#FFFFFF;padding:3px 10px;border-radius:10px;font-weight:700;font-size:11px;">{iter_label}</span></div>
  </div>

  <div class="content">
    <div style="font-size:13.5px;color:#334155;margin-bottom:18px;">
      Halo <strong>Staf Redaksi FH Undip</strong>,<br>
      Sistem mendeteksi 1 postingan baru dari Instagram <strong>@law.undip</strong> bertanggal <strong>{published_at}</strong>. 
      Berikut draf berita jurnalistik dwibahasa (5W+1H) yang telah disusun oleh AI untuk publikasi web.
    </div>

    <!-- Foto Postingan -->
    <div style="text-align:center;margin:16px 0 20px;">
      <img src="cid:post_media" alt="Foto Postingan Instagram" style="max-width:100%;height:auto;border-radius:8px;border:1px solid #E2E8F0;box-shadow:0 4px 10px rgba(0,0,0,0.05);">
    </div>

    <!-- Caption Asli -->
    <div class="section-title">Caption Asli Instagram (@law.undip)</div>
    <div class="caption-box">{caption_raw}</div>

    <!-- Draf Berita Versi Bahasa Indonesia -->
    <div class="section-title">1. Draf Berita Bahasa Indonesia</div>
    <div class="draft-card" style="border-top:3px solid #0B2545;">
      <h2 class="draft-headline">{title_id}</h2>
      <div class="draft-lead"><strong>Lead Paragraph (5W+1H):</strong><br>{lead_id}</div>
      <div class="draft-body">{content_id}</div>
      <div style="border-top:1px dashed #CBD5E1;padding-top:10px;margin-top:14px;">
        <span style="font-size:12px;font-weight:700;color:#64748B;">Cuplikan / Excerpt:</span>
        <div class="excerpt-text">"{excerpt_id}"</div>
      </div>
    </div>

    <!-- Draf Berita Versi English -->
    <div class="section-title">2. English Version Draft (Formal Academic Standard)</div>
    <div class="draft-card" style="border-top:3px solid #134074;">
      <h2 class="draft-headline" style="font-style:italic;">{title_en}</h2>
      <div class="draft-lead" style="border-left-color:#3B82F6;"><strong>Lead Paragraph (5W+1H):</strong><br>{lead_en}</div>
      <div class="draft-body" style="font-style:italic;">{content_en}</div>
      <div style="border-top:1px dashed #CBD5E1;padding-top:10px;margin-top:14px;">
        <span style="font-size:12px;font-weight:700;color:#64748B;">Summary Excerpt:</span>
        <div class="excerpt-text">"{excerpt_en}"</div>
      </div>
    </div>

    <!-- Kategori dan Tag -->
    <div class="section-title">3. Taksonomi &amp; Metadata SEO Web</div>
    <div style="margin-bottom:12px;"><strong>Kategori:</strong> {cat_badges}</div>
    <div><strong>Tags:</strong> {tag_badges}</div>

    <!-- Tombol Persetujuan / Umpan Balik -->
    <div class="button-container">
      <div style="font-size:15px;font-weight:700;color:#0B2545;margin-bottom:12px;">Umpan Balik Kurasi Berita:</div>
      <div style="font-size:13px;color:#64748B;margin-bottom:18px;">Silakan pilih salah satu tombol di bawah untuk menyetujui langsung publikasi ke portal <strong>ilmuhukum.undip.ac.id</strong> atau meminta perbaikan narasi.</div>
      <a href="{approve_url}" class="btn btn-approve" target="_blank">&check; SETUJUI &amp; PUBLIKASIKAN</a>
      <a href="{revise_url}" class="btn btn-revise" target="_blank">&#9998; MINTA PERBAIKAN NARASI</a>
    </div>
  </div>

  <div class="footer">
    Email notifikasi ini dikirim secara otomatis oleh <strong>Redaksi Berita FH Undip Bot</strong> ke alamat <strong>{self.curator_email}</strong>.<br>
    Portal Web Tujuan: <a href="{settings.WP_BASE_URL}" target="_blank" style="color:#0B2545;text-decoration:none;font-weight:600;">{settings.WP_BASE_URL}</a> | Fakultas Hukum Universitas Diponegoro.
  </div>
</div>
</body>
</html>
"""
        return html

    def send_review_email(self, post: Dict[str, Any], recipient: Optional[str] = None) -> bool:
        """
        Mengirimkan email kurasi interaktif ke kurator.
        Juga selalu menyimpan salinan HTML pratinjau lokal di data/email_previews/.
        """
        post_id = post.get("post_id", "Unknown")
        current_iter = post.get("current_iteration", 1)
        draft = post.get("draft") or {}
        title_id = draft.get("title_id", f"Berita Instagram [{post_id}]")
        target_email = recipient or self.curator_email

        approve_url, revise_url = self.build_feedback_urls(post_id)
        html_body = self.build_html_content(post, approve_url, revise_url)

        # Simpan pratinjau HTML lokal
        preview_filename = f"{post_id}_iter{current_iter}.html"
        preview_path = self.previews_dir / preview_filename
        with open(preview_path, "w", encoding="utf-8") as f:
            f.write(html_body)
        logger.info(f"Salinan pratinjau email HTML disimpan di: {preview_path}")

        subject = f"[KURASI BERITA FH UNDIP] {title_id}" if current_iter <= 1 else f"[REVISI #{current_iter} BERITA FH UNDIP] {title_id}"

        # Periksa apakah SMTP kredensial telah dikonfigurasi
        if not self.smtp_user or not self.smtp_password or self.smtp_password.startswith("xxxx"):
            logger.warning(f"SMTP kredensial belum dikonfigurasi di .env (SMTP_USER/SMTP_PASSWORD). Email fisik belum dikirim, namun pratinjau HTML siap dibuka di {preview_path}.")
            return False

        # Bangun MIME Message
        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.smtp_user}>"
        msg["To"] = target_email

        alt_part = MIMEMultipart("alternative")
        msg.attach(alt_part)

        # Plain text fallback
        plain_text = f"Draf Berita: {title_id}\n\nSetujui: {approve_url}\nMinta Perbaikan: {revise_url}"
        alt_part.attach(MIMEText(plain_text, "plain", "utf-8"))
        alt_part.attach(MIMEText(html_body, "html", "utf-8"))

        # Lampirkan inline image
        local_img = post.get("local_image_path")
        if local_img and Path(local_img).exists():
            try:
                with open(local_img, "rb") as f_img:
                    img_data = f_img.read()
                mime_img = MIMEImage(img_data)
                mime_img.add_header("Content-ID", "<post_media>")
                mime_img.add_header("Content-Disposition", "inline", filename=f"{post_id}.jpg")
                msg.attach(mime_img)
            except Exception as e:
                logger.warning(f"Gagal melampirkan gambar inline {local_img}: {e}")

        # Kirim melalui SMTP
        try:
            logger.info(f"Mengirim email kurasi ke {target_email} via {self.smtp_host}:{self.smtp_port}...")
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            logger.info(f"Email kurasi berhasil dikirimkan ke {target_email}!")
            return True
        except Exception as e:
            logger.error(f"Gagal mengirim email via SMTP: {e}")
            return False

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Curator Review Mailer")
    parser.add_argument("--post-id", help="Kirim email hanya untuk post ID tertentu")
    parser.add_argument("--to", help="Target email penerima override")
    args = parser.parse_args()

    mailer = CuratorMailer()

    pending_file = settings.PENDING_POSTS_FILE
    if not pending_file.exists():
        print("Tidak ada file data/pending_posts.json.")
        exit(0)

    with open(pending_file, "r", encoding="utf-8") as f:
        posts = json.load(f)

    if not posts:
        print("Antrean pending_posts.json kosong.")
        exit(0)

    target_post = None
    if args.post_id:
        for p in posts:
            if p.get("post_id") == args.post_id:
                target_post = p
                break
    else:
        target_post = posts[0]

    if target_post:
        success = mailer.send_review_email(target_post, recipient=args.to)
        print(f"\nHasil Pengiriman Email Review: {'SUKSES' if success else 'DISIMPAN DI PREVIEW (SMTP Butuh Kredensial .env)'}")
        preview_file = mailer.previews_dir / f"{target_post.get('post_id')}_iter{target_post.get('current_iteration', 1)}.html"
        print(f"File Pratinjau Interaktif: {preview_file}")
