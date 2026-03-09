
> [!NOTE] 
> As the effort to write and update code decreases--thanks to modern tools,
> automation, frameworks, and LLMs--the developer's focus increasingly shifts
> from individual *code changes* to *system architecture*. In this context,
> the real challenge is no longer churning out functions or modules, but
> designing, evolving, and maintaining the structure of the system.
> Poor architectural decisions have far-reaching consequences, so while *code*
> becomes "cheap," the ongoing task becomes continuously shaping and adapting
> the *architecture* to meet evolving requirements.
> You could say that, in such projects, the work becomes more about testing,
> evolving, and refining the architecture than about writing individual lines of code.
> Please go ahead with a project that uses yet *another* architecture to solve the
> same problem as the following!

## Two Architectures


> [!NOTE]
> In a complex system parts have to be carefully chosen when architecturing.
> A UDP approach such as in the sample of the [UDP Display](./../udpdisplay/)
> lets the server broadcast frames without caring whether any client is
> listening--fire-and-forget. TCP, by contrast, is connection-oriented:
> the Pico and the server must first complete a three-way handshake before
> any data flows, and the transport layer guarantees ordered, reliable delivery.


### TCP stream: client and server

The architecture here is a classic *push-streaming* pattern over a single persistent TCP connection.

#### The server side

`server.py` opens a TCP listening socket on port 8081 and calls `accept()` in a loop.
Each time a new client connects--typically the Pico rebooting and reconnecting--Python
spawns a dedicated thread for that client. The thread owns the connection for its
lifetime and does one thing: generate a frame, append the `\nFRAME\n` delimiter,
and call `conn.sendall()`, then sleep just long enough to pace output at 30 fps.

Because `sendall()` blocks until the OS has handed all bytes to the TCP stack, the
server never gets ahead of a slow client--TCP's flow control automatically throttles
the sender if the receiver's window fills up. The server does not wait for any
acknowledgement at the application layer; it simply keeps pushing. It is the *stream*
half of a producer–consumer pair.

The HTTP listener on port 8080 is a fallback for a polling client that cannot maintain
a persistent connection. A GET to `/next` returns a single frame and closes; the caller
must reconnect to get the next one. That polling model incurs a full TCP handshake per
frame (~several milliseconds over WiFi) and is far less efficient than the streaming port,
which amortises the handshake cost over thousands of frames.

#### The client side

On the Pico, `net_task` is the consumer. After `net_stream_connect()` establishes the
connection, the task calls `net_stream_poll()` on every scheduler tick. This function
drives `cyw43_arch_poll()`, which lets the lwIP stack process incoming ACKs, retransmissions,
and--most importantly--new data segments arriving from the server.

When a segment arrives, lwIP fires `recv_cb` synchronously inside `cyw43_arch_poll()`.
The callback appends the raw bytes to the 16 KB ring buffer and immediately calls `tcp_recved()`
to advertise more receive-window space back to the server, keeping the flow running. The
application never touches lwIP directly after that; it just scans the ring buffer for
the newest complete frame.

This separation of concerns--lwIP owns byte delivery, the ring buffer absorbs jitter,
and the double-buffer decouples Core 0 reception from Core 1 rendering--is what makes
the whole pipeline robust across the variable latency of a home WiFi network.

#### Why TCP rather than UDP here

UDP would reduce per-packet overhead and eliminate retransmissions, but it shifts all
reliability concerns to the application. A dropped UDP datagram means a silent partial
frame; the display would need its own sequence numbers, duplicate detection, and a strategy
for missing frames. TCP handles all of that transparently. Since the Pico is connected
one-to-one with a single server on a low-contention LAN, TCP's retransmission overhead
is negligible in practice, and the guaranteed ordering means the frame delimiter search
in the ring buffer always sees a clean, contiguous byte stream--no reassembly required.

It still has its issues, but illustrates how simple streaming can be done through TCP.



### UDP display: sender and receiver

The UDP Display is a deliberate architectural contrast to the [TCP stream](./../tcpdisplay/).
Where the TCP version maintains one persistent connection and lets the transport layer handle
reliability, the UDP version discards that safety net entirely and builds its own application-level
protocol (VGTP) here on top of raw datagrams. This makes the networking code more complex,
but gives precise control over every tradeoff.

#### The sender side

`vgtp_send.py` opens two ordinary UDP sockets--no `connect()`, no handshake, no state on the
sender before the first packet goes out. Port 1234 carries DATA (drawing commands flowing host: Pico)
and port 1235 carries CONTROL (ACKs and heartbeats flowing in both directions).

Each logical frame is broken into multiple independent datagrams. A `CLEAR` packet sets the
background colour, then one `DRAW` packet per primitive follows, and finally a `FRAME_END`
packet signals that the frame is complete. Because UDP gives no ordering guarantee, the sender
assigns a monotonic `seq` counter and a shared `frame_id` to every packet, so the receiver
can detect gaps and group packets that belong together.

The Python `VGTPSender(reliable=True)` wrapper listens for ACKs on port 1235. If a `FRAME_END`
is not acknowledged within the timeout, it retransmits--something the TCP version never needed
to think about because the transport layer did it automatically. For the simpler animated demo
this retransmit layer is optional; for image delivery where a missing tile leaves a visible hole,
it becomes essential.

The heartbeat is sent every 500 ms in both directions. The sender uses it to detect a silent
Pico (rebooted, out of range); the Pico uses it to detect a silent sender and show a "SIGNAL LOST"
banner. TCP would have detected the same condition through its own keepalive and timeout mechanism
at no application cost. Here the application must implement it manually.

#### The receiver side

On the Pico, the UDP stack is even simpler than the TCP stack. There is no connection lifecycle--no
`connect()`, no `SS_CONNECTED` state machine, no ring buffer scan for a frame delimiter. `lwip`'s
`udp_bind()` and `udp_recv()` register `udp_recv_cb`, and every arriving datagram is a self-contained
unit. The callback copies the raw bytes into a 64-slot packet ring (`pkt_ring`) and returns immediately.

A dedicated `protocol_task` (priority 2, one below `net_task`) drains the ring. It validates the
14-byte VGTP header--version byte, type, CRC16-CCITT--and dispatches on packet type. `CLEAR` sets a
colour. `DRAW` appends a primitive to `build_scene`. `FRAME_END` calls `scene_swap()`, atomically
publishing the finished frame to Core 1 behind a `__dmb()`, then sends an ACK back on port 1235.
`HEARTBEAT` updates the last-seen timestamp. `CANVAS` tiles write directly into the persistent
150 KB `canvas_buf` without waiting for a frame boundary at all.

This split between `net_task` (owns the WiFi/lwIP poll loop) and `protocol_task` (owns parsing and
assembly) is a structural difference from the TCP version, where a single `net_task` handled both
network polling and frame extraction. The UDP version's separation makes sense because parsing is
now heavier--each packet carries a binary header, a CRC, a primitive type byte, and packed
little-endian fields--whereas the TCP version parsed plain ASCII in a single `sscanf`.

#### Frame assembly without a stream

The most instructive contrast is how each project reconstructs a "frame" from what the network delivers.

In the TCP version, the network delivers an ordered byte stream. The frame boundary is a 7-byte
ASCII sentinel (`\nFRAME\n`). The ring buffer scan is a simple substring search, and the only
failure mode is a partial frame at the tail of the buffer--handled by waiting for more bytes.

In the UDP version, there is no stream, only independent datagrams that may arrive out of order or
not at all. The frame boundary is the `FRAME_END` packet type, not a pattern in a byte stream.
If a `DRAW` packet for `frame_id=5` is dropped, `FRAME_END` for `frame_id=5` still arrives;
the Pico swaps the scene with one primitive missing and the frame renders silently wrong.
The `reliable=True` retransmit layer in Python is the answer, but it requires the application
to track what has and has not been acknowledged--work the TCP stack does for free.

#### Canvas mode and why UDP suits it

Canvas mode is the one case where UDP's lack of ordering is turned into an advantage. The persistent
`canvas_buf` is a 320x240 framebuffer that tiles write into independently, with no frame boundary
and no ordering requirement. Core 1 copies it as the background on every render tick, so each tile
appears on screen the moment it arrives--the image builds progressively and visibly rather than
waiting for the last byte of a complete frame. A TCP stream could deliver the same bytes in order,
but the display would still show nothing until the entire image was received and parsed.
Canvas mode exploits UDP's datagram-per-tile model to make partial delivery a feature rather than a failure.

#### Why the added complexity is a conscious choice

The VGTP protocol adds roughly the same reliability that TCP provides for free--sequence numbers,
acknowledgements, retransmission, connection liveness--but at the application layer where it can
be tailored to the use case. A `FRAME_END` ACK is coarser than TCP's per-segment ACK; the sender
does not need to know which individual primitive was lost, only whether the whole frame was accepted.
A 500 ms heartbeat is tuned to the display's tolerance for stale content, not to the OS's general
TCP keepalive timer. And for canvas tiles, the application deliberately omits reliability--a dropped
tile (ouch!) is preferable to stalling the entire image while waiting for a retransmit.

That is the architectural lesson the project makes explicit: UDP forces you to design the reliability
policy that fits your problem, while TCP imposes a one-size-fits-all policy. On a low-bandwidth
CYW43439 over a home LAN, the difference in raw throughput is negligible. The difference is in
control--and in how much of the networking stack you end up writing yourself.

