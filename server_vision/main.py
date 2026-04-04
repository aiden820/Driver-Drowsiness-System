import cv2
import math
import time

try:
    import mediapipe.solutions.face_mesh as mp_face_mesh
except ModuleNotFoundError:
    import mediapipe.python.solutions.face_mesh as mp_face_mesh

# 두 점 사이의 유클리디안 거리 계산 함수 (2D)
def euclidean_distance(p1, p2):
    return math.dist((p1.x, p1.y), (p2.x, p2.y))

# EAR(눈 비율) 계산 함수
def eye_aspect_ratio(eye_landmarks, landmarks):
    p = [landmarks.landmark[i] for i in eye_landmarks]
    v1 = euclidean_distance(p[1], p[5])
    v2 = euclidean_distance(p[2], p[4])
    h = euclidean_distance(p[0], p[3])
    return (v1 + v2) / (2.0 * h)

# MAR(입 비율) 계산 함수
def mouth_aspect_ratio(landmarks):
    top = landmarks.landmark[13]; bottom = landmarks.landmark[14]
    left = landmarks.landmark[78]; right = landmarks.landmark[308]
    return euclidean_distance(top, bottom) / euclidean_distance(left, right)

# 고개 숙임(Pitch) 비율 계산 함수
def head_pitch_ratio(landmarks):
    top = landmarks.landmark[10]   # 이마
    nose = landmarks.landmark[1]   # 코끝
    chin = landmarks.landmark[152] # 턱끝
    
    # y축 거리 기반 비율 계산
    top_to_nose = nose.y - top.y
    nose_to_chin = chin.y - nose.y
    if top_to_nose == 0: return 1.0
    return nose_to_chin / top_to_nose

# --- 🎯 최종 설정값 (친구와 함께 튜닝하세요) ---
EAR_THRESHOLD = 0.20        # 눈 감음 기준
SLEEP_TIME_THRESHOLD = 1.5  # 눈 감음 지속 시간 (초)
MAR_THRESHOLD = 0.55        # 하품 기준
PITCH_THRESHOLD = 0.55      # 고개 숙임 기준 (민감하면 0.50으로 더 낮추세요)
PITCH_TIME_THRESHOLD = 1.0  # 고개 숙임 지속 시간 (초)
MISSING_TIME_THRESHOLD = 2.0 # 얼굴 실종 경고 시간 (초)

# 타이머 변수 초기화
blink_start_time = None
pitch_start_time = None
face_missing_start_time = None

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.8)
cap = cv2.VideoCapture(1)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    # 기본 상태 설정
    status_text = "Awake"
    color = (0, 255, 0)

    if results.multi_face_landmarks:
        face_missing_start_time = None # 얼굴 발견 시 실종 타이머 리셋
        
        for face_landmarks in results.multi_face_landmarks:
            # 수치 계산
            l_ear = eye_aspect_ratio(LEFT_EYE, face_landmarks)
            r_ear = eye_aspect_ratio(RIGHT_EYE, face_landmarks)
            avg_ear = min(l_ear, r_ear) # 안경/머리카락 대응 최솟값 전략
            mar = mouth_aspect_ratio(face_landmarks)
            pitch = head_pitch_ratio(face_landmarks)

            # --- 💡 계층적 판정 로직 (고개 -> 하품 -> 눈) ---
            
            # 1. 고개 숙임 판정
            if pitch < PITCH_THRESHOLD:
                if pitch_start_time is None:
                    pitch_start_time = time.time()
                if time.time() - pitch_start_time >= PITCH_TIME_THRESHOLD:
                    status_text = "HEAD DROP!"
                    color = (0, 0, 255)
            else:
                pitch_start_time = None

            # 2. 하품 판정 (고개 숙임이 아닐 때만 체크)
            if status_text == "Awake" and mar > MAR_THRESHOLD:
                status_text = "YAWNING!"
                color = (0, 255, 255)
            
            # 3. 눈 감음 판정 (앞선 경고들이 없을 때만 체크)
            if status_text == "Awake" and avg_ear < EAR_THRESHOLD:
                if blink_start_time is None:
                    blink_start_time = time.time()
                if time.time() - blink_start_time >= SLEEP_TIME_THRESHOLD:
                    status_text = "DROWSY (EYES)!"
                    color = (0, 0, 255)
            else:
                blink_start_time = None

            # 실시간 수치 모니터링 텍스트
            cv2.putText(frame, f"EAR:{avg_ear:.2f} MAR:{mar:.2f} PITCH:{pitch:.2f}", (30, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    else:
        # 🚨 얼굴 인식 실패 (고개를 너무 숙였거나 뒤로 젖혔을 때)
        pitch_start_time = None
        blink_start_time = None
        
        if face_missing_start_time is None:
            face_missing_start_time = time.time()
        
        missing_duration = time.time() - face_missing_start_time
        if missing_duration >= MISSING_TIME_THRESHOLD:
            status_text = "FACE MISSING! (EMERGENCY)"
            color = (0, 0, 255)
            cv2.putText(frame, f"Missing: {missing_duration:.1f}s", (30, 120), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    # 최종 상태 UI 출력
    cv2.putText(frame, f"Status: {status_text}", (30, 80), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imshow('Drowsy Detection System v4.0', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()