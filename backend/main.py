from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from command_engine import execute_command, get_all_commands
from auth_router import router as auth_router
from admin_router import router as admin_router


import cv2
import numpy as np
import mediapipe as mp
import joblib
import os


# ============================================================
# AI COMMUNICATION ASSISTANT
# BACKEND
# REAL ISL SIGN LANGUAGE MODEL
# ============================================================

MODEL_PATH = rstr(Path(__file__).resolve().parent / "model" / "trained_model" / "isl_sign_model.pkl")


# ============================================================
# LOAD REAL ISL MODEL
# ============================================================

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"ISL model not found: {MODEL_PATH}"
    )

sign_model = joblib.load(MODEL_PATH)

print("======================================")
print(" REAL ISL MODEL LOADED SUCCESSFULLY")
print("======================================")
print()


# ============================================================
# MEDIAPIPE HANDS
# ============================================================

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# ============================================================
# SIGN DETECTION
# ============================================================

def detect_sign(frame):

    # --------------------------------------------------------
    # BGR â†’ RGB
    # --------------------------------------------------------

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    result = hands.process(rgb_frame)


    # --------------------------------------------------------
    # NO HAND
    # --------------------------------------------------------

    if not result.multi_hand_landmarks:

        return {
            "sign": "No hand detected",
            "best_guess": "",
            "confidence": 0.0
        }


    # --------------------------------------------------------
    # FIRST HAND
    # --------------------------------------------------------

    hand_landmarks = result.multi_hand_landmarks[0]


    # --------------------------------------------------------
    # 21 LANDMARKS Ã— X,Y,Z
    # --------------------------------------------------------

    points = np.array(
        [
            [
                landmark.x,
                landmark.y,
                landmark.z
            ]
            for landmark in hand_landmarks.landmark
        ],
        dtype=np.float32
    )


    # --------------------------------------------------------
    # WRIST RELATIVE NORMALIZATION
    # --------------------------------------------------------

    wrist = points[0].copy()

    points = points - wrist


    # --------------------------------------------------------
    # HAND SIZE NORMALIZATION
    # --------------------------------------------------------

    hand_size = np.linalg.norm(
        points[9]
    )

    if hand_size < 1e-6:

        return {
            "sign": "Uncertain",
            "best_guess": "",
            "confidence": 0.0
        }


    points = points / hand_size


    # --------------------------------------------------------
    # FLATTEN
    # 21 Ã— 3 = 63 FEATURES
    # --------------------------------------------------------

    features = points.flatten()

    features = np.array(
        features,
        dtype=np.float32
    ).reshape(1, -1)


    # --------------------------------------------------------
    # MODEL PREDICTION
    # --------------------------------------------------------

    probabilities = sign_model.predict_proba(
        features
    )


    # --------------------------------------------------------
    # BEST PREDICTION
    # --------------------------------------------------------

    best_index = np.argmax(
        probabilities[0]
    )


    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    confidence = float(
        probabilities[0][best_index]
    )


    # --------------------------------------------------------
    # SIGN NAME
    # --------------------------------------------------------

    sign = str(
        sign_model.classes_[best_index]
    )


    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "sign": sign,
        "best_guess": sign,
        "confidence": round(
            confidence,
            3
        )
    }


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI Communication Assistant",
    description=(
        "AI Communication Assistant using "
        "Real Indian Sign Language Model"
    ),
    version="3.0.0"
)
app.include_router(auth_router)
app.include_router(admin_router)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
        "capacitor://localhost"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "status": "online",
        "application": "AI Communication Assistant",
        "model": "Real ISL Sign Language Model",
        "camera": "ready",
        "command_engine": "ready",
        "version": "3.0.0"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():

    return {
        "status": "ok",
        "model": "loaded",
        "camera": "ready",
        "command_engine": "ready",
        "message": "Backend and ISL model are working"
    }


# ============================================================
# SIGN REQUEST
# ============================================================

class SignRequest(BaseModel):

    sign: str


# ============================================================
# RECEIVE SIGN
# ============================================================

@app.post("/api/sign")
def receive_sign(
    data: SignRequest
):

    return {
        "success": True,
        "received": True,
        "sign": data.sign,
        "message": f"Detected sign: {data.sign}"
    }


# ============================================================
# COMMAND REQUEST
# ============================================================

class CommandRequest(BaseModel):

    sign: str


# ============================================================
# COMMAND ENGINE
# ============================================================

@app.post("/api/command")
def run_command(
    data: CommandRequest
):

    result = execute_command(
        data.sign
    )

    return result


# ============================================================
# ALL COMMANDS
# ============================================================

@app.get("/api/commands")
def all_commands():

    return get_all_commands()


# ============================================================
# TEXT MESSAGE
# ============================================================

class MessageRequest(BaseModel):

    text: str


@app.post("/api/message")
def receive_message(
    data: MessageRequest
):

    text = data.text.strip()

    return {
        "success": True,
        "received": True,
        "message": text
    }


# ============================================================
# CAMERA SIGN DETECTION
# ============================================================

@app.post("/api/sign-camera")
async def sign_camera(
    file: UploadFile = File(...)
):

    # --------------------------------------------------------
    # READ IMAGE
    # --------------------------------------------------------

    image_bytes = await file.read()


    # --------------------------------------------------------
    # BYTES â†’ NUMPY
    # --------------------------------------------------------

    image_array = np.frombuffer(
        image_bytes,
        np.uint8
    )


    # --------------------------------------------------------
    # DECODE IMAGE
    # --------------------------------------------------------

    frame = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR
    )


    # --------------------------------------------------------
    # INVALID IMAGE
    # --------------------------------------------------------

    if frame is None:

        return {
            "success": False,
            "sign": "Invalid image",
            "best_guess": "",
            "confidence": 0.0,
            "message": "Could not read camera image"
        }


    # --------------------------------------------------------
    # DETECT SIGN
    # --------------------------------------------------------

    prediction = detect_sign(
        frame
    )


    # --------------------------------------------------------
    # FRONTEND RESPONSE
    # --------------------------------------------------------

    return {
        "success": True,
        "sign": prediction["sign"],
        "best_guess": prediction["best_guess"],
        "confidence": prediction["confidence"],
        "message": (
            f"Detected sign: "
            f"{prediction['sign']}"
        )
    }


# ============================================================
# STARTUP INFORMATION
# ============================================================

print("======================================")
print(" AI COMMUNICATION ASSISTANT BACKEND")
print(" REAL ISL SIGN MODEL READY")
print(" CAMERA API READY")
print(" COMMAND ENGINE READY")
print(" API READY")
print("======================================")
