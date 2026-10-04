import cv2
import mediapipe as mp
import numpy as np

# 🔹 MediaPipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True)

mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(static_image_mode=True)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True)


# 🔥 INJURY TYPE DETECTION
def detect_injury_type(img):

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Red detection
    lower1 = np.array([0,120,70])
    upper1 = np.array([10,255,255])
    lower2 = np.array([170,120,70])
    upper2 = np.array([180,255,255])

    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)

    red_pixels = cv2.countNonZero(mask1 + mask2)

    brightness = np.mean(img)

    if red_pixels > 200:
        return "Cut / Bleeding"

    elif brightness < 80:
        return "Burn Injury"

    elif red_pixels < 50 and brightness > 130:
        return "Swelling"

    return "No clear injury"


# 🔥 FACE REGION ISSUE DETECTION
def detect_face_issues(img, face_landmarks, w, h):

    def get_roi(x, y, size=20):
        return img[max(0,y-size):min(h,y+size), max(0,x-size):min(w,x+size)]

    def red_check(roi):
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        lower1 = np.array([0,120,70])
        upper1 = np.array([10,255,255])
        lower2 = np.array([170,120,70])
        upper2 = np.array([180,255,255])

        mask1 = cv2.inRange(hsv, lower1, upper1)
        mask2 = cv2.inRange(hsv, lower2, upper2)

        return cv2.countNonZero(mask1 + mask2)

    # 👁️ Eyes
    left_eye = face_landmarks.landmark[33]
    right_eye = face_landmarks.landmark[263]

    lx, ly = int(left_eye.x * w), int(left_eye.y * h)
    rx, ry = int(right_eye.x * w), int(right_eye.y * h)

    if red_check(get_roi(lx, ly)) > 30 or red_check(get_roi(rx, ry)) > 30:
        return "Eye Redness / Bleeding"

    # 👄 Mouth
    mouth = face_landmarks.landmark[13]
    mx, my = int(mouth.x * w), int(mouth.y * h)

    if red_check(get_roi(mx, my)) > 50:
        return "Mouth Bleeding"

    # 👂 Ear (approx)
    left_ear = face_landmarks.landmark[234]
    right_ear = face_landmarks.landmark[454]

    ex1, ey1 = int(left_ear.x * w), int(left_ear.y * h)
    ex2, ey2 = int(right_ear.x * w), int(right_ear.y * h)

    if red_check(get_roi(ex1, ey1)) > 50 or red_check(get_roi(ex2, ey2)) > 50:
        return "Ear Bleeding"

    # 👃 Nose
    nose = face_landmarks.landmark[1]
    nx, ny = int(nose.x * w), int(nose.y * h)

    if red_check(get_roi(nx, ny)) > 50:
        return "Nose Bleeding"

    return None


# 🔥 MAIN FUNCTION
def detect_issue(image):

    img = np.array(image)
    h, w, _ = img.shape

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 🔹 Detect injury type
    injury = detect_injury_type(img)

    # 🔹 HAND
    hand_result = hands.process(rgb)
    if hand_result.multi_hand_landmarks:

        if "cut" in injury.lower():
            return f"Hand - {injury}", 0.85
        elif "burn" in injury.lower():
            return f"Hand - {injury}", 0.8
        elif "swelling" in injury.lower():
            return f"Hand - {injury}", 0.75
        else:
            return "Hand Detected (No major issue)", 0.7

    # 🔹 FACE
    face_result = face_mesh.process(rgb)
    if face_result.multi_face_landmarks:

        for face_landmarks in face_result.multi_face_landmarks:

            face_issue = detect_face_issues(img, face_landmarks, w, h)

            if face_issue:
                return f"Face - {face_issue}", 0.9

        return f"Face - {injury}", 0.7

    # 🔹 FULL BODY
    pose_result = pose.process(rgb)

    if pose_result.pose_landmarks:

        landmarks = pose_result.pose_landmarks.landmark

        left_knee = landmarks[25]
        right_knee = landmarks[26]

        if left_knee.visibility > 0.5 or right_knee.visibility > 0.5:

            if "cut" in injury.lower():
                return f"Leg - {injury}", 0.85
            elif "burn" in injury.lower():
                return f"Leg - {injury}", 0.8
            elif "swelling" in injury.lower():
                return f"Leg - {injury}", 0.75
            else:
                return "Leg Detected (No major issue)", 0.7

        return f"Body - {injury}", 0.65

    # 🔹 FINAL
    return f"Unknown - {injury}", 0.5