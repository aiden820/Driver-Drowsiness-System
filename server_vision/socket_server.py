import socket
import threading

# ── 소켓 서버 설정 ─────────────────────────────────────────────
HOST = "0.0.0.0"  # 모든 네트워크 인터페이스에서 수신
PORT = 5000

def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def handle_client(conn, addr):
    print(f"[연결됨] ESP8266 접속: {addr}")
    try:
        while True:
            # 메인 루프에서 status_text 받아서 전송
            pass
    except Exception as e:
        print(f"[연결 끊김] {addr} - {e}")
    finally:
        conn.close()

class SocketServer:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, PORT))
        self.server.listen(1)
        self.conn = None
        print(f"[서버 시작] IP: {get_my_ip()} | PORT: {PORT}")
        print(f"ESP8266에 입력할 IP: {get_my_ip()}")

    def wait_for_client(self):
        print("[대기 중] ESP8266 연결 기다리는 중...")
        self.conn, addr = self.server.accept()
        print(f"[연결됨] {addr}")

    def send_status(self, status_text: str):
        if self.conn:
            try:
                message = status_text + "\n"  # 개행문자로 메시지 구분
                self.conn.sendall(message.encode("utf-8"))
            except Exception as e:
                print(f"[전송 오류] {e}")
                self.conn = None

    def close(self):
        if self.conn:
            self.conn.close()
        self.server.close()