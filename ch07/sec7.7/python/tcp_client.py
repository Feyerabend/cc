"""tcp_client.py   minimal TCP client

Connects to tcp_server.py, sends a message, prints the reply.
Run: python tcp_client.py       (server must already be running)
"""

import socket

HOST = "127.0.0.1"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

msg = b"Hello from Python client"
client.sendall(msg)
print(f"Sent: {msg.decode()}")

data = client.recv(1024)
print(f"Received: {data.decode()}")

client.close()
