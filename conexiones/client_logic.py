import zmq
#import socket

# client initialize a connection
context = zmq.Context()
socket = context.socket(zmq.REQ)

HOST = "127.0.0.1"
PORT = 65432

socket.connect(f"tcp://{HOST}:{PORT}")

#with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#    s.connect((HOST, PORT))

socket.send(b"Hello, World")

data = socket.recv(1024)

# Data exchanged 
    
#    s.sendall(b"Hello, World") # sending the data in 8 bit units (b)
#    data = s.recv(1024)

print(f'Received {data}')
