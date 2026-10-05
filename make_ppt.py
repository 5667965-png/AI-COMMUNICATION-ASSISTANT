# Generates the project presentation: AI Communication Assistant
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ---------- Palette ----------
DARK    = RGBColor(0x1E, 0x1B, 0x4B)   # deep indigo
PRIMARY = RGBColor(0x6D, 0x28, 0xD9)   # violet
ACCENT  = RGBColor(0x06, 0xB6, 0xD4)   # cyan
LIGHT   = RGBColor(0xF5, 0xF3, 0xFF)   # near-white lavender
GREY    = RGBColor(0x6B, 0x72, 0x80)
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
GREEN   = RGBColor(0x05, 0x96, 0x69)
AMBER   = RGBColor(0xD9, 0x77, 0x06)

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW, SH = prs.slide_width, prs.slide_height

def slide():
    return prs.slides.add_slide(BLANK)

def bg(s, color):
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = color

def box(s, l, t, w, h, color, line=None):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = color
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line; sh.line.width = Pt(1)
    sh.shadow.inherit = False
    return sh

def txt(s, l, t, w, h, text, size, color, bold=False, align=PP_ALIGN.LEFT,
        font="Calibri", anchor=MSO_ANCHOR.TOP, spacing=1.0):
    tb = s.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        r = p.add_run(); r.text = line
        r.font.size = Pt(size); r.font.bold = bold
        r.font.color.rgb = color; r.font.name = font
    return tb

def bullets(s, l, t, w, h, items, size=18, color=DARK, gap=6, spacing=1.05):
    tb = s.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame; tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap); p.line_spacing = spacing
        if isinstance(item, tuple):          # (level, text, bold)
            level, text, bold = item
        else:
            level, text, bold = 0, item, False
        p.level = level
        r = p.add_run()
        r.text = ("•  " if level == 0 else "–  ") + text
        r.font.size = Pt(size if level == 0 else size - 2)
        r.font.bold = bold
        r.font.color.rgb = color; r.font.name = "Calibri"
    return tb

def header(s, title, subtitle=None):
    box(s, 0, 0, SW, Inches(1.15), DARK)
    box(s, 0, Inches(1.15), SW, Inches(0.06), ACCENT)
    txt(s, Inches(0.55), Inches(0.18), SW - Inches(1.1), Inches(0.8),
        title, 30, WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    if subtitle:
        txt(s, Inches(0.55), Inches(1.32), SW - Inches(1.1), Inches(0.4),
            subtitle, 14, GREY)

def footer(s, n):
    txt(s, Inches(0.55), SH - Inches(0.45), Inches(8), Inches(0.35),
        "AI Communication Assistant  |  Real Indian Sign Language Technology",
        10, GREY)
    txt(s, SW - Inches(1.0), SH - Inches(0.45), Inches(0.5), Inches(0.35),
        str(n), 10, GREY, align=PP_ALIGN.RIGHT)

# ============================================================
# SLIDE 1 — TITLE
# ============================================================
s = slide(); bg(s, DARK)
box(s, 0, Inches(4.9), SW, Inches(0.07), ACCENT)
box(s, Inches(0.9), Inches(1.15), Inches(1.7), Inches(1.7), PRIMARY)
txt(s, Inches(0.9), Inches(1.15), Inches(1.7), Inches(1.7), "🤟", 66, WHITE,
    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
txt(s, Inches(2.85), Inches(1.25), Inches(9.6), Inches(1.0),
    "AI Communication Assistant", 44, WHITE, bold=True)
txt(s, Inches(2.85), Inches(2.25), Inches(9.6), Inches(0.6),
    "Real Indian Sign Language Recognition  •  Voice  •  Text",
    20, ACCENT)
txt(s, Inches(2.85), Inches(3.0), Inches(9.6), Inches(1.4),
    "An intelligent, accessible communication platform that translates\n"
    "ISL hand signs into natural sentences — breaking communication\n"
    "barriers for the deaf and hard-of-hearing community.",
    16, LIGHT, spacing=1.15)
txt(s, Inches(0.9), Inches(5.25), Inches(11.5), Inches(1.2),
    "Full-Stack Project Presentation\n"
    "Backend: FastAPI + Machine Learning      |      Frontend: React + Vite + Android (Capacitor)",
    14, RGBColor(0xC4, 0xB5, 0xFD), spacing=1.2)

# ============================================================
# SLIDE 2 — PROBLEM
# ============================================================
s = slide(); bg(s, LIGHT); header(s, "The Problem", "Why this project exists")
bullets(s, Inches(0.6), Inches(1.7), Inches(7.2), Inches(4.6), [
    (0, "Communication barriers for the deaf & hard-of-hearing", True),
    (1, "Sign language is not understood by most hearing people", False),
    (1, "Text-only apps are slow and impersonal", False),
    (0, "Existing solutions are expensive or language-limited", True),
    (1, "Most sign-recognition tools support only American Sign Language", False),
    (1, "Indian Sign Language (ISL) is largely underserved by AI", False),
    (0, "Emergency situations need one-tap communication", True),
    (1, "A person in distress may not be able to speak or type", False),
], size=18, gap=10)
box(s, Inches(8.2), Inches(1.7), Inches(4.5), Inches(4.6), WHITE)
txt(s, Inches(8.5), Inches(1.95), Inches(3.9), Inches(0.5),
    "💡 The Gap", 20, PRIMARY, bold=True)
txt(s, Inches(8.5), Inches(2.6), Inches(3.9), Inches(3.4),
    "There was no free, real-time,\n"
    "AI-powered assistant that\n"
    "understands Indian Sign\n"
    "Language and converts it\n"
    "into spoken words,\n"
    "text and actions —\n"
    "all in one accessible app.",
    17, DARK, spacing=1.25)
footer(s, 2)

# ============================================================
# SLIDE 3 — SOLUTION OVERVIEW
# ============================================================
s = slide(); bg(s, LIGHT); header(s, "The Solution", "One intelligent communication assistant")
cards = [
    ("🤟", "ISL Sign Detection", "Real-time hand tracking with MediaPipe + a trained ISL ML model", PRIMARY),
    ("🧠", "AI Sentence Builder", "Combines detected signs into natural, grammatically-correct sentences", ACCENT),
    ("🗣️", "Voice + Text", "Speech-to-text and text-to-speech in English, Hindi & Marathi", GREEN),
    ("🚨", "Emergency Tools", "Double-tap SOS, one-tap emergency messages and GPS location sharing", AMBER),
]
x = Inches(0.6)
for icon, title, desc, color in cards:
    box(s, x, Inches(1.8), Inches(2.95), Inches(4.3), WHITE)
    box(s, x, Inches(1.8), Inches(2.95), Inches(0.14), color)
    txt(s, x, Inches(2.15), Inches(2.95), Inches(0.9), icon, 40, color,
        align=PP_ALIGN.CENTER)
    txt(s, x + Inches(0.2), Inches(3.15), Inches(2.55), Inches(0.7),
        title, 17, DARK, bold=True, align=PP_ALIGN.CENTER)
    txt(s, x + Inches(0.2), Inches(3.95), Inches(2.55), Inches(2.0),
        desc, 13.5, GREY, align=PP_ALIGN.CENTER, spacing=1.15)
    x += Inches(3.12)
txt(s, Inches(0.6), Inches(6.35), Inches(12.1), Inches(0.6),
    "Result: a deaf user signs → the app speaks the sentence aloud → the conversation flows both ways.",
    15, PRIMARY, bold=True, align=PP_ALIGN.CENTER)
footer(s, 3)

# ============================================================
# SLIDE 4 — ARCHITECTURE
# ============================================================
s = slide(); bg(s, LIGHT); header(s, "System Architecture", "End-to-end data flow")
# layers
layers = [
    ("CLIENT LAYER", "React + Vite SPA  •  Android via Capacitor  •  Camera (WebRTC)  •  Mic (Web Speech API)", PRIMARY),
    ("API LAYER", "FastAPI REST API  •  CORS  •  Token authentication  •  File upload for camera frames", ACCENT),
    ("AI LAYER", "MediaPipe Hands (21 landmarks)  •  ISL ML model (joblib)  •  Command Engine (40 signs)", GREEN),
    ("DATA LAYER", "SQLite database  •  Users  •  Sessions  •  History  •  Favorites  •  Emergency contacts", AMBER),
]
y = Inches(1.65)
for name, desc, color in layers:
    box(s, Inches(0.6), y, Inches(3.1), Inches(1.05), color)
    txt(s, Inches(0.6), y, Inches(3.1), Inches(1.05), name, 16, WHITE, bold=True,
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    box(s, Inches(3.85), y, Inches(8.85), Inches(1.05), WHITE)
    txt(s, Inches(4.15), y, Inches(8.3), Inches(1.05), desc, 14.5, DARK,
        anchor=MSO_ANCHOR.MIDDLE, spacing=1.1)
    if y < Inches(5.5):
        ar = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(2.0), y + Inches(1.08), Inches(0.35), Inches(0.28))
        ar.fill.solid(); ar.fill.fore_color.rgb = GREY; ar.line.fill.background(); ar.shadow.inherit = False
    y += Inches(1.38)
footer(s, 4)

# ============================================================
# SLIDE 5 — TECH STACK
# ============================================================
s = slide(); bg(s, LIGHT); header(s, "Technology Stack")
def stack_col(l, title, items, color):
    box(s, l, Inches(1.7), Inches(3.95), Inches(0.6), color)
    txt(s, l, Inches(1.7), Inches(3.95), Inches(0.6), title, 16, WHITE, bold=True,
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    box(s, l, Inches(2.3), Inches(3.95), Inches(4.35), WHITE)
    bullets(s, l + Inches(0.25), Inches(2.5), Inches(3.5), Inches(4.0),
            items, size=14.5, gap=8)
stack_col(Inches(0.6),  "🐍  BACKEND", [
    "FastAPI 0.141 — REST API",
    "Uvicorn — ASGI server",
    "scikit-learn — ML model",
    "MediaPipe — hand tracking",
    "OpenCV — image processing",
    "SQLite + joblib — data & model",
    "python-multipart — uploads",
], PRIMARY)
stack_col(Inches(4.7),  "⚛️  FRONTEND", [
    "React 19 + Vite 8",
    "Capacitor — Android app",
    "Web Speech API — voice",
    "WebRTC — camera stream",
    "Canvas — frame capture",
    "CSS3 — responsive UI",
    "Oxlint — code quality",
], ACCENT)
stack_col(Inches(8.8), "🛠️  TOOLS & OPS", [
    "Git — version control",
    "Firebase — hosting config",
    "CORS — secure API access",
    "Token sessions — auth",
    "RESTful API design",
    "Background services",
    "Cross-platform build",
], GREEN)
footer(s, 5)

# ============================================================
# SLIDE 6 — AI / ML MODEL
# ============================================================
s = slide(); bg(s, LIGHT); header(s, "AI & Machine Learning", "How the ISL model works")
bullets(s, Inches(0.6), Inches(1.65), Inches(6.4), Inches(5.0), [
    (0, "Hand landmark extraction", True),
    (1, "MediaPipe Hands detects 21 hand landmarks", False),
    (1, "Each landmark provides X, Y, Z coordinates", False),
    (1, "21 × 3 = 63 features per frame", False),
    (0, "Normalization pipeline", True),
    (1, "Wrist-relative: subtract wrist position (translation invariant)", False),
    (1, "Scale by hand size (distance invariant)", False),
    (1, "Flatten to a 63-feature vector", False),
    (0, "Prediction", True),
    (1, "Trained classifier predicts the ISL sign + confidence", False),
    (1, "Model file: isl_sign_model.pkl (17 MB, joblib)", False),
], size=16, gap=7)
box(s, Inches(7.35), Inches(1.65), Inches(5.35), Inches(5.0), WHITE)
txt(s, Inches(7.65), Inches(1.9), Inches(4.8), Inches(0.5),
    "🛡️  Stability Engine", 18, PRIMARY, bold=True)
bullets(s, Inches(7.65), Inches(2.5), Inches(4.8), Inches(3.9), [
    "Majority voting over last 7 predictions",
    "Confidence threshold (≥ 45%)",
    "Average confidence ≥ 55%",
    "4 consistent votes required",
    "Recent 4-frame consistency check",
    "Hand-removed detection resets state",
    "→ Filters out jitter & false positives",
], size=15, gap=9)
footer(s, 6)

# ============================================================
# SLIDE 7 — KEY FEATURES
# ============================================================
s = slide(); bg(s, LIGHT); header(s, "Key Features")
features = [
    ("🤟", "ISL Camera Detection", "Live camera sign recognition with auto-detect mode"),
    ("📝", "Natural Sentences", "AI builder turns sign sequences into full sentences"),
    ("🎤", "Voice → Text", "Speech recognition (English / Hindi / Marathi)"),
    ("🔊", "Text → Voice", "Auto-read detected sentences aloud"),
    ("💬", "Two-Way Conversation", "One screen for ISL user + speaking user"),
    ("⚡", "Quick Messages", "One-tap food, water, medicine, doctor, SOS"),
    ("⭐", "Favorites", "Save & reuse frequent messages"),
    ("🕘", "History", "Persistent log of all communication"),
    ("🚨", "Emergency Center", "Double-tap SOS + SMS + optional GPS location"),
    ("🏥", "Medical ID", "Blood group, allergies, medicines, doctor contact"),
    ("🛡️", "Admin Dashboard", "User stats, accounts & activity management"),
    ("🔐", "Secure Auth", "Register / login with token sessions"),
]
x, y = Inches(0.6), Inches(1.6)
for i, (icon, title, desc) in enumerate(features):
    box(s, x, y, Inches(3.95), Inches(1.62), WHITE)
    txt(s, x + Inches(0.18), y + Inches(0.12), Inches(0.75), Inches(0.6), icon, 24, PRIMARY)
    txt(s, x + Inches(0.95), y + Inches(0.14), Inches(2.9), Inches(0.45), title, 14.5, DARK, bold=True)
    txt(s, x + Inches(0.95), y + Inches(0.62), Inches(2.9), Inches(0.95), desc, 12, GREY, spacing=1.1)
    x += Inches(4.12)
    if (i + 1) % 3 == 0:
        x = Inches(0.6); y += Inches(1.78)
footer(s, 7)

# ============================================================
# SLIDE 8 — COMMAND ENGINE
# ============================================================
s = slide(); bg(s, LIGHT); header(s, "Command Engine", "40 ISL signs mapped to actions")
txt(s, Inches(0.6), Inches(1.6), Inches(12), Inches(0.5),
    "Every detected sign is converted into a structured command the app can act on:",
    16, DARK)
groups = [
    ("Social", "hello • goodbye • thank_you • sorry • please • yes • no • okay", PRIMARY),
    ("Actions", "help • stop • come • go • sit • stand • eat • drink • write • read", ACCENT),
    ("Questions", "where • what • when • today • me • you • he • she", GREEN),
    ("People", "mother • father • brother • sister • friend • teacher • student", AMBER),
    ("Places", "home • school • hospital • market", RGBColor(0xDB, 0x27, 0x77)),
    ("Needs", "water • food • tea", RGBColor(0x47, 0x55, 0x69)),
]
y = Inches(2.25)
for name, signs, color in groups:
    box(s, Inches(0.6), y, Inches(2.3), Inches(0.72), color)
    txt(s, Inches(0.6), y, Inches(2.3), Inches(0.72), name, 15, WHITE, bold=True,
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    box(s, Inches(3.05), y, Inches(9.65), Inches(0.72), WHITE)
    txt(s, Inches(3.35), y, Inches(9.1), Inches(0.72), signs, 14, DARK,
        anchor=MSO_ANCHOR.MIDDLE)
    y += Inches(0.86)
footer(s, 8)

# ============================================================
# SLIDE 9 — BACKEND API
# ============================================================
s = slide(); bg(s, LIGHT); header(s, "Backend REST API")
apis = [
    ("GET",  "/api/health", "Health check — model & services status", GREEN),
    ("POST", "/api/sign", "Receive a detected sign", PRIMARY),
    ("POST", "/api/sign-camera", "Upload camera frame → ISL prediction", PRIMARY),
    ("POST", "/api/command", "Convert sign → command + message", PRIMARY),
    ("GET",  "/api/commands", "List all 40 available commands", PRIMARY),
    ("POST", "/api/message", "Send a text message", ACCENT),
    ("POST", "/api/auth/register", "Create account", GREEN),
    ("POST", "/api/auth/login", "Login → session token", GREEN),
    ("GET",  "/api/user/history", "Communication history", AMBER),
    ("GET",  "/api/user/favorites", "Saved favorites", AMBER),
    ("GET",  "/api/user/emergency-contacts", "Emergency contacts", AMBER),
    ("GET",  "/api/admin/*", "Admin dashboard (stats, users, activity)", RGBColor(0xDB, 0x27, 0x77)),
]
y = Inches(1.6)
for method, path, desc, color in apis:
    box(s, Inches(0.6), y, Inches(1.05), Inches(0.42), color)
    txt(s, Inches(0.6), y, Inches(1.05), Inches(0.42), method, 11.5, WHITE, bold=True,
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    txt(s, Inches(1.8), y, Inches(4.3), Inches(0.42), path, 13.5, DARK, bold=True,
        anchor=MSO_ANCHOR.MIDDLE, font="Consolas")
    txt(s, Inches(6.2), y, Inches(6.5), Inches(0.42), desc, 13, GREY,
        anchor=MSO_ANCHOR.MIDDLE)
    y += Inches(0.5)
footer(s, 9)

# ============================================================
# SLIDE 10 — SECURITY
# ============================================================
s = slide(); bg(s, LIGHT); header(s, "Security & Data", "How user data is protected")
bullets(s, Inches(0.6), Inches(1.7), Inches(6.2), Inches(4.8), [
    (0, "Authentication", True),
    (1, "Register / login with email + password", False),
    (1, "SHA-256 password hashing in SQLite", False),
    (1, "Token-based sessions (secrets.token_urlsafe)", False),
    (1, "Protected endpoints require Bearer token", False),
    (0, "Admin panel", True),
    (1, "Separate admin login & token store", False),
    (1, "Environment-configured credentials", False),
    (0, "Data storage", True),
    (1, "Local SQLite — no external data leaks", False),
    (1, "Per-user isolation of history, favorites, contacts", False),
], size=16, gap=8)
box(s, Inches(7.2), Inches(1.7), Inches(5.5), Inches(4.8), WHITE)
txt(s, Inches(7.5), Inches(1.95), Inches(4.9), Inches(0.5),
    "🔒  Privacy First", 19, PRIMARY, bold=True)
txt(s, Inches(7.5), Inches(2.6), Inches(4.9), Inches(3.6),
    "• Camera video is processed frame-by-frame\n"
    "  and never stored or uploaded as video\n\n"
    "• Only the detected sign text is saved\n\n"
    "• All data stays on the user's device\n\n"
    "• Emergency SMS uses the device's\n"
    "  native messaging — no third party",
    15, DARK, spacing=1.15)
footer(s, 10)

# ============================================================
# SLIDE 11 — ACCESSIBILITY
# ============================================================
s = slide(); bg(s, LIGHT); header(s, "Accessibility", "Designed for everyone")
items = [
    ("🔠", "Adjustable text size", "A− / A+ scaling from 0.9× to 1.5× across the whole interface"),
    ("🌐", "Multi-language", "English, Hindi and Marathi for speech & voice output"),
    ("👆", "Large touch targets", "Big buttons for motor-impaired users"),
    ("⚡", "One-tap quick messages", "No typing needed for everyday needs"),
    ("🚨", "Double-tap SOS", "Emergency trigger that works even when the user cannot speak"),
    ("📱", "Mobile + Android", "Runs in the browser or as a native Android app via Capacitor"),
]
y = Inches(1.7)
for icon, title, desc in items:
    box(s, Inches(0.6), y, Inches(12.1), Inches(0.82), WHITE)
    txt(s, Inches(0.85), y, Inches(0.9), Inches(0.82), icon, 26, PRIMARY,
        anchor=MSO_ANCHOR.MIDDLE)
    txt(s, Inches(1.85), y, Inches(3.6), Inches(0.82), title, 16, DARK, bold=True,
        anchor=MSO_ANCHOR.MIDDLE)
    txt(s, Inches(5.6), y, Inches(6.9), Inches(0.82), desc, 13.5, GREY,
        anchor=MSO_ANCHOR.MIDDLE)
    y += Inches(0.95)
footer(s, 11)

# ============================================================
# SLIDE 12 — HOW TO RUN
# ============================================================
s = slide(); bg(s, LIGHT); header(s, "How to Run")
box(s, Inches(0.6), Inches(1.7), Inches(5.95), Inches(4.9), DARK)
txt(s, Inches(0.9), Inches(1.95), Inches(5.4), Inches(0.5), "🐍  Backend", 20, ACCENT, bold=True)
txt(s, Inches(0.9), Inches(2.6), Inches(5.4), Inches(3.8),
    "cd backend\n"
    "venv311\\Scripts\\activate\n\n"
    "pip install -r requirements.txt\n\n"
    "python -m uvicorn main:app \\\n"
    "      --host 0.0.0.0 --port 8000\n\n"
    "→ API: http://localhost:8000\n"
    "→ Docs: http://localhost:8000/docs",
    14.5, WHITE, font="Consolas", spacing=1.1)
box(s, Inches(6.75), Inches(1.7), Inches(5.95), Inches(4.9), DARK)
txt(s, Inches(7.05), Inches(1.95), Inches(5.4), Inches(0.5), "⚛️  Frontend", 20, ACCENT, bold=True)
txt(s, Inches(7.05), Inches(2.6), Inches(5.4), Inches(3.8),
    "cd frontend\n"
    "npm install\n\n"
    "npm run dev\n\n"
    "→ App: http://localhost:5173\n\n"
    "npm run build     (production)\n"
    "npx cap add android  (mobile)",
    14.5, WHITE, font="Consolas", spacing=1.1)
footer(s, 12)

# ============================================================
# SLIDE 13 — FUTURE SCOPE
# ============================================================
s = slide(); bg(s, LIGHT); header(s, "Future Scope")
bullets(s, Inches(0.6), Inches(1.7), Inches(6.2), Inches(4.9), [
    (0, "Expand the ISL vocabulary", True),
    (1, "Train on a larger, real ISL dataset", False),
    (1, "Add two-hand and facial-expression signs", False),
    (0, "Deeper AI", True),
    (1, "Deep learning (CNN / Transformer) models", False),
    (1, "Continuous sign-to-text (not just single signs)", False),
    (0, "Communication features", True),
    (1, "Real-time translation mode", False),
    (1, "Chat with saved conversations", False),
    (1, "Offline-first mobile app", False),
], size=16, gap=8)
box(s, Inches(7.2), Inches(1.7), Inches(5.5), Inches(4.9), WHITE)
txt(s, Inches(7.5), Inches(1.95), Inches(4.9), Inches(0.5),
    "🚀  Roadmap", 19, PRIMARY, bold=True)
bullets(s, Inches(7.5), Inches(2.6), Inches(4.9), Inches(3.8), [
    "More Indian languages",
    "Voice-controlled navigation",
    "Wearable / smart-glove input",
    "Cloud sync of user data",
    "Caregiver dashboard",
    "Accessibility certifications",
], size=15.5, gap=10)
footer(s, 13)

# ============================================================
# SLIDE 14 — CONCLUSION
# ============================================================
s = slide(); bg(s, DARK)
box(s, 0, Inches(2.1), SW, Inches(0.07), ACCENT)
txt(s, Inches(0.9), Inches(1.0), Inches(11.5), Inches(1.0),
    "Conclusion", 40, WHITE, bold=True)
txt(s, Inches(0.9), Inches(2.5), Inches(11.5), Inches(2.6),
    "The AI Communication Assistant turns Indian Sign Language into\n"
    "spoken and written communication — in real time.\n\n"
    "It combines computer vision, machine learning and inclusive design\n"
    "to give the deaf and hard-of-hearing community a voice.",
    20, LIGHT, spacing=1.25)
box(s, Inches(0.9), Inches(5.5), Inches(11.5), Inches(0.05), PRIMARY)
txt(s, Inches(0.9), Inches(5.75), Inches(11.5), Inches(0.8),
    "🤟  Communicate without barriers.",
    24, ACCENT, bold=True)
txt(s, Inches(0.9), Inches(6.55), Inches(11.5), Inches(0.5),
    "Thank you  •  Questions welcome", 14, RGBColor(0xC4, 0xB5, 0xFD))

prs.save(r"C:\communcation\AI_Communication_Assistant_Presentation.pptx")
print("Saved presentation with", len(prs.slides.__iter__.__self__._sldIdLst), "slides")
