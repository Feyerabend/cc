
## Foundations ..

A single-file C program illustrating the four low-level primitives that underpin
actor-model frameworks like *Akka*. No libraries beyond POSIX.

```
gcc -std=c11 -Wall -Wextra -pthread -o foundations foundations.c && ./foundations
```

Tested on Linux and macOS. Uses only C11 + POSIX threads — no platform-specific headers.


### Pillar 1 — Threads

Two `pthread` threads race to increment the same counter 100 000 times each. One path
is guarded by a `pthread_mutex_t`; the other is naked. The guarded counter always
lands at 200 000. The naked one loses updates--the missing count appears in the output
(a live data race).

*The point:* threads are what make parallelism structural. Each actor in a framework
like Akka gets a slice of a thread-pool, so work genuinely runs concurrently rather than taking turns.



### Pillar 2 — Re-entrant Functions

Two threads tokenize different sentences at the same moment using `strtok_r`. The safe
version passes a `char **saved` pointer as an argument, so each thread carries its own
parse position on its own stack. A non-re-entrant version (using `static char *saved`)
would let one thread silently clobber the other's position mid-parse.

*The point:* an actor's behavior function may be invoked from many threads simultaneously.
It must depend only on its arguments and local variables--no hidden static state.
Akka actors satisfy this by holding mutable state *inside* the actor object, not in globals.



### Pillar 3 — Context Switches

Three actor threads each park on a `Gate` — a small struct wrapping a `pthread_cond_t`,
a mutex, and a flag. A round-robin scheduler signals them one at a time with `gate_signal`,
waits for the actor to yield back with `gate_wait`, then moves to the next. The output
interleaving — 0 -> 1 -> 2 -> 0 -> 1 -> 2 — is the scheduler's hand made visible.

*The point:* a context switch is the OS parking one thread and resuming another.
Akka's thread-pool executor does this at scale: thousands of actors mapped onto
tens of OS threads, none of them blocking the thread while waiting for a message.



### Pillar 4 — Memory Barriers

A producer thread writes `payload = 42` and then sets a flag with `memory_order_release`.
A consumer thread spins on the flag with `memory_order_acquire`. The release/acquire pair
forms a *happens-before* contract: once the consumer observes `ready = 1`, the CPU
guarantees that `payload` is also visible. Without the barrier, the compiler and CPU
are free to reorder the writes, and the consumer could read stale data.

*The point:* when an Akka actor sends a message, the framework inserts a happens-before
edge so the receiving actor sees the sender's state consistently--the same guarantee,
expressed through a higher-level API.



### What the program means, taken as a whole

These four primitives are not independent features bolted onto each other. They form a
dependency chain. Threads create the parallelism, but raw parallelism is unsafe--re-entrant 
functions make concurrent logic modular and correct. Running many actors on few threads
requires switching between them efficiently--context switches provide that.
And when threads do share any memory at all, reordering by CPU and compiler threatens
consistency--memory barriers restore it.

Actor frameworks like Akka exist precisely to manage this complexity on your behalf:
each actor gets its own isolated state (re-entrancy), scheduled across a thread pool 
context switches), communicating only through a message queue whose delivery is wrapped
in the appropriate barriers. What this program shows in raw C, Akka packages into an
API--but the machine underneath is doing exactly this.


https://github.com/akka/akka-core
