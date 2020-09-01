from socket import *
import sys
sys.path.insert(1, "C:/Users/Lukas/Documents/projects/libet_presentation/presentation/")
from tcp import CustomSocket


class  InternalTCP:
    def __init__(self, IP='192.168.2.128', port=5005, BufferSize=1024, encoding='utf-8', timeout=0.01):
        ''' This method creates an internal socket connection which enables 
        communication between this neurofeedback program and the libet stimulus
        presentation program. 
        '''
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

        print("Internal TCP Communication Established")
        
    def quit(self):
        self.con.close()
