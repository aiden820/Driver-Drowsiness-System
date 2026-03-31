# Driver-Drowsiness-System
Vision-based Drowsiness Detection with TCP/IP &amp; CAN Bus Communication

# 🚗 졸음운전 방지 시스템 (Drowsy Driving Prevention System)

**OpenCV 기반 영상 인식과 CAN 통신을 결합한 임베디드 안전 시스템**

### 🛠 기술 스택
- **Vision/Server:** Python, OpenCV, MediaPipe
- **Gateway:** ESP32 (C/C++, TCP/IP to CAN)
- **Control:** STM32 (C, CAN Bus Control)

### 📂 폴더 구조
- `server_vision/`: 맥북 카메라 졸음 감지 및 TCP 서버 로직
- `firmware_esp32/`: Wi-Fi 데이터를 CAN 패킷으로 변환하는 게이트웨이
- `firmware_stm32/`: CAN 신호를 받아 부저 및 모터 제어
