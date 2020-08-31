from socket import *
import numpy as np
from socket import *
import time

# Define IP and Port
TCP_IP = '192.168.2.128'  # '127.0.0.1'
TCP_PORT = 5005
BufferSize = 1024

# Connect
con = socket(AF_INET, SOCK_STREAM)
con.connect((TCP_IP, TCP_PORT))

# Receive messages
# print("Read first message")
# data = con.recv(BufferSize)
# msg = int.from_bytes(data, "big")
# print(f"msg = {msg}")
# print("Into the while")
encoding = 'utf-8'
while True:
    time.sleep(0.2)
    
    data = con.recv(BufferSize)
    # msg = int.from_bytes(data, "big")
    msg = data.decode(encoding)
    print(f"msg = {msg}")
    con.send((msg+msg).encode(encoding))
    print(f"Sent answer: {msg+msg}")
    if msg == '':
        break
    
