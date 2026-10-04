import numpy as np
import cv2
import mediapipe as mp
import json

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

def get_face_landmarks(pil_img):
    try:
        img = np.array(pil_img)
        h, w, _ = img.shape
        rgb = cv2.cvtColor(img, cv2.COLOR_RGB2BGR) # PIL image is RGB, cv2 expects BGR internally but let's convert to RGB for MediaPipe
        rgb_mp = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
        
        results = face_mesh.process(rgb_mp)
        if not results.multi_face_landmarks:
            return None
        return results.multi_face_landmarks[0]
    except Exception as e:
        print("Error getting face landmarks:", e)
        return None

def dist_3d(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)

def calculate_ear(landmarks):
    # Landmark coordinates
    points = [(l.x, l.y, l.z) for l in landmarks.landmark]
    
    # Left eye landmarks
    # vertical lids: 160-144, 158-153
    # horizontal: 33-133
    d_v1 = dist_3d(points[160], points[144])
    d_v2 = dist_3d(points[158], points[153])
    d_h = dist_3d(points[33], points[133])
    left_ear = (d_v1 + d_v2) / (2.0 * d_h) if d_h > 0 else 0
    
    # Right eye landmarks
    # vertical lids: 386-374, 385-373
    # horizontal: 263-362
    d_rv1 = dist_3d(points[386], points[374])
    d_rv2 = dist_3d(points[385], points[373])
    d_rh = dist_3d(points[263], points[362])
    right_ear = (d_rv1 + d_rv2) / (2.0 * d_rh) if d_rh > 0 else 0
    
    return left_ear, right_ear

def calculate_smile_ratio(landmarks):
    points = [(l.x, l.y, l.z) for l in landmarks.landmark]
    
    # Mouth corners: 61, 291
    mouth_width = dist_3d(points[61], points[291])
    
    # Outer eye corners for normalization: 33, 263
    eye_dist = dist_3d(points[33], points[263])
    
    # Smile ratio (mouth width relative to eye distance)
    return mouth_width / eye_dist if eye_dist > 0 else 0

def get_face_signature(landmarks):
    # Stabilized landmarks representing general face structure
    key_indices = [
        33, 133, 159, 145, # Left eye key points
        263, 362, 386, 374, # Right eye key points
        1, 4, 168, 197, # Nose bridge and tip
        61, 291, 13, 14, # Mouth corners and lips center
        152, 10, 234, 454 # Forehead, chin, ears/jaw border
    ]
    
    points = [(l.x, l.y, l.z) for l in landmarks.landmark]
    nose_center = points[1] # center of nose tip
    eye_dist = dist_3d(points[33], points[263])
    
    if eye_dist == 0:
        eye_dist = 1.0
        
    normalized_signature = []
    for idx in key_indices:
        p = points[idx]
        # Translate to nose center and scale by eye distance
        nx = (p[0] - nose_center[0]) / eye_dist
        ny = (p[1] - nose_center[1]) / eye_dist
        nz = (p[2] - nose_center[2]) / eye_dist
        normalized_signature.append([nx, ny, nz])
        
    return normalized_signature

def verify_face(sig_a_json, sig_b_json, threshold=0.22):
    try:
        if not sig_a_json or not sig_b_json:
            return False, 999.0
            
        sig_a = json.loads(sig_a_json) if isinstance(sig_a_json, str) else sig_a_json
        sig_b = json.loads(sig_b_json) if isinstance(sig_b_json, str) else sig_b_json
        
        if len(sig_a) != len(sig_b):
            return False, 999.0
            
        distances = []
        for p_a, p_b in zip(sig_a, sig_b):
            distances.append(np.sqrt((p_a[0] - p_b[0])**2 + (p_a[1] - p_b[1])**2 + (p_a[2] - p_b[2])**2))
            
        avg_dist = np.mean(distances)
        return avg_dist < threshold, avg_dist
    except Exception as e:
        print("Error verifying face:", e)
        return False, 999.0
