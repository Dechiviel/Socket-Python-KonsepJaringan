import socket
import sys
import threading
import signal
import logging
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
            self.running = True
            self.client_names = {}
            signal.signal(signal.SIGINT, self.shutdown)
            logging.basicConfig(
                filename='chat_log.txt',
                level=logging.INFO,
                format='%(asctime)s - %(message)s'
            )
            

    def start(self):
        print("Memulai server.")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(5)

        print(f"Server berjalan di {self.host}:{self.port}")
        print("Perintah server: list | send <id> <msg> | broadcast <msg>\n")

        threading.Thread(target=self.server_input, daemon=True).start()

        while self.running:
            try:
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
            except OSError:
                break

    def handle_client(self, client_socket, client_id):
        nickname = None
        try:    
            client_socket.send("Masukkan nickname anda: ".encode())
            nickname = client_socket.recv(1024).decode().strip()

            with self.lock:
                self.clients.name[client_id] = nickname

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] [INFO] Client{client_id} set nickname: {nickname}")
    
            while True:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break

                    msg = data.decode().strip()
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{ts}] [{nickname}] >> {msg}")
                    logging.info(f"[{nickname}] >> {msg}")

                except Exception as e:
                    print(f"Error receiving from {nickname}: {e}")
                    break

        except Exception as e:
            print(f"Error handling client{client_id}: {e}")
        finally:
            with self.lock:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if client_id in self.clients:
                    print(f"[{ts}] [INFO] Client{client_id} terputus.")
                    del self.clients[client_id]
                if client_id in self.client_names:
                    del self.client_names[client_id]
        try:
            client_socket.close()
        except:
            pass

    def server_input(self):
        """Server mengetik command (list, send, broadcast)."""
        while self.running:
            try:
                cmd = input("")

                if cmd == "list":
                    print("\n=== Daftar Client ===")
                    with self.lock:
                        if not self.clients:
                            print("Tidak ada client terhubung.")
                    for cid in self.clients:
                        nickname = self.client_names.get(cid, "Unknown")
                        print(f"Client{cid}: {nickname}")
                    print("=====================\n")

                elif cmd == "help":
                    print("\n=== Server Commands ===")
                    print("list              - Show all connected clients")
                    print("send <id> <msg>   - Send message to specific client")
                    print("broadcast <msg>   - Send message to all clients")
                    print("kick <id>         - Disconnect a client")
                    print("======================\n")

                elif cmd.startswith("send "):
                    parts = cmd.split(" ", 2)
                    if len(parts) < 3:
                        print("Format salah: send <id> <pesan>")
                        continue
                    
                    try:
                        target = int(parts[1])
                    except ValueError:
                        print("ID harus berupa angka!")
                        continue

                    msg = parts[2]

                    with self.lock:
                        if target in self.clients:
                            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            msg_to_send = f"[{ts}] [SERVER] {msg}"
                            try:
                                self.clients[target].send(msg_to_send.encode())
                                nickname = self.client_names.get(target, "Unknown")
                                print(f"[{ts}] [SERVER] Mengirim ke Client{nickname}: {msg}")
                            except Exception as e:
                                print(f"[{ts}] [ERROR] Failed to send to Client{target}: {e}")
                        else:
                            print("Client tidak ditemukan.")

                elif cmd.startswith("broadcast "):
                    msg = cmd.split(" ", 1)[1]
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with self.lock:
                        success_count = 0
                        for cid, sock in list(self.clients.items()):
                            try:
                                sock.send(f"[{ts}] [Broadcast] {msg}".encode())
                                success_count += 1
                            except Exception:
                                # ignore sending errors for broadcast
                                pass
                    print(f"[{ts}] Broadcast berhasil ke {success_count} client")
                
                elif cmd.startswith("kick "):
                    parts = cmd.split(" ", 1)
                    if len(parts) < 2:
                        print("Format salah: kick <id>")
                        continue

                    try:
                        target = int(parts[1])
                    except ValueError:
                        print("ID harus berupa angka!")
                        continue

                    with self.lock:
                        if target in self.clients:
                            try:
                                self.clients[target].close()
                                print(f"Client{target} dikick dari server")
                            except Exception as e:
                                print("fError kicking client: {e}")

                        else:
                            print("Client tidak ditemukan.")

                elif cmd == "exit" or cmd == "quit":
                    self.shutdown(None, None)

                elif cmd.strip():
                        print("Peritah tidak dikenal!")

            except EOFError:
                break
            except Exception as e:
                print(f"Error: {e}")

    def shutdown(self, signum, frame):
        print("\n[INFO] shutting down server...")
        self.running = False
        with self.lock:
            for sock in self.clients.values():
                try:
                    sock.close()
                except:
                    pass
        try:
            self.server.close()
        except:
            pass
        sys.exit(0)

if __name__ == "__main__":
    Server().start()
