import cv2
import mediapipe as mp

# 0번은 맥북 내장 카메라입니다.
cap = cv2.VideoCapture(1)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("카메라를 찾을 수 없습니다.")
        break

    # 화면에 안내 문구 출력
    cv2.putText(frame, "Testing Camera... Press 'q' to Quit", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # 실제 창 띄우기
    cv2.imshow('Drowsy System Test', frame)

    # 'q' 키를 누르면 루프 탈출
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()