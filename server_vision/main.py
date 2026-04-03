import cv2
import mediapipe.python.solutions.face_mesh as mp_face_mesh
import math

# 1. 설정
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)
cap = cv2.VideoCapture(1) # 아까 성공한 1번 카메라

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # 왼쪽 눈 위/아래 특징점 추출 (번호: 159, 145)
            # .y 값은 0~1 사이의 비율이므로 화면 높이를 곱해줍니다.
            ih, iw, ic = frame.shape
            p_top = face_landmarks.landmark[159]
            p_bottom = face_landmarks.landmark[145]
            
            # 수직 거리 계산
            distance = abs(p_top.y - p_bottom.y)
            
            # 화면에 수치 표시
            color = (0, 255, 0) # 평소엔 초록색
            if distance < 0.015: # 눈을 감았다고 판단되는 수치 (직접 조절해보세요!)
                color = (0, 0, 255) # 감으면 빨간색
                cv2.putText(frame, "SLEEPING!", (100, 200), 
                            cv2.FONT_HERSHEY_SIMPLEX, 3, color, 5)
            
            cv2.putText(frame, f"Eye: {distance:.4f}", (30, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    cv2.imshow('Drowsy Detection Test', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()