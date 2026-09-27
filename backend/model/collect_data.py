import cv2
import mediapipe as mp
import csv
import os

DATASET_FILE = "dataset/sign_data.csv"

os.makedirs("dataset", exist_ok=True)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera could not be opened.")
    exit()

print("====================================")
print(" AI SIGN DATA COLLECTION")
print("====================================")
print("Enter sign name:")
sign_name = input("Sign: ").strip()

if not sign_name:
    print("Sign name cannot be empty.")
    cap.release()
    exit()

print()
print(f"Collecting data for: {sign_name}")
print("Press SPACE to save a sample.")
print("Press Q to quit.")
print()

file_exists = os.path.exists(DATASET_FILE)

with open(DATASET_FILE, "a", newline="") as file:
    writer = csv.writer(file)

    if not file_exists:
        header = ["label"]

        for i in range(21):
            header.extend([f"x{i}", f"y{i}", f"z{i}"])

        writer.writerow(header)

    sample_count = 0

    while True:
        success, frame = cap.read()

        if not success:
            print("Could not read camera.")
            break

        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            hand_landmarks = result.multi_hand_landmarks[0]

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            cv2.putText(
                frame,
                f"Sign: {sign_name}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"Samples: {sample_count}",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                "SPACE = Save | Q = Quit",
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

        else:
            cv2.putText(
                frame,
                "No hand detected",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

        cv2.imshow("AI Sign Data Collection", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        if key == 32 and result.multi_hand_landmarks:
            landmarks = result.multi_hand_landmarks[0]

            row = [sign_name]

            for landmark in landmarks.landmark:
                row.extend([
                    landmark.x,
                    landmark.y,
                    landmark.z
                ])

            writer.writerow(row)
            file.flush()

            sample_count += 1
            print(f"Sample saved: {sample_count}")

cap.release()
cv2.destroyAllWindows()
hands.close()

print()
print(f"Finished. Total samples collected: {sample_count}")