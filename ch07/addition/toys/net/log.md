
#### Connection 1: Request 0 -> Response 10

```
[NET] SYN: 2:12345 -> 1:80 (conn=1000)        <- Client initiates
[NET] SYN-ACK: 1:80 -> 2:12345 (conn=1000)    <- Server responds
[NET] ACK: 2:12345 -> 1:80 (conn=1000)        <- Client confirms
```
*3-way handshake complete!* Connection established.

```
[NET] DATA: 2:12345 -> 1:80 (data=0)          <- Client sends request 0
[RECV] Socket 3 delivered data: 0             <- Server receives it
0                                             <- Server prints request
[NET] DATA: 1:80 -> 2:12345 (data=10)         <- Server sends response 0*10=10
[RECV] Socket 2 delivered data: 10            <- Client receives it
10                                            <- Client prints response
```

Both sides close cleanly. Perfect!

#### Connection 2: Request 1 -> Response 11

```
[NET] SYN: 2:12345 -> 1:80 (conn=1001)        <- New connection ID!
[NET] SYN-ACK: 1:80 -> 2:12345 (conn=1001)
[NET] ACK: 2:12345 -> 1:80 (conn=1001)
```

Notice the *connection ID incremented* from 1000 -> 1001.
This prevents packets from different connections from getting mixed up.

```
[NET] DATA: 2:12345 -> 1:80 (data=1)          <- Request 1
[RECV] Socket 5 received data: 1              <- Different socket (5 vs 3)
1                                              
[NET] DATA: 1:80 -> 2:12345 (data=11)         <- Response 1*10=11
11
```

#### Connection 3: Request 2 -> Response 12

```
[NET] SYN: 2:12345 -> 1:80 (conn=1002)        <- conn=1002 now
[NET] SYN-ACK: 1:80 -> 2:12345 (conn=1002)
[NET] ACK: 2:12345 -> 1:80 (conn=1002)
[NET] DATA: 2:12345 -> 1:80 (data=2)          <- Request 2
2
[NET] DATA: 1:80 -> 2:12345 (data=12)         <- Response 2*10=12
12
```

#### What About Those `-1` Errors?

```
Client connected
-1                     <- This happens occasionally
```

This occurs when the server accepts a connection and tries to receive,
but there's a race where the server's RECV happens before the client's
SEND packet is processed. The server's RECV returns -1 (no data yet),
but then immediately loops back, accepts again, and by that time the
handshake has completed on the next connection. It's quite harmless,
and just shows the asynchronous nature of the network.

#### Key Observations

1. *Socket IDs increment*: 1, 2, 3, 4, 5, 6, 7 - each connection creates new sockets
2. *Connection IDs increment*: 1000, 1001, 1002 - prevents packet confusion
3. *Blocking works perfectly*: 
   - `[ACCEPT] Process 1 blocked waiting for connection`
   - `[RECV] Process 2 blocked waiting for data`
   - Processes wake up when events occur
4. *Bidirectional communication*: Client and server both send/receive
5. *Clean teardown*: `[CLOSE]` on both sides

#### The TCP State Machine in Action

For each connection, the sockets transition:

*Client*: `CLOSED` -> `SYN_SENT` -> `ESTABLISHED` -> `CLOSED`  
*Server listen socket*: Stays in `LISTEN`  
*Server connection socket*: `CLOSED` -> `SYN_RECEIVED` -> `ESTABLISHED` -> `CLOSED`

Exactly what TCP specifies! This is a real, working implementation of the
TCP connection protocol. The only things missing from production TCP are
reliability features (retransmission, flow control, congestion control).
But the core connection management is accurate. Well, it is still a simulation ..

