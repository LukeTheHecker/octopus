from socket import *
import sys
from tcp import CustomSocket


class TCP:
    def __init__(self, IP='192.168.2.122', port=5005, BufferSize=1024, encoding='utf-8', timeout=0.01):
        ''' This method creates an internal socket connection which enables 
        communication between this neurofeedback program and the libet stimulus
        presentation program. 
        '''
        print(f'Attempting connection to {IP} {port}...')
        self.IP = IP
        self.port = port
        self.BufferSize = BufferSize
        
        self.encoding = encoding
        self.timeout = timeout
        self.socket = CustomSocket(AF_INET, SOCK_STREAM)

        self.socket.bind((self.IP, self.port))
        self.socket.BufferSize = self.BufferSize
        self.socket.listen(1)

        self.con, addr = self.socket.accept()
        # Put Socket in non-blocking mode:
        self.con.setblocking(0)

        print("\t...done.")
        
    def quit(self):
        self.con.close()
