
## Networks, Web Servers, Microservices, and Concurrency

When you open a browser and navigate to a website, dozens of programs running on
machines spread across the globe coordinate in milliseconds to deliver a page to
your screen.  None of those programs runs in isolation.  They send messages,
wait for replies, share data, and sometimes fail--all while you expect the
experience to feel instant and seamless.

We will build up from the very bottom--raw network sockets--through HTTP, web
servers, and microservices, to a complete mini distributed system you can run on
your own laptop.  Along the way we will look at concurrency: what it means for
multiple things to happen "at the same time" in software, and how two very
different approaches (threads and async) trade off against each other.

The goal is not to teach you every API.  It is to give you a mental model of
*why* each layer exists, and what it would cost you to do without it.

This is almost repeating the contents from the book, but here we also get the
complete samples layed out.


### 2. The Network Stack--A Mental Model

Before writing a single line of code it helps to have a picture of how network
communication is organised.  The most practical model for application
programmers is a four-layer view (a simplification of the full OSI stack):

```
   HTTP, DNS, FTP, SMTP, WebSocket ..          Layer 4: Application (what your code speaks)
   TCP  /  UDP                                 Layer 3: Transport (reliable vs. unreliable delivery)
   IP  (routing packets across networks)       Layer 2: Internet (addressing and routing)
   Ethernet, Wi-Fi, 4G ..                      Layer 1: Link (physical + data-link)
```

Each layer *hides* the complexity of the layers below it.  You, as an
application programmer, almost never touch IP or Ethernet directly.  You talk
TCP through an abstraction called a *socket*, and often you don't even do
that--you let an HTTP library handle the socket for you.

This is the central engineering trade-off of layering:

| What you gain.     | What you lose               |
|--------------------|-----------------------------|
| Simpler code       | Some control and visibility |
| Portability        | Overhead from wrapping      |
| Faster development | Harder to debug at the seam |

Understanding what each layer does is what lets you debug the seam when things
go wrong.



### 3. TCP/IP: The Foundation

#### 3.1 What TCP Does

*IP* (Internet Protocol) routes packets from one machine to another.  It does
so on a best-effort basis: packets can be lost, reordered, or duplicated.

*TCP* (Transmission Control Protocol) sits on top of IP and adds:
- *Reliability*--lost packets are retransmitted automatically.
- *Ordering*--bytes arrive in the order they were sent.
- *Flow control*--the sender slows down if the receiver is overwhelmed.
- *Congestion control*--the sender slows down if the network is congested.

From the application's perspective, TCP provides a *byte stream*: you write
bytes at one end and they come out the other end, in order, exactly once.

#### 3.2 Ports and Connections

A TCP connection is identified by a 4-tuple:

```
(source IP, source port, destination IP, destination port)
```

The *IP address* identifies a machine.  The *port* (0-65535) identifies a
specific *process* on that machine.  Well-known ports include:

| Port | Protocol   |
|------|------------|
| 80   | HTTP       |
| 443  | HTTPS      |
| 22   | SSH        |
| 25   | SMTP       |
| 5432 | PostgreSQL |

Ports below 1024 are "privileged"--on most operating systems only root/admin
can bind to them.

#### 3.3 The Three-Way Handshake

Before any data flows, TCP establishes a connection through a three-message
exchange:

```
Client                          Server
  |---- SYN (I want to connect) ------>|
  |<--- SYN-ACK (OK, ready)     -------|
  |---- ACK (confirmed)         ------>|
  |                                    |
  |   <-- data flows both ways --->    |
  |                                    |
  |---- FIN (I'm done)          ------>|
  |<--- ACK + FIN               -------|
  |---- ACK                     ------>|
```

This handshake is why TCP connections have *latency*: even if the server is
ready, the client must wait for one round-trip before it can send data.

#### 3.4 Sockets: The Programming Interface

The *socket API* is how applications access TCP (and UDP).  It was designed at
Berkeley in the 1980s and is available in almost every language and OS.

A socket is a file-like object.  You can read from it and write to it, and the
OS handles all the TCP machinery beneath.

*Server lifecycle:*

```
socket() --> bind() --> listen() --> accept() --> recv()/send() --> close()
```

*Client lifecycle:*

```
socket() --> connect() --> send()/recv() --> close()
```

See `c/tcp_server.c`, `c/tcp_client.c`, `python/tcp_server.py`,
`python/tcp_client.py` for working examples.

#### 3.5 What the C Code Shows

In `c/tcp_server.c`:

```c
server_fd = socket(AF_INET, SOCK_STREAM, 0);   // AF_INET=IPv4, SOCK_STREAM=TCP
setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
bind(server_fd, (struct sockaddr *)&addr, sizeof(addr));
listen(server_fd, 1);                          // queue up to 1 pending connection
client_fd = accept(server_fd, ...);            // blocks until a client connects
recv(client_fd, buf, BUFSZ - 1, 0);
send(client_fd, reply, strlen(reply), 0);
close(client_fd);
```

`SO_REUSEADDR` is a practical detail: without it, the OS holds the port in a
`TIME_WAIT` state for ~60 seconds after the server exits, making rapid
restarts during development painful.

#### 3.6 What the Python Code Hides

Python's `socket` module is a thin wrapper around the same system calls.  It is
almost identical to the C API:

```python
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)
conn, addr = server.accept()
data = conn.recv(1024)
conn.sendall(b"Hello from Python server")
```

The main difference: Python uses objects and raises exceptions on error;
C uses integer return values and errno.



### 4. The Client-Server Model

#### 4.1 Roles

The *client-server model* is a fundamental pattern for distributed computation:

- The *server* is a long-running process that waits for requests and responds
  to them. It is the *reactive* party.
- The *client* initiates contact, sends a request, waits for a reply. It is
  the *active* party.

The same machine can run both.  On your laptop, `curl http://127.0.0.1:8000`
makes your machine act as both the HTTP server and the HTTP client.

#### 4.2 Request-Response

Every interaction in the client-server model follows a request-response cycle:

```
Client                        Server
  |--- Request (what I want) -->|
  |                             |  (server does work)
  |<-- Response (here it is) ---|
```

This is synchronous: the client waits.  For slow operations (database queries,
external API calls) this becomes a bottleneck--which is why concurrency matters
(see Section 9).

#### 4.3 Statefulness

A key design question is whether the server remembers previous interactions.

- *Stateless*: each request is self-contained.  HTTP/1.1 is stateless by
  design.  The server treats every request independently.  This makes scaling
  easy: any server can handle any request.
- *Stateful*: the server remembers past exchanges.  A WebSocket connection or
  a TCP session is stateful.  Scaling is harder: you must route a client to the
  same server, or share state across servers.

Stateless services are dramatically easier to scale.  This is one reason HTTP
APIs (REST) became the dominant style for microservices.



### 5. HTTP: The Application Layer

#### 5.1 What HTTP Is

HTTP (Hypertext Transfer Protocol) is a *text-based, request-response protocol*
that runs on top of TCP.  "Text-based" means that, at the TCP level, an HTTP
request is literally a string of ASCII bytes.  You could write one with `nc`
(netcat) by hand.

A minimal HTTP/1.1 request:

```
GET /hello HTTP/1.1\r\n
Host: 127.0.0.1:8000\r\n
\r\n
```

The server's response:

```
HTTP/1.1 200 OK\r\n
Content-Type: text/plain\r\n
Content-Length: 19\r\n
\r\n
Hello, HTTP world!
```

Everything before the blank line (`\r\n\r\n`) is *headers*.  Everything after
is the *body*.

#### 5.2 Methods

HTTP defines a set of *methods* (also called verbs) that express intent:

| Method  | Meaning                           | Safe? | Idempotent? |
|---------|-----------------------------------|-------|-------------|
| GET     | Retrieve a resource               | Yes   | Yes         |
| POST    | Submit data (create a resource)   | No    | No          |
| PUT     | Replace a resource                | No    | Yes         |
| PATCH   | Partially update a resource       | No    | No          |
| DELETE  | Remove a resource                 | No    | Yes         |

*Safe* means the method should not change server state.  *Idempotent* means
calling it multiple times has the same effect as calling it once.

#### 5.3 Status Codes

Status codes tell the client how the request went:

| Range | Meaning      | Common examples                                    |
|-------|--------------|----------------------------------------------------|
| 2xx   | Success      | 200 OK, 201 Created, 204 No Content                |
| 3xx   | Redirect     | 301 Moved Permanently, 302 Found                   |
| 4xx   | Client error | 400 Bad Request, 401 Unauthorized, 404 Not Found   |
| 5xx   | Server error | 500 Internal Server Error, 503 Service Unavailable |

#### 5.4 How `c/http_server.c` Works

The C HTTP server does something instructive: it handles HTTP using *nothing but
raw socket code*.  This makes the protocol completely transparent.

It receives a raw TCP byte stream, finds the first line, extracts the path, and
constructs an HTTP response string:

```c
snprintf(header, sizeof(header),
    "HTTP/1.1 %d %s\r\n"
    "Content-Type: text/plain\r\n"
    "Content-Length: %zu\r\n"
    "Connection: close\r\n"
    "\r\n",
    status, status_text, strlen(body));
send(fd, header, hlen, 0);
send(fd, body, strlen(body), 0);
```

HTTP is *just text*.  The browser doesn't need anything special from the server;
it just needs the right bytes in the right order.

Run the server and then do:

```bash
curl -v http://127.0.0.1:8080/hello
```

The `-v` flag makes `curl` show the raw HTTP headers, which is exactly what the
server sends.



### 6. Web Servers

#### 6.1 What a Web Server Does

A web server is an HTTP server with the following general responsibilities:

1. Accept TCP connections from clients.
2. Read and parse HTTP requests.
3. Route the request to the appropriate handler (based on path, method, etc.).
4. Execute the handler (which may query a database, call other services, etc.).
5. Serialize the response and send it back.
6. Handle errors, timeouts, and connection cleanup.

#### 6.2 The Problem of Concurrency in Web Servers

A naive server handles one request at a time:

```
[req 1]----------------[done]
                             [req 2]--[done]
                                            [req 3]--[done]
```

If each request takes 100 ms and you get 100 requests per second, the last
request waits 10 seconds.  This is unacceptable.

Real web servers handle many requests simultaneously.  The two dominant models:

- *Thread-per-request*: spawn (or reuse from a pool) one OS thread per
  incoming connection.  Simple to program.  Limited by memory (each thread uses
  1-8 MB of stack) and by OS scheduling overhead.
- *Event loop / async*: a single thread multiplexes thousands of connections
  via non-blocking I/O (`select`, `epoll`, `kqueue`).  More complex to program,
  but far more scalable.

`c/concurrent_server.c` demonstrates the thread-per-client model.
`python/concurrency_async.py` demonstrates the event-loop model.

#### 6.3 Python's `http.server`

`python/http_server.py` uses the `http.server` module from the standard library.
It hides the socket code but is still serial (one request at a time)--suitable
for demos and local development, not production.

For production Python HTTP servers, frameworks like Flask or FastAPI run *behind*
a production WSGI/ASGI server (Gunicorn, Uvicorn) that handles concurrency.



### 7. Microservices Architecture

#### 7.1 The Monolith

The traditional alternative to microservices is a *monolith*: a single process
that contains the entire application.

```
+------------------------------------------+
|                 Monolith                 |
|  +----------+ +----------+ +----------+  |
|  |   Auth   | |   Data   | | Billing  |  |
|  |  module  | |  module  | |  module  |  |
|  +----------+ +----------+ +----------+  |
|           (all in one process)           |
+------------------------------------------+
```

Monoliths have real advantages:
- Simpler to develop (no network calls between components).
- Simpler to test (everything is in memory).
- Simpler to deploy (one artifact).
- Simple to debug (one log stream, one stack trace).

For many applications, especially early-stage ones, a monolith is the right
choice.

#### 7.2 Why Microservices?

As systems grow, monoliths develop problems:

- A bug in billing can crash auth.
- Deploying a one-line change to auth requires redeploying everything.
- The auth team and billing team step on each other's code.
- You can't scale auth independently of billing.

*Microservices* decompose the application into *small, independent services*,
each with its own process, codebase, and deployment lifecycle.

```
+-----------+     HTTP    +-----------+
|  Client   |------------>|  Gateway  |
+-----------+             +-----+-----+
                                |
               +----------------+--------------+
               v                               v
        +------------+                   +------------+
        |   Auth     |                   |    Data    |
        |  Service   |                   |  Service   |
        +------------+                   +------------+
```

#### 7.3 Properties of a Microservice

A well-designed microservice is:

- *Small*: does one thing and does it well.
- *Independent*: can be deployed without redeploying others.
- *Owned*: has a clear team responsible for it.
- *Loosely coupled*: communicates with others only via well-defined APIs.
- *Highly cohesive*: all its code relates to one business capability.

#### 7.4 The Costs

Microservices are not free:

| Problem                | Description                                                                |
|------------------------|----------------------------------------------------------------------------|
| *Network latency*      | In-process function calls take nanoseconds; HTTP calls take milliseconds.  |
| *Failure modes*        | If auth is down, everything that depends on auth fails.                    |
| *Distributed tracing*  | A single request may span 5 services; debugging requires correlating logs. |
| *Data consistency*     | Without a shared database, keeping data in sync is hard.                   |
| *Operational overhead* | 10 services = 10 deployment pipelines, 10 log streams, 10 health checks.   |

This is why experienced architects often recommend starting with a monolith and
*extracting* microservices only when the pain is real and measurable.

#### 7.5 The Flask Services in This Section

`python/auth_service.py`, `python/data_service.py`, and `python/gateway.py`
are intentionally small Flask services.  Flask is not a microservice framework
--it's an HTTP framework.  But it is small enough that the structure of the
service (routes, request parsing, JSON responses) doesn't obscure the concepts.



### 8. Service-to-Service Communication

#### 8.1 The Basic Pattern

When service A needs data from service B, it makes an HTTP request:

```python
r = requests.get(f"{OTHER_SERVICE}/endpoint", timeout=2)
data = r.json()
```

This looks trivial.  But it introduces several failure modes that don't exist
in function calls:

1. *Connection refused*: the other service is not running.
2. *Timeout*: the other service is slow or overloaded.
3. *HTTP 5xx*: the other service crashed while handling the request.
4. *Malformed response*: the other service returned unexpected JSON (or HTML).

#### 8.2 Timeouts Are Mandatory

A service call without a timeout can block indefinitely.  If service A calls B
and B hangs, A's thread hangs too.  If A's thread hangs, A's thread pool fills
up.  A stops responding.  Its callers start hanging.  The whole system freezes.

This is called a *cascade failure* or *thundering herd* depending on the
pattern.  Always pass `timeout=N` to `requests.get()`.

#### 8.3 Error Propagation

```python
@app.get("/profile/<name>")
def profile(name):
    try:
        r = requests.get(f"{USER_SERVICE}/user/{name}", timeout=2)
        r.raise_for_status()
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "user service unavailable"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "user service timed out"}), 504
```

The gateway must decide: should it fail fast (return an error immediately) or
retry?  Retries can help with transient failures but can worsen cascade failures
under load.  This is the essence of *resilience engineering*.

#### 8.4 The Dependency Graph

Every service-to-service dependency is an edge in a graph.  If the graph has
a long chain:

```
Client --> Gateway --> Auth --> Database
```

The failure of the database takes down Auth, which takes down Gateway, which
takes down the Client.  The depth of the chain is the blast radius of a single
failure.

A well-architected system limits chain depth, adds circuit breakers, and caches
results from downstream services where possible.



### 9. Concurrency: Threads vs Async

#### 9.1 Why Concurrency?

Concurrency is the ability to make progress on multiple tasks without waiting
for each to finish before starting the next.

The canonical case: a web server needs to handle 1000 simultaneous HTTP
connections.  Each connection is mostly *waiting*--for the database, for the
filesystem, for another service.  Without concurrency, connection 1000 would
wait for connections 1-999 to finish, even though none of them are using the
CPU.

#### 9.2 Threads

An *OS thread* is an independent unit of execution managed by the kernel.
Multiple threads share the same process memory but run concurrently (in parallel
on multi-core CPUs, or interleaved on a single core).

```
Thread 1:  [work]--[sleep(2)]--[work]--[done]
Thread 2:  [work]--[sleep(2)]--[work]--[done]
Thread 3:  [work]--[sleep(2)]--[work]--[done]
                                              Wall time: ~2 s (not 6 s)
```

Threads are good at:
- CPU-bound parallelism (Python: use `multiprocessing` due to GIL; C: use `pthread`).
- Code that can't be restructured as callbacks or coroutines.
- Mixing legacy blocking code with concurrent execution.

Threads are expensive:
- Each thread in Linux uses ~2-8 MB of stack by default.
- Context switches are not free.
- Shared mutable state requires locks; locks are subtle.

See `c/concurrency_threads.c` and `python/concurrency_threads.py`.

#### 9.3 The Global Interpreter Lock (Python)

CPython (the standard Python interpreter) has a *Global Interpreter Lock (GIL)*:
only one Python thread executes Python bytecode at a time. This means:

- Python threads *do not provide true parallelism for CPU-bound code*.
- Python threads *do* provide concurrency for I/O-bound code (while one thread
  blocks waiting for I/O, others can run).

For CPU-bound work in Python: use `multiprocessing` (separate processes) or a
compiled extension (NumPy, Cython).

#### 9.4 Async / Event Loop

An *event loop* is a single thread that manages many I/O operations by:
1. Registering interest in I/O events (`select`/`epoll`).
2. Handing control to code that has data ready.
3. Immediately giving up control when code needs to wait for I/O.

In Python this is `asyncio`.  Functions that can yield control are marked `async`
and awaited with `await`:

```python
async def task(i):
    print(f"Task {i} start")
    await asyncio.sleep(2)      # yields to event loop--other tasks run here
    print(f"Task {i} end")

await asyncio.gather(task(0), task(1), task(2), task(3), task(4))
# All 5 tasks interleave. Wall time: ~2 s, using one thread.
```

Async is good at:
- High-concurrency I/O (thousands of simultaneous HTTP connections).
- Network servers and clients.
- Anything where you spend most time waiting, not computing.

Async is bad at:
- CPU-bound work (blocks the event loop for everyone).
- Mixing with synchronous blocking calls (a single `time.sleep()` in async code
  stalls the entire event loop).

#### 9.5 Comparison Table

|                            | OS Threads                      | Async (event loop)        |
|----------------------------|---------------------------------|---------------------------|
| Concurrency model          | Preemptive (kernel schedules)   | Cooperative (code yields) |
| Parallelism (Python)       | No (GIL)                        | No (single thread)        |
| Parallelism (C)            | Yes                             | Possible with one thread  |
| Memory per concurrent task | ~2-8 MB (stack)                 | ~few KB (coroutine frame) |
| Scalability (I/O bound)    | Thousands                       | Tens of thousands         |
| Complexity                 | Locks, races                    | Must never block          |
| Debugging                  | Stack traces straightforward    | Can be harder to trace    |

#### 9.6 In C: Threads with pthreads

C has no built-in async/await, but the same event-loop pattern is available via
`select()`, `poll()`, or `epoll()`.  Most C network servers either use threads
(Apache's old model) or epoll (nginx's model).

`c/concurrent_server.c` demonstrates thread-per-client.  Each accepted
connection gets a detached thread:

```c
pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);
pthread_create(&tid, &attr, handle_client, c);
```

"Detached" means the thread cleans up its own resources when it exits.  We don't
need to `pthread_join()` it, which would block the main loop.

#### 9.7 Blocking vs Non-Blocking I/O

By default, all socket operations *block*: `recv()` suspends the calling thread
until data arrives.  This is convenient but incompatible with a single-threaded
event loop.

*Non-blocking sockets* return immediately with `EAGAIN`/`EWOULDBLOCK` if no
data is ready.  The event loop uses `select()`/`epoll()` to know *when* data
is ready before calling `recv()`, so it never needs to wait.

Python's `asyncio` handles all of this transparently.  When you `await` a
network read, the event loop registers the socket with the OS and runs other
coroutines until the OS says the data is ready.



### 10. A Complete Distributed System

The code in `python/auth_service.py`, `python/data_service.py`,
`python/gateway.py`, and `python/client.py` forms a minimal but realistic
distributed system.

#### 10.1 Architecture

```
Client --> Gateway (5000) --> Auth Service (5001)
                          --> Data Service (5002)
```

Each service is a separate Flask process.  Communication is HTTP.  There is no
shared memory, no shared database, and no framework beyond Flask and `requests`.

#### 10.2 The Auth Service

```python
VALID_TOKENS = {"abc123": "alice", "def456": "bob"}

@app.get("/validate")
def validate():
    token = request.headers.get("Authorization", "").strip()
    user = VALID_TOKENS.get(token)
    if not user:
        return jsonify({"valid": False}), 403
    return jsonify({"valid": True, "user": user})
```

The auth service is the *trust anchor* of the system.  All identity decisions
go through it.  If it returns `"valid": True` and a username, the system accepts
that username as fact.

Hardcoded tokens are a stand-in for a proper authentication system (JWT, OAuth
2.0, API keys stored in a database).  The structure--centralised validation,
returning a resolved identity--is real.

#### 10.3 The Data Service

```python
@app.get("/data/<user>")
def get_data(user):
    return jsonify({"user": user, "data": DATA.get(user, [])})
```

The data service *trusts the gateway completely*.  It does no authentication
of its own.  This is the microservice boundary contract: if you call me, you
have already verified the caller.

In a real system, data services run in a private network inaccessible from the
internet.  Only the gateway (or other internal services) can reach them.

#### 10.4 The Gateway

The gateway is the most interesting service.  It:

1. Receives a request from the client.
2. Extracts the bearer token.
3. Calls the auth service to validate the token and resolve the username.
4. Calls the data service with the resolved username.
5. Composes a unified response.

```python
ok, auth_resp = validate_token(token)
if not ok:
    return jsonify({"error": "unauthorized"}), 403

user = auth_resp["user"]
r = requests.get(f"{DATA_SERVICE}/data/{user}", timeout=2)
return jsonify({"gateway": "ok", "auth_user": user, "payload": r.json()})
```

Every external request touches the gateway.  Internal services never directly
face the public.  This is the *single entry point* or *API gateway* pattern.

#### 10.5 Latency Composition

Each hop in a chain adds latency.  For a single client request:

```
Client --> Gateway --> Auth --> Gateway --> Data --> Gateway --> Client
```

If each network hop is 1 ms (realistic on localhost; could be 50+ ms between
data centers), a single user-visible request involves six hops = 6 ms of
network time before any business logic runs.

In large systems this stacks up.  A frontend page load may trigger 10 API calls,
each spanning 3-5 internal services.

#### 10.6 Running the System

```bash
# Terminal 1
python auth_service.py

# Terminal 2
python data_service.py

# Terminal 3
python gateway.py

# Terminal 4
python client.py
```

Or use the Makefile shortcut (handles all four in one command):

```bash
cd python
make microservices
```

#### 10.7 What to Observe

1. *Valid token* (`abc123`): the gateway gets a `200` from auth, fetches data,
   returns a composed response.
2. *Invalid token* (`xxxxxx`): auth returns `403`, the gateway propagates the
   error.
3. *Kill auth* (`pkill -f auth_service.py`) and retry: the gateway returns
   `503`.  The data service is completely unaware of the failure.
4. *Add a sleep* inside `auth_service.py`'s handler and notice how the
   gateway's `timeout=2` eventually fires.

These four observations cover most of what distributed systems engineering is
about in practice.



### 11. Key Concepts Summary

| Concept            | One-line definition                                                            |
|--------------------|--------------------------------------------------------------------------------|
| Socket             | OS abstraction for a TCP (or UDP) connection                                   |
| Port               | Number identifying a service on a host                                         |
| HTTP               | Text-based request-response protocol over TCP                                  |
| Status code        | Three-digit number signalling the outcome of an HTTP request                   |
| Web server         | Long-running HTTP server that routes requests to handlers                      |
| Microservice       | Small, independently deployable HTTP service with a single responsibility      |
| Gateway            | Entry point that routes, authenticates, and composes calls to backend services |
| Thread             | OS-managed unit of execution; shares memory with other threads                 |
| Async / event loop | Single-threaded cooperative concurrency via non-blocking I/O                   |
| Cascade failure    | One service's failure propagating to its callers                               |
| Timeout            | Maximum time a caller will wait for a response                                 |
| Idempotent         | Operation that produces the same result when repeated                          |
| Stateless          | Server retains no memory between requests                                      |



### 12. Conclusions

We have followed a single idea--*how do programs on different machines
communicate?*--from its lowest accessible level (TCP sockets and the
three-way handshake) up through HTTP, web servers, microservices, and a
complete running distributed system.

A few things to carry forward:

*Abstraction layers are not free.*  HTTP costs more than raw TCP.  Flask costs
more than `http.server`.  Microservices cost more than a monolith.  Each layer
adds latency, debugging difficulty, and operational surface area.  The question
is always: does the problem being solved justify the cost?

*Failure is not exceptional.*  In a distributed system, every network call can
fail.  Designing for failure from the start--with timeouts, error propagation,
and graceful degradation--is not defensive programming; it is correct
programming.

*Concurrency is a tool, not a goal.*  Threads and async both exist to handle
waiting more efficiently.  Choose based on the problem: async for high-volume
I/O, threads when blocking code is unavoidable or when you need true CPU
parallelism (in C or with `multiprocessing`).

*Start simple.*  The three-service system in Section 10 is already complex
enough to have non-trivial failure modes.  Real systems with 50+ services are
much harder to reason about.  The discipline of keeping services small, their
interfaces clear, and their dependencies minimal is what makes such systems
maintainable.



### 13. Projects and Exercises

These projects increase in difficulty.  Each builds on concepts from previous
in the book/repo.



#### Starter Projects

*S1. Echo server*
Modify `c/tcp_server.c` to loop indefinitely, accepting and echoing messages
from multiple sequential clients (one at a time).  Then modify it to handle
one persistent connection and echo each line the client sends.

*S2. HTTP method router*
Extend `c/http_server.c` to handle `POST` requests.  Accept JSON in the body
(parse it manually as a string), and store submitted key-value pairs in a
global `struct` or hash table.  A subsequent `GET /data` should return all
stored pairs.

*S3. Timed concurrency comparison*
Modify `python/concurrency_threads.py` and `python/concurrency_async.py` to
accept the number of workers and sleep duration as command-line arguments.
Plot wall time vs. number of workers for both models.  At what point do threads
start losing to async due to scheduling overhead?



#### Intermediate Projects

*I1. Persistent multi-client TCP chat server (C)*
Write a server in C using pthreads that accepts multiple simultaneous clients.
When any client sends a message, the server broadcasts it to all other connected
clients.  Use a mutex to protect the list of connected sockets.

*I2. Minimal HTTP file server (C)*
Extend `c/http_server.c` to serve files from a directory.  A `GET /foo.txt`
should open and stream `./files/foo.txt`.  Implement proper `Content-Length`
and `Content-Type` headers (at least distinguish text from binary).  Guard
against path traversal attacks (requests like `GET /../../../etc/passwd`).

*I3. Auth token expiry*
Add expiring tokens to `python/auth_service.py`.  Tokens should be issued via a
`POST /login` endpoint with a username and password, and should expire after
60 seconds.  The `GET /validate` endpoint should check expiry.  Use Python's
`time.time()`--no external libraries.

*I4. Service-to-service circuit breaker (Python)*
Implement a simple circuit breaker in `python/gateway.py`.  Track the failure
rate of calls to the auth service.  If more than 50% of the last 10 calls
failed, open the circuit: return `503` immediately for the next 10 seconds
without even calling auth.  After 10 seconds, close the circuit and try again.

*I5. Async gateway with httpx (Python)*
Rewrite `python/gateway.py` to use `httpx.AsyncClient` and FastAPI (async
Flask equivalent).  Benchmark both versions using `wrk` or `hey`--at what
request rate does the async version start outperforming the threaded Flask
version?



#### Advanced Projects

*A1. Non-blocking event-loop server (C)*
Rewrite `c/concurrent_server.c` to use a single thread with `select()` or
`epoll()` instead of one thread per client.  Handle up to 1024 simultaneous
connections.  Compare throughput and memory usage to the thread-per-client
version under load using `ab` (ApacheBench).

*A2. Service discovery and load balancing*
Add a simple service registry: a fourth service that accepts `POST /register`
(service name, host, port) and answers `GET /lookup/<name>` with a list of
available instances.  Modify the gateway to look up the auth and data service
addresses from the registry at startup.  Then run two instances of the data
service on different ports and implement round-robin load balancing in the
gateway.

*A3. Distributed logging and trace IDs*
Add a `X-Request-ID` header to every request entering the gateway.  Propagate
it to all downstream service calls.  Have every service log the request ID
alongside each message.  This gives you a way to correlate all logs produced
by a single client request across three services--a stripped-down version of
distributed tracing.

*A4. Persistent data service with SQLite*
Replace the hardcoded `DATA` dictionary in `python/data_service.py` with a
SQLite database.  Add endpoints to create, update, and delete records.
Handle concurrent writes correctly (SQLite is safe for concurrent reads but
serialises writes).  Add a simple benchmark: how many reads per second can the
service handle under concurrent load from the client?

*A5. TLS everywhere (C)*
Add TLS to `c/http_server.c` using OpenSSL.  The server should generate a
self-signed certificate if none exists, present it to the client, and upgrade
the connection before parsing any HTTP.  `curl -k https://127.0.0.1:8443/`
should work.  Then add mutual TLS: require the client to present a certificate
too, and reject connections without one.


![TCP/IP](./../assets/image/tcpip.png)
