from socket import *
import numpy as np
import time
import string
import random
def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

TCP_IP = '192.168.2.128'  # '127.0.0.1'
TCP_PORT = 5005
BufferSize = 1024

s = socket(AF_INET, SOCK_STREAM)
print("socket created")

s.bind((TCP_IP, TCP_PORT))
print("binded")

s.listen(1)

con, addr = s.accept()

print("Internal TCP Communication Established")

encoding = 'utf-8'
for _ in range(3):

    # Send string:
    state = get_random_string(np.random.randint(5, 10))
    print(f'state = {state}')
    msg = state.encode(encoding)


    # Send integer:
    # state = np.random.randint(0, 100)
    # msg = int(state).to_bytes(1, byteorder='big')

    con.send(msg)
    # print(f'sent message {int.from_bytes(msg, "big")}')
    print(f'sent message {msg.decode(encoding)}')
    while True:
        data = con.recv(BufferSize)
        received_msg = data.decode(encoding)
        if received_msg == state+state:
            print(f"""received appropriate answer: {received_msg}""")
            break
        time.sleep(0.2)

    time.sleep(1)



