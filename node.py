import socket
import hashlib

# Create client socket.
client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to server (replace 127.0.0.1 with the real server IP).
print("right before socket connect")
client_sock.connect(('10.141.0.30', 6543))

# Send some data to server.
client_sock.sendall(b'Hello, world')
client_sock.shutdown(socket.SHUT_WR)

# Receive some data back.
chunks = []
while True:
    data = client_sock.recv(2048)
    if not data:
        break
    chunks.append(data)
print('Received', repr(b''.join(chunks)))

# Disconnect from server.
client_sock.close()


Class Node:
    def __init__():
        self.hostname = socket.gethostname()
        self.ip = socket.gethostbyname(self.hostname)
        self.id = 
        self.position =
        
    def 