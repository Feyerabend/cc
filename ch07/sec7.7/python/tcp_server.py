"""tcp_server.py   minimal TCP server

Waits for one client, receives a message, replies, and exits.
Run: python tcp_server.py       (start this first)
"""

import socket

HOST = "127.0.0.1"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(1)

print(f"TCP server listening on {HOST}:{PORT} ...")

conn, addr = server.accept()
print(f"Connected by: {addr}")

data = conn.recv(1024)
print(f"Received: {data.decode()}")

conn.sendall(b"Hello from Python server")
conn.close()
server.close()
