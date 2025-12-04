# Socket Python - Konsep Jaringan

Server-Client chat application dengan fitur peer-to-peer messaging dan file transfer menggunakan username.

## Fitur

### 1. **Username-Based System**
- Client harus set username saat pertama connect
- Username harus unik (tidak boleh sama dengan client lain)
- Semua komunikasi menggunakan username (tidak ada ID)
- Server log semua activity dengan username

### 2. **Direct Peer-to-Peer Messaging**
- Client bisa langsung kirim pesan ke client lain tanpa persetujuan
- Command: `/msg <username> <message>` - Kirim pesan langsung
- Tidak perlu request/accept, langsung bisa chat
- Server relay dan log semua pesan

### 3. **File Transfer**
- Client bisa kirim file langsung ke client lain
- Command: `/sendfile <username> <filepath>` - Kirim file
- Command: `/acceptfile <username>` - Terima file
- Command: `/rejectfile <username>` - Tolak file
- File di-encode Base64 untuk transmisi JSON
- File diterima disimpan dengan prefix `received_`

### 4. **Server Traffic Logging**
- Server melihat dan log semua traffic:
  - Client connections dengan username
  - Peer messages (isi pesan lengkap)
  - File transfers (nama file & ukuran)
  - File accept/reject
- Format log: `[TRAFFIC] <username> -> <action>: <details>`

### 5. **Client List**
- Command: `/list` - Lihat daftar semua username yang online
- Hanya menampilkan username (tanpa ID)

## Cara Menjalankan

### 1. Jalankan Server
```bash
python3 Server.py 0.0.0.0 8000
```

Server command:
- `list` - Lihat daftar client online
- `send <username> <message>` - Kirim pesan ke client tertentu
- `broadcast <message>` - Broadcast pesan ke semua client

### 2. Jalankan Client (di terminal lain)
```bash
python3 Client.py localhost 8000
```

Client akan:
1. Diminta input username
2. Username dikirim ke server untuk validasi
3. Jika username tersedia, client terhubung
4. Jika username sudah dipakai, koneksi ditolak
5. Melihat daftar command yang tersedia
6. Bisa mulai kirim command atau pesan

## Contoh Penggunaan

### Skenario: Alice dan Bob ingin chat dan kirim file

**Terminal 1 - Server:**
```bash
python3 Server.py 0.0.0.0 8000
```

**Terminal 2 - Alice:**
```bash
python3 Client.py localhost 8000
# Masukkan username Anda: Alice
# Selamat datang, Alice!

# Lihat siapa yang online
/list

# Kirim pesan langsung ke Bob
/msg Bob Hello Bob, how are you?

# Kirim file ke Bob
/sendfile Bob test_file.txt
```

**Terminal 3 - Bob:**
```bash
python3 Client.py localhost 8000
# Masukkan username Anda: Bob
# Selamat datang, Bob!

# Balas pesan Alice
/msg Alice Hi Alice! I'm good, thanks!

# Terima file dari Alice
/acceptfile Alice
```

**Server Output (Traffic Log):**
```
[TRAFFIC] Alice -> MSG: {'type': 'MSG', 'to_username': 'Bob', 'message': 'Hello Bob, how are you?'}
[TRAFFIC] MSG: Alice -> Bob: Hello Bob, how are you?
[TRAFFIC] Bob -> MSG: {'type': 'MSG', 'to_username': 'Alice', 'message': "Hi Alice! I'm good, thanks!"}
[TRAFFIC] MSG: Bob -> Alice: Hi Alice! I'm good, thanks!
[TRAFFIC] Alice -> FILE: {'type': 'FILE', 'to_username': 'Bob', 'filename': 'test_file.txt', ...}
[TRAFFIC] FILE: Alice -> Bob: test_file.txt (123 bytes)
[TRAFFIC] FILE_ACCEPTED: Bob menerima file 'test_file.txt' dari Alice
```

## Client Commands

| Command | Deskripsi |
|---------|-----------|
| `/list` | Lihat daftar client online |
| `/msg <username> <message>` | Kirim pesan langsung ke user lain |
| `/sendfile <username> <filepath>` | Kirim file ke user lain |
| `/acceptfile <username>` | Terima file dari user |
| `/rejectfile <username>` | Tolak file dari user |

## Protokol Komunikasi

Menggunakan JSON untuk semua komunikasi server-client:

**Message Types:**
- `SET_USERNAME` - Client set username saat connect
- `MSG` - Peer-to-peer message
- `FILE` - File transfer
- `FILE_OFFER` - Server relay file offer ke target
- `FILE_RESPONSE` - Accept/reject file
- `LIST` - Request daftar client
- `CLIENT_LIST` - Server kirim daftar client online
- `SERVER_MSG` - Pesan dari server
- `BROADCAST` - Broadcast message
- `SUCCESS/ERROR/INFO` - Status messages

## Keamanan & Batasan

- Username harus unik per koneksi
- File di-encode dengan Base64 untuk transmisi JSON
- Buffer size: 4096 bytes per receive
- File transfer untuk file kecil-menengah (< 10MB recommended)
- Tidak ada autentikasi password (username only)
- Semua traffic terlihat di server (no privacy)
- Client bisa langsung message client lain tanpa permission

## Requirements

- Python 3.6+
- Standard library (socket, threading, json, base64)
- No external dependencies

## Changes dari Versi Sebelumnya

**✓ Dihapus:**
- Sistem ID client (Client1, Client2, dst)
- Request/Accept mechanism
- Command `/username` untuk ganti username
- Command `/request`, `/accept`, `/reject`

**✓ Ditambah:**
- Username prompt saat connect
- Validasi username unik
- Direct messaging tanpa permission
- Komunikasi sepenuhnya dengan username

## Notes

- Server harus jalan dulu sebelum client connect
- Username harus unik dan diset saat connect
- Username tidak bisa diganti setelah connect (reconnect untuk ganti)
- File yang diterima disimpan dengan prefix `received_`
- Server bisa send/broadcast ke client kapan saja
- Client bisa langsung chat dengan siapa saja yang online
