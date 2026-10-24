import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Initialize Presentation with 16:9 widescreen dimensions
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

SCREENSHOTS_DIR = "/Users/sunilsaraf/.gemini/antigravity/scratch/ComplaintIQ/screenshots"
OUTPUT_PATH = "/Users/sunilsaraf/.gemini/antigravity/scratch/ComplaintIQ/ComplaintIQ_Presentation.pptx"

# Color Palette Constants
DARK_BG = RGBColor(15, 23, 42)          # Slate 900
DARK_CARD = RGBColor(30, 41, 59)        # Slate 800
DARK_CARD_BORDER = RGBColor(51, 65, 85) # Slate 700

LIGHT_BG = RGBColor(248, 250, 252)      # Slate 50
LIGHT_CARD = RGBColor(255, 255, 255)    # White
LIGHT_CARD_BORDER = RGBColor(226, 232, 240) # Slate 200

INDIGO_PRIMARY = RGBColor(79, 70, 229)  # Indigo 600
INDIGO_LIGHT = RGBColor(129, 140, 248)  # Indigo 400
CYAN_ACCENT = RGBColor(6, 182, 212)     # Cyan 500
EMERALD_ACCENT = RGBColor(16, 185, 129) # Emerald 500
AMBER_ACCENT = RGBColor(245, 158, 11)   # Amber 500
ROSE_ACCENT = RGBColor(244, 63, 94)     # Rose 500

TEXT_DARK = RGBColor(15, 23, 42)        # Slate 900
TEXT_MUTED = RGBColor(100, 116, 139)    # Slate 500
TEXT_LIGHT = RGBColor(248, 250, 252)    # Slate 50
TEXT_LIGHT_MUTED = RGBColor(148, 163, 184) # Slate 400

FONT_NAME = "Calibri"

def add_slide_background(slide, is_dark=False):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = DARK_BG if is_dark else LIGHT_BG
    bg.line.fill.background()
    return bg

def add_header(slide, badge_text, title_text, subtitle_text, is_dark=False, slide_num="01 / 12"):
    # Header badge pill
    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.42), Inches(5.2), Inches(0.28))
    pill.fill.solid()
    pill.fill.fore_color.rgb = RGBColor(49, 46, 129) if is_dark else RGBColor(238, 242, 255)
    pill.line.color.rgb = INDIGO_LIGHT if is_dark else INDIGO_PRIMARY
    pill.line.width = Pt(1)
    
    tf_pill = pill.text_frame
    tf_pill.word_wrap = False
    tf_pill.margin_top = Pt(2)
    tf_pill.margin_bottom = Pt(2)
    tf_pill.margin_left = Pt(8)
    tf_pill.margin_right = Pt(8)
    p_pill = tf_pill.paragraphs[0]
    p_pill.text = badge_text.upper()
    p_pill.font.name = FONT_NAME
    p_pill.font.size = Pt(8.5)
    p_pill.font.bold = True
    p_pill.font.color.rgb = INDIGO_LIGHT if is_dark else INDIGO_PRIMARY

    # Title and Subtitle Box
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.76), Inches(11.5), Inches(0.95))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0)
    tf.margin_top = Inches(0)
    
    p_title = tf.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = FONT_NAME
    p_title.font.size = Pt(21)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_LIGHT if is_dark else TEXT_DARK
    
    p_sub = tf.add_paragraph()
    p_sub.text = subtitle_text
    p_sub.font.name = FONT_NAME
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = TEXT_LIGHT_MUTED if is_dark else TEXT_MUTED
    p_sub.space_before = Pt(2)

    # Slide Footer
    tb_footer = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(11.733), Inches(0.3))
    tf_footer = tb_footer.text_frame
    tf_footer.margin_left = Inches(0)
    tf_footer.margin_top = Inches(0)
    p_foot = tf_footer.paragraphs[0]
    p_foot.text = f"ComplaintIQ — Autonomous Financial Grievance Intelligence & Forecasting Platform  |  Slide {slide_num}"
    p_foot.font.name = FONT_NAME
    p_foot.font.size = Pt(9)
    p_foot.font.color.rgb = RGBColor(71, 85, 105) if is_dark else RGBColor(148, 163, 184)

def add_card(slide, left, top, width, height, is_dark=False, border_color=None, bg_color=None):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color if bg_color else (DARK_CARD if is_dark else LIGHT_CARD)
    card.line.color.rgb = border_color if border_color else (DARK_CARD_BORDER if is_dark else LIGHT_CARD_BORDER)
    card.line.width = Pt(1)
    return card

def add_screenshot_container(slide, img_path, left, top, width, height, title="Interface Screenshot", is_dark=False):
    card = add_card(slide, left, top, width, height, is_dark=is_dark)
    
    tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.12), width - Inches(0.4), Inches(0.28))
    tf = tb.text_frame
    tf.margin_left = Inches(0)
    tf.margin_top = Inches(0)
    p = tf.paragraphs[0]
    p.text = f"●  {title.upper()}"
    p.font.name = FONT_NAME
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = INDIGO_LIGHT if is_dark else INDIGO_PRIMARY

    # Inner image calculations (maintain 1.6 aspect ratio)
    avail_w = width - Inches(0.4)
    avail_h = height - Inches(0.55)
    img_w = avail_w
    img_h = img_w / 1.6
    if img_h > avail_h:
        img_h = avail_h
        img_w = img_h * 1.6
    
    img_left = left + (width - img_w) / 2
    img_top = top + Inches(0.42) + (avail_h - img_h) / 2
    slide.shapes.add_picture(img_path, img_left, img_top, width=img_w, height=img_h)

def add_bullet_item(tf, bold_label, desc, is_dark=False, space_before=Pt(6)):
    p = tf.add_paragraph()
    p.space_before = space_before
    run_bold = p.add_run()
    run_bold.text = f"•  {bold_label}: "
    run_bold.font.name = FONT_NAME
    run_bold.font.size = Pt(10)
    run_bold.font.bold = True
    run_bold.font.color.rgb = TEXT_LIGHT if is_dark else TEXT_DARK
    
    run_desc = p.add_run()
    run_desc.text = desc
    run_desc.font.name = FONT_NAME
    run_desc.font.size = Pt(10)
    run_desc.font.color.rgb = TEXT_LIGHT_MUTED if is_dark else TEXT_MUTED

# ==========================================================
# SLIDE 1: Title & Hero Slide (Theme: Dark Slate)
# ==========================================================
slide1 = prs.slides.add_slide(blank_layout)
add_slide_background(slide1, is_dark=True)

# Top Badge
tb_top = slide1.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(11.733), Inches(0.4))
tf_top = tb_top.text_frame
p_top = tf_top.paragraphs[0]
p_top.text = "ACADEMIC CAPSTONE PROJECT  •  ENTERPRISE FINTECH AI & REGULATORY ANALYTICS"
p_top.font.name = FONT_NAME
p_top.font.size = Pt(10)
p_top.font.bold = True
p_top.font.color.rgb = INDIGO_LIGHT

# Main Hero Title
tb_hero = slide1.shapes.add_textbox(Inches(0.8), Inches(0.95), Inches(11.733), Inches(1.8))
tf_hero = tb_hero.text_frame
tf_hero.word_wrap = True
p_h1 = tf_hero.paragraphs[0]
p_h1.text = "ComplaintIQ"
p_h1.font.name = FONT_NAME
p_h1.font.size = Pt(44)
p_h1.font.bold = True
p_h1.font.color.rgb = RGBColor(255, 255, 255)

p_h2 = tf_hero.add_paragraph()
p_h2.text = "Autonomous Financial Grievance Intelligence, Anomaly Detection & Time-Series Forecasting Platform"
p_h2.font.name = FONT_NAME
p_h2.font.size = Pt(14)
p_h2.font.bold = True
p_h2.font.color.rgb = CYAN_ACCENT
p_h2.space_before = Pt(4)

p_h3 = tf_hero.add_paragraph()
p_h3.text = "An end-to-end decision-support system analyzing 6,956+ consumer financial complaints with sublinear TF-IDF, calibrated Linear SVM, NMF topic decomposition, rolling MAD seasonal surge detection, and damped Holt-Winters forecasting."
p_h3.font.name = FONT_NAME
p_h3.font.size = Pt(10.5)
p_h3.font.color.rgb = TEXT_LIGHT_MUTED
p_h3.space_before = Pt(6)

# 4 Team Member Cards
team_members = [
    {
        "name": "Aryan Turalkar",
        "roll": "Roll No: A152",
        "role": "NLP & Classification Lead",
        "detail": "TF-IDF vectorizer, negation handling, LinearSVC classifier, and Platt probability calibration."
    },
    {
        "name": "Suryansh Saraf",
        "roll": "Roll No: A-125",
        "role": "Full-Stack System Architect",
        "detail": "React 18 Command Center, UI/UX design, FastAPI async REST API, and Cloudflare integration."
    },
    {
        "name": "Soham Hande",
        "roll": "Roll No: A-129",
        "role": "Anomaly Detection Engineer",
        "detail": "Day-of-Week rolling MAD z-scores, Isolation Forest ensemble, and surge severity rules."
    },
    {
        "name": "Pratham Deepak",
        "roll": "Roll No: A-114",
        "role": "Time-Series & Operations Lead",
        "detail": "Additive damped Holt-Winters forecasting, incident alert lifecycle, and deduplication."
    }
]

card_w = Inches(2.78)
card_h = Inches(2.25)
card_top = Inches(3.25)
for i, member in enumerate(team_members):
    c_left = Inches(0.8) + i * Inches(2.98)
    card = add_card(slide1, c_left, card_top, card_w, card_h, is_dark=True, border_color=INDIGO_PRIMARY)
    
    tb_m = slide1.shapes.add_textbox(c_left + Inches(0.18), card_top + Inches(0.18), card_w - Inches(0.36), card_h - Inches(0.36))
    tf_m = tb_m.text_frame
    tf_m.word_wrap = True
    tf_m.margin_left = tf_m.margin_top = tf_m.margin_right = tf_m.margin_bottom = Inches(0)
    
    p1 = tf_m.paragraphs[0]
    p1.text = member["name"]
    p1.font.name = FONT_NAME
    p1.font.size = Pt(13)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)
    
    p2 = tf_m.add_paragraph()
    p2.text = member["roll"]
    p2.font.name = FONT_NAME
    p2.font.size = Pt(10)
    p2.font.bold = True
    p2.font.color.rgb = INDIGO_LIGHT
    p2.space_before = Pt(2)
    
    p3 = tf_m.add_paragraph()
    p3.text = member["role"]
    p3.font.name = FONT_NAME
    p3.font.size = Pt(9.5)
    p3.font.bold = True
    p3.font.color.rgb = CYAN_ACCENT
    p3.space_before = Pt(4)
    
    p4 = tf_m.add_paragraph()
    p4.text = member["detail"]
    p4.font.name = FONT_NAME
    p4.font.size = Pt(8.5)
    p4.font.color.rgb = TEXT_LIGHT_MUTED
    p4.space_before = Pt(5)

# Tech Stack Banner
tb_tech = slide1.shapes.add_textbox(Inches(0.8), Inches(5.95), Inches(11.733), Inches(0.75))
tf_tech = tb_tech.text_frame
tf_tech.word_wrap = True
p_t1 = tf_tech.paragraphs[0]
p_t1.text = "CORE TECHNOLOGY STACK"
p_t1.font.name = FONT_NAME
p_t1.font.size = Pt(9)
p_t1.font.bold = True
p_t1.font.color.rgb = TEXT_LIGHT_MUTED

p_t2 = tf_tech.add_paragraph()
p_t2.text = "Frontend: React 18  •  TypeScript  •  TailwindCSS  •  Lucide Icons  •  Recharts  |  Backend: FastAPI  •  Python 3.13  •  Scikit-Learn  •  SQLite  •  Cloudflare Tunnel"
p_t2.font.name = FONT_NAME
p_t2.font.size = Pt(10)
p_t2.font.bold = True
p_t2.font.color.rgb = RGBColor(255, 255, 255)
p_t2.space_before = Pt(3)

# Slide Footer
tb_foot1 = slide1.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(11.733), Inches(0.3))
tf_foot1 = tb_foot1.text_frame
tf_foot1.margin_left = Inches(0)
p_f1 = tf_foot1.paragraphs[0]
p_f1.text = "ComplaintIQ Capstone Presentation  |  Team Members: Aryan Turalkar (A152), Suryansh Saraf (A-125), Soham Hande (A-129), Pratham Deepak (A-114)  |  Slide 01 / 12"
p_f1.font.name = FONT_NAME
p_f1.font.size = Pt(9)
p_f1.font.color.rgb = RGBColor(71, 85, 105)

print("Slide 1 generated.")

# ==========================================================
# SLIDE 2: Problem Statement & Motivation (Theme: Light)
# ==========================================================
slide2 = prs.slides.add_slide(blank_layout)
add_slide_background(slide2, is_dark=False)
add_header(slide2, "Executive Context & Problem Definition", "The Regulatory Grievance Bottleneck", 
           "Why manual triage, static threshold alerts, and black-box AI fail modern financial institutions", is_dark=False, slide_num="02 / 12")

c2_w = Inches(3.68)
c2_h = Inches(4.35)
c2_top = Inches(1.95)

# Card 1: Volume & Ingestion Lag
card2_1 = add_card(slide2, Inches(0.8), c2_top, c2_w, c2_h, is_dark=False)
tb2_1 = slide2.shapes.add_textbox(Inches(1.0), c2_top + Inches(0.2), c2_w - Inches(0.4), c2_h - Inches(0.4))
tf2_1 = tb2_1.text_frame
tf2_1.word_wrap = True
tf2_1.margin_left = tf2_1.margin_top = Inches(0)
p = tf2_1.paragraphs[0]
p.text = "1. INGESTION & TRIAGE LATENCY"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = ROSE_ACCENT

add_bullet_item(tf2_1, "Massive Complaint Scale", "CFPB receives hundreds of thousands of customer disputes annually across multiple channels (Web, Phone, Mail, Referral).")
add_bullet_item(tf2_1, "Manual Routing Bottleneck", "Human classification takes 24–72 hours per complaint, creating severe response delays and SLA penalties.")
add_bullet_item(tf2_1, "Unstructured Narratives", "Complex, emotionally charged customer texts conceal the root financial problem, requiring extensive manual reading.")
add_bullet_item(tf2_1, "Operational Cost", "Financial institutions spend millions on human reviewers just performing basic category routing.")

# Card 2: Undetected Systemic Surges
card2_2 = add_card(slide2, Inches(4.82), c2_top, c2_w, c2_h, is_dark=False)
tb2_2 = slide2.shapes.add_textbox(Inches(5.02), c2_top + Inches(0.2), c2_w - Inches(0.4), c2_h - Inches(0.4))
tf2_2 = tb2_2.text_frame
tf2_2.word_wrap = True
tf2_2.margin_left = tf2_2.margin_top = Inches(0)
p = tf2_2.paragraphs[0]
p.text = "2. UNDETECTED SYSTEMIC SURGES"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = AMBER_ACCENT

add_bullet_item(tf2_2, "Hidden Infrastructure Glitches", "Systemic failures (e.g. gateway timeouts, improper loan escrow deductions) remain hidden until customer churn peaks.")
add_bullet_item(tf2_2, "Weekend Seasonality Trap", "Static thresholds fail due to 70% volume drops on weekends: Monday surges trigger false alarms, Saturday spikes are missed.")
add_bullet_item(tf2_2, "Alert Fatigue", "Naïve alert systems flood compliance teams with duplicate notifications, leading to critical warnings being ignored.")
add_bullet_item(tf2_2, "Regulatory Penalties", "Failure to detect systemic spikes quickly leads to massive regulatory fines and public enforcement actions.")

# Card 3: The Black-Box Dilemma
card2_3 = add_card(slide2, Inches(8.84), c2_top, c2_w, c2_h, is_dark=False)
tb2_3 = slide2.shapes.add_textbox(Inches(9.04), c2_top + Inches(0.2), c2_w - Inches(0.4), c2_h - Inches(0.4))
tf2_3 = tb2_3.text_frame
tf2_3.word_wrap = True
tf2_3.margin_left = tf2_3.margin_top = Inches(0)
p = tf2_3.paragraphs[0]
p.text = "3. BLACK-BOX AI & PLANNING VOID"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = INDIGO_PRIMARY

add_bullet_item(tf2_3, "Strict Regulatory Auditing", "Compliance officers cannot adopt 'black-box' deep learning models that cannot provide token-level mathematical proof.")
add_bullet_item(tf2_3, "Uncalibrated Confidence", "Raw model scores misrepresent actual uncertainty, leading to dangerous automated misrouting.")
add_bullet_item(tf2_3, "Zero Predictive Capacity", "Operations managers react to spikes after they occur rather than forecasting staffing needs 14–30 days in advance.")
add_bullet_item(tf2_3, "Disconnected Tooling", "ML models rarely integrate into an actionable incident triage workflow with audit histories.")

# Bottom Banner
banner2 = add_card(slide2, Inches(0.8), Inches(6.45), Inches(11.733), Inches(0.45), is_dark=False, bg_color=RGBColor(238, 242, 255), border_color=INDIGO_PRIMARY)
tb_b2 = slide2.shapes.add_textbox(Inches(1.0), Inches(6.47), Inches(11.333), Inches(0.38))
tf_b2 = tb_b2.text_frame
p_b2 = tf_b2.paragraphs[0]
p_b2.text = "PROJECT OBJECTIVE: Deliver an end-to-end, sub-50ms explainable triage platform with seasonality-aware anomaly detection and capacity forecasting."
p_b2.font.name = FONT_NAME
p_b2.font.size = Pt(9.5)
p_b2.font.bold = True
p_b2.font.color.rgb = INDIGO_PRIMARY

print("Slide 2 generated.")

# ==========================================================
# SLIDE 3: System Architecture & Technical Pipeline (Theme: Light)
# ==========================================================
slide3 = prs.slides.add_slide(blank_layout)
add_slide_background(slide3, is_dark=False)
add_header(slide3, "System Architecture & Data Flow", "Decoupled Multi-Tier System Architecture", 
           "High-throughput pipeline uniting supervised/unsupervised machine learning microservices with an interactive web dashboard", is_dark=False, slide_num="03 / 12")

c3_w = Inches(3.68)
c3_h = Inches(4.85)
c3_top = Inches(1.95)

# Tier 1
card3_1 = add_card(slide3, Inches(0.8), c3_top, c3_w, c3_h, is_dark=False)
tb3_1 = slide3.shapes.add_textbox(Inches(1.0), c3_top + Inches(0.2), c3_w - Inches(0.4), c3_h - Inches(0.4))
tf3_1 = tb3_1.text_frame
tf3_1.word_wrap = True
tf3_1.margin_left = tf3_1.margin_top = Inches(0)
p = tf3_1.paragraphs[0]
p.text = "TIER 1: INGESTION & PREPROCESSING"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = INDIGO_PRIMARY

add_bullet_item(tf3_1, "CFPB Complaint Corpus", "6,956 real-world consumer complaints across 5 core financial products: Credit Cards, Mortgages, Student Loans, Debt Collection, Bank Accounts.")
add_bullet_item(tf3_1, "Text Normalization", "Regex cleaning, punctuation stripping, lowercasing, and custom financial stopword filtering.")
add_bullet_item(tf3_1, "Negation Tokenizer", "Binds negations to adjacent words (e.g., 'not_received', 'no_refund') preserving crucial semantic polarity.")
add_bullet_item(tf3_1, "Sublinear TF-IDF Vectorizer", "Applies 1 + log(tf) scaling to suppress repetitive legal boilerplate; extracts top 10,000 unigram & bigram features.")
add_bullet_item(tf3_1, "Data Integrity", "Automated validation of complaint metadata, timestamps, product codes, and company responses.")

# Tier 2
card3_2 = add_card(slide3, Inches(4.82), c3_top, c3_w, c3_h, is_dark=False)
tb3_2 = slide3.shapes.add_textbox(Inches(5.02), c3_top + Inches(0.2), c3_w - Inches(0.4), c3_h - Inches(0.4))
tf3_2 = tb3_2.text_frame
tf3_2.word_wrap = True
tf3_2.margin_left = tf3_2.margin_top = Inches(0)
p = tf3_2.paragraphs[0]
p.text = "TIER 2: ML & ANALYTICS CORE"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = CYAN_ACCENT

add_bullet_item(tf3_2, "Calibrated Linear SVM", "High-margin hyperplane classification with Platt sigmoid calibration for compliant, bounded probability outputs.")
add_bullet_item(tf3_2, "Token Feature Attribution", "Mathematical decision weights (w_i * x_i) showing exact positive and negative keywords driving every prediction.")
add_bullet_item(tf3_2, "Latent Topic Extraction (NMF)", "Non-Negative Matrix Factorization decomposing term-document matrix into 8 interpretable regulatory topics.")
add_bullet_item(tf3_2, "K-Means Document Clustering", "Vector space clustering (k=5) with silhouette score optimization for unsupervised cohort analysis.")
add_bullet_item(tf3_2, "Time-Series Anomaly Engine", "Day-of-Week normalized Rolling MAD z-scores combined with Isolation Forest ensemble.")
add_bullet_item(tf3_2, "Damped Holt-Winters Forecasting", "Triple exponential smoothing with additive weekly seasonality and trend damping parameter.")

# Tier 3
card3_3 = add_card(slide3, Inches(8.84), c3_top, c3_w, c3_h, is_dark=False)
tb3_3 = slide3.shapes.add_textbox(Inches(9.04), c3_top + Inches(0.2), c3_w - Inches(0.4), c3_h - Inches(0.4))
tf3_3 = tb3_3.text_frame
tf3_3.word_wrap = True
tf3_3.margin_left = tf3_3.margin_top = Inches(0)
p = tf3_3.paragraphs[0]
p.text = "TIER 3: APPLICATION & UI LAYER"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = EMERALD_ACCENT

add_bullet_item(tf3_3, "FastAPI High-Speed Backend", "Asynchronous Python 3.13 REST API server delivering sub-50ms p95 latency on inference endpoints.")
add_bullet_item(tf3_3, "SQLite Transactional Store", "Persistent database holding complaints, predictions, audit histories, and active alert statuses.")
add_bullet_item(tf3_3, "React 18 & TypeScript SPA", "Modern responsive web dashboard featuring TailwindCSS, Lucide icons, and Recharts interactive graphics.")
add_bullet_item(tf3_3, "Alert State Machine", "Deduplicated incident lifecycle (Triggered -> Investigating -> Resolved) with immutable audit logging.")
add_bullet_item(tf3_3, "Cloudflare Edge Tunnel", "Secure zero-open-port edge tunneling allowing real-time global accessibility and peer review.")

print("Slide 3 generated.")

# ==========================================================
# SLIDE 4: Real-Time Command Center UI (Screenshot: overview.png)
# ==========================================================
slide4 = prs.slides.add_slide(blank_layout)
add_slide_background(slide4, is_dark=False)
add_header(slide4, "Command Center UI Preview", "Home Command Center & Executive KPI Ribbon", 
           "Unified single-pane operational view delivering situational awareness across volume, anomalies, and active models", is_dark=False, slide_num="04 / 12")

overview_img = os.path.join(SCREENSHOTS_DIR, "overview.png")
add_screenshot_container(slide4, overview_img, Inches(0.8), Inches(1.95), Inches(6.8), Inches(4.85), 
                         title="Live Overview Interface (Command Center)", is_dark=False)

card4_right = add_card(slide4, Inches(7.8), Inches(1.95), Inches(4.733), Inches(4.85), is_dark=False)
tb4_r = slide4.shapes.add_textbox(Inches(8.0), Inches(2.15), Inches(4.333), Inches(4.45))
tf4_r = tb4_r.text_frame
tf4_r.word_wrap = True
tf4_r.margin_left = tf4_r.margin_top = Inches(0)

p = tf4_r.paragraphs[0]
p.text = "EXECUTIVE OPERATIONAL DASHBOARD"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = INDIGO_PRIMARY

add_bullet_item(tf4_r, "Real-Time KPI Ribbon", "Instant visibility into Total Complaints (6,956), Active Anomaly Signals (5), Critical Incident Alerts, and Model Calibration status.")
add_bullet_item(tf4_r, "30-Day Volume Trajectory", "Interactive Recharts dual-line time series displaying daily incoming complaints alongside moving averages and highlighted anomaly spikes.")
add_bullet_item(tf4_r, "Product Distribution Breakdown", "Visual breakdown across 5 major financial products: Credit Cards, Mortgages, Student Loans, Debt Collection, Bank Accounts.")
add_bullet_item(tf4_r, "Submission Channel Mix", "Tracks intake across Web, Phone, Mail, and Referral channels to monitor ingestion channel health.")
add_bullet_item(tf4_r, "Embedded Live Quick Predictor", "Allows operations managers to paste raw narrative text right on the home screen for instantaneous classification testing.")

print("Slide 4 generated.")

# ==========================================================
# SLIDE 5: Automated Complaint Explorer & Triage (Screenshot: explorer.png)
# ==========================================================
slide5 = prs.slides.add_slide(blank_layout)
add_slide_background(slide5, is_dark=False)
add_header(slide5, "Operational Tooling & Record Audit", "Complaint Explorer, Smart Presets & Audit Trail", 
           "High-throughput search and detailed narrative drawer engineered for compliance analysts and auditors", is_dark=False, slide_num="05 / 12")

card5_left = add_card(slide5, Inches(0.8), Inches(1.95), Inches(4.733), Inches(4.85), is_dark=False)
tb5_l = slide5.shapes.add_textbox(Inches(1.0), Inches(2.15), Inches(4.333), Inches(4.45))
tf5_l = tb5_l.text_frame
tf5_l.word_wrap = True
tf5_l.margin_left = tf5_l.margin_top = Inches(0)

p = tf5_l.paragraphs[0]
p.text = "TRIAGE & AUDITING CAPABILITIES"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = INDIGO_PRIMARY

add_bullet_item(tf5_l, "Sub-10ms Debounced Search", "Fast client-side full-text search across 6,956 consumer narratives with instant keyword matching and highlighting.")
add_bullet_item(tf5_l, "Curated One-Click Presets", "Instant operational filters including 'Urgent Disputed', 'Identity Theft', 'Student Loans / Mortgages', and 'Recent 30 Days'.")
add_bullet_item(tf5_l, "Multi-Faceted Filtering", "Simultaneously filter by Product vertical, Issue category, Submission Channel, and Anomaly surge status.")
add_bullet_item(tf5_l, "Slide-Out Narrative Drawer", "Clicking any record opens a detailed drawer displaying verbatim consumer narratives, company responses, and regulatory tags.")
add_bullet_item(tf5_l, "Analyst Actionability", "Enables rapid escalation of high-risk complaints directly from the search view to mitigate regulatory exposure.")

explorer_img = os.path.join(SCREENSHOTS_DIR, "explorer.png")
add_screenshot_container(slide5, explorer_img, Inches(5.733), Inches(1.95), Inches(6.8), Inches(4.85), 
                         title="Complaint Explorer Interface & Filter Presets", is_dark=False)

print("Slide 5 generated.")

# ==========================================================
# SLIDE 6: NLP Pipeline & Text Classification (Screenshot: nlp.png)
# ==========================================================
slide6 = prs.slides.add_slide(blank_layout)
add_slide_background(slide6, is_dark=False)
add_header(slide6, "NLP & Supervised Learning", "Sublinear TF-IDF & Calibrated Linear Support Vector Machine", 
           "Robust multi-class document classification pipeline achieving 89.6% accuracy over financial narratives", is_dark=False, slide_num="06 / 12")

nlp_img = os.path.join(SCREENSHOTS_DIR, "nlp.png")
add_screenshot_container(slide6, nlp_img, Inches(0.8), Inches(1.95), Inches(6.8), Inches(4.85), 
                         title="NLP Intelligence View: Tokens, Categories & Accuracy", is_dark=False)

card6_right = add_card(slide6, Inches(7.8), Inches(1.95), Inches(4.733), Inches(4.85), is_dark=False)
tb6_r = slide6.shapes.add_textbox(Inches(8.0), Inches(2.15), Inches(4.333), Inches(4.45))
tf6_r = tb6_r.text_frame
tf6_r.word_wrap = True
tf6_r.margin_left = tf6_r.margin_top = Inches(0)

p = tf6_r.paragraphs[0]
p.text = "TEXT CLASSIFICATION ARCHITECTURE"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = INDIGO_PRIMARY

add_bullet_item(tf6_r, "Sublinear Term Frequency", "Applies 1 + log(tf) scaling to compress term frequencies, preventing common repetitive financial jargon from skewing vectors.")
add_bullet_item(tf6_r, "N-Gram Vocabulary Capture", "Captures 10,000 unigram and bigram features, retaining critical compound expressions like 'late fee', 'credit report', 'unauthorized charge'.")
add_bullet_item(tf6_r, "Model Benchmark Comparison", "Evaluated Multinomial Naive Bayes (82.1%), Logistic Regression (87.4%), and Calibrated Linear SVM (89.6%).")
add_bullet_item(tf6_r, "Convex Hyperplane Separation", "Linear SVM outperforms tree models in high-dimensional sparse text space by maximizing the separation margin between product classes.")
add_bullet_item(tf6_r, "Platt Sigmoid Calibration", "Applies sigmoid calibration P(y|f) = 1 / (1 + exp(A*f + B)) to convert raw margin distances into true posterior probabilities.")

print("Slide 6 generated.")

# ==========================================================
# SLIDE 7: Interpretable ML & Live Feature Attribution (Theme: Light)
# ==========================================================
slide7 = prs.slides.add_slide(blank_layout)
add_slide_background(slide7, is_dark=False)
add_header(slide7, "Model Explainability & Regulatory Compliance", "White-Box Interpretability & Live Decision Explainer", 
           "Eliminating the black-box adoption barrier through transparent token-level mathematical attribution", is_dark=False, slide_num="07 / 12")

c7_w = Inches(3.68)
c7_h = Inches(4.85)
c7_top = Inches(1.95)

# Card 1: Math Formulation
card7_1 = add_card(slide7, Inches(0.8), c7_top, c7_w, c7_h, is_dark=False)
tb7_1 = slide7.shapes.add_textbox(Inches(1.0), c7_top + Inches(0.2), c7_w - Inches(0.4), c7_h - Inches(0.4))
tf7_1 = tb7_1.text_frame
tf7_1.word_wrap = True
tf7_1.margin_left = tf7_1.margin_top = Inches(0)
p = tf7_1.paragraphs[0]
p.text = "1. MATHEMATICAL FORMULATION"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = INDIGO_PRIMARY

add_bullet_item(tf7_1, "Exact Linear Attribution", "The decision logit for class c is the direct dot product: z_c = b_c + SUM(w_{c,i} * x_i).")
add_bullet_item(tf7_1, "Word-Level Justification", "Every token in the complaint is scored individually: positive weights push toward the predicted class; negative weights penalize alternative categories.")
add_bullet_item(tf7_1, "Regulatory Transparency", "Compliance officers can present exact mathematical token weights during regulatory audits without resorting to heuristic approximations.")
add_bullet_item(tf7_1, "Zero Inference Overhead", "Because feature weights are pre-computed during model training, local explanations compute in less than 2 milliseconds.")

# Card 2: Domain Evidence
card7_2 = add_card(slide7, Inches(4.82), c7_top, c7_w, c7_h, is_dark=False)
tb7_2 = slide7.shapes.add_textbox(Inches(5.02), c7_top + Inches(0.2), c7_w - Inches(0.4), c7_h - Inches(0.4))
tf7_2 = tb7_2.text_frame
tf7_2.word_wrap = True
tf7_2.margin_left = tf7_2.margin_top = Inches(0)
p = tf7_2.paragraphs[0]
p.text = "2. DOMAIN FEATURE PATTERNS"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = CYAN_ACCENT

add_bullet_item(tf7_2, "Credit Reporting", "Dominant driving keywords: 'experian', 'equifax', 'transunion', 'credit report', 'inaccurate', 'score'.")
add_bullet_item(tf7_2, "Debt Collection", "Dominant driving keywords: 'harass', 'threaten', 'collector', 'debt validation', 'cease and desist', 'phone calls'.")
add_bullet_item(tf7_2, "Mortgages & Escrow", "Dominant driving keywords: 'escrow', 'foreclosure', 'loan servicer', 'modification', 'property deed'.")
add_bullet_item(tf7_2, "Credit Card Disputes", "Dominant driving keywords: 'unauthorized charge', 'late fee', 'billing dispute', 'fraudulent purchase', 'interest rate'.")

# Card 3: Live Sandbox
card7_3 = add_card(slide7, Inches(8.84), c7_top, c7_w, c7_h, is_dark=False)
tb7_3 = slide7.shapes.add_textbox(Inches(9.04), c7_top + Inches(0.2), c7_w - Inches(0.4), c7_h - Inches(0.4))
tf7_3 = tb7_3.text_frame
tf7_3.word_wrap = True
tf7_3.margin_left = tf7_3.margin_top = Inches(0)
p = tf7_3.paragraphs[0]
p.text = "3. INTERACTIVE TESTING SANDBOX"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = EMERALD_ACCENT

add_bullet_item(tf7_3, "Real-Time Classification UI", "Dedicated interactive prediction box allows analysts to paste customer emails, letters, or tickets for instant diagnosis.")
add_bullet_item(tf7_3, "Multi-Class Probability Distribution", "Visualizes normalized confidence bars across all 5 financial products simultaneously.")
add_bullet_item(tf7_3, "Top Influential Keywords", "Renders the top 5 positive feature keywords that exerted the greatest numerical influence on the classification outcome.")
add_bullet_item(tf7_3, "Sub-30ms Round-Trip", "Powered by an optimized FastAPI REST endpoint (/api/ml/predict) for instantaneous operational decision support.")

print("Slide 7 generated.")

# ==========================================================
# SLIDE 8: Unsupervised Discovery (Screenshot: ml.png)
# ==========================================================
slide8 = prs.slides.add_slide(blank_layout)
add_slide_background(slide8, is_dark=False)
add_header(slide8, "Unsupervised Discovery & Thematic Cohorts", "Latent Topic Extraction (NMF) & Document Clustering (K-Means)", 
           "Automatically surfacing emerging regulatory themes and consumer behavior cohorts without human labels", is_dark=False, slide_num="08 / 12")

card8_left = add_card(slide8, Inches(0.8), Inches(1.95), Inches(4.733), Inches(4.85), is_dark=False)
tb8_l = slide8.shapes.add_textbox(Inches(1.0), Inches(2.15), Inches(4.333), Inches(4.45))
tf8_l = tb8_l.text_frame
tf8_l.word_wrap = True
tf8_l.margin_left = tf8_l.margin_top = Inches(0)

p = tf8_l.paragraphs[0]
p.text = "UNSUPERVISED INSIGHT ENGINE"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = INDIGO_PRIMARY

add_bullet_item(tf8_l, "Non-Negative Matrix Factorization", "Decomposes the term-document matrix V (N x M) into non-negative factor matrices W (documents x topics) and H (topics x terms).")
add_bullet_item(tf8_l, "8 Latent Thematic Topics", "Automatically extracts distinct complaint archetypes without supervision: Credit Inaccuracies, Debt Collector Harassment, Mortgage Escrow, Card Fee Disputes, etc.")
add_bullet_item(tf8_l, "Intuitive Parts-Based Semantics", "Unlike LDA or SVD, non-negativity guarantees purely additive combinations, resulting in cleaner, interpretable topics for business teams.")
add_bullet_item(tf8_l, "K-Means Clustering (k=5)", "Optimized using silhouette score analysis to partition complaint narratives into distinct behavioral cohorts.")
add_bullet_item(tf8_l, "Surfacing Emerging Risks", "Identifies newly surging grievance themes before formal regulatory inquiries or class actions materialize.")

ml_img = os.path.join(SCREENSHOTS_DIR, "ml.png")
add_screenshot_container(slide8, ml_img, Inches(5.733), Inches(1.95), Inches(6.8), Inches(4.85), 
                         title="ML Intelligence: NMF Topics & Document Clustering", is_dark=False)

print("Slide 8 generated.")

# ==========================================================
# SLIDE 9: Time-Series Anomaly Detection Engine (Theme: Light)
# ==========================================================
slide9 = prs.slides.add_slide(blank_layout)
add_slide_background(slide9, is_dark=False)
add_header(slide9, "Surveillance Algorithms & Volume Spikes", "Seasonality-Adjusted Rolling MAD & Isolation Forest Engine", 
           "Dual-layer anomaly surveillance eliminating weekend false alarms and detecting operational complaint surges", is_dark=False, slide_num="09 / 12")

c9_w = Inches(3.68)
c9_h = Inches(4.85)
c9_top = Inches(1.95)

# Card 1: Rolling MAD
card9_1 = add_card(slide9, Inches(0.8), c9_top, c9_w, c9_h, is_dark=False)
tb9_1 = slide9.shapes.add_textbox(Inches(1.0), c9_top + Inches(0.2), c9_w - Inches(0.4), c9_h - Inches(0.4))
tf9_1 = tb9_1.text_frame
tf9_1.word_wrap = True
tf9_1.margin_left = tf9_1.margin_top = Inches(0)
p = tf9_1.paragraphs[0]
p.text = "1. DAY-OF-WEEK ROLLING MAD"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = INDIGO_PRIMARY

add_bullet_item(tf9_1, "The Weekend Seasonality Problem", "Complaint volume drops 70% every Saturday/Sunday. Standard 3-sigma Gaussian z-scores flag every Monday as an anomaly and miss severe weekend spikes.")
add_bullet_item(tf9_1, "DoW Partitioning (28 Days)", "ComplaintIQ evaluates volume relative to the median of the same day-of-week over a trailing 28-day window.")
add_bullet_item(tf9_1, "Robust Scale Estimator", "Formula: Modified Z = (x_t - Median_d) / (MAD_d * 1.4826). The median and MAD are immune to historical extreme outliers.")
add_bullet_item(tf9_1, "Zero Baseline Distortion", "Prior historical surge events do not artificially inflate future standard deviations, preserving detection sensitivity.")

# Card 2: Isolation Forest
card9_2 = add_card(slide9, Inches(4.82), c9_top, c9_w, c9_h, is_dark=False)
tb9_2 = slide9.shapes.add_textbox(Inches(5.02), c9_top + Inches(0.2), c9_w - Inches(0.4), c9_h - Inches(0.4))
tf9_2 = tb9_2.text_frame
tf9_2.word_wrap = True
tf9_2.margin_left = tf9_2.margin_top = Inches(0)
p = tf9_2.paragraphs[0]
p.text = "2. MULTIVARIATE ISOLATION FOREST"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = CYAN_ACCENT

add_bullet_item(tf9_2, "Multi-Dimensional Features", "Evaluates daily complaint count, 3-day volume acceleration (second derivative), and consumer dispute ratio simultaneously.")
add_bullet_item(tf9_2, "Ensemble of 100 Isolation Trees", "Partitions feature space with random axis-aligned splits; anomalies require fewer splits and isolate near root nodes.")
add_bullet_item(tf9_2, "Anomaly Score Formulation", "Computes average path length E(h(x)) normalized against average tree depth; scores above threshold indicate abnormal multi-variate events.")
add_bullet_item(tf9_2, "Non-Parametric Flexibility", "Detects complex non-linear combinations of velocity and dispute spikes without assuming Gaussian distributions.")

# Card 3: Tiered Severity
card9_3 = add_card(slide9, Inches(8.84), c9_top, c9_w, c9_h, is_dark=False)
tb9_3 = slide9.shapes.add_textbox(Inches(9.04), c9_top + Inches(0.2), c9_w - Inches(0.4), c9_h - Inches(0.4))
tf9_3 = tb9_3.text_frame
tf9_3.word_wrap = True
tf9_3.margin_left = tf9_3.margin_top = Inches(0)
p = tf9_3.paragraphs[0]
p.text = "3. TIERED SEVERITY MATRIX"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = ROSE_ACCENT

add_bullet_item(tf9_3, "INFO Severity (Z >= 2.0)", "Minor statistical elevation; recorded in surveillance ledger for trend monitoring without disturbing on-call staff.")
add_bullet_item(tf9_3, "WARNING Severity (Z >= 2.5)", "Actionable volume surge; notifies operations leads for queue prioritization and triage allocation.")
add_bullet_item(tf9_3, "CRITICAL Severity (Z >= 3.0)", "Severe systemic crisis (e.g. major gateway outage or billing failure); automatically triggers an incident alert ticket.")
add_bullet_item(tf9_3, "Operational Impact", "Successfully filtered out 100% of false weekend alerts in historical backtests while capturing all confirmed crisis spikes.")

print("Slide 9 generated.")

# ==========================================================
# SLIDE 10: Chronological Forecasting & Capacity Planning (Theme: Light)
# ==========================================================
slide10 = prs.slides.add_slide(blank_layout)
add_slide_background(slide10, is_dark=False)
add_header(slide10, "Predictive Modeling & Capacity Planning", "Damped Additive Holt-Winters Exponential Smoothing", 
           "Anticipating future complaint volumes to optimize compliance workforce staffing and safeguard regulatory SLAs", is_dark=False, slide_num="10 / 12")

c10_w = Inches(3.68)
c10_h = Inches(4.85)
c10_top = Inches(1.95)

# Card 1: Math Formulation
card10_1 = add_card(slide10, Inches(0.8), c10_top, c10_w, c10_h, is_dark=False)
tb10_1 = slide10.shapes.add_textbox(Inches(1.0), c10_top + Inches(0.2), c10_w - Inches(0.4), c10_h - Inches(0.4))
tf10_1 = tb10_1.text_frame
tf10_1.word_wrap = True
tf10_1.margin_left = tf10_1.margin_top = Inches(0)
p = tf10_1.paragraphs[0]
p.text = "1. TRIPLE EXPONENTIAL SMOOTHING"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = INDIGO_PRIMARY

add_bullet_item(tf10_1, "Level Smoothing (l_t)", "l_t = alpha * (x_t - s_{t-m}) + (1 - alpha) * (l_{t-1} + phi * b_{t-1}). Dynamically updates baseline volume.")
add_bullet_item(tf10_1, "Trend Smoothing (b_t)", "b_t = beta * (l_t - l_{t-1}) + (1 - beta) * phi * b_{t-1}. Captures directional trajectory over time.")
add_bullet_item(tf10_1, "Seasonality Smoothing (s_t)", "s_t = gamma * (x_t - l_{t-1} - phi * b_{t-1}) + (1 - gamma) * s_{t-m}. Models 7-day cyclical weekly volume patterns (m=7).")
add_bullet_item(tf10_1, "Trend Damping (phi = 0.90)", "Damps the linear trend component to prevent unrealistically steep forecasts over 14-day and 30-day horizons.")

# Card 2: Walk-Forward Validation
card10_2 = add_card(slide10, Inches(4.82), c10_top, c10_w, c10_h, is_dark=False)
tb10_2 = slide10.shapes.add_textbox(Inches(5.02), c10_top + Inches(0.2), c10_w - Inches(0.4), c10_h - Inches(0.4))
tf10_2 = tb10_2.text_frame
tf10_2.word_wrap = True
tf10_2.margin_left = tf10_2.margin_top = Inches(0)
p = tf10_2.paragraphs[0]
p.text = "2. WALK-FORWARD BACKTESTING"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = CYAN_ACCENT

add_bullet_item(tf10_2, "Strict Chronological Splits", "Evaluated using expanding-window backtesting; ensures zero future data leakage or lookahead bias.")
add_bullet_item(tf10_2, "Seasonal Naive Baseline", "7-Day Seasonal Naive benchmark achieved Mean Absolute Error (MAE) of 14.2 complaints/day.")
add_bullet_item(tf10_2, "Rolling Mean Baseline", "14-Day Rolling Mean benchmark achieved MAE of 12.8 complaints/day.")
add_bullet_item(tf10_2, "Damped Holt-Winters Result", "Achieved superior MAE of 8.6 and RMSE of 11.2, reducing forecast error by over 32% compared to baselines.")

# Card 3: Capacity Planning
card10_3 = add_card(slide10, Inches(8.84), c10_top, c10_w, c10_h, is_dark=False)
tb10_3 = slide10.shapes.add_textbox(Inches(9.04), c10_top + Inches(0.2), c10_w - Inches(0.4), c10_h - Inches(0.4))
tf10_3 = tb10_3.text_frame
tf10_3.word_wrap = True
tf10_3.margin_left = tf10_3.margin_top = Inches(0)
p = tf10_3.paragraphs[0]
p.text = "3. CAPACITY PLANNING IMPACT"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = EMERALD_ACCENT

add_bullet_item(tf10_3, "14-Day & 30-Day Projections", "Delivers daily expected complaint influx with 80% and 95% confidence bounds for risk management.")
add_bullet_item(tf10_3, "Workforce Staffing Alignment", "Enables operations managers to schedule complaint resolution officers based on expected weekly volume peaks.")
add_bullet_item(tf10_3, "SLA Breach Prevention", "Prevents regulatory response backlog before spikes happen, decreasing the risk of statutory fine violations.")
add_bullet_item(tf10_3, "Automated Re-training", "Pipeline periodically updates parameters to adapt to long-term macro trend shifts in complaint volume.")

print("Slide 10 generated.")

# ==========================================================
# SLIDE 11: Alert Center & Incident Workflow (Screenshot: alerts.png)
# ==========================================================
slide11 = prs.slides.add_slide(blank_layout)
add_slide_background(slide11, is_dark=False)
add_header(slide11, "Incident Response & Operational Triage", "Automated Incident Generation, Deduplication & Triage Workflow", 
           "Closing the loop between machine learning surge detection and human operational remediation", is_dark=False, slide_num="11 / 12")

alerts_img = os.path.join(SCREENSHOTS_DIR, "alerts.png")
add_screenshot_container(slide11, alerts_img, Inches(0.8), Inches(1.95), Inches(6.8), Inches(4.85), 
                         title="Alert Center: Incident Triage, Dedup & Resolution Ledger", is_dark=False)

card11_right = add_card(slide11, Inches(7.8), Inches(1.95), Inches(4.733), Inches(4.85), is_dark=False)
tb11_r = slide11.shapes.add_textbox(Inches(8.0), Inches(2.15), Inches(4.333), Inches(4.45))
tf11_r = tb11_r.text_frame
tf11_r.word_wrap = True
tf11_r.margin_left = tf11_r.margin_top = Inches(0)

p = tf11_r.paragraphs[0]
p.text = "INCIDENT LIFECYCLE MANAGEMENT"
p.font.name = FONT_NAME
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = INDIGO_PRIMARY

add_bullet_item(tf11_r, "Automated Incident Triggering", "Surge events exceeding z-score threshold automatically generate persistent incident records in SQLite database.")
add_bullet_item(tf11_r, "Deterministic Deduplication", "Generates unique deduplication key: hash(product, anomaly_type, date_bucket). Prevents alert storms and notification fatigue during multi-day surges.")
add_bullet_item(tf11_r, "Analyst State Lifecycle", "Strict operational state machine: NEW / TRIGGERED -> INVESTIGATING -> RESOLVED / ACKNOWLEDGED with real-time UI status toggles.")
add_bullet_item(tf11_r, "Root Cause Attribution", "Compliance officers record investigation findings and assign root cause tags (e.g. Core Banking Glitch, Policy Change, False Positive).")
add_bullet_item(tf11_r, "Immutable Audit Trail", "Maintains full timestamped audit logs of all analyst actions for regulatory review and SLA compliance tracking.")

print("Slide 11 generated.")

# ==========================================================
# SLIDE 12: Project Evaluation, Team & Future Scope (Theme: Dark Slate)
# ==========================================================
slide12 = prs.slides.add_slide(blank_layout)
add_slide_background(slide12, is_dark=True)
add_header(slide12, "Capstone Synthesis & Technical Impact", "ComplaintIQ: Outcomes, Team Contributions & Roadmap", 
           "Comprehensive evaluation of system achievements, individual contributions, and future architectural roadmap", is_dark=True, slide_num="12 / 12")

# Top Half: 4 Team Member Contribution Cards
c12_w = Inches(2.78)
c12_h = Inches(2.55)
c12_top = Inches(1.95)

team_contributions = [
    {
        "name": "Aryan Turalkar",
        "roll": "Roll No: A152",
        "role": "NLP & Classification Lead",
        "work": [
            "Engineered sublinear TF-IDF vectorization with 10k unigrams/bigrams.",
            "Trained LinearSVC achieving 89.6% classification accuracy.",
            "Implemented Platt scaling for calibrated probabilities.",
            "Formulated linear feature attribution (w_i * x_i) for white-box interpretability."
        ]
    },
    {
        "name": "Suryansh Saraf",
        "roll": "Roll No: A-125",
        "role": "Full-Stack System Architect",
        "work": [
            "Architected full-stack React 18, TypeScript & TailwindCSS Command Center.",
            "Developed FastAPI asynchronous backend with SQLite database.",
            "Built Complaint Explorer with debounced search & smart presets.",
            "Configured Cloudflare Tunnel for secure global deployment."
        ]
    },
    {
        "name": "Soham Hande",
        "roll": "Roll No: A-129",
        "role": "Anomaly Detection Engineer",
        "work": [
            "Designed Day-of-Week normalized Rolling MAD algorithm.",
            "Integrated multivariate Isolation Forest ensemble (100 trees).",
            "Eliminated 100% of false weekend alerts in historical backtesting.",
            "Established multi-tier severity thresholds (Info, Warning, Critical)."
        ]
    },
    {
        "name": "Pratham Deepak",
        "roll": "Roll No: A-114",
        "role": "Time-Series & Operations Lead",
        "work": [
            "Implemented Additive Damped Holt-Winters exponential smoothing.",
            "Conducted walk-forward backtesting showing 32% error reduction.",
            "Architected Alert Center state machine and deduplication engine.",
            "Built incident resolution logging and SLA compliance tracking."
        ]
    }
]

for i, tc in enumerate(team_contributions):
    c_left = Inches(0.8) + i * Inches(2.98)
    card = add_card(slide12, c_left, c12_top, c12_w, c12_h, is_dark=True, border_color=INDIGO_PRIMARY)
    
    tb = slide12.shapes.add_textbox(c_left + Inches(0.16), c12_top + Inches(0.14), c12_w - Inches(0.32), c12_h - Inches(0.28))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = Inches(0)
    
    p1 = tf.paragraphs[0]
    p1.text = tc["name"]
    p1.font.name = FONT_NAME
    p1.font.size = Pt(12)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)
    
    p2 = tf.add_paragraph()
    p2.text = f"{tc['roll']}  •  {tc['role']}"
    p2.font.name = FONT_NAME
    p2.font.size = Pt(8.5)
    p2.font.bold = True
    p2.font.color.rgb = CYAN_ACCENT
    p2.space_before = Pt(2)
    
    for bullet in tc["work"]:
        pb = tf.add_paragraph()
        pb.space_before = Pt(3)
        run_b = pb.add_run()
        run_b.text = "• "
        run_b.font.bold = True
        run_b.font.color.rgb = INDIGO_LIGHT
        run_t = pb.add_run()
        run_t.text = bullet
        run_t.font.name = FONT_NAME
        run_t.font.size = Pt(8.5)
        run_t.font.color.rgb = TEXT_LIGHT_MUTED

# Bottom Half: Two Wide Summary Cards
bottom_w = Inches(5.76)
bottom_h = Inches(2.15)
bottom_top = Inches(4.7)

# Card 1: Key Performance Metrics
card_res = add_card(slide12, Inches(0.8), bottom_top, bottom_w, bottom_h, is_dark=True, border_color=EMERALD_ACCENT)
tb_res = slide12.shapes.add_textbox(Inches(1.0), bottom_top + Inches(0.15), bottom_w - Inches(0.4), bottom_h - Inches(0.3))
tf_res = tb_res.text_frame
tf_res.word_wrap = True
tf_res.margin_left = tf_res.margin_top = Inches(0)
p = tf_res.paragraphs[0]
p.text = "KEY QUANTITATIVE ACCOMPLISHMENTS"
p.font.name = FONT_NAME
p.font.size = Pt(10.5)
p.font.bold = True
p.font.color.rgb = EMERALD_ACCENT

add_bullet_item(tf_res, "89.6% Classification Accuracy", "Calibrated Linear SVM outperforms traditional Naive Bayes and Logistic Regression baselines.", is_dark=True, space_before=Pt(4))
add_bullet_item(tf_res, "Sub-45ms p95 API Latency", "High-throughput asynchronous FastAPI architecture enabling real-time production triage.", is_dark=True, space_before=Pt(3))
add_bullet_item(tf_res, "Zero Weekend False Positives", "Day-of-Week normalized Rolling MAD successfully eliminates weekend seasonal bias.", is_dark=True, space_before=Pt(3))
add_bullet_item(tf_res, "32% Forecast Error Reduction", "Damped Holt-Winters beats standard 7-day seasonal naive and rolling average baselines.", is_dark=True, space_before=Pt(3))

# Card 2: Future Roadmap & Next Steps
card_road = add_card(slide12, Inches(6.77), bottom_top, bottom_w, bottom_h, is_dark=True, border_color=CYAN_ACCENT)
tb_road = slide12.shapes.add_textbox(Inches(6.97), bottom_top + Inches(0.15), bottom_w - Inches(0.4), bottom_h - Inches(0.3))
tf_road = tb_road.text_frame
tf_road.word_wrap = True
tf_road.margin_left = tf_road.margin_top = Inches(0)
p = tf_road.paragraphs[0]
p.text = "FUTURE ROADMAP & PRODUCTION EXTENSIONS"
p.font.name = FONT_NAME
p.font.size = Pt(10.5)
p.font.bold = True
p.font.color.rgb = CYAN_ACCENT

add_bullet_item(tf_road, "Generative LLM Auto-Drafting", "Fine-tuned LLM agents to draft legally compliant initial response letters for analyst review.", is_dark=True, space_before=Pt(4))
add_bullet_item(tf_road, "Distributed Stream Ingestion", "Integrate Apache Kafka and Redis Streams for high-velocity multi-million message streaming.", is_dark=True, space_before=Pt(3))
add_bullet_item(tf_road, "Multilingual NLP Embeddings", "Incorporate multilingual transformer embeddings to support Spanish and international complaints.", is_dark=True, space_before=Pt(3))
add_bullet_item(tf_road, "Automated Model Drift Monitoring", "Continuous Kolmogorov-Smirnov test tracking covariate shift in customer complaint vocabularies.", is_dark=True, space_before=Pt(3))

# Final Q&A Banner
tb_qa = slide12.shapes.add_textbox(Inches(0.8), Inches(7.0), Inches(11.733), Inches(0.35))
tf_qa = tb_qa.text_frame
p_qa = tf_qa.paragraphs[0]
p_qa.text = "THANK YOU  •  QUESTIONS & DISCUSSION  •  COMPLAINTIQ ACADEMIC CAPSTONE PRESENTATION"
p_qa.alignment = PP_ALIGN.CENTER
p_qa.font.name = FONT_NAME
p_qa.font.size = Pt(9.5)
p_qa.font.bold = True
p_qa.font.color.rgb = INDIGO_LIGHT

print("Slide 12 generated.")

# ==========================================================
# SAVE PRESENTATION
# ==========================================================
prs.save(OUTPUT_PATH)
file_size_kb = os.path.getsize(OUTPUT_PATH) / 1024
print(f"\n=======================================================")
print(f"Presentation successfully created at: {OUTPUT_PATH}")
print(f"Total Slides: {len(prs.slides)}")
print(f"File Size: {file_size_kb:.2f} KB ({file_size_kb / 1024:.2f} MB)")
print(f"=======================================================")
