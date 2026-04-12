
PENDING:
    TCP/IP
    web server
    microservices
    concurrency

---

NOTES:

TCP Server

```python
import socket

HOST = "127.0.0.1"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print("TCP server listening..")

conn, addr = server.accept()
print("Connected by:", addr)

data = conn.recv(1024)
print("Received:", data.decode())

conn.sendall(b"Hello from server")
conn.close()
```



TCP Client

```python
import socket

HOST = "127.0.0.1"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

client.sendall(b"Hello server")
data = client.recv(1024)

print("Received:", data.decode())
client.close()
```



2. Simple Web Server (show HTTP abstraction)

Using the built-in `http.server` to show HTTP over TCP/IP.

```python
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Hello HTTP world")

server = HTTPServer(("127.0.0.1", 8000), Handler)
print("HTTP server running on port 8000...")
server.serve_forever()
```



3. Microservice (simple API service)

A microservice is typically a small, independent HTTP service.

Using Flask (reduce complexity):

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/status")
def status():
    return jsonify({"service": "auth", "status": "ok"})

@app.get("/user/<name>")
def user(name):
    return jsonify({"user": name, "role": "reader"})

if __name__ == "__main__":
    app.run(port=5001)
```



Run multiple services:
* auth service (5001)
* product service (5002)
* gateway service (optional)

More?


4. Microservice communication (service calling service)

Example: one service calling another using HTTP.

```python
import requests
from flask import Flask, jsonify

app = Flask(__name__)

USER_SERVICE = "http://127.0.0.1:5001"

@app.get("/profile/<name>")
def profile(name):
    r = requests.get(f"{USER_SERVICE}/user/{name}")
    user_data = r.json()

    return jsonify({
        "profile": user_data,
        "settings": {"theme": "dark"}
    })

if __name__ == "__main__":
    app.run(port=5002)
```

This demonstrates:

* service independence
* network-based communication
* failure dependency risk




5. Concurrency (threads vs async)

Thread-based concurrency (simple blocking I/O model)

```python
import threading
import time

def worker(i):
    print(f"Worker {i} starting")
    time.sleep(2)
    print(f"Worker {i} done")

threads = []

for i in range(5):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```



Async concurrency (modern network style)

This better represents microservices and web servers.

```python
import asyncio

async def task(i):
    print(f"Task {i} start")
    await asyncio.sleep(2)
    print(f"Task {i} end")

async def main():
    await asyncio.gather(*(task(i) for i in range(5)))

asyncio.run(main())
```



IDEAS:

1. Foundations
    * TCP/IP (raw sockets example)
    * client/server model

2. Application layer
    * HTTP basics
    * simple web server

3. Architecture
    * microservices concept
    * service-to-service communication

4. Scalability
    * concurrency (threads vs async)
    * blocking vs non-blocking I/O








A minimal but realistic distributed system in Python

Three services:
* *Auth service* (validates users / tokens)
* *Data service* (returns protected data)
* *Gateway* (single entry point, routes requests, enforces auth)

no databases, no Docker, no frameworks beyond Flask + requests.


System overview

```
Client -> Gateway -> Auth Service
                  -> Data Service
```

Flow:
1. Client calls gateway
2. Gateway checks token via auth service
3. If valid --> gateway fetches data from data service
4. Response returned to client



1. Auth Service (port 5001)

Validates a token (hardcoded for simplicity)

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

VALID_TOKENS = {"abc123": "alice", "def456": "bob"}

@app.get("/validate")
def validate():
    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"valid": False}), 401

    user = VALID_TOKENS.get(token)

    if not user:
        return jsonify({"valid": False}), 403

    return jsonify({"valid": True, "user": user})

if __name__ == "__main__":
    app.run(port=5001)
```



2. Data Service (port 5002)

Returns protected data (assumes gateway already authenticated user)

```python
from flask import Flask, jsonify

app = Flask(__name__)

DATA = {
    "alice": ["alice_doc_1", "alice_doc_2"],
    "bob":   ["bob_report",  "bob_notes"]
}

@app.get("/data/<user>")
def get_data(user):
    return jsonify({
        "user": user,
        "data": DATA.get(user, [])
    })

if __name__ == "__main__":
    app.run(port=5002)
```



3. Gateway (port 5000)

This is the orchestrator:
    * validates token via auth service
    * forwards request to data service

```python
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

AUTH_SERVICE = "http://127.0.0.1:5001"
DATA_SERVICE = "http://127.0.0.1:5002"

def validate_token(token):
    r = requests.get(
        f"{AUTH_SERVICE}/validate",
        headers={"Authorization": token}
    )
    return r.status_code == 200, r.json()

@app.get("/api/data")
def api_data():
    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"error": "missing token"}), 401

    ok, auth_response = validate_token(token)

    if not ok:
        return jsonify({"error": "unauthorized"}), 403

    user = auth_response["user"]

    r = requests.get(f"{DATA_SERVICE}/data/{user}")
    return jsonify({
        "gateway": "ok",
        "auth_user": user,
        "payload": r.json()
    })

if __name__ == "__main__":
    app.run(port=5000)
```



4. Client example

```python
import requests

GATEWAY = "http://127.0.0.1:5000/api/data"

token = "abc123"

r = requests.get(
    GATEWAY,
    headers={"Authorization": token}
)

print(r.status_code)
print(r.json())
```



RUN

Open 3 terminals:

```bash
python auth_service.py
python data_service.py
python gateway.py
```

Run the client.


So what is it:

__1. TCP/IP abstraction chain__
* sockets → HTTP → microservices

__2. Service decomposition__
* auth is independent
* data is independent
* gateway is coordination layer

__3. Network dependency graph__
* gateway depends on both services
* failure propagation risk (auth down -> everything fails)

__4. Security boundary__
* auth service centralizes identity
* gateway enforces trust boundary

__5. Latency composition__

Each request is now:

```
Client --> Gateway --> Auth --> Gateway --> Data --> Gateway --> Client
```




POSSIBLE: Replace requests with `httpx.AsyncClient`.
AND/OR: Cache auth results in gateway.
AND/OR: Randomly fail auth or data service to show resilience issues.
AND/OR: Run multiple data services on different ports.


