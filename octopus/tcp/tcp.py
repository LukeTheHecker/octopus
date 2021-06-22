import socket

class CustomSocket(socket.socket):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.BufferSize = None
        self.state = None