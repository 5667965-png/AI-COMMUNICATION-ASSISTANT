"""
AI Communication Assistant — Streamlit Edition
==============================================
Free online deployment: Streamlit Community Cloud (share.streamlit.io)

Deploy steps (see streamlit_app/DEPLOY.md for the full guide):
  1. Push this repository to GitHub (public)
  2. Open https://share.streamlit.io  ->  New app  ->  select repo
  3. Main file path: streamlit_app/streamlit_app.py
  4. Deploy — the app goes live at https://<app>.streamlit.app
"""

import io
import sys
import types
from pathlib import Path

import streamlit as st
import numpy as np
import joblib

try:
    import cv2  # noqa: F401  (MediaPipe imports cv2 for its drawing helpers)
except ImportError:
    # Streamlit Cloud installs the GUI OpenCV that MediaPipe depends on, and
    # that build cannot load without libGL. This app never calls cv2 directly
    # (Pillow/numpy do the image work), so a stub satisfies MediaPipe's import.
    sys.modules["cv2"] = types.ModuleType("cv2")

import mediapipe as mp
from PIL import Image
from gtts import gTTS

# ============================================================
# MODEL
# ============================================================

MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "backend"
    / "model"
    / "trained_model"
    / "isl_sign_model.pkl"
)


@st.cache_resource(show_spinner=False)
def load_sign_model():
    return joblib.load(MODEL_PATH)


@st.cache_resource(show_spinner=False)
def get_hands():
    # MediaPipe Tasks API (mediapipe>=0.10.35 removed the old mp.solutions API).
    model_path = Path(__file__).resolve().parent / "models" / "hand_landmarker.task"
    options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
        num_hands=1,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
    )
    return mp.tasks.vision.HandLandmarker.create_from_options(options)


def detect_sign(frame, model, hands):
    """Detect one ISL sign from a BGR image frame."""
    rgb = np.ascontiguousarray(frame[..., ::-1])  # BGR -> RGB
    result = hands.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))

    if not result.hand_landmarks:
        return {"sign": "No hand detected", "confidence": 0.0}

    points = np.array(
        [[lm.x, lm.y, lm.z] for lm in result.hand_landmarks[0]], dtype=np.float32
    )

    # Wrist-relative normalization (translation invariant).
    wrist = points[0].copy()
    points = points - wrist

    # Hand-size normalization (scale invariant).
    hand_size = np.linalg.norm(points[9])
    if hand_size < 1e-6:
        return {"sign": "Uncertain", "confidence": 0.0}
    points = points / hand_size

    # 21 landmarks x 3 = 63 features.
    features = points.flatten().reshape(1, -1)
    probabilities = model.predict_proba(features)
    best = int(np.argmax(probabilities[0]))

    return {
        "sign": str(model.classes_[best]),
        "confidence": float(probabilities[0][best]),
    }


# ============================================================
# COMMAND ENGINE  (40 ISL signs -> actions)
# ============================================================

COMMANDS = {
    "hello": ("GREETING", "Hello! How can I help you?"),
    "goodbye": ("GOODBYE", "Goodbye!"),
    "thank_you": ("THANK_YOU", "You're welcome!"),
    "sorry": ("SORRY", "It's okay."),
    "please": ("PLEASE", "Please."),
    "yes": ("YES", "Yes."),
    "no": ("NO", "No."),
    "okay": ("OKAY", "Okay."),
    "help": ("HELP", "Help command activated."),
    "stop": ("STOP", "Stop command activated."),
    "come": ("COME", "Come."),
    "go": ("GO", "Go."),
    "sit": ("SIT", "Sit."),
    "stand": ("STAND", "Stand."),
    "eat": ("EAT", "I want to eat."),
    "drink": ("DRINK", "I want to drink."),
    "write": ("WRITE", "Write."),
    "read": ("READ", "Read."),
    "today": ("TODAY", "Today."),
    "where": ("WHERE", "Where?"),
    "what": ("WHAT", "What?"),
    "when": ("WHEN", "When?"),
    "me": ("ME", "Me."),
    "you": ("YOU", "You."),
    "he": ("HE", "He."),
    "she": ("SHE", "She."),
    "mother": ("MOTHER", "Mother."),
    "father": ("FATHER", "Father."),
    "brother": ("BROTHER", "Brother."),
    "sister": ("SISTER", "Sister."),
    "friend": ("FRIEND", "Friend."),
    "teacher": ("TEACHER", "Teacher."),
    "student": ("STUDENT", "Student."),
    "home": ("HOME", "Home."),
    "school": ("SCHOOL", "School."),
    "hospital": ("HOSPITAL", "Hospital."),
    "market": ("MARKET", "Market."),
    "water": ("WATER", "Water."),
    "food": ("FOOD", "Food."),
    "tea": ("TEA", "Tea."),
}


def run_command(sign):
    sign = (sign or "").strip().lower()
    if not sign:
        return {"success": False, "command": "UNKNOWN", "message": "No sign received."}
    if sign in COMMANDS:
        command, message = COMMANDS[sign]
        return {"success": True, "sign": sign, "command": command, "message": message}
    return {
        "success": False,
        "sign": sign,
        "command": "UNKNOWN",
        "message": f"I don't have a command for '{sign}' yet.",
    }


# ============================================================
# AI NATURAL SENTENCE BUILDER
# ============================================================

def capitalize_first(value):
    return value[:1].upper() + value[1:] if value else ""


def build_natural_sentence(words):
    """Combine detected signs into a natural sentence."""
    if not words:
        return ""

    clean = [str(w or "").lower().strip() for w in words if str(w or "").strip()]
    if not clean:
        return ""

    # Remove consecutive duplicates.
    unique = [w for i, w in enumerate(clean) if i == 0 or w != clean[i - 1]]
    key = "|".join(unique)

    exact = {
        "hello": "Hello.", "goodbye": "Goodbye.", "thank_you": "Thank you.",
        "sorry": "Sorry.", "please": "Please.", "yes": "Yes.", "no": "No.",
        "okay": "Okay.", "help": "I need help.", "stop": "Please stop.",
        "eat": "I want to eat.", "drink": "I want to drink.",
        "water": "I want water.", "food": "I want food.", "tea": "I want tea.",
        "come": "Please come.", "go": "Please go.", "sit": "Please sit.",
        "stand": "Please stand.", "read": "I want to read.",
        "write": "I want to write.", "today": "Today.", "where": "Where?",
        "what": "What?", "when": "When?", "me": "Me.", "you": "You.",
        "he": "He.", "she": "She.", "mother": "Mother.", "father": "Father.",
        "brother": "Brother.", "sister": "Sister.", "friend": "Friend.",
        "teacher": "Teacher.", "student": "Student.", "home": "Home.",
        "school": "School.", "hospital": "Hospital.", "market": "Market.",
    }

    has = lambda w: w in unique
    contains = lambda a, b: has(a) and has(b)

    if len(unique) == 1:
        return exact.get(key, capitalize_first(unique[0].replace("_", " ")) + ".")

    # First-person requests.
    if contains("me", "water"): return "I want water."
    if contains("me", "food"): return "I want food."
    if contains("me", "tea"): return "I want tea."
    if contains("me", "eat"): return "I want to eat."
    if contains("me", "drink"): return "I want to drink."
    if contains("me", "read"): return "I want to read."
    if contains("me", "write"): return "I want to write."
    if contains("me", "go") and has("school"): return "I want to go to school."
    if contains("me", "go") and has("market"): return "I want to go to the market."
    if contains("me", "go") and has("hospital"): return "I want to go to the hospital."
    if contains("me", "go"): return "I want to go."
    if contains("me", "come"): return "I want to come."

    # Requests involving another person.
    if contains("you", "come"): return "Please come."
    if contains("you", "go") and has("school"): return "Please go to school."
    if contains("you", "go") and has("market"): return "Please go to the market."
    if contains("you", "go"): return "Please go."
    if contains("you", "sit"): return "Please sit."
    if contains("you", "stand"): return "Please stand."

    # Location / people combinations.
    if contains("mother", "home"): return "Mother is at home."
    if contains("father", "home"): return "Father is at home."
    if contains("brother", "home"): return "Brother is at home."
    if contains("sister", "home"): return "Sister is at home."
    if contains("friend", "home"): return "My friend is at home."
    if contains("teacher", "school"): return "The teacher is at school."
    if contains("student", "school"): return "The student is at school."

    # Need / emergency combinations.
    if contains("help", "hospital"): return "I need help at the hospital."
    if contains("help", "friend"): return "I need help from my friend."
    if contains("help", "teacher"): return "I need help from my teacher."
    if contains("help", "mother"): return "I need help from my mother."
    if contains("help", "father"): return "I need help from my father."
    if contains("stop", "please"): return "Please stop."

    # Question combinations.
    if contains("where", "home"): return "Where is home?"
    if contains("where", "school"): return "Where is the school?"
    if contains("where", "hospital"): return "Where is the hospital?"
    if contains("where", "market"): return "Where is the market?"
    if contains("what", "food"): return "What is the food?"
    if contains("what", "drink"): return "What should I drink?"
    if contains("when", "school"): return "When is school?"
    if contains("when", "today"): return "When today?"

    # Time / activity combinations.
    if contains("today", "school"): return "I have school today."
    if contains("today", "home"): return "I am at home today."
    if contains("today", "go") and has("school"): return "I want to go to school today."
    if contains("today", "go") and has("market"): return "I want to go to the market today."
    if contains("today", "go") and has("hospital"): return "I want to go to the hospital today."

    # Direct action + destination combinations.
    if contains("go", "school"): return "I want to go to school."
    if contains("go", "market"): return "I want to go to the market."
    if contains("go", "hospital"): return "I want to go to the hospital."
    if contains("come", "home"): return "Please come home."
    if contains("sit", "home"): return "Please sit at home."
    if contains("stand", "school"): return "Please stand at school."

    # Polite action phrases.
    if contains("please", "eat"): return "Please eat."
    if contains("please", "drink"): return "Please drink."
    if contains("please", "come"): return "Please come."
    if contains("please", "go"): return "Please go."
    if contains("please", "sit"): return "Please sit."
    if contains("please", "stand"): return "Please stand."
    if contains("please", "help"): return "Please help me."

    # Food / drink combinations.
    if contains("food", "tea"): return "I want food and tea."
    if contains("water", "tea"): return "I want water and tea."
    if contains("eat", "food"): return "I want to eat food."
    if contains("drink", "water"): return "I want to drink water."
    if contains("drink", "tea"): return "I want to drink tea."

    # Relationships.
    if contains("mother", "father"): return "Mother and father."
    if contains("brother", "sister"): return "Brother and sister."
    if contains("friend", "teacher"): return "My friend and teacher."

    # Fallback: readable sequence of signs.
    return capitalize_first(" ".join(w.replace("_", " ") for w in unique)) + "."


# ============================================================
# TEXT TO SPEECH (gTTS — works on Streamlit Cloud)
# ============================================================

LANG_CODES = {"English": "en", "Hindi": "hi", "Marathi": "mr"}


def speak(text, language):
    """Return mp3 audio bytes for the given text."""
    if not text or not text.strip():
        return None
    try:
        tts = gTTS(text=text, lang=LANG_CODES.get(language, "en"))
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.getvalue()
    except Exception:
        return None


# ============================================================
# APP STATE
# ============================================================

QUICK_MESSAGES = [
    ("🍽️", "Food", "I want to eat food."),
    ("💧", "Water", "I want to drink water."),
    ("💊", "Medicine", "I need my medicine."),
    ("🚽", "Bathroom", "I need to go to the bathroom."),
    ("🛌", "Rest", "I want to rest."),
    ("🆘", "Help", "I need help immediately!"),
    ("👨‍⚕️", "Doctor", "Please call a doctor."),
    ("👨‍👩‍👧", "Family", "Please call my family."),
]

EMERGENCY_MESSAGES = [
    "I need help.",
    "Please call my family.",
    "Please call an ambulance.",
    "Please take me to a hospital.",
]


def init_state():
    defaults = {
        "page": "Home",
        "sentence_signs": [],
        "sentence": "",
        "detected": None,
        "history": [],
        "favorites": [],
        "contacts": [],
        "language": "English",
        "auto_read": True,
        "font_scale": 1.0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_history(kind, value):
    if not value or not value.strip():
        return
    st.session_state.history.insert(
        0, {"type": kind, "value": value.strip(), "time": ""}
    )
    st.session_state.history = st.session_state.history[:100]


def speak_if_enabled(text):
    if st.session_state.auto_read:
        audio = speak(text, st.session_state.language)
        if audio:
            st.audio(audio, format="audio/mp3")


# ============================================================
# PAGES
# ============================================================

st.set_page_config(
    page_title="AI Communication Assistant",
    page_icon="🤟",
    layout="centered",
)

init_state()

font_scale = st.session_state.font_scale
st.markdown(
    f"""<style>
    .big {{ font-size: {int(22 * font_scale)}px; }}
    .conf {{ color: #059669; font-weight: 600; }}
    </style>""",
    unsafe_allow_html=True,
)

st.title("🤟 AI Communication Assistant")
st.caption("Real Indian Sign Language • Voice • Text — free online edition")

page = st.sidebar.radio(
    "Menu",
    ["Home", "🤟 ISL Detection", "⚡ Quick Messages", "🚨 Emergency",
     "⭐ Favorites", "🕘 History", "⚙️ Settings"],
    index=["Home", "🤟 ISL Detection", "⚡ Quick Messages", "🚨 Emergency",
           "⭐ Favorites", "🕘 History", "⚙️ Settings"].index(st.session_state.page),
)
st.session_state.page = page

# ------------------------------------------------------------
# HOME
# ------------------------------------------------------------
if page == "Home":
    st.header("Communicate without barriers")
    st.markdown(
        "This free online app turns **Indian Sign Language (ISL)** into "
        "spoken and written communication."
    )

    with st.expander("ℹ️ How it works", expanded=True):
        st.markdown(
            "1. Open **🤟 ISL Detection**\n"
            "2. Show your hand sign to the camera (or upload a photo)\n"
            "3. The AI model recognizes the sign\n"
            "4. Signs are combined into a natural sentence\n"
            "5. The app speaks the sentence aloud"
        )

    col1, col2, col3 = st.columns(3)
    col1.metric("Signs supported", "40")
    col2.metric("Languages", "3")
    col3.metric("Model", "Real ISL")

    st.info("💡 Tip: keep one hand clearly visible in good light for best results.")

# ------------------------------------------------------------
# ISL DETECTION
# ------------------------------------------------------------
elif page == "🤟 ISL Detection":
    st.header("🤟 ISL Sign Detection")

    model = load_sign_model()
    hands = get_hands()

    source = st.radio("Capture a photo", ["Camera", "Upload image"], horizontal=True)

    image_bytes = None
    if source == "Camera":
        pic = st.camera_input("📷 Take a photo")
        if pic is not None:
            image_bytes = pic.getvalue()
    else:
        up = st.file_uploader("📤 Upload a hand photo", type=["jpg", "jpeg", "png"])
        if up is not None:
            image_bytes = up.getvalue()

    if image_bytes is not None:
        # Pillow decodes to RGB; flip to BGR so the display and detection code
        # (which expect a BGR frame, like the old cv2.imdecode produced) work on.
        frame = np.ascontiguousarray(
            np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))[..., ::-1]
        )
        col_l, col_r = st.columns(2)
        with col_l:
            st.image(frame, channels="BGR", caption="Captured frame")

        with col_r:
            with st.spinner("Detecting sign..."):
                result = detect_sign(frame, model, hands)

            sign = result["sign"]
            conf = result["confidence"]

            if sign in ("No hand detected", "Uncertain") or conf < 0.45:
                st.warning(f"🟡 {sign} — confidence {conf:.0%}. Try again with a clear hand.")
            else:
                st.success(f"🟢 Sign: **{sign}**")
                st.markdown(f'<p class="conf">Confidence: {conf:.0%}</p>', unsafe_allow_html=True)

                command = run_command(sign)
                if command["success"]:
                    st.markdown(
                        f"⚙️ Command: **{command['command']}** — {command['message']}"
                    )

                if st.button("➕ Add to sentence", use_container_width=True):
                    st.session_state.sentence_signs.append(sign)
                    st.session_state.sentence_signs = st.session_state.sentence_signs[-12:]
                    st.session_state.sentence = build_natural_sentence(
                        st.session_state.sentence_signs
                    )
                    add_history("ISL", sign)
                    st.rerun()

    st.divider()
    st.subheader("📝 Current sentence")
    if st.session_state.sentence:
        st.markdown(f'<p class="big">{st.session_state.sentence}</p>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        if col1.button("🔊 Speak", use_container_width=True):
            speak_if_enabled(st.session_state.sentence)
        if col2.button("⭐ Favorite", use_container_width=True):
            if st.session_state.sentence not in st.session_state.favorites:
                st.session_state.favorites.insert(0, st.session_state.sentence)
        if col3.button("🗑️ Clear", use_container_width=True):
            st.session_state.sentence_signs = []
            st.session_state.sentence = ""
            st.rerun()
    else:
        st.caption("Detected signs will build a sentence here.")

    if st.session_state.sentence_signs:
        st.caption("Signs: " + " → ".join(st.session_state.sentence_signs))

# ------------------------------------------------------------
# QUICK MESSAGES
# ------------------------------------------------------------
elif page == "⚡ Quick Messages":
    st.header("⚡ Quick Messages")
    st.caption("One tap to send and speak common needs.")

    for icon, label, message in QUICK_MESSAGES:
        if st.button(f"{icon}  {label}", use_container_width=True):
            add_history("QUICK", message)
            st.session_state.sentence = message
            speak_if_enabled(message)
            st.rerun()

# ------------------------------------------------------------
# EMERGENCY
# ------------------------------------------------------------
elif page == "🚨 Emergency":
    st.header("🚨 Emergency Center")

    st.subheader("Quick emergency messages")
    for msg in EMERGENCY_MESSAGES:
        if st.button(f"🆘 {msg}", use_container_width=True):
            add_history("EMERGENCY", msg)
            speak_if_enabled(msg)

    st.divider()
    st.subheader("📞 Emergency contacts")

    new_contact = st.text_input("Add a contact number", placeholder="+91 00000 00000")
    if st.button("➕ Add contact") and new_contact.strip():
        if new_contact.strip() not in st.session_state.contacts:
            st.session_state.contacts.append(new_contact.strip())

    for contact in st.session_state.contacts:
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"📱 {contact}")
        if c2.button("Remove", key=f"rm_{contact}"):
            st.session_state.contacts.remove(contact)
            st.rerun()

    st.divider()
    st.warning(
        "On a phone, use the native **SMS** app with these messages. "
        "Online apps cannot send SMS directly for security reasons."
    )

# ------------------------------------------------------------
# FAVORITES
# ------------------------------------------------------------
elif page == "⭐ Favorites":
    st.header("⭐ Favorite Messages")

    if not st.session_state.favorites:
        st.info("No favorites yet. Save a sentence from ISL Detection.")
    for fav in st.session_state.favorites:
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.markdown(fav)
        if c2.button("🔊", key=f"sp_{fav}"):
            speak_if_enabled(fav)
        if c3.button("🗑️", key=f"del_{fav}"):
            st.session_state.favorites.remove(fav)
            st.rerun()

# ------------------------------------------------------------
# HISTORY
# ------------------------------------------------------------
elif page == "🕘 History":
    st.header("🕘 Communication History")

    if not st.session_state.history:
        st.info("No history yet.")
    else:
        for item in st.session_state.history[:50]:
            st.markdown(f"**{item['type']}** — {item['value']}")
        if st.button("🗑️ Clear history", use_container_width=True):
            st.session_state.history = []
            st.rerun()

# ------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------
elif page == "⚙️ Settings":
    st.header("⚙️ Settings")

    st.selectbox("🌐 Language", ["English", "Hindi", "Marathi"],
                 index=["English", "Hindi", "Marathi"].index(st.session_state.language),
                 key="language")

    st.toggle("🔊 Auto-read sentences aloud", value=st.session_state.auto_read,
              key="auto_read")

    scale = st.slider("🔠 Text size", 0.9, 1.5, st.session_state.font_scale, 0.1)
    st.session_state.font_scale = scale

    st.divider()
    st.caption("AI Communication Assistant — Streamlit free edition")
