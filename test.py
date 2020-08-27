from plot import Buttons
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

#------------------------------------------------#
# Create TCP Server
from socket import *
 
TCP_IP = '192.168.2.128'  # '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024
MESSAGE = "Hello, World!"

s = socket(AF_INET, SOCK_STREAM)
print("socket created")

s.bind((TCP_IP, TCP_PORT))
print("binded")

s.listen(1)

conn, addr = s.accept()
print('Connection address:', addr)
#------------------------------------------------#
myVar = True

def toggle(event):
    global myVar
    global buttonHandle
    global button_text
    myVar = not myVar
    buttonHandle.label.set_text(button_text[int(myVar)])
    # print(f'myVar={myVar}')

button_text = ['Toggle: Off', 'Toggle: On']

plt.ion()
fig = plt.figure(num=10)
ax = fig.add_axes([0.5, 0.5, 0.1, 0.075])
buttonHandle = Button(ax, button_text[int(myVar)])
buttonHandle.on_clicked(toggle)
plt.show(block=False)
print("into while loop")

lastMyVar = myVar

while True:
    # if myVar != lastMyVar:
    #     lastMyVar = myVar
    #     # print(f'myVar={myVar}')
    msg = int(myVar).to_bytes(1, byteorder='big')
    #     # Send via TCP
    conn.send(msg)

    plt.pause(0.5)