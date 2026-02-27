
## Event Loops

An event loop is a programming construct used to manage and coordinate multiple tasks in a
single-threaded, non-blocking manner, commonly found in systems that handle asynchronous
operations, such as user interfaces, network servers, or real-time applications. At its core,
it’s a central loop that continuously monitors for events--things like user inputs, network
messages, or timers--and dispatches them to appropriate handlers for processing.

Imagine a busy receptionist at a front desk. The receptionist doesn’t handle one task to
completion before moving to the next; instead, they keep an eye on multiple sources of
activity (phone calls, visitors, emails) and address each as it comes up, quickly switching
between them. The event loop works similarly: it checks a queue or set of sources for
events, picks up any that are ready, and passes them to specific routines designed to
handle them, all while keeping the system responsive.


The loop operates in a cycle:

1. *Wait for Events*: It monitors various sources (like user actions,
   incoming data, or scheduled tasks) to see if something needs attention.

2. *Detect Events*: When an event occurs (e.g., a button click or a
   network packet arriving), it’s added to a queue or flagged for processing.

3. *Dispatch Events*: The loop selects an event and hands it off
   to a designated handler--a function or routine that knows how
   to process it (e.g., displaying a message or sending a response).

4. *Repeat*: The loop returns to waiting, ensuring it doesn’t
   get stuck on any single task.

This approach is often called the *reactor pattern*, where the loop "reacts" to events as they
happen, or the *proactor pattern*, where it proactively initiates tasks and handles their completion.
The key benefit is efficiency: by avoiding blocking operations, the system can juggle many tasks
concurrently without needing multiple threads, which can be resource-heavy.

In real-world terms, event loops are like the conductor of an orchestra, coordinating different
instruments (tasks) to play at the right time without letting any one section dominate. They’re
essential in scenarios where responsiveness is critical, such as:
- *Graphical User Interfaces*: Handling clicks, keystrokes, or window updates without freezing
  the interface.
- *Network Servers*: Managing multiple client connections, receiving messages, and sending
  responses simultaneously.
- *Real-time Systems*: Processing sensor data or timers in embedded devices or IoT applications.

The trade-off is complexity: designing systems to work asynchronously requires careful handling
of event priorities and potential race conditions, but the result is a highly responsive and
scalable system that makes efficient use of resources.


### Event Loops in C

In C, we’ll create a basic event loop that handles timer events using a queue.
This example uses a simple array-based event queue and checks for events in a
loop. The `usleep` function simulates waiting without blocking the loop entirely.

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>

#define MAX_EVENTS 10

// event structure
typedef struct {
    int event_id;
    time_t trigger_time;
    void (*handler)(int);
} Event;

// event queue
typedef struct {
    Event events[MAX_EVENTS];
    int count;
} EventQueue;

// init queue
void init_queue(EventQueue *queue) {
    queue->count = 0;
}

// add event to queue
int add_event(EventQueue *queue, int event_id, int delay_ms, void (*handler)(int)) {
    if (queue->count >= MAX_EVENTS) return -1;
    Event *ev = &queue->events[queue->count++];
    ev->event_id = event_id;
    ev->trigger_time = time(NULL) + (delay_ms / 1000);
    ev->handler = handler;
    return 0;
}

// sample event handlers
void handle_event1(int id) { printf("Handling event %d: Timer 1 triggered!\n", id); }
void handle_event2(int id) { printf("Handling event %d: Timer 2 triggered!\n", id); }

// event loop
void run_event_loop(EventQueue *queue) {
    while (1) {
        time_t now = time(NULL);
        for (int i = 0; i < queue->count; i++) {
            if (now >= queue->events[i].trigger_time) {
                queue->events[i].handler(queue->events[i].event_id);
                // remove event by shifting others
                for (int j = i; j < queue->count - 1; j++) {
                    queue->events[j] = queue->events[j + 1];
                }
                queue->count--;
                i--;
            }
        }
        if (queue->count == 0) break; // exit when no events remain
        usleep(100000); // sleep 100ms to avoid CPU hogging
    }
}

int main() {
    EventQueue queue;
    init_queue(&queue);

    // add some timer events
    add_event(&queue, 1, 2000, handle_event1); // trigger after 2s
    add_event(&queue, 2, 4000, handle_event2); // trigger after 4s

    printf("Starting event loop...\n");
    run_event_loop(&queue);
    printf("Event loop finished.\n");
    return 0;
}
```

*Explanation*:
- *Event Structure*: The `Event` struct holds an ID, trigger time,
  and a function pointer to a handler.
- *Event Queue*: A simple array-based queue stores events.
- *Event Loop*: The `run_event_loop` function continuously checks
  if any event’s trigger time has passed, then calls its handler and removes it.
- *Non-blocking*: `usleep` simulates a non-blocking wait, allowing the
  loop to check events periodically.
- *Reactor Pattern*: The loop reacts to events (timers here) by dispatching
  them to handlers when conditions are met.

When run, this program schedules two timer events and processes them after
their respective delays, printing messages when triggered.


### Event Loops in Python 

In Python, we can use the `asyncio` library, which provides a built-in event
loop for asynchronous programming. This example schedules coroutines as events,
mimicking a reactor pattern.

```python
import asyncio
import time

# event handlers (coroutines)
async def handle_event1(event_id):
    print(f"Handling event {event_id}: Timer 1 triggered at {time.strftime('%X')}")
    await asyncio.sleep(0)  # yield control back to event loop

async def handle_event2(event_id):
    print(f"Handling event {event_id}: Timer 2 triggered at {time.strftime('%X')}")
    await asyncio.sleep(0)

# event loop with scheduled events
async def event_loop():
    # schedule events with delays
    tasks = [
        asyncio.create_task(asyncio.sleep(2, result=(1, handle_event1))),  # trigger after 2s
        asyncio.create_task(asyncio.sleep(4, result=(2, handle_event2)))   # trigger after 4s
    ]

    # process events as they complete
    for task in asyncio.as_completed(tasks):
        event_id, handler = await task
        await handler(event_id)


def main():
    print("Starting event loop...")
    asyncio.run(event_loop())
    print("Event loop finished.")

if __name__ == "__main__":
    main()
```

*Explanation*:
- *Asyncio Event Loop*: Python’s `asyncio` provides a built-in event loop,
  which we use to schedule and run coroutines.
- *Event Handlers*: The `handle_event1` and `handle_event2` coroutines act
  as event handlers, printing messages when triggered.
- *Scheduling Events*: `asyncio.sleep` simulates timer events by delaying
  execution, returning a tuple with the event ID and handler.
- *Reactor Pattern*: The `event_loop` coroutine uses `asyncio.as_completed`
  to process events as they complete, reacting to their readiness.
- *Non-blocking*: The `await` keyword ensures the loop remains non-blocking,
  allowing other tasks to run while waiting.

When run, this program schedules two events with delays of 2 and 4 seconds,
respectively, and processes them when they trigger, printing messages.


### Differences

- *C*: Lower-level, manual implementation of the event loop and queue. Uses
  `usleep` for non-blocking behavior, which is less precise and more CPU-intensive.
  Suitable for systems where fine control is needed.

- *Python*: Higher-level, leveraging `asyncio` for a robust event loop. More concise
  and abstracted, with built-in support for coroutines and precise timing. Ideal
  for rapid development and modern async applications.

Both examples demonstrate a *reactor-style* event loop where the program waits for
events (timers in this case) and dispatches them to handlers when ready. The C
version is more manual and suited for embedded or performance-critical systems,
while the Python version is more abstracted and suited for high-level applications
like servers or GUIs.


### Example: TCP Server

A common real-world use case for an event loop is in a *simple TCP server*, which
handles multiple client connections asynchronously. The server listens for incoming
connections, reads messages from clients, and responds, all within a single-threaded
event loop using a reactor pattern. This is typical in network servers (e.g., chat
servers or IoT device hubs). Below, are examples in C and Python that simulate
a TCP server handling multiple clients, processing messages, and responding.


### C Implementation

In C, we’ll use the `select` system call to implement a non-blocking event loop for
a TCP server. The server listens for new connections and client messages, responding
with an acknowledgment (ACK).

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/select.h>

#define PORT 8080
#define MAX_CLIENTS 10
#define BUFFER_SIZE 1024

void handle_client_message(int client_fd, char *buffer) {
    printf("Received from client %d: %s", client_fd, buffer);
    char response[] = "ACK\n";
    send(client_fd, response, strlen(response), 0);
}

int main() {
    int server_fd, client_fds[MAX_CLIENTS], max_fd;
    struct sockaddr_in server_addr, client_addr;
    fd_set read_fds;
    char buffer[BUFFER_SIZE];
    int client_count = 0;

    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("Socket creation failed");
        exit(1);
    }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    if (bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Bind failed");
        exit(1);
    }
    if (listen(server_fd, MAX_CLIENTS) < 0) {
        perror("Listen failed");
        exit(1);
    }

    printf("Server listening on port %d...\n", PORT);

    for (int i = 0; i < MAX_CLIENTS; i++) client_fds[i] = -1;

    // event loop
    while (1) {
        FD_ZERO(&read_fds);
        FD_SET(server_fd, &read_fds);
        max_fd = server_fd;

        for (int i = 0; i < MAX_CLIENTS; i++) {
            if (client_fds[i] != -1) {
                FD_SET(client_fds[i], &read_fds);
                if (client_fds[i] > max_fd) max_fd = client_fds[i];
            }
        }

        if (select(max_fd + 1, &read_fds, NULL, NULL, NULL) < 0) {
            perror("Select failed");
            exit(1);
        }

        if (FD_ISSET(server_fd, &read_fds)) {
            socklen_t client_len = sizeof(client_addr);
            int new_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);
            if (new_fd < 0) {
                perror("Accept failed");
                continue;
            }
            for (int i = 0; i < MAX_CLIENTS; i++) {
                if (client_fds[i] == -1) {
                    client_fds[i] = new_fd;
                    client_count++;
                    printf("New client connected: %d\n", new_fd);
                    break;
                }
            }
        }

        for (int i = 0; i < MAX_CLIENTS; i++) {
            if (client_fds[i] != -1 && FD_ISSET(client_fds[i], &read_fds)) {
                int bytes_read = recv(client_fds[i], buffer, BUFFER_SIZE - 1, 0);
                if (bytes_read <= 0) {
                    printf("Client %d disconnected\n", client_fds[i]);
                    close(client_fds[i]);
                    client_fds[i] = -1;
                    client_count--;
                } else {
                    buffer[bytes_read] = '\0';
                    handle_client_message(client_fds[i], buffer);
                }
            }
        }
    }

    close(server_fd);
    return 0;
}
```

*How to Test*:
1. Compile and run: `gcc server.c -o server && ./server`
2. Use a tool like `nc` (netcat) to connect: `nc localhost 8080` (or use `client.c`)
3. Type messages and press Enter; the server will respond with "ACK".
4. Open multiple terminal windows with `nc` to simulate multiple clients.

*Explanation*:
- *Event Loop*: Uses `select` to monitor the server socket (for new connections)
  and client sockets (for messages).
- *Reactor Pattern*: The loop reacts to socket events (new connections or data)
  and dispatches them to handlers (e.g., `handle_client_message`).
- *Non-blocking*: `select` ensures the server doesn’t block, allowing it to
  handle multiple clients concurrently.
- *Real-world Context*: This mimics servers like Redis or older HTTP servers,
  where a single thread handles multiple connections using an event loop.


### Python Implementation

In Python, we’ll use `asyncio` to create a TCP server that handles multiple clients
asynchronously. The server reads messages and responds with an acknowledgment.

```python
import asyncio

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"New client connected: {addr}")

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
            message = data.decode().strip()
            print(f"Received from {addr}: {message}")

            writer.write("ACK\n".encode())
            await writer.drain()
    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        print(f"Client {addr} disconnected")
        writer.close()
        await writer.wait_closed()

async def event_loop():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8080)
    print("Server listening on port 8080...")

    async with server:
        await server.serve_forever()

def main():
    try:
        asyncio.run(event_loop())
    except KeyboardInterrupt:
        print("Server stopped.")

if __name__ == "__main__":
    main()
```

*How to Test*:
1. Run the script: `python3 server.py`
2. Connect using netcat: `nc localhost 8080`
3. Send messages; the server responds with "ACK".
4. Use multiple `nc` instances to simulate concurrent clients.

*Explanation*:
- *Event Loop*: `asyncio`’s event loop manages connections and data events asynchronously.
- *Reactor Pattern*: The `handle_client` coroutine reacts to client messages, processing
  them as they arrive.
- *Non-blocking*: `await reader.read` and `await writer.drain` ensure non-blocking I/O.
- *Real-world Context*: This resembles modern async servers like those built with Python’s
  `aiohttp` or Node.js, used in web servers or real-time applications like chat systems.


### Real-World Relevance

- *Use Case*: This TCP server pattern is used in applications like chat servers (e.g., IRC),
  IoT hubs (handling device messages), or lightweight web servers.
- *C*: Suitable for high-performance or embedded systems (e.g., Nginx-like servers or IoT
  firmware). It’s more manual but offers fine-grained control.
- *Python*: Ideal for rapid development of modern networked applications (e.g., web sockets,
  async APIs). It’s more abstracted and easier to extend.


### Simulation Notes

- Both examples handle multiple clients concurrently in a single thread, demonstrating the
  event loop’s power.
- The C version uses `select`, which is portable but limited to ~1024 file descriptors;
  real-world servers might use `epoll` (Linux) or `kqueue` (BSD) for scalability.
- The Python version leverages `asyncio`, which abstracts the underlying system calls
  (`epoll` or equivalent), making it more portable and developer-friendly.

You can simulate real-world scenarios by:
- Connecting multiple clients via `nc`.
- Sending varied messages to see how the server handles them.
- Closing connections to test disconnection handling.
- Modifying the handler to process specific commands (e.g., a simple chat protocol).

