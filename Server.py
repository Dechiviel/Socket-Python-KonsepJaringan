import socket
import sys
import threading
from datetime import datetime

class Server:
    def __init__(self):
        if len(sys.argv) != 3:
            print("Usage: " + sys.argv[0] + " <hostf> <port>")
            sys.exit(1)
        else:
            self.host = sys.argv[1]
            self.port = int(sys.argv[2])
            self.clients = {}
            self.client_counter = 1
            self.lock = threading.Lock()

    def start(self):
        print("Memulai server.")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(5)

        print(f"Server berjalan di {self.host}:{self.port}")
        print("Perintah server: list | send <id> <msg> | broadcast <msg>\n")

        threading.Thread(target=self.server_input, daemon=True).start()

        while True:
            sock, addr = self.server.accept()

            with self.lock:
                client_id = self.client_counter
                self.clients[client_id] = sock
                self.client_counter += 1

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] [INFO] Client{client_id} terhubung dari {addr}.")

            threading.Thread(
                target=self.handle_client,
                args=(sock, client_id),
                daemon=True
            ).start()

    def handle_client(self, client_socket, client_id):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Menangani pesan dari client.")
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break

                msg = data.decode().strip()
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{ts}] [Client{client_id}] >> {msg}")

            except:
                break

        with self.lock:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] [INFO] Client{client_id} terputus.")
            del self.clients[client_id]

        client_socket.close()

    def server_input(self):
        """Server mengetik command (list, send, broadcast)."""
        while True:
            cmd = input("")

            if cmd == "list":
                print("\n=== Daftar Client ===")
                with self.lock:
                    for cid in self.clients:
                        print(f"Client{cid}")
                print("=====================\n")

            elif cmd.startswith("send "):
                parts = cmd.split(" ", 2)
                if len(parts) < 3:
                    print("Format salah: send <id> <pesan>")
                    continue

                target = int(parts[1])
                msg = parts[2]

                with self.lock:
                    if target in self.clients:
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        msg_to_send = f"[{ts}] {msg}"
                        try:
                            self.clients[target].send(msg_to_send.encode())
                            print(f"[{ts}] [SERVER] Mengirim ke Client{target}: {msg}")
                        except Exception as e:
                            print(f"[{ts}] [ERROR] Failed to send to Client{target}: {e}")
                    else:
                        print("Client tidak ditemukan.")

            elif cmd.startswith("broadcast "):
                msg = cmd.split(" ", 1)[1]
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with self.lock:
                    for cid, sock in list(self.clients.items()):
                        try:
                            sock.send(f"[{ts}] [Broadcast] {msg}".encode())
                        except Exception:
                            # ignore sending errors for broadcast
                            pass
                print(f"[{ts}] Broadcast berhasil.")

            else:
                print("Perintah tidak dikenal!")



if __name__ == "__main__":
    Server().start()
