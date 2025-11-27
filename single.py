#!/usr/bin/env python

# import modul socket dan sys
import socket, sys

# Untuk welcome string
welstr = r'''
Selamat datang di dr_slump chat server
Powered by dr_slump Technology

User Access Verification
Password: '''

class Net:
 def __init__(self):
 # Cek argumen, jika tidak sama dengan 3
 # tampilkan cara penggunaan
    if len(sys.argv) != 3:
        print("Usage: " + sys.argv[0] + " <hostip> <port>")
        sys.exit(1)
    else:
        self.HOST = sys.argv[1] # Set nilai variabel dari
        self.PORT = int(sys.argv[2]) # parameter yang diberikan
        self.prompt = 'chat> ' # prompt yang akan ditampilkan
        
        
 def Create(self):
    try:
        # Buat socket INET dengan protocol TCP
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    except:
        print("Buat socket error...")
    else:
        # Binding ip dan port
        s.bind((self.HOST, self.PORT))
        # Mendengarkan koneksi
        s.listen(2)
        # Menerima koneksi yang datang
        koneksi, alamat = s.accept()
        # Setelah koneksi diterima, server mengirim pesan

        # selamat datang ke client
        koneksi.send(welstr.encode())
        stat=0 # Flag untuk status koneksi
        # 0=tdk terkoneksi, 1=terkoneksi
    while 1:
        # Terima data
        data = koneksi.recv(100).decode().strip()
        
        if not data: break
        if stat==0:
            if data.strip() == "password":
                stat=1
                isi=self.prompt
                koneksi.send("Anda berhasil login ke server\n\r".encode())
        
            else:
                isi = 'Password: '
        else:
            if data[:8] == 'hostname':
                host = data.split(' ')[1]
                self.prompt = host.strip() + '> '
                isi=self.prompt
        if data.strip() in ['keluar']:
            koneksi.close()
            break
        print('Data diterima: ' + str(data))
        koneksi.send(isi.encode())
    s.close()

net = Net()
net.Create()