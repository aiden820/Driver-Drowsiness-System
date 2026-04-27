import cv2
import math
import time
import mediapipe as mp

# ── MediaPipe 초기화 (버전 호환 방어 코드 포함) ──────────────────────────
try:
    mp_face_mesh = mp.solutions.face_mesh
except AttributeError:
    # mediapipe 0.10+ Apple Silicon 대응
    from mediapipe.tasks import python as mp_python
    raise RuntimeError(
        "mediapipe 버전 오류!\n"
        "pip install mediapipe==0.10.9  또는\n"
        "pip install mediapipe-silicon  을 실행하세요."
    )

# ── 유틸 함수 ─────────────────────────────────────────────────────────────
def euclidean_distance(p1, p2):
    return math.dist((p1.x, p1.y), (p2.x, p2.y))

def eye_aspect_ratio(eye_landmarks, landmarks):
    p = [landmarks.landmark[i] for i in eye_landmarks]
    v1 = euclidean_distance(p[1], p[5])
    v2 = euclidean_distance(p[2], p[4])
    h  = euclidean_distance(p[0], p[3])
    return (v1 + v2) / (2.0 * h) if h > 0 else 0.0

def mouth_aspect_ratio(landmarks):
    top    = landmarks.landmark[13]
    bottom = landmarks.landmark[14]
    left   = landmarks.landmark[78]
    right  = landmarks.landmark[308]
    denom  = euclidean_distance(left, right)
    return euclidean_distance(top, bottom) / denom if denom > 0 else 0.0

def head_pitch_ratio(landmarks):
    top  = landmarks.landmark[10]   # 이마
    nose = landmarks.landmark[1]    # 코끝
    chin = landmarks.landmark[152]  # 턱끝
    top_to_nose  = nose.y - top.y
    nose_to_chin = chin.y - nose.y
    return nose_to_chin / top_to_nose if top_to_nose > 0 else 1.0

# ── 설정값 ────────────────────────────────────────────────────────────────
EAR_THRESHOLD          = 0.20   # 눈 감음 기준
SLEEP_TIME_THRESHOLD   = 1.5    # 눈 감음 지속 시간 (초)
MAR_THRESHOLD          = 0.55   # 하품 기준
PITCH_THRESHOLD        = 0.55   # 고개 숙임 기준
PITCH_TIME_THRESHOLD   = 1.0    # 고개 숙임 지속 시간 (초)
MISSING_TIME_THRESHOLD = 2.0    # 얼굴 실종 경고 시간 (초)

LEFT_EYE  = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33,  160, 158, 133, 153, 144]

# ── 카메라 자동 탐색 (0 → 1 순서로 시도) ─────────────────────────────────
def open_camera():
    for idx in range(2):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            print(f"카메라 {idx}번 연결 성공")
            return cap
        cap.release()
    raise RuntimeError("사용 가능한 카메라를 찾을 수 없습니다.")

# ── 경고 카운터 & 로그 ────────────────────────────────────────────────────
warning_counts = {"HEAD DROP": 0, "YAWNING": 0, "DROWSY": 0, "FACE MISSING": 0}
log_entries    = []

def trigger_alert(label):
    warning_counts[label] += 1
    log_entries.append({"time": time.strftime("%H:%M:%S"), "event": label})
    # macOS 알림음 (시스템 벨)
    print("\a", end="", flush=True)

# ── 메인 루프 ─────────────────────────────────────────────────────────────
def main():
    blink_start_time       = None
    pitch_start_time       = None
    face_missing_start_time = None
    prev_status            = "Awake"

    cap = open_camera()

    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.8,
        min_tracking_confidence=0.5,
    ) as face_mesh:

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results   = face_mesh.process(rgb_frame)

            status_text = "Awake"
            color       = (0, 255, 0)

            if results.multi_face_landmarks:
                face_missing_start_time = None

                for face_landmarks in results.multi_face_landmarks:
                    l_ear   = eye_aspect_ratio(LEFT_EYE,  face_landmarks)
                    r_ear   = eye_aspect_ratio(RIGHT_EYE, face_landmarks)
                    avg_ear = (l_ear + r_ear) / 2          # 평균값 사용 (오판 감소)
                    mar     = mouth_aspect_ratio(face_landmarks)
                    pitch   = head_pitch_ratio(face_landmarks)

                    # 1️⃣ 고개 숙임 — 수치 자체로 먼저 경보 준비
                    if pitch < PITCH_THRESHOLD:
                        if pitch_start_time is None:
                            pitch_start_time = time.time()
                        elapsed = time.time() - pitch_start_time
                        if elapsed >= PITCH_TIME_THRESHOLD:
                            status_text = "HEAD DROP!"
                            color       = (0, 0, 255)
                        else:
                            # 타이머 진행 중에도 하품/눈 판정 차단
                            status_text = "HEAD WARNING"
                            color       = (0, 165, 255)
                    else:
                        pitch_start_time = None

                    # 2️⃣ 하품 — 고개 이상 없을 때만
                    if status_text == "Awake" and mar > MAR_THRESHOLD:
                        status_text = "YAWNING!"
                        color       = (0, 255, 255)

                    # 3️⃣ 눈 감음 — 앞선 경고 없을 때만
                    if status_text == "Awake":
                        if avg_ear < EAR_THRESHOLD:
                            if blink_start_time is None:
                                blink_start_time = time.time()
                            if time.time() - blink_start_time >= SLEEP_TIME_THRESHOLD:
                                status_text = "DROWSY (EYES)!"
                                color       = (0, 0, 255)
                        else:
                            blink_start_time = None
                    else:
                        # 다른 경고 상태일 때 눈 타이머 리셋
                        blink_start_time = None

                    # 수치 모니터링
                    cv2.putText(frame,
                        f"EAR:{avg_ear:.2f}  MAR:{mar:.2f}  PITCH:{pitch:.2f}",
                        (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

            else:
                # 얼굴 미검출
                pitch_start_time = None
                blink_start_time = None

                if face_missing_start_time is None:
                    face_missing_start_time = time.time()

                missing_dur = time.time() - face_missing_start_time
                if missing_dur >= MISSING_TIME_THRESHOLD:
                    status_text = "FACE MISSING!"
                    color       = (0, 0, 255)
                    cv2.putText(frame, f"Missing: {missing_dur:.1f}s",
                        (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

            # ── 경고 전환 감지 → 알림 트리거 ──────────────────────────
            alert_key = None
            if "HEAD DROP"     in status_text: alert_key = "HEAD DROP"
            elif "YAWNING"     in status_text: alert_key = "YAWNING"
            elif "DROWSY"      in status_text: alert_key = "DROWSY"
            elif "FACE MISSING" in status_text: alert_key = "FACE MISSING"

            if alert_key and prev_status != status_text:
                trigger_alert(alert_key)
            prev_status = status_text

            # ── 경고 카운터 & FPS 표시 ────────────────────────────────
            cv2.putText(frame, f"Status: {status_text}",
                (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.putText(frame,
                f"HEAD:{warning_counts['HEAD DROP']}  "
                f"YAWN:{warning_counts['YAWNING']}  "
                f"DROWSY:{warning_counts['DROWSY']}",
                (30, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

            cv2.imshow("Drowsy Detection System v5.0", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()

    # 종료 후 간단 리포트
    print("\n── 세션 경고 요약 ──────────────────")
    for k, v in warning_counts.items():
        print(f"  {k}: {v}회")

if __name__ == "__main__":
    main()