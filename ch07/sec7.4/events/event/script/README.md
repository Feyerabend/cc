# EventScript: TRUE Event Loop Implementation

A complete event-driven programming language with a **real event loop**, timers, and continuous operation - matching the event loop patterns described in the README.md document.

## What Makes This a "True" Event Loop?

Unlike the basic version, this implementation has:

✅ **Continuous Operation** - Runs indefinitely until no events remain  
✅ **Timer Support** - Schedule events to fire after delays  
✅ **Non-blocking Waits** - Uses `select()` to sleep efficiently  
✅ **Event Queue Processing** - FIFO processing of ready events  
✅ **Reactor Pattern** - Waits for events, dispatches to handlers  
✅ **Time-based Triggers** - External event sources (timers)  

This matches the **C event loop example** from README.md!

## Architecture

```
┌─────────────────────────────────────┐
│       Main Execution Phase          │
│  - Register handlers                │
│  - Schedule timers                  │
│  - Emit immediate events            │
└──────────────┬──────────────────────┘
               │ HALT
               ↓
┌─────────────────────────────────────┐
│      Continuous Event Loop          │
│  ┌───────────────────────────────┐  │
│  │ 1. Check for expired timers   │  │
│  │    → Enqueue events           │  │
│  ├───────────────────────────────┤  │
│  │ 2. Process event queue        │  │
│  │    → Dispatch to handlers     │  │
│  │    → Handlers may emit/timer  │  │
│  ├───────────────────────────────┤  │
│  │ 3. Calculate next wake time   │  │
│  │    → select() wait            │  │
│  └───────────────────────────────┘  │
│                ↓                     │
│  Loop until: no timers AND no events│
└─────────────────────────────────────┘
```

## Language Features

### 1. Event Handlers (Callbacks)
```
on "event_name" {
    print "Handle event"
}
```

Registers a callback to be invoked when the event is emitted.

### 2. Immediate Event Emission
```
emit "event_name", data
```

Adds event to queue immediately. Processed in current or next loop iteration.

### 3. **NEW: Timer Events**
```
after 1000ms emit "event_name", data
```

Schedules an event to be emitted after a delay. This is what makes it a **true event loop**!

### 4. Event Chaining
```
on "click" {
    after 500ms emit "process", 10
}
```

Handlers can schedule new timers, creating event chains.

## Comparison to README.md Event Loop Example

### README.md C Example:
```c
// Event structure with trigger time
typedef struct {
    int event_id;
    time_t trigger_time;
    void (*handler)(int);
} Event;

// Event loop checks time
void run_event_loop(EventQueue *queue) {
    while (1) {
        time_t now = time(NULL);
        for (int i = 0; i < queue->count; i++) {
            if (now >= queue->events[i].trigger_time) {
                queue->events[i].handler(...);
                // Remove event
            }
        }
        if (queue->count == 0) break;
        usleep(100000);  // Non-blocking wait
    }
}
```

### EventScript Implementation:
```c
void vm_event_loop_forever(VM *vm) {
    while (vm->loop_active) {
        // 1. Check timers
        gettimeofday(&now, NULL);
        while (vm->timers && timer_expired(vm->timers, now)) {
            enqueue_event(vm, timer->event_name, timer->data);
            remove_timer(vm->timers);
        }
        
        // 2. Process events
        while (vm->event_queue_head) {
            event = dequeue();
            find_and_execute_handlers(vm, event);
        }
        
        // 3. Sleep until next timer
        calculate_timeout(&timeout, vm->timers);
        select(0, NULL, NULL, NULL, &timeout);
        
        // Exit if empty
        if (!vm->timers && !vm->event_queue_head) break;
    }
}
```

**Same pattern!**

## Examples

### Example 1: Simple Timer
```
on "timeout" { print "Timer fired!" }
after 1000ms emit "timeout", 42
```

**Output:**
```
[TIMER] Scheduled 'timeout' for +1000ms
[EVENT LOOP] Entering continuous event loop...
[TIMER FIRED] 'timeout' triggered
[EVENT] Processing: timeout (data=42)
  [HANDLER OUTPUT] Timer fired!
```

### Example 2: Multiple Timers
```
on "tick" { print "Tick!" }
on "tock" { print "Tock!" }
after 500ms emit "tick", 1
after 1000ms emit "tock", 2
after 1500ms emit "tick", 3
```

**Execution Timeline:**
```
T=0ms:    Program starts, schedules 3 timers
T=500ms:  "tick" fires → prints "Tick!"
T=1000ms: "tock" fires → prints "Tock!"
T=1500ms: "tick" fires → prints "Tick!"
T=1501ms: No more timers, loop exits
```

### Example 3: Event Chaining
```
on "start" {
    after 500ms emit "process", 10
}
on "process" {
    print "Processing..."
}
emit "start", 0
```

**Flow:**
1. "start" event emitted immediately
2. Handler schedules timer for "process"
3. Event loop waits 500ms
4. "process" event fires, prints message

### Example 4: Mixed Immediate & Delayed
```
on "start" { print "Starting system..." }
on "ready" { print "System ready!" }
emit "start", 0              # Immediate
after 1000ms emit "ready", 1  # Delayed
```

**Output:**
```
[EVENT] Processing: start
  Starting system...
[Waiting 1000ms...]
[TIMER FIRED] 'ready'
[EVENT] Processing: ready
  System ready!
```

## Implementation Details

### Timer Queue

Timers are stored in a **sorted linked list** by trigger time:

```c
typedef struct TimerEntry {
    char *event_name;
    Value data;
    struct timeval trigger_time;  // Absolute time to fire
    struct TimerEntry *next;
} TimerEntry;
```

Insertion maintains sorted order, so the next timer is always at the head.

### Event Loop Logic

```c
1. Check if any timers have expired
   → Move expired timers to event queue

2. Process all queued events
   → Execute matching handlers
   → Handlers may emit more events or schedule timers

3. If event queue is empty and timers exist:
   → Calculate time until next timer
   → select() with timeout (non-blocking wait)
   
4. If no timers and no events:
   → Exit loop

5. Repeat
```

### Non-Blocking Wait

Uses POSIX `select()` for portable non-blocking wait:

```c
struct timeval timeout;
// Calculate timeout from next timer
timeout.tv_sec = ...;
timeout.tv_usec = ...;

select(0, NULL, NULL, NULL, &timeout);
```

This is identical to the approach in README.md's event loop!

## Building and Running

### Compile
```bash
make -f Makefile_full
```

### Run Demo
```bash
./eventscript_full
```

### Clean
```bash
make -f Makefile_full clean
```

## Code Structure

```
eventscript_full.h    - Header with timer support
ast_full.c            - AST with timer nodes
compiler_full.c       - Compiler with OP_TIMER
vm_full.c             - VM with continuous event loop
demo_full.c           - Examples with timers
Makefile_full         - Build system
```

## Key Differences from Basic Version

| Feature | Basic EventScript | Full EventScript |
|---------|------------------|------------------|
| Event Loop | One-pass | Continuous (while loop) |
| Timers | ❌ No | ✅ Yes |
| Waiting | ❌ None | ✅ select() |
| External Events | ❌ Only manual emit | ✅ Time-based triggers |
| Exit Condition | After queue empty | When queue AND timers empty |
| Pattern | Callback demo | True reactor pattern |

## Event Loop Concepts Illustrated

### ✅ Callbacks
Event handlers are still callbacks registered with `on`.

### ✅ Event Queue
FIFO queue of pending events to be dispatched.

### ✅ **NEW: Reactor Pattern**
```
while (true) {
    wait_for_events();      // select() on timers
    dispatch_ready_events(); // Process queue
}
```

### ✅ **NEW: Non-Blocking I/O**
`select()` allows waiting without blocking the CPU.

### ✅ **NEW: Time-Based Events**
Timers provide external event sources beyond manual `emit`.

### ✅ **NEW: Continuous Operation**
Runs indefinitely until no work remains.

## Real-World Parallels

This is now structurally similar to:

- **Node.js Event Loop** - timers, event queue, continuous operation
- **Browser Event Loop** - setTimeout(), event handlers, run-to-completion
- **libuv** - Timer heap, I/O polling, event dispatch
- **Python asyncio** - Event loop with timers and futures
- **Traditional select() servers** - Wait on file descriptors + timeouts

## Educational Value

This implementation demonstrates:

✅ **Complete event loop lifecycle**  
✅ **Timer scheduling and expiration**  
✅ **Non-blocking waits** with select()  
✅ **Event queue management**  
✅ **Handler registration and dispatch**  
✅ **Reactor pattern** implementation  
✅ **Continuous polling** architecture  

Perfect for understanding how Node.js, browsers, and async frameworks work under the hood!

## Extending Further

Want to make it even more realistic? Add:

- **I/O events**: File descriptors, sockets
- **Priority queues**: Different event priorities  
- **Microtasks**: Immediate vs deferred execution
- **Error handling**: Try/catch in handlers
- **Cancellable timers**: clearTimeout() equivalent

## License

Public Domain / MIT - Use freely for learning!
