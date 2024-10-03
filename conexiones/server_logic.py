import zmq
#import socket

# 1 - server sets up to listening port

HOST = "127.0.0.1"

PORT = 65432

context = zmq.Context()

#with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#    s.bind((HOST, PORT))
#    s.listen() # listening the request from client
#    conn, adrss = s.accept()

socket = context.socket(zmq.REP)
socket.bind(f"tcp://{HOST}:{PORT}")

adrss = socket.getsockopt(zmq.LAST_ENDPOINT)
print(f'server is listening to {adrss}')

while True:
    message = socket.recv(1024)
    socket.send(message)

# 3 Data exchange between client and server
    
#    with conn:
#        print(f"Connected by {adrss}")
#        while True:
#            data = conn.recv(1024) # recieves data from  client
#            if not data:
#                break            # the cicle will break when the client doesnt send more data
#            conn.sendall(data) # send the data to client(in this example give the same)