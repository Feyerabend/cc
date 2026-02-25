
## ToyNet - TCP/IP Network Stack

Simulation of a full network stack with socket API
and TCP state machine in ~1000 lines of C.

#### Socket API
Complete BSD-style socket interface:
- `socket()` - Create a communication endpoint
- `bind()` - Assign address (port) to socket
- `listen()` - Mark socket as passive (accepting connections)
- `accept()` - Accept incoming connection (blocks until client connects)
- `connect()` - Initiate connection to server (blocks until handshake completes)
- `send()` - Transmit data over established connection
- `recv()` - Receive data (blocks until data arrives)
- `close()` - Close socket

#### TCP State Machine
Full 3-way handshake implementation:

```
CLIENT                    SERVER
  |                          |
  |-------SYN--------->      |  (client initiates)
  |                    [SYN_SENT]
  |                          |
  |       <------SYN-ACK-----|  (server responds)
  |                  [SYN_RECEIVED]
  |                          |
  |--------ACK--------->     |  (client confirms)
[ESTABLISHED]        [ESTABLISHED]
  |                          |
  |<----------DATA---------->|  (bidirectional communication)
  |                          |
```

States:
- `CLOSED` - Socket created but not yet connected
- `LISTEN` - Server socket waiting for connections
- `SYN_SENT` - Client sent SYN, waiting for SYN-ACK
- `SYN_RECEIVED` - Server got SYN, sent SYN-ACK, waiting for ACK
- `ESTABLISHED` - Connection ready for data transfer
- `CLOSE_WAIT`, `FIN_WAIT` - Connection teardown (simplified)

#### Virtual Network
- *Packet switching*: Central packet queue simulates network
- *Port management*: Each socket has a port number
- *Connection table*: Maps (src_pid, src_port, dst_pid, dst_port) to connections
- *Packet types*: SYN, SYN-ACK, ACK, DATA, FIN

#### Blocking I/O
Network operations properly block when needed:
- `accept()` blocks until a client connects
- `connect()` blocks until handshake completes
- `recv()` blocks until data arrives

Each blocking call:
1. Pushes a placeholder return value on stack
2. Sets process state to `PS_WAITING`
3. When event occurs (packet arrives),
   overwrites placeholder with real value
4. Wakes up process and adds to run queue


### Demo: HTTP-like Server

The demo shows a simple request/response pattern:

*Server* (port 80):
```
1. Create socket
2. Bind to port 80
3. Listen for connections
4. Loop:
   - Accept client connection (blocks)
   - Receive request number (blocks)
   - Send response = request * 10
   - Close connection
   - Repeat
```

*Client*:
```
1. Loop 3 times:
   - Create socket
   - Connect to server port 80 (blocks)
   - Send loop counter as request
   - Receive response (blocks)
   - Print response
   - Close socket
```

### Output Example

```
Server listening on port 80
  [NET] SYN: 2:12345 -> 1:80 (conn=1000, data=0)
  [NET] SYN-ACK: 1:80 -> 2:12345 (conn=1000, data=0)
  [NET] ACK: 2:12345 -> 1:80 (conn=1000, data=0)
Client connected
Connected to server
  [NET] DATA: 2:12345 -> 1:80 (conn=1000, data=0)
  [SEND] Socket 2 sent data: 0
  [RECV] Socket 3 delivered data: 0
0                          <- server prints request
  [NET] DATA: 1:80 -> 2:12345 (conn=1000, data=10)
  [SEND] Socket 3 sent data: 10
  [RECV] Socket 2 delivered data: 10
10                         <- client prints response
```

Perfect handshake, bidirectional data flow, clean connection handling!


### Key Design Decisions

#### 1. In-Memory Packet Queue
Real networks have physical wires and network cards. We simulate this with a
central `PacketQueue` that all processes send to and receive from.
The scheduler calls `process_network_packets()` each tick to deliver packets.

#### 2. Connection Identifiers
Each connection gets a unique `conn_id`. Packets carry this ID so the receiver
can match packets to the right socket, even when multiple connections exist
between the same two processes.

#### 3. Blocking Syscall Pattern
For syscalls that block:
```c
// In syscall implementation:
push(p, placeholder_value);  // -2 usually
p->state = PS_WAITING;
socket->waiting_for_X = p->pid;

// Later, when event occurs:
Process *p = find_process(os, socket->waiting_for_X);
p->stack[p->sp] = actual_return_value;  // overwrite placeholder
p->state = PS_READY;
enqueue_process(os, p->pid);
```

This pattern ensures the return value is on the stack when the process resumes.

#### 4. Per-Process Socket Table
Each process has a `socket_fds[]` array mapping local file descriptor numbers
to socket IDs. This mimics Unix's per-process fd table. Multiple processes
can have fd=0, but they refer to different sockets.



### Educational Value

This implementation demonstrates:

1. *How sockets work under the hood*
   - Sockets are just kernel data structures
   - File descriptors are indices into tables
   - Blocking is implemented with wait queues

2. *TCP state machine in action*
   - SYN/SYN-ACK/ACK handshake prevents connection confusion
   - State transitions ensure protocol correctness
   - Connection IDs prevent cross-talk

3. *Scheduler integration*
   - Network I/O causes context switches
   - Blocking on network = same as blocking on lock
   - Packet arrival = same as resource becoming available

4. *Clean layering*
   - Application code uses socket API
   - OS implements sockets using packets
   - Kernel provides scheduling/blocking primitives


### Comparison to Real TCP/IP

| Feature | ToyNet | Real TCP/IP |
|---------|--------|-------------|
| Handshake | 3-way SYN/SYN-ACK/ACK | Same |
| Flow control | None | Sliding window |
| Congestion control | None | Various algorithms |
| Retransmission | None | Timeout + retries |
| Packet loss | Impossible (in-memory) | Handled by retransmit |
| Routing | Direct delivery | IP routing tables |
| Fragmentation | None (fixed size) | MTU-based |
| Checksums | None | TCP/IP checksums |

ToyNet implements the *connection management* core of TCP accurately,
omitting the reliability and performance features.

### Next Steps

This network stack enables several extensions:

#### 1. UDP Support (Easy)
Add datagram sockets - no handshake, just send/recv packets.

#### 2. Multiple Network Interfaces (Medium)
Simulate different processes on different "machines" with routing between them.

#### 3. HTTP Server (Medium)
Build a proper HTTP/1.0 server that:
- Parses "GET /path" requests
- Serves files from VFS
- Returns status codes

#### 4. Chat Server (Medium)
Multi-client chat room using multiple connections.

#### 5. Packet Loss Simulation (Advanced)
Randomly drop packets, implement retransmission with timeouts.

#### 6. SSL/TLS Simulation (Advanced)
Add connection encryption handshake.


### Code Stats

- Total lines: ~1000
- Core network code: ~400 lines
- Socket syscalls: ~300 lines
- Packet processing: ~200 lines
- Demo program: ~100 lines

### Success Metrics

- TCP 3-way handshake works correctly
- Multiple sequential connections work
- Bidirectional data flow works
- Blocking I/O properly suspends/resumes processes
- Server can handle multiple clients (sequentially)
- Clean separation: app -> socket API -> packets -> scheduler


### So ..

1. *Sockets are just structs with queues* - Not magic, just data structures tracking connection state
2. *Blocking = waiting in a queue* - Network I/O blocking is identical to lock blocking
3. *Packets are messages* - Network packets are just messages passed between processes
4. *State machines prevent chaos* - TCP states ensure both sides agree on connection status
5. *The kernel is the network* - In a single-machine OS, the kernel IS the network switch!

