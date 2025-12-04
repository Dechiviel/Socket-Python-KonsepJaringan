import socket
import sys
import threading
import json
import os
import base64
from datetime import datetime

class Server:
    def __init__(self):
        if len(sys.argv) != 3:
            print("Usage: " + sys.argv[0] + " <hostf> <port>")
            sys.exit(1)
        else:
            self.host = sys.argv[1]
            self.port = int(sys.argv[2])
            self.clients = {}  # {username: socket}
            self.lock = threading.Lock()

    def start(self):
        print("Memulai server.")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(5)

        print(f"Server berjalan di {self.host}:{self.port}")
        print("Perintah server: list | send <username> <msg> | broadcast <msg>\n")

        threading.Thread(target=self.server_input, daemon=True).start()

        while True:
            sock, addr = self.server.accept()

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] [INFO] Client baru terhubung dari {addr}.")

            threading.Thread(
                target=self.handle_client,
                args=(sock, addr),
                daemon=True
            ).start()

    def handle_client(self, client_socket, addr):
        username = None
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Menunggu client set username...")
        
        # Client harus set username dulu
        try:
            data = client_socket.recv(4096)
            if data:
                payload = json.loads(data.decode().strip())
                if payload.get('type') == 'SET_USERNAME':
                    username = payload.get('username', '').strip()
                    
                    with self.lock:
                        if username in self.clients:
                            # Username sudah dipakai
                            client_socket.send(json.dumps({
                                'type': 'ERROR',
                                'message': f'Username "{username}" sudah digunakan. Koneksi ditutup.'
                            }).encode())
                            client_socket.close()
                            return
                        
                        self.clients[username] = client_socket
                    
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{ts}] [INFO] Client terdaftar dengan username: {username}")
                    
                    client_socket.send(json.dumps({
                        'type': 'SUCCESS',
                        'message': f'Selamat datang, {username}!'
                    }).encode())
                else:
                    client_socket.close()
                    return
        except Exception as e:
            print(f"Error during username setup: {e}")
            client_socket.close()
            return
        
        # Handle messages
        while True:
            try:
                data = client_socket.recv(4096)
                if not data:
                    break

                msg = data.decode().strip()
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                try:
                    payload = json.loads(msg)
                    msg_type = payload.get('type')
                    
                    print(f"[{ts}] [TRAFFIC] {username} -> {msg_type}: {payload}")
                    
                    if msg_type == 'MSG':
                        self.handle_peer_message(username, payload)
                    elif msg_type == 'FILE':
                        self.handle_file_transfer(username, payload)
                    elif msg_type == 'FILE_RESPONSE':
                        self.handle_file_response(username, payload)
                    elif msg_type == 'LIST':
                        self.handle_list_clients(username)
                    else:
                        print(f"[{ts}] [WARNING] Unknown message type: {msg_type}")
                        
                except json.JSONDecodeError:
                    print(f"[{ts}] [{username}] >> {msg}")

            except Exception as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {username}: {e}")
                break

        with self.lock:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if username and username in self.clients:
                print(f"[{ts}] [INFO] {username} terputus.")
                del self.clients[username]

        client_socket.close()
    
    def send_to_client(self, username, payload):
        """Helper untuk mengirim JSON ke client"""
        try:
            with self.lock:
                if username in self.clients:
                    msg = json.dumps(payload)
                    self.clients[username].send(msg.encode())
                    return True
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] Send to {username}: {e}")
        return False
    
    def handle_peer_message(self, from_username, payload):
        to_username = payload.get('to_username')
        message = payload.get('message', '')
        
        if not to_username:
            return
        
        with self.lock:
            if to_username not in self.clients:
                self.send_to_client(from_username, {'type': 'ERROR', 'message': f'User "{to_username}" tidak ditemukan atau tidak online'})
                return
        
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] [TRAFFIC] MSG: {from_username} -> {to_username}: {message}")
        
        self.send_to_client(to_username, {
            'type': 'PEER_MSG',
            'from_username': from_username,
            'message': message
        })
    
    def handle_file_transfer(self, from_username, payload):
        to_username = payload.get('to_username')
        filename = payload.get('filename', '')
        filedata = payload.get('filedata', '')
        
        if not to_username or not filename:
            return
        
        with self.lock:
            if to_username not in self.clients:
                self.send_to_client(from_username, {'type': 'ERROR', 'message': f'User "{to_username}" tidak ditemukan atau tidak online'})
                return
        
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filesize = len(filedata) if filedata else 0
        print(f"[{ts}] [TRAFFIC] FILE: {from_username} -> {to_username}: {filename} ({filesize} bytes)")
        
        self.send_to_client(to_username, {
            'type': 'FILE_OFFER',
            'from_username': from_username,
            'filename': filename,
            'filedata': filedata,
            'message': f'{from_username} mengirim file: {filename}. Ketik /acceptfile {from_username} atau /rejectfile {from_username}'
        })
        self.send_to_client(from_username, {'type': 'INFO', 'message': f'File {filename} dikirim ke {to_username}, menunggu respons...'})
    
    def handle_file_response(self, responder_username, payload):
        sender_username = payload.get('from_username')
        accepted = payload.get('accepted', False)
        filename = payload.get('filename', '')
        
        if not sender_username:
            return
        
        with self.lock:
            if sender_username not in self.clients:
                return
        
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if accepted:
            print(f"[{ts}] [TRAFFIC] FILE_ACCEPTED: {responder_username} menerima file '{filename}' dari {sender_username}")
            self.send_to_client(sender_username, {
                'type': 'FILE_ACCEPTED',
                'from_username': responder_username,
                'filename': filename,
                'message': f'{responder_username} menerima file {filename}'
            })
        else:
            print(f"[{ts}] [TRAFFIC] FILE_REJECTED: {responder_username} menolak file '{filename}' dari {sender_username}")
            self.send_to_client(sender_username, {
                'type': 'FILE_REJECTED',
                'from_username': responder_username,
                'filename': filename,
                'message': f'{responder_username} menolak file {filename}'
            })
    
    def handle_list_clients(self, requester_username):
        with self.lock:
            client_list = []
            for username in self.clients.keys():
                if username != requester_username:
                    client_list.append({'username': username})
        
        self.send_to_client(requester_username, {
            'type': 'CLIENT_LIST',
            'clients': client_list
        })

    def server_input(self):
        """Server mengetik command (list, send, broadcast)."""
        while True:
            cmd = input("")

            if cmd == "list":
                print("\n=== Daftar Client ===")
                with self.lock:
                    for username in self.clients.keys():
                        print(f"Username: {username}")
                print("=====================\n")

            elif cmd.startswith("send "):
                parts = cmd.split(" ", 2)
                if len(parts) < 3:
                    print("Format salah: send <username> <pesan>")
                    continue
                    
                target_username = parts[1]
                msg = parts[2]

                with self.lock:
                    if target_username in self.clients:
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        payload = {'type': 'SERVER_MSG', 'message': msg}
                        try:
                            self.clients[target_username].send(json.dumps(payload).encode())
                            print(f"[{ts}] [SERVER] Mengirim ke {target_username}: {msg}")
                        except Exception as e:
                            print(f"[{ts}] [ERROR] Failed to send to {target_username}: {e}")
                    else:
                        print("Client tidak ditemukan.")

            elif cmd.startswith("broadcast "):
                msg = cmd.split(" ", 1)[1]
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                payload = {'type': 'BROADCAST', 'message': msg}
                with self.lock:
                    for username, sock in list(self.clients.items()):
                        try:
                            sock.send(json.dumps(payload).encode())
                        except Exception:
                            pass
                print(f"[{ts}] Broadcast berhasil.")

            else:
                print("Perintah tidak dikenal!")



if __name__ == "__main__":
    Server().start()
