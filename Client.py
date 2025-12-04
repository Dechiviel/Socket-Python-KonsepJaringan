import socket
import sys
import threading
import json
import os
import base64
from datetime import datetime


class Client:
    def __init__(self):
        if len(sys.argv) != 3:
            print("Usage: " + sys.argv[0] + " <hostf> <port>")
            sys.exit(1)
        else:
            self.host = sys.argv[1]
            self.port = int(sys.argv[2])
        self.username = None
        self.pending_files = {}  # {from_username: {'filename': str, 'filedata': str}}

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] Connected to server.")
        
        # Minta username
        while not self.username:
            username = input("Masukkan username Anda: ").strip()
            if username:
                self.username = username
                # Kirim username ke server
                try:
                    self.sock.send(json.dumps({'type': 'SET_USERNAME', 'username': username}).encode())
                    
                    # Tunggu konfirmasi
                    data = self.sock.recv(4096)
                    if data:
                        response = json.loads(data.decode())
                        if response.get('type') == 'SUCCESS':
                            print(f"\n{response.get('message')}\n")
                            break
                        elif response.get('type') == 'ERROR':
                            print(f"\n[ERROR] {response.get('message')}\n")
                            self.username = None
                            self.sock.close()
                            return
                except Exception as e:
                    print(f"Error: {e}")
                    return
            else:
                print("Username tidak boleh kosong!")
        
        print("=== Commands ===")
        print("/list                        - Lihat daftar client online")
        print("/msg <username> <message>    - Kirim pesan ke user lain")
        print("/sendfile <username> <path>  - Kirim file ke user lain")
        print("/acceptfile <username>       - Terima file dari user")
        print("/rejectfile <username>       - Tolak file dari user")
        print("================\n")
        print("Type messages or commands:")

        threading.Thread(target=self.receive_messages, daemon=True).start()

        while True:
            try:
                msg = input()
            except EOFError:
                break

            if not msg:
                continue

            self.process_input(msg)

    def process_input(self, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if msg == '/list':
            self.send_json({'type': 'LIST'})
        
        elif msg.startswith('/msg '):
            parts = msg.split(' ', 2)
            if len(parts) < 3:
                print(f"[{ts}] Usage: /msg <username> <message>")
                return
            to_username = parts[1].strip()
            message = parts[2]
            self.send_json({'type': 'MSG', 'to_username': to_username, 'message': message})
            print(f"[{ts}] [YOU -> {to_username}] {message}")
        
        elif msg.startswith('/sendfile '):
            parts = msg.split(' ', 2)
            if len(parts) < 3:
                print(f"[{ts}] Usage: /sendfile <username> <filepath>")
                return
            to_username = parts[1].strip()
            filepath = parts[2].strip()
            self.send_file(to_username, filepath)
        
        elif msg.startswith('/acceptfile '):
            parts = msg.split(' ', 1)
            if len(parts) < 2:
                print(f"[{ts}] Usage: /acceptfile <username>")
                return
            from_username = parts[1].strip()
            if from_username in self.pending_files:
                file_info = self.pending_files[from_username]
                self.save_file(file_info['filename'], file_info['filedata'])
                self.send_json({
                    'type': 'FILE_RESPONSE',
                    'from_username': from_username,
                    'accepted': True,
                    'filename': file_info['filename']
                })
                del self.pending_files[from_username]
                print(f"[{ts}] File '{file_info['filename']}' berhasil disimpan")
            else:
                print(f"[{ts}] Tidak ada file pending dari {from_username}")
        
        elif msg.startswith('/rejectfile '):
            parts = msg.split(' ', 1)
            if len(parts) < 2:
                print(f"[{ts}] Usage: /rejectfile <username>")
                return
            from_username = parts[1].strip()
            if from_username in self.pending_files:
                file_info = self.pending_files[from_username]
                self.send_json({
                    'type': 'FILE_RESPONSE',
                    'from_username': from_username,
                    'accepted': False,
                    'filename': file_info['filename']
                })
                del self.pending_files[from_username]
                print(f"[{ts}] File dari {from_username} ditolak")
            else:
                print(f"[{ts}] Tidak ada file pending dari {from_username}")
        
        else:
            try:
                self.sock.send(msg.encode())
                print(f"[{ts}] [YOU] >> {msg}")
            except Exception as e:
                print(f"[{ts}] [ERROR] Failed to send: {e}")
    
    def send_json(self, payload):
        try:
            msg = json.dumps(payload)
            self.sock.send(msg.encode())
        except Exception as e:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] [ERROR] Failed to send: {e}")
    
    def send_file(self, to_username, filepath):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not os.path.exists(filepath):
            print(f"[{ts}] [ERROR] File tidak ditemukan: {filepath}")
            return
        
        try:
            with open(filepath, 'rb') as f:
                filedata = f.read()
            
            filedata_b64 = base64.b64encode(filedata).decode('utf-8')
            filename = os.path.basename(filepath)
            
            self.send_json({
                'type': 'FILE',
                'to_username': to_username,
                'filename': filename,
                'filedata': filedata_b64
            })
            
            print(f"[{ts}] Mengirim file '{filename}' ({len(filedata)} bytes) ke {to_username}...")
            
        except Exception as e:
            print(f"[{ts}] [ERROR] Gagal membaca/mengirim file: {e}")
    
    def save_file(self, filename, filedata_b64):
        try:
            filedata = base64.b64decode(filedata_b64)
            
            save_path = f"received_{filename}"
            counter = 1
            while os.path.exists(save_path):
                name, ext = os.path.splitext(filename)
                save_path = f"received_{name}_{counter}{ext}"
                counter += 1
            
            with open(save_path, 'wb') as f:
                f.write(filedata)
            
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] File disimpan sebagai: {save_path}")
            
        except Exception as e:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] [ERROR] Gagal menyimpan file: {e}")
    
    def receive_messages(self):
        while True:
            try:
                data = self.sock.recv(4096)
                if not data:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{ts}] [INFO] Server closed the connection.")
                    break

                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                try:
                    payload = json.loads(data.decode())
                    msg_type = payload.get('type')
                    
                    if msg_type == 'SUCCESS':
                        print(f"\n[{ts}] [SUCCESS] {payload.get('message')}")
                    
                    elif msg_type == 'ERROR':
                        print(f"\n[{ts}] [ERROR] {payload.get('message')}")
                    
                    elif msg_type == 'INFO':
                        print(f"\n[{ts}] [INFO] {payload.get('message')}")
                    
                    elif msg_type == 'PEER_MSG':
                        from_username = payload.get('from_username', 'Unknown')
                        message = payload.get('message', '')
                        print(f"\n[{ts}] [{from_username}] {message}")
                    
                    elif msg_type == 'FILE_OFFER':
                        from_username = payload.get('from_username', 'Unknown')
                        filename = payload.get('filename', '')
                        filedata = payload.get('filedata', '')
                        filesize = len(base64.b64decode(filedata)) if filedata else 0
                        
                        self.pending_files[from_username] = {
                            'filename': filename,
                            'filedata': filedata
                        }
                        
                        print(f"\n[{ts}] [FILE] {from_username} mengirim file: {filename} ({filesize} bytes)")
                        print(f"[{ts}] Ketik /acceptfile {from_username} untuk menerima atau /rejectfile {from_username} untuk menolak")
                    
                    elif msg_type == 'FILE_ACCEPTED':
                        from_username = payload.get('from_username', 'Unknown')
                        filename = payload.get('filename', '')
                        print(f"\n[{ts}] [FILE] {from_username} menerima file '{filename}'")
                    
                    elif msg_type == 'FILE_REJECTED':
                        from_username = payload.get('from_username', 'Unknown')
                        filename = payload.get('filename', '')
                        print(f"\n[{ts}] [FILE] {from_username} menolak file '{filename}'")
                    
                    elif msg_type == 'CLIENT_LIST':
                        clients = payload.get('clients', [])
                        print(f"\n[{ts}] === Daftar Client Online ===")
                        for client in clients:
                            username = client.get('username')
                            print(f"  • {username}")
                        print(f"[{ts}] ============================")
                    
                    elif msg_type == 'SERVER_MSG':
                        print(f"\n[{ts}] [SERVER] {payload.get('message')}")
                    
                    elif msg_type == 'BROADCAST':
                        print(f"\n[{ts}] [BROADCAST] {payload.get('message')}")
                    
                    else:
                        print(f"\n[{ts}] [SERVER] {data.decode()}")
                        
                except json.JSONDecodeError:
                    print(f"\n[{ts}] [SERVER] {data.decode()}")
                    
            except Exception as e:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{ts}] [ERROR] Connection error or interrupted: {e}")
                break


if __name__ == "__main__":
    Client().start()
