import cv2
import mediapipe as mp
import pandas as pd
import os
import numpy as np


# ==========================================
# PATHS
# ==========================================

DATASET_DIR = r"C:\communcation\backend\ISL_DATASET"

OUTPUT_FILE = (
    r"C:\communcation\backend\model\dataset\sign_landmarks.csv"
)


# ==========================================
# MEDIAPIPE
# ==========================================

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# ==========================================
# NORMALIZATION FUNCTION
# ==========================================

def normalize_landmarks(hand_landmarks):

    points = np.array(
        [
            [landmark.x, landmark.y, landmark.z]
            for landmark in hand_landmarks.landmark
        ],
        dtype=np.float32
    )

    # --------------------------------------
    # Wrist becomes origin
    # --------------------------------------

    wrist = points[0].copy()

    points = points - wrist


    # --------------------------------------
    # Hand-size normalization
    # Distance:
    # Wrist → Middle finger MCP
    # --------------------------------------

    hand_size = np.linalg.norm(points[9])

    if hand_size < 1e-6:
        return None

    points = points / hand_size


    # --------------------------------------
    # Flatten
    # 21 landmarks × 3 values
    # = 63 features
    # --------------------------------------

    return points.flatten().tolist()


# ==========================================
# DATA STORAGE
# ==========================================

rows = []


# ==========================================
# HEADER
# ==========================================

print("======================================")
print(" ADVANCED ISL LANDMARK EXTRACTION")
print("======================================")
print()

print("Normalization:")
print(" - Wrist-relative coordinates")
print(" - Hand-size normalization")
print(" - 63 normalized features")
print()


# ==========================================
# DATASET CHECK
# ==========================================

if not os.path.exists(DATASET_DIR):

    print("ERROR: Dataset folder not found!")
    print(DATASET_DIR)

    hands.close()

    exit()


# ==========================================
# FIND SIGN FOLDERS
# ==========================================

sign_folders = [
    folder
    for folder in os.listdir(DATASET_DIR)
    if os.path.isdir(
        os.path.join(DATASET_DIR, folder)
    )
    and folder != ".cache"
]


print(f"Signs found: {len(sign_folders)}")
print()


# ==========================================
# COUNTERS
# ==========================================

total_videos = 0
processed_videos = 0
failed_videos = 0
total_frames = 0
normalized_frames = 0


# ==========================================
# PROCESS DATASET
# ==========================================

for sign in sorted(sign_folders):

    sign_path = os.path.join(
        DATASET_DIR,
        sign
    )


    video_files = [
        file
        for file in os.listdir(sign_path)
        if file.lower().endswith(".mp4")
    ]


    if not video_files:
        continue


    print(
        f"[SIGN] {sign} -> "
        f"{len(video_files)} videos"
    )


    # ======================================
    # PROCESS EACH VIDEO
    # ======================================

    for video_name in sorted(video_files):

        total_videos += 1

        video_path = os.path.join(
            sign_path,
            video_name
        )


        cap = cv2.VideoCapture(video_path)


        if not cap.isOpened():

            print(
                f"  ERROR: {video_name}"
            )

            failed_videos += 1

            continue


        frame_count = 0
        landmark_frames = []


        # ==================================
        # READ VIDEO
        # ==================================

        while True:

            success, frame = cap.read()


            if not success:
                break


            frame_count += 1
            total_frames += 1


            # -------------------------------
            # Process every 3rd frame
            # -------------------------------

            if frame_count % 3 != 0:
                continue


            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )


            result = hands.process(rgb)


            if not result.multi_hand_landmarks:
                continue


            hand = result.multi_hand_landmarks[0]


            # -------------------------------
            # NORMALIZE LANDMARKS
            # -------------------------------

            normalized = normalize_landmarks(
                hand
            )


            if normalized is None:
                continue


            landmark_frames.append(
                normalized
            )


            normalized_frames += 1


        cap.release()


        # ==================================
        # CHECK VIDEO
        # ==================================

        if not landmark_frames:

            print(
                f"  WARNING: "
                f"No valid hand -> {video_name}"
            )

            failed_videos += 1

            continue


        # ==================================
        # ADD FRAMES
        # ==================================

        for landmarks in landmark_frames:

            row = [sign]

            row.extend(landmarks)

            rows.append(row)


        processed_videos += 1


    print()


# ==========================================
# EXTRACTION SUMMARY
# ==========================================

print("======================================")
print(" EXTRACTION FINISHED")
print("======================================")
print()

print(
    f"Total videos       : {total_videos}"
)

print(
    f"Processed videos   : {processed_videos}"
)

print(
    f"Failed videos      : {failed_videos}"
)

print(
    f"Total frames       : {total_frames}"
)

print(
    f"Valid landmarks    : {normalized_frames}"
)

print(
    f"Dataset samples    : {len(rows)}"
)

print()


# ==========================================
# CHECK DATA
# ==========================================

if not rows:

    print(
        "ERROR: "
        "No landmark data was created."
    )

    hands.close()

    exit()


# ==========================================
# CREATE COLUMN NAMES
# ==========================================

columns = ["label"]


for i in range(21):

    columns.extend(
        [
            f"x{i}",
            f"y{i}",
            f"z{i}"
        ]
    )


# ==========================================
# CREATE DATAFRAME
# ==========================================

df = pd.DataFrame(
    rows,
    columns=columns
)


# ==========================================
# CREATE OUTPUT DIRECTORY
# ==========================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)


# ==========================================
# SAVE CSV
# ==========================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==========================================
# FINAL INFORMATION
# ==========================================

print("======================================")
print(" NORMALIZED CSV CREATED SUCCESSFULLY")
print("======================================")
print()

print("Saved at:")
print(OUTPUT_FILE)

print()

print(
    f"Rows    : {len(df)}"
)

print(
    f"Columns : {len(df.columns)}"
)

print()

print("Feature format:")
print("63 normalized landmark features")

print()

print("======================================")
print(" NEXT STEP: ADVANCED MODEL TRAINING")
print("======================================")


# ==========================================
# CLOSE MEDIAPIPE
# ==========================================

hands.close()