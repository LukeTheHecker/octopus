from socket import AF_INET, SOCK_STREAM, gethostbyname, gethostname
import socket
from octopus import tcp
import select
import time

class TCP:
    def __init__(self, port=5005, BufferSize=1024, \
        encoding='utf-8', timeout=10):
        ''' This method creates an internal socket connection which enables 
        communication between this neurofeedback program and the libet stimulus
        presentation program. 
        '''
        
        self.IP = gethostbyname(gethostname())
        self.port = port
        self.BufferSize = BufferSize
        
        self.encoding = encoding
        self.timeout = timeout
        self.socket = tcp.CustomSocket(AF_INET, SOCK_STREAM)
        self.socket.settimeout(self.timeout)
        self.connected = False
        self.retryText = ('Try again?', 'Connection to TCP of Libet PC could not be established.')
        self.connect()
        
    def connect(self):
        if self.connected:
            print(f"Internal TCP connection is already established to {self.IP} {self.port}")
            return True
        # try:
        print(f'Attempting connection to {self.IP} {self.port}...')
        try:
            self.socket.bind((self.IP, self.port))
        except OSError:
            print(f'\t...failed due to OSError. Possibly IP/port are invalid.')
            return False
        self.socket.BufferSize = self.BufferSize
        self.socket.listen(1)
        self.accept_connection()
    
    def accept_connection(self):
        try:
            self.con, _ = self.socket.accept()
            # Put Socket in non-blocking mode:
            self.con.setblocking(0)
            self.connected = True
            print("\t...done.")
            return True
        except socket.timeout:
            self.connected = False
            print('\t...failed due to timeout.')
            return False
        except:
            self.connected = False
            print('\t...failed.')
            return False

    def quit(self):
        self.con.close()

class StimulusCommunication(TCP):
    def __init__(self, model, **kwargs):
        super(StimulusCommunication, self).__init__(**kwargs)
        self.model = model
    
    def communication_routines(self):
        self.communicate_state()
        respRequest = self.check_response()        
        if respRequest:
            return (True, True)
        elif not self.connected:
            return (False, 42)
        else:
            return (False, False)
    
    def check_response(self):
        ''' Receive response from participant through internal TCP connection with the 
            libet presentation
        '''
        if not self.connected:
            # If connection is not established yet
            return False
        
        if self.con.fileno() != -1:
            # If connection is running
            try:
                msg_libet = self.read_from_socket()
                if msg_libet.decode(self.encoding) == self.model.targetMarker or self.model.targetMarker in msg_libet.decode(self.encoding):
                    print('Response!')                
                    self.model.checkState(recent_response=True)
                    return True
                else:
                    return False
            except OSError as err:
                print("Connection probably closed")
                self.connected = False
        else:
            return
    
    def communicate_state(self, val=None):
        ''' This method communicates via the TCP Port that is connected with 
            the libet presentation.
        '''
        if not self.connected:
            # If connection is not established yet
            return
        if self.con.fileno() == -1:
            # If connection was closed at some point
            return

        if val is None:
            try:
                # Send Current state (allow or forbid) to the libet presentation
                allow_presentation = self.model.allow_presentation
                msg = int(allow_presentation).to_bytes(1, byteorder='big')
                self.con.send(msg)
                # print(f'sent {int(allow_presentation)} to libet PC')
            except OSError as err:
                print("Connection probably closed")
                self.connected = False
            except Exception as e:
                print(type(e))
                print(e.args)
                print(e)
        else:
            msg = int(val).to_bytes(1, byteorder='big')
            self.con.send(msg)
            # print(f'sent {int(val)} to libet PC')  
    
    def read_from_socket(self):
        if self.con.fileno() == -1:
            return

        ready = select.select([self.con], [], [], 0.05)
        response = b''
        if ready[0]:
            response = self.con.recv(self.BufferSize)

        return response
    
    def quit(self):
        self.connected = False
        self.socket.close()
    
    def communicateQuit(self):
        # Send message to libet presentation that the experiment is over
        self.con.setblocking(0)
        self.communicate_state(val=self.model.communicate_quit_code)

        response = self.read_from_socket()
        
        
        while int.from_bytes(response, "big") != self.model.communicate_quit_code**2:
            print("waiting for libet to quit...")
            self.communicate_state(val=self.model.communicate_quit_code)
            response = self.read_from_socket()
            time.sleep(0.1)
        print(f'Recieved response: {response}')