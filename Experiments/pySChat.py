#!/usr/bin/env python
from socket import *
import sys


class TCPServer:

    def __init__(self):
        if len(sys.argv) != 3:
            print ('Penggunaan: ' + sys.argv[0] + ' [ip_address] [nomor_port]')
            sys.exit(1)
        else:
            self.HOST = sys.argv[1]
            self.PORT = int(sys.argv[2])

    def Create(self):
        try:
            self.sockTCP = socket(AF_INET, SOCK_STREAM)
            self.sockTCP.bind((self.HOST, self.PORT))
            self.sockTCP.listen(1)
        except:
            print('Socket error [ip dan port harus valid]')
            sys.exit()
        else:
            print('Server Message [tekan Ctrl-C untuk keluar]')
            print('--------------')
            print('Mendengarkan pada port ' + str(self.PORT))

    def Accept(self):
        koneksi, alamat = self.sockTCP.accept()
        print('Koneksi dari ' + str(alamat))
        while True:
            data = koneksi.recv(1024)
            print('Pesan dari client >> ' + data.decode().strip())

            if not data:
                break

            if len(data) > 1:
                koneksi.send(('[' + data.decode().strip() + '] sudah diterima server.').encode())

    def Run(self):
        self.Create()
        self.Accept()

    def __del__(self):
        self.sockTCP.close()


if __name__ == '__main__':
    TCPServer().Run()
