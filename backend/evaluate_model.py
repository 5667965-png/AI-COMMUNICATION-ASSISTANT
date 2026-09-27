import os
import cv2
import joblib
import numpy as np
import mediapipe as mp

from collections import defaultdict
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_DIR = os.path.join(
    BASE_DIR,
    "ISL_DATASET"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "model",
    "trained_model",
    "isl_sign_model.pkl"
)


# ============================================================
# LOAD MODEL
# ============================================================

print("\n========================================")
print(" AI COMMUNICATION ASSISTANT")
print(" AUTOMATED ISL MODEL EVALUATION")
print("========================================\n")

if not os.path.exists(MODEL_PATH):
    print("ERROR: Model file not found:")
    print(MODEL_PATH)
    raise SystemExit

if not os.path.exists(DATASET_DIR):
    print("ERROR: Dataset folder not found:")
    print(DATASET_DIR)
    raise SystemExit


model = joblib.load(MODEL_PATH)

print("Model loaded successfully.")
print("Dataset:", DATASET_DIR)
print()


# ============================================================
# MEDIAPIPE
# ============================================================

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# ============================================================
# NORMALIZATION
# SAME METHOD USED DURING TRAINING
# ============================================================

def normalize_landmarks(hand_landmarks):

    points = np.array(
        [
            [landmark.x, landmark.y, landmark.z]
            for landmark in hand_landmarks.landmark
        ],
        dtype=np.float32
    )

    wrist = points[0].copy()

    points = points - wrist

    hand_size = np.linalg.norm(points[9])

    if hand_size < 1e-6:
        return None

    points = points / hand_size

    return points.flatten().tolist()


# ============================================================
# DATA COLLECTION
# ============================================================

y_true = []
y_pred = []

class_total = defaultdict(int)
class_correct = defaultdict(int)

video_count = 0
frame_count = 0
valid_count = 0


# ============================================================
# FIND VIDEOS
# ============================================================

video_extensions = (
    ".mp4",
    ".avi",
    ".mov",
    ".mkv"
)

video_files = []

for root, dirs, files in os.walk(DATASET_DIR):

    for file in files:

        if file.lower().endswith(video_extensions):

            video_files.append(
                os.path.join(root, file)
            )


video_files.sort()

print("Videos found:", len(video_files))
print()


# ============================================================
# PROCESS VIDEOS
# ============================================================

for video_path in video_files:

    video_count += 1

    filename = os.path.basename(video_path)

    # --------------------------------------------------------
    # LABEL FROM FOLDER NAME
    # --------------------------------------------------------

    parent_folder = os.path.basename(
        os.path.dirname(video_path)
    )

    label = parent_folder.strip().lower()

    # --------------------------------------------------------
    # IF DATASET HAS ALL VIDEOS IN SAME FOLDER,
    # USE FILENAME AS LABEL
    # --------------------------------------------------------

    if label in ["isl_dataset", "videos", "data", "dataset"]:

        filename_without_ext = os.path.splitext(
            filename
        )[0]

        label = filename_without_ext.split("_")[0].lower()

    # --------------------------------------------------------
    # OPEN VIDEO
    # --------------------------------------------------------

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():

        print(
            "Could not open:",
            filename
        )

        continue

    local_frame = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame_count += 1
        local_frame += 1

        # ----------------------------------------------------
        # PROCESS EVERY 3rd FRAME
        # ----------------------------------------------------

        if local_frame % 3 != 0:
            continue

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        result = hands.process(rgb)

        if not result.multi_hand_landmarks:
            continue

        hand_landmarks = result.multi_hand_landmarks[0]

        features = normalize_landmarks(
            hand_landmarks
        )

        if features is None:
            continue

        valid_count += 1

        X = np.array(
            [features],
            dtype=np.float32
        )

        prediction = model.predict(X)[0]

        predicted_label = str(
            prediction
        ).strip().lower()

        actual_label = label

        y_true.append(actual_label)
        y_pred.append(predicted_label)

        class_total[actual_label] += 1

        if predicted_label == actual_label:

            class_correct[actual_label] += 1


    cap.release()

    if video_count % 25 == 0:

        print(
            f"Processed {video_count}/{len(video_files)} videos..."
        )


# ============================================================
# RESULTS
# ============================================================

print("\n========================================")
print(" EVALUATION COMPLETE")
print("========================================\n")

print(
    "Videos processed:",
    video_count
)

print(
    "Total frames:",
    frame_count
)

print(
    "Valid hand samples:",
    valid_count
)

print(
    "Samples evaluated:",
    len(y_true)
)

print()


if len(y_true) == 0:

    print(
        "No valid samples were evaluated."
    )

    hands.close()

    raise SystemExit


# ============================================================
# OVERALL ACCURACY
# ============================================================

accuracy = accuracy_score(
    y_true,
    y_pred
)

print(
    f"OVERALL ACCURACY: {accuracy * 100:.2f}%"
)

print()


# ============================================================
# PER SIGN ACCURACY
# ============================================================

print("========================================")
print(" PER-SIGN ACCURACY")
print("========================================")

all_classes = sorted(
    set(y_true)
)

for sign in all_classes:

    total = class_total[sign]

    correct = class_correct[sign]

    if total > 0:

        sign_accuracy = (
            correct / total
        ) * 100

    else:

        sign_accuracy = 0

    print(
        f"{sign:<15} "
        f"{correct:>4}/{total:<4} "
        f"{sign_accuracy:>6.2f}%"
    )


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\n========================================")
print(" CLASSIFICATION REPORT")
print("========================================\n")

print(
    classification_report(
        y_true,
        y_pred,
        zero_division=0
    )
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("\n========================================")
print(" CONFUSION MATRIX")
print("========================================\n")

labels = sorted(
    set(y_true) | set(y_pred)
)

matrix = confusion_matrix(
    y_true,
    y_pred,
    labels=labels
)

print(
    "Labels:"
)

print(
    labels
)

print()

print(matrix)


# ============================================================
# WEAK SIGNS
# ============================================================

print("\n========================================")
print(" WEAK SIGNS (< 60%)")
print("========================================")

weak_found = False

for sign in all_classes:

    total = class_total[sign]

    correct = class_correct[sign]

    if total == 0:
        continue

    sign_accuracy = (
        correct / total
    ) * 100

    if sign_accuracy < 60:

        weak_found = True

        print(
            f"{sign:<15} "
            f"{sign_accuracy:.2f}%"
        )


if not weak_found:

    print(
        "No sign below 60% in this evaluation."
    )


# ============================================================
# FINISH
# ============================================================

hands.close()

print("\n========================================")
print(" TEST FINISHED")
print("========================================")