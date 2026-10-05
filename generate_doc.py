import os
import json
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    shading_xml = f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table, color="D3D3D3"):
    tblPr = table._tbl.tblPr
    borders_xml = f'''
    <w:tblBorders {nsdecls("w")}>
        <w:top w:val="single" w:sz="4" w:space="0" w:color="{color}"/>
        <w:bottom w:val="single" w:sz="6" w:space="0" w:color="{color}"/>
        <w:left w:val="none"/>
        <w:right w:val="none"/>
        <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>
        <w:insideV w:val="none"/>
    </w:tblBorders>
    '''
    tblPr.append(parse_xml(borders_xml))

def create_documentation():
    base_dir = "/mnt/d/dev_intagram_fh"
    json_path = os.path.join(base_dir, "posts_raw.json")
    img_dir = os.path.join(base_dir, "images")
    output_docx = os.path.join(base_dir, "dokumentasi.docx")

    with open(json_path, 'r', encoding='utf-8') as f:
        posts = json.load(f)

    doc = Document()

    # Set page margins (1 inch / 2.54 cm)
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Color Palette: UNDIP Navy (#0B2545), Slate Blue (#134074), Dark Slate (#1D2A44), Charcoal (#333333)
    COLOR_PRIMARY = RGBColor(11, 37, 69)      # #0B2545
    COLOR_SECONDARY = RGBColor(19, 64, 116)  # #134074
    COLOR_MUTED = RGBColor(100, 110, 120)    # Gray
    HEX_HEADER_BG = "0B2545"
    HEX_ZEBRA_BG = "F4F6F9"
    HEX_CARD_BG = "F8FAFC"

    # --- TITLE / HEADER SECTION ---
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_title.add_run("LAPORAN & DOKUMENTASI MEDIA SOSIAL\n")
    run_sub.font.name = "Arial"
    run_sub.font.size = Pt(11)
    run_sub.font.bold = True
    run_sub.font.color.rgb = COLOR_SECONDARY

    run_title = p_title.add_run("ANALISIS POSTINGAN INSTAGRAM @LAW.UNDIP\nFAKULTAS HUKUM UNIVERSITAS DIPONEGORO")
    run_title.font.name = "Arial"
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = COLOR_PRIMARY

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_meta = p_meta.add_run("Tanggal Pengambilan Data: 5 Oktober 2026 | Sumber: https://www.instagram.com/law.undip/\nDokumentasi Arsip & Studi Pola Komunikasi Publik")
    run_meta.font.name = "Arial"
    run_meta.font.size = Pt(9.5)
    run_meta.font.italic = True
    run_meta.font.color.rgb = COLOR_MUTED

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # --- SECTION 1: PROFIL & IKHTISAR AKUN ---
    h1 = doc.add_heading(level=1)
    r_h1 = h1.add_run("1. Profil Akun & Informasi Umum")
    r_h1.font.name = "Arial"
    r_h1.font.size = Pt(14)
    r_h1.font.bold = True
    r_h1.font.color.rgb = COLOR_PRIMARY
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(6)

    p_desc = doc.add_paragraph()
    p_desc.add_run("Akun Instagram ")
    r_acc = p_desc.add_run("@law.undip")
    r_acc.bold = True
    p_desc.add_run(" merupakan kanal komunikasi resmi Fakultas Hukum Universitas Diponegoro (FH Undip) untuk diseminasi informasi akademik, kegiatan kemahasiswaan, agenda internasional, serta interaksi dengan calon mahasiswa dan alumni.")

    # Table Profil
    tbl_profile = doc.add_table(rows=6, cols=2)
    tbl_profile.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_profile, "CCD5E1")

    profile_data = [
        ("Nama Akun Resmi", "Fakultas Hukum UNDIP (@law.undip)"),
        ("Afiliasi Resmi", "Universitas Diponegoro (@undip.official)"),
        ("Situs Web Resmi", "https://fh.undip.ac.id"),
        ("Jumlah Pengikut (Followers)", "23,1 Ribu (23.1K) Pengikut"),
        ("Mengikuti (Following)", "122 Akun"),
        ("Tagline / Karakter Branding", "Kampus Hukum Progresif (#KampusHukumProgresif, #LawUndip)")
    ]

    for row_idx, (k, v) in enumerate(profile_data):
        row = tbl_profile.rows[row_idx]
        cell_k = row.cells[0]
        cell_v = row.cells[1]
        cell_k.width = Inches(2.2)
        cell_v.width = Inches(4.3)
        set_cell_margins(cell_k, top=80, bottom=80, left=100, right=100)
        set_cell_margins(cell_v, top=80, bottom=80, left=100, right=100)
        if row_idx % 2 == 1:
            set_cell_background(cell_k, HEX_ZEBRA_BG)
            set_cell_background(cell_v, HEX_ZEBRA_BG)
        
        p_k = cell_k.paragraphs[0]
        r_k = p_k.add_run(k)
        r_k.font.bold = True
        r_k.font.size = Pt(9.5)
        r_k.font.name = "Arial"

        p_v = cell_v.paragraphs[0]
        r_v = p_v.add_run(v)
        r_v.font.size = Pt(9.5)
        r_v.font.name = "Arial"

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # --- SECTION 2: STUDI & ANALISIS POLA KONTEN ---
    h2 = doc.add_heading(level=1)
    r_h2 = h2.add_run("2. Studi & Analisis Pola Komunikasi Konten")
    r_h2.font.name = "Arial"
    r_h2.font.size = Pt(14)
    r_h2.font.bold = True
    r_h2.font.color.rgb = COLOR_PRIMARY
    h2.paragraph_format.space_before = Pt(14)
    h2.paragraph_format.space_after = Pt(6)

    p_study_intro = doc.add_paragraph()
    p_study_intro.add_run("Berdasarkan observasi mendalam terhadap 12 postingan terbaru yang berhasil diekstraksi, terdapat 5 pilar utama dan karakteristik komunikasi digital yang dijalankan oleh @law.undip:")

    pillars = [
        ("A. Penguatan Reputasi Global (Undip Global Classroom & Studium Generale)", 
         "Sebanyak 5 dari 12 postingan (41.6%) didedikasikan untuk program internasionalisasi. FH Undip secara konsisten menyelenggarakan kuliah tamu dengan narasumber dari universitas terkemuka dunia seperti The National University of Malaysia (UKM), Hankuk University (Korea Selatan), dan Macquarie University (Australia). Topik yang diangkat sangat mutakhir, meliputi Perpajakan Perusahaan, Hukum Kontrak Malaysia, Resiliensi Demokrasi Digital di Korea, hingga Isu Perlindungan Anak & Kemiskinan."),
        
        ("B. Kunjungan Sekolah & Branding Calon Mahasiswa (School Outreach)", 
         "Tiga postingan video Reels mendokumentasikan kunjungan siswa sekolah menengah (SMA Presiden Bekasi, SMA Muhammadiyah 3 Jakarta, dan SMA Hangtuah 4 Surabaya). Format Reels dikemas ringan dan ramah generasi muda dengan copywriting ajakan: 'Siapa tahu, next time ketemu lagi sebagai mahasiswa FH Undip!'."),
        
        ("C. Publikasi Prestasi Mahasiswa (Student Recognition)", 
         "Pemberitaan Juara 1 Kompetisi Debat Penegakan Hukum Pemilu VI Bawaslu RI Tingkat Nasional oleh tim Kelompok Riset dan Debat (KRD) FH Undip menggunakan format carousel multi-foto, menegaskan keunggulan kompetitif mahasiswa di kancah nasional."),
        
        ("D. Peningkatan Mutu & Transparansi Akademik (Tracer Study & IKU)", 
         "Dokumentasi Workshop Tracer Study 2026 yang mengedukasi sivitas akademika dan alumni mengenai pentingnya feedback lulusan demi pemenuhan Indikator Kinerja Utama (IKU 2) PTNBH."),
        
        ("E. Solidaritas Sosial & Peringatan Hari Kebangsaan", 
         "Unggahan penghormatan Hari Kesaktian Pancasila (1 Oktober 2026) dan ucapan belasungkawa resmi atas wafatnya mahasiswa Sarjana Hukum Angkatan 2023, menunjukkan kehadiran fakultas dalam aspek nilai kebangsaan dan empati kemanusiaan.")
    ]

    for p_title_text, p_body_text in pillars:
        p_item = doc.add_paragraph()
        r_item_t = p_item.add_run(f"• {p_title_text}\n")
        r_item_t.bold = True
        r_item_t.font.name = "Arial"
        r_item_t.font.size = Pt(10)
        r_item_t.font.color.rgb = COLOR_SECONDARY

        r_item_b = p_item.add_run(p_body_text)
        r_item_b.font.name = "Arial"
        r_item_b.font.size = Pt(9.5)
        p_item.paragraph_format.left_indent = Inches(0.2)
        p_item.paragraph_format.space_after = Pt(4)

    # Distribusi Media
    p_dist = doc.add_paragraph()
    p_dist.paragraph_format.space_before = Pt(6)
    r_dist = p_dist.add_run("Distribusi Format Media:")
    r_dist.bold = True
    r_dist.font.name = "Arial"
    r_dist.font.size = Pt(10)

    p_dist_stats = doc.add_paragraph()
    p_dist_stats.paragraph_format.left_indent = Inches(0.2)
    p_dist_stats.add_run("1. Single Image Feed (Foto/Poster): 5 postingan (41.7%)\n")
    p_dist_stats.add_run("2. Video Reels / Clips: 5 postingan (41.7%)\n")
    p_dist_stats.add_run("3. Carousel Multi-Foto: 2 postingan (16.6%)\n")
    p_dist_stats.add_run("Total Sampel Dianalisis: 12 Postingan Terkini")

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # --- SECTION 3: TABEL DAFTAR POSTINGAN ---
    h3 = doc.add_heading(level=1)
    r_h3 = h3.add_run("3. Tabel Inventarisasi Seluruh Postingan Terkini")
    r_h3.font.name = "Arial"
    r_h3.font.size = Pt(14)
    r_h3.font.bold = True
    r_h3.font.color.rgb = COLOR_PRIMARY
    h3.paragraph_format.space_before = Pt(14)
    h3.paragraph_format.space_after = Pt(6)

    # Table of 12 posts
    tbl_posts = doc.add_table(rows=1 + len(posts), cols=5)
    tbl_posts.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_posts, "CBD5E1")

    headers = ["No", "Tanggal", "Tipe Media", "Topik / Inti Konten", "Kode / URL"]
    hdr_row = tbl_posts.rows[0]
    hdr_widths = [Inches(0.4), Inches(1.1), Inches(1.0), Inches(2.8), Inches(1.2)]

    for idx, name in enumerate(headers):
        cell = hdr_row.cells[idx]
        cell.width = hdr_widths[idx]
        set_cell_background(cell, HEX_HEADER_BG)
        set_cell_margins(cell, top=100, bottom=100, left=60, right=60)
        p = cell.paragraphs[0]
        run = p.add_run(name)
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(255, 255, 255)

    post_meta_summary = [
        ("04 Okt 2026", "Feed Image", "Duka Cita: Wafatnya Mahasiswa FH Undip 2023", "DeF_pD9JEiX"),
        ("01 Okt 2026", "Feed Image", "Peringatan Hari Kesaktian Pancasila", "Dd8vxdypDo0"),
        ("29 Sep 2026", "Feed Image", "UGC: Corporate Income Tax (Kuliah Terbuka)", "Dd3tDVuJLFD"),
        ("28 Sep 2026", "Reels Video", "Kunjungan SMA Presiden (Boarding School) Bekasi", "Dd2hTYlJQBt"),
        ("28 Sep 2026", "Feed Image", "UGC: Contract Law Malaysia (Univ. Kebangsaan)", "Dd1HhYnJrZx"),
        ("28 Sep 2026", "Feed Image", "UGC: Korea's Democratic Resilience (Hankuk Univ)", "Dd1HXEvJukf"),
        ("25 Sep 2026", "Carousel (3)", "Workshop Tracer Study 2026 (IKU 2 PTNBH)", "DdtCa-nCVoK"),
        ("24 Sep 2026", "Feed Image", "UGC: Exploring Human Rights Beyond Borders", "Dds2itBxzZK"),
        ("24 Sep 2026", "Carousel (4)", "Prestasi: Juara 1 Debat Pemilu Bawaslu RI 2026", "DdsX6ZECQ5c"),
        ("24 Sep 2026", "Reels Video", "Kunjungan SMA Muhammadiyah 3 Jakarta", "DdsOxAop2BH"),
        ("23 Sep 2026", "Reels Video", "Studium Generale: Child Protection (Macquarie)", "Ddp0JWMp_8M"),
        ("23 Sep 2026", "Reels Video", "Kunjungan Siswa SMA Hangtuah 4 Surabaya", "Ddnwck6Ry6R")
    ]

    for i, item in enumerate(post_meta_summary):
        row = tbl_posts.rows[i + 1]
        for col_idx, text_val in enumerate([str(i+1), item[0], item[1], item[2], item[3]]):
            cell = row.cells[col_idx]
            cell.width = hdr_widths[col_idx]
            set_cell_margins(cell, top=70, bottom=70, left=60, right=60)
            if i % 2 == 1:
                set_cell_background(cell, HEX_ZEBRA_BG)
            p = cell.paragraphs[0]
            run = p.add_run(text_val)
            run.font.name = "Arial"
            run.font.size = Pt(8.5)
            if col_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif col_idx == 4:
                run.font.size = Pt(8)
                run.font.color.rgb = COLOR_SECONDARY

    doc.add_page_break()

    # --- SECTION 4: DETAIL LENGKAP POSTINGAN BESERTA GAMBAR & CAPTION ---
    h4 = doc.add_heading(level=1)
    r_h4 = h4.add_run("4. Rincian Dokumentasi Setiap Postingan")
    r_h4.font.name = "Arial"
    r_h4.font.size = Pt(14)
    r_h4.font.bold = True
    r_h4.font.color.rgb = COLOR_PRIMARY
    h4.paragraph_format.space_before = Pt(10)
    h4.paragraph_format.space_after = Pt(10)

    for i, p in enumerate(posts):
        code = p.get('code')
        prod_type = p.get('product_type')
        access_caption = p.get('accessibility_caption', '')
        caption_text = (p.get('caption') or {}).get('text', '(Tidak ada teks caption)')
        img_filename = f"{i+1:02d}_{code}.jpg"
        img_path = os.path.join(img_dir, img_filename)

        # Heading 2 for post
        h_post = doc.add_heading(level=2)
        r_hp = h_post.add_run(f"Post #{i+1}: {post_meta_summary[i][2]}")
        r_hp.font.name = "Arial"
        r_hp.font.size = Pt(11.5)
        r_hp.font.bold = True
        r_hp.font.color.rgb = COLOR_SECONDARY
        h_post.paragraph_format.space_before = Pt(12)
        h_post.paragraph_format.space_after = Pt(4)

        # Meta Table / Box
        tbl_meta = doc.add_table(rows=3, cols=2)
        tbl_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(tbl_meta, "E2E8F0")

        tbl_meta.rows[0].cells[0].paragraphs[0].add_run("Tipe Media:").bold = True
        tbl_meta.rows[0].cells[0].paragraphs[0].runs[0].font.size = Pt(8.5)
        r_type = tbl_meta.rows[0].cells[0].paragraphs[0].add_run(f" {post_meta_summary[i][1]} ({prod_type})")
        r_type.font.size = Pt(8.5)

        tbl_meta.rows[0].cells[1].paragraphs[0].add_run("Tanggal Unggah:").bold = True
        tbl_meta.rows[0].cells[1].paragraphs[0].runs[0].font.size = Pt(8.5)
        r_date = tbl_meta.rows[0].cells[1].paragraphs[0].add_run(f" {post_meta_summary[i][0]}")
        r_date.font.size = Pt(8.5)

        tbl_meta.rows[1].cells[0].paragraphs[0].add_run("URL Langsung:").bold = True
        tbl_meta.rows[1].cells[0].paragraphs[0].runs[0].font.size = Pt(8.5)
        r_url = tbl_meta.rows[1].cells[0].paragraphs[0].add_run(f" https://www.instagram.com/law.undip/p/{code}/")
        r_url.font.size = Pt(8)
        r_url.font.color.rgb = COLOR_SECONDARY

        tbl_meta.rows[1].cells[1].paragraphs[0].add_run("Kategori Konten:").bold = True
        tbl_meta.rows[1].cells[1].paragraphs[0].runs[0].font.size = Pt(8.5)
        r_cat = tbl_meta.rows[1].cells[1].paragraphs[0].add_run(f" {post_meta_summary[i][2].split(':')[0]}")
        r_cat.font.size = Pt(8.5)

        tbl_meta.rows[2].cells[0].paragraphs[0].add_run("Deskripsi AI (Alt Text):").bold = True
        tbl_meta.rows[2].cells[0].paragraphs[0].runs[0].font.size = Pt(8.5)
        r_alt = tbl_meta.rows[2].cells[0].paragraphs[0].add_run(f" {access_caption}")
        r_alt.font.size = Pt(8)
        r_alt.font.italic = True
        # merge row 2 across cols
        tbl_meta.rows[2].cells[0].merge(tbl_meta.rows[2].cells[1])

        for r in tbl_meta.rows:
            for c in r.cells:
                set_cell_background(c, HEX_CARD_BG)
                set_cell_margins(c, top=50, bottom=50, left=80, right=80)

        doc.add_paragraph().paragraph_format.space_after = Pt(4)

        # Media Image & Caption in a side-by-side or stacked presentation
        # Stacked layout: Image centered (width 3.2 inches), then blockquote caption
        if os.path.exists(img_path):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(4)
            p_img.paragraph_format.space_after = Pt(4)
            run_img = p_img.add_run()
            try:
                run_img.add_picture(img_path, width=Inches(3.2))
            except Exception as e:
                p_img.add_run(f"[Gambar tidak dapat dimuat: {e}]")

        # Caption Section
        p_cap_label = doc.add_paragraph()
        r_cl = p_cap_label.add_run("Teks Asli Caption:")
        r_cl.bold = True
        r_cl.font.name = "Arial"
        r_cl.font.size = Pt(9.5)
        p_cap_label.paragraph_format.space_before = Pt(4)
        p_cap_label.paragraph_format.space_after = Pt(2)

        p_caption = doc.add_paragraph()
        p_caption.paragraph_format.left_indent = Inches(0.25)
        p_caption.paragraph_format.right_indent = Inches(0.25)
        p_caption.paragraph_format.space_after = Pt(12)
        r_cap = p_caption.add_run(caption_text)
        r_cap.font.name = "Consolas"
        r_cap.font.size = Pt(8.5)
        r_cap.font.color.rgb = RGBColor(40, 45, 55)

        # Small divider between posts
        p_div = doc.add_paragraph()
        p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_div = p_div.add_run("―" * 40)
        r_div.font.color.rgb = RGBColor(200, 205, 215)
        p_div.paragraph_format.space_after = Pt(10)

    # --- SECTION 5: KESIMPULAN & REKOMENDASI STRATEGIS ---
    doc.add_page_break()
    h5 = doc.add_heading(level=1)
    r_h5 = h5.add_run("5. Kesimpulan & Rekomendasi Strategis")
    r_h5.font.name = "Arial"
    r_h5.font.size = Pt(14)
    r_h5.font.bold = True
    r_h5.font.color.rgb = COLOR_PRIMARY
    h5.paragraph_format.space_before = Pt(10)
    h5.paragraph_format.space_after = Pt(6)

    recs = [
        ("Konsistensi Branding 'Kampus Hukum Progresif'", 
         "Penggunaan tagar #KampusHukumProgresif dan penekanan wawasan global pada setiap materi hukum membuktikan positioning yang sangat kuat dan modern bagi FH Undip dibandingkan institusi pendidikan hukum konvensional."),
        ("Keseimbangan Format Edukasi & Interaksi Siswa", 
         "Kombinasi antara flyer akademik formal (UGC) dan video Reels yang menghibur untuk kunjungan sekolah berhasil menjangkau dua target audiens sekaligus: akademisi/mahasiswa aktif dan calon mahasiswa baru."),
        ("Peluang Penguatan Call-to-Action (CTA)", 
         "Pada postingan edukasi hukum internasional, penambahan tautan registrasi yang lebih ringkas (misal via bit.ly atau Linktree di bio) dan pembukaan kolom diskusi interaktif di caption akan semakin meningkatkan engagement rate."),
        ("Arsip Digital & Integrasi Website", 
         "Konten-konten bernilai tinggi seperti hasil Tracer Study dan rekaman kuliah Undip Global Classroom sangat potensial untuk dihubungkan langsung ke portal berita resmi di https://fh.undip.ac.id guna meningkatkan domain authority dan SEO web kampus.")
    ]

    for rec_t, rec_b in recs:
        p_r = doc.add_paragraph()
        r_rt = p_r.add_run(f"✔ {rec_t}\n")
        r_rt.bold = True
        r_rt.font.name = "Arial"
        r_rt.font.size = Pt(10)
        r_rt.font.color.rgb = COLOR_SECONDARY

        r_rb = p_r.add_run(rec_b)
        r_rb.font.name = "Arial"
        r_rb.font.size = Pt(9.5)
        p_r.paragraph_format.left_indent = Inches(0.2)
        p_r.paragraph_format.space_after = Pt(6)

    # Save document
    doc.save(output_docx)
    print(f"Document successfully created at: {output_docx}")

if __name__ == "__main__":
    create_documentation()
