import socket
import sys
import threading
from datetime import datetime


class Client:
    def __init__(self):
        if len(sys.argv) != 3:
            print("Usage: " + sys.argv[0] + " <hostf> <port>")
            sys.exit(1)
        else:
            self.host = sys.argv[1]
            self.port = int(sys.argv[2])
            self.running = True

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] Connected to server.")
        threading.Thread(target=self.receive_messages, daemon=True).start()
        import time
        time.sleep(0.1)

        print(f"Type messages to send to the server:")

        while self.running:
            try:
                msg = input()
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\n[INFO] Disconnecting...")

            if not msg.strip():
                continue

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                self.sock.send(msg.encode())
                if msg.strip():
                    pass
            except BrokenPipeError:
                print(f"[{ts}] [ERROR] Server closed the connection.")
                break
            except Exception as e:
                print(f"[ERROR] Connection error: {e}")
            finally:
                self.cleanup()

    def receive_messages(self):
        while self.running:
            try:
                data = self.sock.recv(1024)
                if not data:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{ts}] [INFO] Server closed the connection.")
                    self.running = False
                    break

                message = data.decode().strip()
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if "Masukkan nickname" in message:
                    print(f"\n{message}", end="", flush=True)
                else:
                    print(f"\n[{ts}] {message}")

            except ConnectionResetError:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{ts}] [ERROR] Connection error or interrupted.")
                break


if __name__ == "__main__":
    Client().start()
