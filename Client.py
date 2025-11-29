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

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] Connected to server.")
        print("Type messages to send to the server:")

        threading.Thread(target=self.receive_messages, daemon=True).start()

        while True:
            try:
                msg = input()
            except EOFError:
                break

            if not msg:
                continue

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                self.sock.send(msg.encode())
                print(f"[{ts}] [YOU] >> {msg}")
            except Exception as e:
                print(f"[{ts}] [ERROR] Failed to send: {e}")
                break

    def receive_messages(self):
        while True:
            try:
                data = self.sock.recv(1024)
                if not data:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{ts}] [INFO] Server closed the connection.")
                    break

                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{ts}] [SERVER] {data.decode()}")
            except:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{ts}] [ERROR] Connection error or interrupted.")
                break


if __name__ == "__main__":
    Client().start()
