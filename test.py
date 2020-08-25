a = bytearray(b'RP\x00')
print(f'a={a}')
b = a.decode('utf-8')
print(f'b={b}')
# for i in range(len(a)):
#     print(f'a[{i}]={a[i]} of type {type(a[i])}')
#     print(bytes(a[i]))

# print(bytes(''))