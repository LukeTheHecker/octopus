from socket import *
import sys
from tcp import CustomSocket
from util import gui_retry_cancel

class TCP:
    def __init__(self, IP='192.168.2.122', port=5005, BufferSize=1024, \
        encoding='utf-8', timeout=0.01):
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
        self.connected = False
        self.retryText = ('Try again?', 'Connection to TCP of Libet PC could not be established.')
        self.connect()
        

        
    def connect(self):
        if self.connected:
            print(f"Internal TCP connection is already established to \
                {self.IP} {self.port}")
            return
        try:
            print(f'Attempting connection to {self.IP} {self.port}...')
            self.socket.bind((self.IP, self.port))
            self.socket.BufferSize = self.BufferSize
            self.socket.listen(1)

            self.con, addr = self.socket.accept()
            # Put Socket in non-blocking mode:
            self.con.setblocking(0)
            self.connected = True
            print("\t...done.")
        except:
            self.connected = False
            gui_retry_cancel(self.connect, self.retryText)
            # print("\t...connection to Libet PC could not be established.")

    def quit(self):
        self.con.close()
