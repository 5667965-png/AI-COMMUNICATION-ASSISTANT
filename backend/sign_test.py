import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Camera could not be opened")
    exit()

print("Sign detection started!")
print("Press Q to close.")

while True:
    success, frame = camera.read()

    if not success:
        print("Could not read camera.")
        break

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    sign = "No hand detected"

    if result.multi_hand_landmarks:
        hand_landmarks = result.multi_hand_landmarks[0]

        mp_drawing.draw_landmarks(
            frame,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS
        )

        # Finger tip and joint landmark numbers
        tips = [8, 12, 16, 20]
        joints = [6, 10, 14, 18]

        fingers_up = 0

        for tip, joint in zip(tips, joints):
            if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[joint].y:
                fingers_up += 1

        if fingers_up == 0:
            sign = "Fist"
        elif fingers_up == 4:
            sign = "Open Hand"
        else:
            sign = f"{fingers_up} Finger(s)"

    cv2.putText(
        frame,
        "Sign: " + sign,
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow(
        "AI Communication Assistant - Sign Test",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
hands.close()
cv2.destroyAllWindows()