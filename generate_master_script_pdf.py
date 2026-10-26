import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT

OUTPUT_PDF = "/Users/sunilsaraf/.gemini/antigravity/scratch/ComplaintIQ/ComplaintIQ_Master_Presentation_Script.pdf"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        # Running Top Header (Pages 2+)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#475569"))
            self.drawString(40, 810, "ComplaintIQ — Autonomous Financial Grievance Intelligence & Forecasting")
            self.setFont("Helvetica", 8)
            self.drawRightString(A4[0] - 40, 810, "Course Code: 702AI0C009 (NLP Sem VII)")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(40, 804, A4[0] - 40, 804)

        # Running Bottom Footer
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(40, 25, "Mukesh Patel School of Technology Management & Engineering (MPSTME) | SVKM's NMIMS")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 40, 25, page_text)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(40, 35, A4[0] - 40, 35)
        self.restoreState()

def create_callout(text, title="IMPORTANT KEY POINT", bg_color="#EEF2FF", border_color="#4F46E5", title_color="#3730A3"):
    styles = getSampleStyleSheet()
    title_p = Paragraph(f"<b>{title.upper()}</b>", ParagraphStyle(
        'CalloutTitle', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor(title_color), leading=12
    ))
    body_p = Paragraph(text, ParagraphStyle(
        'CalloutBody', fontName='Helvetica', fontSize=8.5, textColor=colors.HexColor("#1E293B"), leading=12
    ))
    t = Table([[title_p], [body_p]], colWidths=[A4[0] - 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor(border_color)),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    return t

def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()
    
    # Custom Typographic Hierarchy
    style_main_title = ParagraphStyle(
        'MainTitle', fontName='Helvetica-Bold', fontSize=22, leading=26,
        textColor=colors.HexColor("#0F172A"), alignment=TA_CENTER
    )
    style_sub_title = ParagraphStyle(
        'SubTitle', fontName='Helvetica-Bold', fontSize=12, leading=16,
        textColor=colors.HexColor("#4F46E5"), alignment=TA_CENTER
    )
    style_meta_header = ParagraphStyle(
        'MetaHeader', fontName='Helvetica', fontSize=8.5, leading=12,
        textColor=colors.HexColor("#475569"), alignment=TA_CENTER
    )
    style_h1 = ParagraphStyle(
        'H1', fontName='Helvetica-Bold', fontSize=14, leading=18,
        textColor=colors.HexColor("#0F172A"), spaceBefore=14, spaceAfter=6, keepWithNext=True
    )
    style_h2 = ParagraphStyle(
        'H2', fontName='Helvetica-Bold', fontSize=11, leading=15,
        textColor=colors.HexColor("#1E293B"), spaceBefore=10, spaceAfter=4, keepWithNext=True
    )
    style_h3 = ParagraphStyle(
        'H3', fontName='Helvetica-Bold', fontSize=9.5, leading=13,
        textColor=colors.HexColor("#334155"), spaceBefore=6, spaceAfter=3, keepWithNext=True
    )
    style_body = ParagraphStyle(
        'Body', fontName='Helvetica', fontSize=8.5, leading=12,
        textColor=colors.HexColor("#1E293B"), spaceAfter=5, alignment=TA_JUSTIFY
    )
    style_spoken = ParagraphStyle(
        'Spoken', fontName='Helvetica-Oblique', fontSize=8.5, leading=12.5,
        textColor=colors.HexColor("#0F172A"), spaceAfter=5
    )
    style_action = ParagraphStyle(
        'Action', fontName='Helvetica-Bold', fontSize=8.5, leading=12,
        textColor=colors.HexColor("#B45309")
    )
    style_code = ParagraphStyle(
        'Code', fontName='Courier', fontSize=8, leading=10.5,
        textColor=colors.HexColor("#0F172A")
    )
    style_table_head = ParagraphStyle(
        'TableHead', fontName='Helvetica-Bold', fontSize=8, leading=10,
        textColor=colors.white, alignment=TA_CENTER
    )
    style_table_cell = ParagraphStyle(
        'TableCell', fontName='Helvetica', fontSize=7.5, leading=9.5,
        textColor=colors.HexColor("#1E293B")
    )
    style_table_cell_bold = ParagraphStyle(
        'TableCellBold', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5,
        textColor=colors.HexColor("#0F172A")
    )

    story = []

    # =========================================================================
    # COVER / HEADER BLOCK
    # =========================================================================
    story.append(Paragraph("SVKM'S NMIMS — MUKESH PATEL SCHOOL OF TECHNOLOGY MANAGEMENT & ENGINEERING", style_meta_header))
    story.append(Paragraph("Department of Artificial Intelligence & Data Science | Sem VII (Academic Year 2026–2027)", style_meta_header))
    story.append(Paragraph("Course Name & Code: Natural Language Processing (702AI0C009)", style_meta_header))
    story.append(Spacer(1, 8))
    story.append(Paragraph("ComplaintIQ: Complete Master Presentation Script & Course Policy Defense", style_main_title))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Autonomous Financial Grievance Intelligence, Anomaly Detection & Time-Series Forecasting Platform", style_sub_title))
    story.append(Spacer(1, 10))

    # Team Members & Faculty Info Table
    team_data = [
        [
            Paragraph("<b>Candidate Name</b>", style_table_head),
            Paragraph("<b>Roll Number</b>", style_table_head),
            Paragraph("<b>SAP ID</b>", style_table_head),
            Paragraph("<b>Core Project Responsibility</b>", style_table_head)
        ],
        [
            Paragraph("<b>Aryan Turalkar</b>", style_table_cell_bold),
            Paragraph("A152", style_table_cell),
            Paragraph("70562300045", style_table_cell),
            Paragraph("NLP Feature Pipeline, Calibrated Linear SVM, Platt Scaling & Token Attribution", style_table_cell)
        ],
        [
            Paragraph("<b>Suryansh Saraf</b>", style_table_cell_bold),
            Paragraph("A125", style_table_cell),
            Paragraph("70562300034", style_table_cell),
            Paragraph("Full-Stack Architecture, React 18 / Tailwind Dashboard & FastAPI Microservices", style_table_cell)
        ],
        [
            Paragraph("<b>Soham Hande</b>", style_table_cell_bold),
            Paragraph("A129", style_table_cell),
            Paragraph("70562300062", style_table_cell),
            Paragraph("Seasonality-Aware Rolling MAD Anomaly Engine, Isolation Forest & NMF Topics", style_table_cell)
        ],
        [
            Paragraph("<b>Pratham Deepak</b>", style_table_cell_bold),
            Paragraph("A114", style_table_cell),
            Paragraph("70562300078", style_table_cell),
            Paragraph("Damped Additive Holt-Winters Forecasting, Alert Deduplication & State Machine", style_table_cell)
        ],
    ]
    t_team = Table(team_data, colWidths=[120, 65, 80, 250])
    t_team.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_team)
    story.append(Spacer(1, 8))

    exec_summary_text = (
        "<b>Executive Summary & Platform State:</b> ComplaintIQ is a production-grade NLP and time-series decision "
        "support system operating over <b>6,924 real-world banking and financial complaints</b> across 8 core product "
        "verticals. It couples sublinear TF-IDF representation and Calibrated Linear SVM (<b>98.7% accuracy, 0.985 F1</b>) "
        "with white-box token-level feature attribution ($w_i \\cdot x_i$), unsupervised Non-Negative Matrix Factorization (NMF, $k=8$), "
        "a Day-of-Week normalized Rolling Median Absolute Deviation (MAD) anomaly detector that eliminates 100% of weekend "
        "false alarms, and a Damped Holt-Winters forecasting engine yielding a 32% error reduction over seasonal baselines. "
        "This master script is your comprehensive reference guide for conducting the live web application walkthrough, "
        "defending academic Course Policy alignment, and acing the faculty cross-examination."
    )
    story.append(create_callout(exec_summary_text, title="PROJECT BRIEF & EXECUTIVE SUMMARY", bg_color="#F1F5F9", border_color="#94A3B8", title_color="#0F172A"))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 1: SETUP & TIMELINE
    # =========================================================================
    story.append(Paragraph("1. Live Presentation Setup, Timing & Protocol", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=6))
    
    setup_p = (
        "<b>Pre-Presentation Setup Checklist:</b><br/>"
        "• <b>Active URLs:</b> Open <code>http://localhost:5173</code> in Google Chrome or Safari in <b>Full Screen Mode</b>. "
        "Ensure the backend is healthy on <code>http://localhost:8001/api/health</code> (returning 6,924 complaints).<br/>"
        "• <b>Clipboard Buffer:</b> Have this test string pre-copied in case you need to paste manually: "
        "<code>I noticed an unauthorized charge of $450 from an unknown foreign merchant on my credit card that I never made.</code><br/>"
        "• <b>Pacing Allocation:</b> Total presentation time is 10 to 12 minutes, structured as: "
        "Home Command Center (2 min) $\\to$ Live AI Prediction Demo (2 min) $\\to$ Complaint Explorer (1.5 min) $\\to$ "
        "NLP Intelligence (1.5 min) $\\to$ ML Intelligence & Topics (1.5 min) $\\to$ Alert Center (1 min) $\\to$ "
        "Conclusion & Team Roles (1 min) $\\to$ Faculty Viva Cross-Examination (3–5 min)."
    )
    story.append(Paragraph(setup_p, style_body))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 2: WORD-FOR-WORD SPEAKING SCRIPT
    # =========================================================================
    story.append(Paragraph("2. Complete Word-for-Word Live-Frontend Speaking Script", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=6))

    script_intro = (
        "The following script is designed for live screen-sharing. As you speak, follow the exact <b>[Action]</b> cues "
        "with your mouse cursor and clicks. Deliver the text in a natural, authoritative tone."
    )
    story.append(Paragraph(script_intro, style_body))
    story.append(Spacer(1, 6))

    # Step 1
    story.append(Paragraph("Step 1: Opening & Banking Domain Motivation [0:00 – 1:45]", style_h2))
    story.append(Paragraph("<b>[Screen Position]:</b> Home Command Center (<code>http://localhost:5173/</code>) in full screen. Mouse hovering over header badge.", style_action))
    s1_text = (
        "\"Respected faculty members, good morning / afternoon. Today, rather than flipping through static presentation slides, "
        "our team will demonstrate our fully functional capstone platform live directly from the running web browser.<br/><br/>"
        "Our project is <b>ComplaintIQ</b> — an Autonomous Financial Grievance Intelligence, Anomaly Detection & Time-Series Forecasting Platform.<br/>"
        "My team members are <b>Aryan Turalkar (A152)</b>, <b>Soham Hande (A-129)</b>, <b>Pratham Deepak (A-114)</b>, and myself, <b>Suryansh Saraf (A-125)</b>.<br/><br/>"
        "<b>The Problem We Solved:</b> In modern retail and commercial banking, institutions receive thousands of grievances daily across "
        "Credit Cards, Savings Accounts, Home Mortgages, UPI & Net Banking, and Loans. In standard operations, human triage takes between "
        "<b>24 to 72 hours per record</b>, delaying critical fraud containment and risking statutory penalties from regulatory bodies like the RBI and CFPB. "
        "Furthermore, when systemic failures occur—such as an automated overdraft batch glitch or a regional UPI switch outage—operations teams only "
        "detect them days later because complaint volume drops 70% over weekends, blinding naive monitoring tools.<br/><br/>"
        "To solve this, we engineered an end-to-end intelligence system operating over <b>6,924 real-world banking complaints</b>, powered by "
        "FastAPI, React 18, TypeScript, TailwindCSS, Scikit-Learn, and SQLite.\""
    )
    story.append(Paragraph(s1_text, style_spoken))
    story.append(Spacer(1, 6))

    # Step 2
    story.append(Paragraph("Step 2: Executive KPI Ribbon & 30-Day Volume Trajectory [1:45 – 3:15]", style_h2))
    story.append(Paragraph("<b>[Action]:</b> Hover over the 4 Top KPI cards, then hover over the Recharts volume trend chart. Toggle 'Weekly', then switch back to 'Daily'. Point cursor to red circular anomaly markers.", style_action))
    s2_text = (
        "\"Here on the <b>Home Command Center</b>, operations managers obtain real-time situational awareness:<br/>"
        "• <b>Inbound Volume:</b> Tracks active complaint volume across our 6,924 corpus and percentage change versus the historical baseline.<br/>"
        "• <b>Negative Sentiment Rate:</b> Real-time proportion of grievances expressing customer frustration or escalation threats.<br/>"
        "• <b>Average Sentiment Score:</b> Bounded continuously on a calibrated -1.0 to +1.0 scale.<br/>"
        "• <b>Active Warnings:</b> Displays currently flagged anomaly incidents requiring operational attention.<br/><br/>"
        "Right below is our <b>Interactive Volume Trajectory</b> built using Recharts. It plots daily customer complaint volume against "
        "moving averages. Notice these highlighted circular red markers: these are <b>not</b> random daily variances. Our backend statistical "
        "anomaly engine identified them as abnormal volume surges where complaint velocity significantly exceeded seasonal weekday thresholds. "
        "If an operations lead clicks on any spike, the system automatically cross-filters the underlying complaints in the Explorer for immediate investigation.\""
    )
    story.append(Paragraph(s2_text, style_spoken))
    story.append(Spacer(1, 6))

    # Step 3
    story.append(Paragraph("Step 3: The Showstopper — Live AI Classifier & Feature Attribution [3:15 – 5:00]", style_h2))
    story.append(Paragraph("<b>[Action]:</b> On the right-side card, click the sample chip '💳 Unauthorized Card Charge'. The text auto-populates. Click 'Analyze Complaint'. Point to the result appearing in under 20 milliseconds.", style_action))
    s3_text = (
        "\"Now, let us demonstrate our live model inference in real time. In this <b>Live AI Classifier Box</b>, an operations officer can test "
        "any customer dispute letter, email, or chatbot escalation.<br/>"
        "<i>[Click Analyze Complaint]</i><br/>"
        "In <b>under 20 milliseconds</b>, the FastAPI backend executes our sublinear TF-IDF pipeline:<br/>"
        "1. <b>Classification Output:</b> It classified this complaint as <b>'Unauthorized Fraud'</b> with <b>99.9% Calibrated Confidence</b>.<br/>"
        "2. <b>Probability Distribution:</b> Below, you see normalized posterior probabilities across all 8 banking categories: Billing & Fees, "
        "Loan & Mortgage, Transaction Failure, Account & KYC, Credit Reporting, etc.<br/>"
        "3. <b>Mathematical Token Attribution:</b> Look at these weight badges below: <code>unauthorized (+0.24)</code>, <code>never made (+0.21)</code>, <code>unauthorized charge (+0.21)</code>.<br/><br/>"
        "<b>Why is this critical for regulatory compliance?</b> Banking compliance officers strictly reject black-box deep learning models "
        "where you cannot justify why an automated classification occurred. Our model computes exact linear feature attribution: "
        "<b>z_c = b_c + SUM(w_{c,i} * x_i)</b>. Every word is scored individually based on its trained linear hyperplane coefficient w_{c,i} "
        "and TF-IDF feature weight x_i, providing auditable mathematical proof for regulatory compliance.\""
    )
    story.append(Paragraph(s3_text, style_spoken))
    story.append(Spacer(1, 6))

    # Step 4
    story.append(Paragraph("Step 4: Complaint Explorer & Slide-Out Audit Drawer [5:00 – 6:30]", style_h2))
    story.append(Paragraph("<b>[Action]:</b> Click 'Complaint Explorer' in top navbar. Click preset pill '⚡ UPI & Transaction Outage'. In search box, type 'escrow'. Click any row to open the slide-out drawer.", style_action))
    s4_text = (
        "\"Next is the <b>Complaint Explorer</b>, designed for compliance officers handling dispute audits.<br/>"
        "• <b>One-Click Analytical Presets:</b> With a single tap, an auditor can isolate 'UPI & Transaction Outage' (failed transfers), "
        "'ATM Skimming & Fraud' (compromised cards), or 'Overdraft / Double-Debit' (billing calculation errors).<br/>"
        "• <b>Sub-10ms Debounced Search:</b> Notice that as I type 'escrow', our sub-10 millisecond debounced full-text search filters across "
        "all 6,924 complaint records in real time with zero UI lag.<br/>"
        "• <b>Slide-Out Inspection Drawer:</b> Clicking any complaint record opens our Slide-Out Inspection Drawer. Without losing search context, "
        "an auditor can examine the customer's verbatim narrative, product vertical (Home Mortgage, Credit Card, Savings Account), "
        "submission channel (Mobile App, Net Banking, Branch, Ombudsman), and model-assigned dispute tags.\""
    )
    story.append(Paragraph(s4_text, style_spoken))
    story.append(Spacer(1, 6))

    # Step 5
    story.append(Paragraph("Step 5: NLP Intelligence — Model Benchmarks, Calibration & ECE [6:30 – 8:00]", style_h2))
    story.append(Paragraph("<b>[Action]:</b> Click 'NLP Intelligence' in top navbar. Point to the Model Comparison Table, highlighting Linear SVM vs Logistic Regression vs Baseline. Scroll to Confusion Matrix and Per-Class metrics.", style_action))
    s5_text = (
        "\"Under the <b>NLP Intelligence</b> tab, we present our supervised model evaluation on held-out test splits:<br/>"
        "• <b>Benchmark Comparison:</b> We benchmarked multiple classifiers on sublinear TF-IDF features: Majority Baseline scored ~18.5%, "
        "Logistic Regression reached ~92.4%, and our <b>Calibrated Linear Support Vector Machine achieved 98.7% Accuracy and 0.985 Macro F1 score</b>.<br/>"
        "• <b>Why Linear SVM over Deep Neural Networks?</b> In text classification with a 10,000-feature unigram/bigram vocabulary, the data space is "
        "high-dimensional and sparse. SVM's convex hyperplane margin maximization provides superior separation compared to tree models, while executing "
        "inference in under 2 milliseconds on standard CPU hardware with zero GPU dependency.<br/>"
        "• <b>Platt Sigmoid Calibration & ECE:</b> Notice the <b>ECE (Expected Calibration Error)</b> column. A standard SVM outputs uncalibrated "
        "geometric distances from the hyperplane. We applied Platt Scaling—fitting a cross-validated logistic sigmoid—guaranteeing that an output "
        "confidence of 95% represents a true 95% empirical probability.<br/>"
        "• <b>Confusion Matrix & Influential Terms:</b> Below, the confusion matrix heatmap confirms near-perfect diagonal concentration across all 8 classes, "
        "while the Influential Terms section displays the top learned positive coefficients for each banking category.\""
    )
    story.append(Paragraph(s5_text, style_spoken))
    story.append(Spacer(1, 6))

    # Step 6
    story.append(Paragraph("Step 6: ML Intelligence — Topics, Rolling MAD & Holt-Winters [8:00 – 9:45]", style_h2))
    story.append(Paragraph("<b>[Action]:</b> Click 'ML Intelligence' in top navbar. In 'Clustering' tab, show 2D PCA cluster map and silhouette table. Switch to 'Anomalies' tab. Switch to 'Forecasting' tab and toggle 7/14/30 day horizon.", style_action))
    s6_text = (
        "\"Now we move to <b>ML Intelligence</b>, which houses our unsupervised discovery and time-series algorithms:<br/>"
        "1. <b>Unsupervised Latent Topics (Tab 1):</b> Supervised learning only categorizes known classes. Using <b>Non-Negative Matrix Factorization (NMF, k=8)</b> "
        "and <b>K-Means Clustering (k=5)</b>, the system automatically extracts emerging complaint themes—like ATM skimming surges or escrow tax delays—without "
        "needing human labels. We scanned k from 3 to 8, choosing k=5 by maximizing the silhouette coefficient, and mapped them in 2D using PCA.<br/>"
        "2. <b>Seasonality-Adjusted Anomaly Detection (Tab 2):</b> In banking, complaint volume drops by 70% every Saturday and Sunday. A standard 3-sigma "
        "Gaussian test triggers false alarms every Monday and misses real weekend spikes. We formulated a <b>Day-of-Week Normalized Rolling MAD Algorithm</b>: "
        "we compute the median and Median Absolute Deviation over a 28-day window partitioned by day-of-week. Because median and MAD have a 50% breakdown point, "
        "historical surges do not corrupt the baseline, eliminating 100% of weekend false alarms.<br/>"
        "3. <b>Capacity Planning via Damped Holt-Winters (Tab 3):</b> To prevent regulatory SLA breaches, we forecast incoming complaint volume 14 to 30 days "
        "in advance using Additive Damped Holt-Winters Exponential Smoothing. It tracks level (l_t), trend (b_t), and 7-day cyclical weekly seasonality (s_t), "
        "with a damping parameter phi = 0.90 to prevent linear runaway projections. Evaluated using expanding-window chronological backtesting, it reduced "
        "forecasting error by over 32% compared to standard baselines.\""
    )
    story.append(Paragraph(s6_text, style_spoken))
    story.append(Spacer(1, 6))

    # Step 7
    story.append(Paragraph("Step 7: Alert Center & Incident Deduplication [9:45 – 10:45]", style_h2))
    story.append(Paragraph("<b>[Action]:</b> Click 'Alert Center' in top navbar. Point to active alerts and priority badges. Toggle status from 'TRIGGERED' -> 'INVESTIGATING' -> 'RESOLVED'. Point to root-cause investigation notes.", style_action))
    s7_text = (
        "\"Our final operational module is the <b>Alert Center</b>. In real production monitoring, anomaly detectors suffer from <b>Alert Fatigue</b>: "
        "a multi-day system outage floods teams with hundreds of duplicate tickets.<br/>"
        "To prevent this, we engineered <b>Deterministic Deduplication Keying</b>: <code>hash(product, anomaly_type, date_bucket)</code>. "
        "When a spike persists, it updates the existing incident timeline instead of spamming analysts with new alerts.<br/>"
        "Analysts follow an auditable state machine: <b>TRIGGERED -> INVESTIGATING -> RESOLVED</b>. Analysts can record investigation notes and tag "
        "verified root causes (such as 'Core Banking Firmware Upgrade' or 'UPI Switch Timeout'), creating an immutable audit trail stored in SQLite "
        "for regulatory review.\""
    )
    story.append(Paragraph(s7_text, style_spoken))
    story.append(Spacer(1, 6))

    # Step 8
    story.append(Paragraph("Step 8: Conclusion & Individual Team Contributions [10:45 – 11:30]", style_h2))
    story.append(Paragraph("<b>[Action]:</b> Navigate back to Home Command Center. Summarize outcomes cleanly and open for questions.", style_action))
    s8_text = (
        "\"To conclude our presentation:<br/>"
        "• <b>98.7% classification accuracy</b> across 8 banking verticals with calibrated probabilities and token attribution.<br/>"
        "• <b>Sub-20ms API latency</b> using an asynchronous FastAPI architecture.<br/>"
        "• <b>Zero false positive weekend alerts</b> using Day-of-Week normalized Rolling MAD.<br/>"
        "• <b>32% forecast error reduction</b> via Damped Holt-Winters exponential smoothing.<br/><br/>"
        "<b>Individual Team Contributions:</b><br/>"
        "• <b>Aryan Turalkar (A152):</b> Designed NLP preprocessing, sublinear TF-IDF vectorization, LinearSVM training, Platt scaling calibration, and feature attribution.<br/>"
        "• <b>Suryansh Saraf (A-125):</b> Architected the full-stack system, designed the React 18 / Tailwind Command Center, built the FastAPI REST services, and set up deployment.<br/>"
        "• <b>Soham Hande (A-129):</b> Formulated the Day-of-Week Rolling MAD algorithm, integrated the multivariate Isolation Forest ensemble, and conducted NMF latent topic modeling.<br/>"
        "• <b>Pratham Deepak (A-114):</b> Implemented the Damped Holt-Winters time-series model, expanding-window walk-forward backtesting, and built the Alert Center deduplication lifecycle.<br/><br/>"
        "Thank you, professors. We are now open for your questions and discussion.\""
    )
    story.append(Paragraph(s8_text, style_spoken))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 3: COURSE POLICY ALIGNMENT
    # =========================================================================
    story.append(Paragraph("3. Course Policy (702AI0C009) Curriculum Mapping & Theory Deep-Dive", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=6))

    cp_intro = (
        "The Natural Language Processing course policy (702AI0C009) at MPSTME specifies 4 Course Outcomes (CO1–CO4), "
        "7 Theory Units, and 10 Lab Experiments. ComplaintIQ addresses all course outcomes with rigorous mathematical implementations:"
    )
    story.append(Paragraph(cp_intro, style_body))
    story.append(Spacer(1, 6))

    # Unit breakdown cards
    u1 = (
        "<b>CO1 / Unit 1 & 2: Text Preprocessing & Negation Preservation (Exp 1, 2)</b><br/>"
        "• <b>Contraction Expansion & Cleaning:</b> Regular expressions expand contractions (<code>won't</code> $\\to$ <code>will not</code>, "
        "<code>cannot</code> $\\to$ <code>can not</code>) and strip non-alphabetic noise while preserving word boundaries.<br/>"
        "• <b>The Negation Preservation Trick:</b> Standard stopwords (NLTK) blindly discard words like <code>not</code>, <code>no</code>, "
        "<code>never</code>, <code>without</code>. In banking complaints, discarding negations inverts sentence polarity (e.g., 'cash <b>not</b> dispensed' "
        "becomes 'cash dispensed'). ComplaintIQ explicitly isolates negations in a protected set, allowing them to bind to adjacent verbs in bigrams."
    )
    story.append(Paragraph(u1, style_body))
    story.append(Spacer(1, 4))

    u2 = (
        "<b>CO2 / Unit 2 & 3: Sublinear TF-IDF & (1,2)-Gram Language Modeling (Exp 3, 5)</b><br/>"
        "• <b>Mathematical Formulation:</b> Feature representation utilizes sublinear term frequency: "
        "<b>tf_{sublinear} = 1 + log(tf)</b> for tf > 0, multiplied by Inverse Document Frequency <b>idf(t) = log((1 + n) / (1 + df(t))) + 1</b>.<br/>"
        "• <b>N-Gram Vocabulary:</b> Extracts unigrams and bigrams (e.g., <code>unauthorized charge</code>, <code>late fee</code>, <code>minimum balance</code>), "
        "capturing critical compound expressions up to 10,000 dimensions with sublinear scaling to prevent repetitive legal boilerplate from dominating vectors."
    )
    story.append(Paragraph(u2, style_body))
    story.append(Spacer(1, 4))

    u3 = (
        "<b>CO2 / Unit 4: Syntax Level Analysis & Linear Feature Attribution (Exp 6, 7)</b><br/>"
        "• <b>Decision Logit Equation:</b> Local feature attribution for class c is computed as: "
        "<b>z_c = b_c + SUM(w_{c,i} * x_i)</b>, where w_{c,i} is the learned hyperplane weight and x_i is the TF-IDF feature value.<br/>"
        "• <b>White-Box Auditability:</b> Every token's contribution is isolated: positive weights provide affirmative evidence, while negative weights penalize "
        "alternative categories. Pre-computed weights allow local explanations in under 2ms without slow surrogate approximations like LIME or SHAP."
    )
    story.append(Paragraph(u3, style_body))
    story.append(Spacer(1, 4))

    u4 = (
        "<b>CO3 / Unit 5: Semantic Analysis, Latent Topics & Clustering (Exp 4, 8, 9)</b><br/>"
        "• <b>Non-Negative Matrix Factorization (NMF, k=8):</b> Decomposes term-document matrix <b>V_{N x M} approx W_{N x K} * H_{K x M}</b> into 8 latent topics. "
        "The non-negativity constraint guarantees purely additive, parts-based semantic representations without negative cancellations.<br/>"
        "• <b>K-Means Clustering with Silhouette Optimization:</b> Scans cluster counts k from 3 to 8, evaluating the Silhouette Coefficient: "
        "<b>s(i) = (b(i) - a(i)) / max(a(i), b(i))</b> to select the optimal natural cohort grouping (k=5), visualized via 2D PCA projection."
    )
    story.append(Paragraph(u4, style_body))
    story.append(Spacer(1, 4))

    u5 = (
        "<b>CO4 / Unit 7: Multi-Class Text Classification, Sentiment & Platt Scaling (Exp 10, 11)</b><br/>"
        "• <b>Calibrated Linear SVM:</b> Solves convex margin optimization: min 0.5 * ||w||^2 + C * SUM(xi_i).<br/>"
        "• <b>Platt Sigmoid Calibration:</b> Fits a logistic sigmoid <b>P(y=1 | f) = 1 / (1 + exp(A*f + B))</b> via maximum likelihood on cross-validation folds, "
        "transforming uncalibrated margin distances into compliant posterior probabilities and evaluated using Expected Calibration Error (ECE)."
    )
    story.append(Paragraph(u5, style_body))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 4: FRONTEND VISUAL MAP
    # =========================================================================
    story.append(Paragraph("4. Frontend UI Visual Map (Where Every Concept Lives on Screen)", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=6))

    fmap_data = [
        [
            Paragraph("<b>Frontend Page & Component</b>", style_table_head),
            Paragraph("<b>NLP / ML Concept Implemented</b>", style_table_head),
            Paragraph("<b>Visual Indicators on Screen</b>", style_table_head)
        ],
        [
            Paragraph("<b>Home: Live AI Classifier</b><br/>(<code>LivePredictBox.tsx</code>)", style_table_cell_bold),
            Paragraph("• Sublinear TF-IDF Vectorization<br/>• Calibrated Linear SVM<br/>• Platt Scaling ($P \\in [0, 1]$)<br/>• Token Attribution ($w_i \\cdot x_i$)<br/>• Sentiment Polarity", style_table_cell),
            Paragraph("• Result rendered in < 20ms<br/>• <b>99.9% Confidence</b> badge<br/>• Alternative category probability bars<br/>• <b>Influencing term badges</b> with +weights<br/>• Sentiment score and colored balance meter", style_table_cell)
        ],
        [
            Paragraph("<b>Home: Command Center</b><br/>(<code>Overview.tsx</code>)", style_table_cell_bold),
            Paragraph("• Day-of-Week Rolling MAD Anomaly Surveillance<br/>• Category Distribution<br/>• Channel Ingestion Mix", style_table_cell),
            Paragraph("• 4 Top KPI cards (Volume, Negative %, Sentiment, Warnings)<br/>• Recharts 30-day dual line trajectory<br/>• <b>Red circular surge anomaly markers</b><br/>• Categories bar chart & Sentiment donut chart", style_table_cell)
        ],
        [
            Paragraph("<b>Complaint Explorer</b><br/>(<code>Explorer.tsx</code>)", style_table_cell_bold),
            Paragraph("• Sub-10ms Debounced Full-Text Search<br/>• Curated Operational Presets<br/>• Contextual Narrative Inspection", style_table_cell),
            Paragraph("• Search bar with real-time text debouncing<br/>• 4 Preset pills (Overdraft, App Login, UPI, Skimming)<br/>• Multi-column filter dropdowns<br/>• <b>Slide-out inspection drawer</b> showing full complaint", style_table_cell)
        ],
        [
            Paragraph("<b>NLP Intelligence</b><br/>(<code>NLPIntelligence.tsx</code>)", style_table_cell_bold),
            Paragraph("• Supervised Model Benchmarking<br/>• Expected Calibration Error (ECE)<br/>• 5-Fold Cross Validation<br/>• Confusion Matrix & Macro F1", style_table_cell),
            Paragraph("• Model comparison table (SVM deployed vs LR vs Baseline)<br/>• <b>Confusion matrix heatmap</b> (diagonal concentration)<br/>• Per-class Precision, Recall, F1 table<br/>• <b>Influential terms per class</b> keyword cards", style_table_cell)
        ],
        [
            Paragraph("<b>ML Intelligence: Clusters</b><br/>(<code>MLIntelligence.tsx</code>)", style_table_cell_bold),
            Paragraph("• Latent Topic Modeling (NMF, k=8)<br/>• K-Means Document Clustering<br/>• Silhouette Score Optimization<br/>• 2D PCA Dimensionality Reduction", style_table_cell),
            Paragraph("• <b>2D PCA Cluster Scatter Plot</b><br/>• Silhouette score evaluation scan table (k=3 to 8)<br/>• Cluster cards with extracted semantic topics, percentage share, and representative text snippets", style_table_cell)
        ],
        [
            Paragraph("<b>ML Intelligence: Forecast</b><br/>(<code>MLIntelligence.tsx</code>)", style_table_cell_bold),
            Paragraph("• Damped Additive Holt-Winters Exponential Smoothing (m=7, phi=0.90)<br/>• Expanding-Window Walk-Forward Validation", style_table_cell),
            Paragraph("• 7/14/30-Day forecast trajectory chart with confidence bands<br/>• Holdout evaluation table comparing Damped Holt-Winters vs Seasonal Naive vs Rolling Mean (MAE, RMSE, Bias)", style_table_cell)
        ],
        [
            Paragraph("<b>Alert Center</b><br/>(<code>AlertCenter.tsx</code>)", style_table_cell_bold),
            Paragraph("• Deterministic Deduplication Hashing<br/>• Incident State Lifecycle Machine<br/>• Regulatory Root-Cause Ledger", style_table_cell),
            Paragraph("• Active incident ticket cards with CRITICAL/WARNING badges<br/>• <b>hash(product, anomaly, date)</b> deduplication key<br/>• <b>Status toggle: TRIGGERED -> INVESTIGATING -> RESOLVED</b><br/>• Root-cause notes and timestamped audit log", style_table_cell)
        ],
    ]
    t_fmap = Table(fmap_data, colWidths=[130, 185, 200])
    t_fmap.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_fmap)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 5: FACULTY VIVA DEFENSE
    # =========================================================================
    story.append(Paragraph("5. Faculty Viva & Cross-Examination Defense (Top 10 Lethal Questions)", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=6))

    viva_intro = (
        "Be fully prepared for examiners challenging your algorithmic and architecture decisions. "
        "Here are the exact answers to the 10 most common and difficult questions faculty ask:"
    )
    story.append(Paragraph(viva_intro, style_body))
    story.append(Spacer(1, 4))

    vivas = [
        ("Q1: Why didn't you use BERT, RoBERTa, or a Generative LLM for text classification?",
         "In production banking compliance, sub-20ms latency and exact token attribution are legally mandated. "
         "Linear SVM runs in under 2ms with zero GPU dependency, achieves 98.7% accuracy, and provides exact mathematical "
         "weights (w_i * x_i) that compliance auditors can verify, unlike black-box deep networks requiring heuristic approximations like LIME."),
        
        ("Q2: Why use modified Z-score with MAD instead of standard 3-sigma standard deviation?",
         "Standard deviation uses the mean and variance, which are distorted by extreme spikes (outlier masking). "
         "The median and MAD have a 50% breakdown point, resisting outlier contamination. Combining MAD with 28-day "
         "Day-of-Week grouping accounts for the 70% weekend volume drop and eliminates false Monday alarms."),
         
        ("Q3: What is Platt scaling and why couldn't you just use SVM's decision function?",
         "A Support Vector Machine outputs an uncalibrated signed hyperplane distance f(x) in (-inf, +inf). "
         "While the sign gives the class, the magnitude is not a probability. Platt scaling fits a logistic sigmoid "
         "P(y=1 | f) = 1 / (1 + exp(A*f + B)) via maximum likelihood over cross-validation folds, guaranteeing that a 95% "
         "confidence score represents a true 95% empirical likelihood."),
         
        ("Q4: How did you prevent data leakage during time-series forecasting validation?",
         "Standard k-fold cross-validation or random train-test splitting introduces lookahead bias because future points "
         "bleed into past training splits. We implemented Expanding-Window Chronological Backtesting: the model was trained "
         "strictly on historical data up to day T, and evaluated on unseen future days T+1 to T+14."),
         
        ("Q5: Why did you use NMF instead of LDA (Latent Dirichlet Allocation) for topic modeling?",
         "LDA is sensitive to Dirichlet prior hyperparameters (alpha, beta) and frequently generates overlapping, noisy topics "
         "on short customer texts. NMF uses non-negative matrix decomposition (V approx W * H). Because negative values are forbidden, "
         "features can only be added together, creating clean, interpretable, parts-based topics for business teams."),
         
        ("Q6: What is the purpose of the damping parameter (phi = 0.90) in Holt-Winters?",
         "Standard Holt-Winters assumes trend continues linearly to infinity, leading to unrealistically steep forecasts over "
         "14–30 days. The damping factor (phi = 0.90) damps trend accumulation: SUM(phi^i * b_t), leveling off projections "
         "to reflect realistic banking operational capacity."),
         
        ("Q7: How does the system handle alert fatigue in the Alert Center?",
         "If an infrastructure outage lasts 4 days, naive monitors fire hundreds of duplicate emails. We implemented "
         "deterministic hashing: dedup_key = hash(product, anomaly_type, date_bucket). When a spike persists, the system "
         "increments the incident count and updates the existing ticket rather than creating redundant alerts."),
         
        ("Q8: How does your system perform local feature attribution?",
         "Because our features are normalized TF-IDF weights x_i and our classifier is linear with learned weights w_{c,i}, "
         "the classification logit is z_c = b_c + SUM(w_{c,i} * x_i). Every token's contribution is isolated and computed "
         "in under 2 milliseconds without needing perturbation-based surrogate models."),
         
        ("Q9: What happens if a complaint talks about multiple issues simultaneously?",
         "Our probability calibration handles this cleanly. Instead of just returning a single hard label, the API returns "
         "the full posterior probability distribution across all 8 classes. If a customer mentions an ATM cash failure and an "
         "overdraft penalty, the model outputs, for example, 55% Transaction Failure and 38% Billing & Fees, highlighting tokens from both."),
         
        ("Q10: How would this system scale if complaint volume increased from 7,000 to 1,000,000?",
         "The FastAPI backend is stateless and horizontally scalable behind NGINX or Kubernetes. TF-IDF vectorizers and SVM models "
         "are serialized pickle artifacts loaded into RAM once at startup, serving predictions in under 2ms. The SQLite store can be "
         "transitioned seamlessly to PostgreSQL or Amazon RDS with zero application code changes.")
    ]

    for q, a in vivas:
        story.append(Paragraph(f"<b>{q}</b>", style_h3))
        story.append(Paragraph(f"<b>Defense:</b> {a}", style_body))
        story.append(Spacer(1, 2))

    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 6: INDIVIDUAL TEAM MEMBER DEFENSES
    # =========================================================================
    story.append(Paragraph("6. Individual Contribution Defenses (What to Say When Asked: 'What Did YOU Do?')", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=6))

    roles = [
        ("Aryan Turalkar (Roll No: A152) — NLP & Machine Learning Lead",
         "\"I designed and implemented the Natural Language Processing and supervised classification core. Specifically, I engineered "
         "the custom regex preprocessing pipeline, contraction expansion, and negation-preserving tokenizer. I tuned the sublinear "
         "TF-IDF vectorizer over 10,000 unigrams and bigrams, trained the LinearSVC model achieving 98.7% accuracy, implemented Platt "
         "sigmoid probability calibration with ECE evaluation, and formulated the linear feature attribution algorithm (w_i * x_i) for white-box interpretability.\""),
        
        ("Suryansh Saraf (Roll No: A-125) — Full-Stack Architect & UI/UX Lead",
         "\"I architected the entire full-stack system end-to-end. I built the modern React 18, TypeScript, and TailwindCSS Command Center, "
         "Complaint Explorer with sub-10ms debounced search, and the interactive Live Predictor widget. On the backend, I engineered the "
         "asynchronous FastAPI REST microservices, database schemas in SQLAlchemy/SQLite, and edge deployment configurations, ensuring sub-20ms round-trip latency.\""),
         
        ("Soham Hande (Roll No: A-129) — Statistical Anomaly Detection & Clustering Lead",
         "\"I developed the statistical surveillance and unsupervised discovery engines. I formulated the Day-of-Week normalized Rolling MAD "
         "algorithm that groups data by weekday to eliminate weekend volume bias, integrated the multivariate Isolation Forest ensemble, "
         "and tuned the multi-tier severity thresholds (Info, Warning, Critical). Furthermore, I implemented Non-Negative Matrix Factorization "
         "(NMF, k=8) and K-Means clustering with silhouette score optimization.\""),
         
        ("Pratham Deepak (Roll No: A-114) — Time-Series Forecasting & Operations Lead",
         "\"I led the predictive time-series modeling and incident operational workflow. I formulated the Additive Damped Holt-Winters "
         "exponential smoothing model with 7-day seasonality, performed expanding-window chronological backtesting demonstrating a 32% "
         "error reduction over baseline models, and engineered the Alert Center deterministic deduplication keying and incident lifecycle state machine.\"")
    ]

    for title, speech in roles:
        story.append(Paragraph(f"<b>{title}</b>", style_h3))
        story.append(Paragraph(speech, style_spoken))
        story.append(Spacer(1, 4))

    # Final wrap-up note
    story.append(Spacer(1, 10))
    final_note = (
        "<b>Final Presentation Advice:</b> Stay calm, speak clearly, and let the live working frontend do the talking. "
        "Whenever a faculty member asks a conceptual question, use the navbar to switch to the relevant tab (NLP Intelligence, "
        "ML Intelligence, Explorer) and point directly to the numbers and graphs. Good luck!"
    )
    story.append(create_callout(final_note, title="EXAMINATION CONFIDENCE TIP", bg_color="#ECFDF5", border_color="#10B981", title_color="#065F46"))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Master Script PDF built successfully at: {OUTPUT_PDF}")

if __name__ == "__main__":
    build_pdf()
