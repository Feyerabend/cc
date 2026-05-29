## Foundations: Hardware, Software, and the Boundary Between Them

### 1. The Physical Layer as a First Principle

Most of this book deals with abstractions that run comfortably above the hardware.
Chapter 4 reverses that relationship. The Raspberry Pi Pico is close enough to
the metal that abstractions leak constantly, and the programmer must understand
what lies beneath.

This is not a step backward. It is a reminder that all software ultimately executes
on physical matter — transistors switching, capacitors charging, signals propagating
at finite speed. The abstractions that higher layers provide are real and useful, but
they are not free. They have a cost: in latency, in power, in the instructions that
must execute before your code can run. Embedded programming makes those costs visible.

The most important thing the physical layer teaches is *timing*. A desktop program
can assume that if something is done before something else in source code, it will
happen before it in execution. In an embedded program communicating with hardware,
this is false. Signals take time. Peripherals have setup and hold times. Interrupts
can arrive between any two instructions. The program must reason about time explicitly.


### 2. Event-Driven Programming and Reactive Systems

Embedded software is almost always *reactive*: its job is to respond to events from
the physical world. This is fundamentally different from batch processing, which takes
input, transforms it, and produces output in a single forward pass.

A reactive system maintains state and responds to events that arrive unpredictably.
This makes state machines the natural design tool. A state machine makes explicit
what the program is doing (its current state), what it can respond to (its enabled
transitions), and what it cannot respond to (transitions not defined from the current
state). This explicitness is a form of correctness by design: a state machine cannot
do something undefined.

The ECS (Entity-Component-System) pattern from `ch04/addition/games/` is a different
kind of reactive structure: instead of one machine with global state, it composes
many small, focused systems that each handle a narrow concern. Both models address the
same underlying challenge — managing complexity in a system that must respond to the
world — but they do so at different levels and for different problem shapes.


### 3. Concurrency Without an Operating System

On a desktop system, the operating system manages concurrency: scheduling threads,
handling interrupts, arbitrating hardware access. Embedded software often has no
such support. The programmer must implement whatever concurrency model is needed.

The simplest model is a cooperative "superloop": a single infinite loop that polls
all inputs and updates all outputs in sequence. This is predictable and easy to
analyse, but it cannot respond to events faster than one full loop iteration.

Interrupts provide genuine asynchrony: a peripheral fires an interrupt, the CPU
suspends the main loop, executes a short handler, and resumes. The handler must be
fast, atomic, and careful about shared data. Any variable touched by both the
main loop and an ISR must be protected — on a single-core system, by disabling
interrupts; on a multi-core system, by proper synchronisation primitives.

The Pico's two cores introduce genuine parallelism. Core 0 and Core 1 run
independently and communicate through shared memory. This is a simplified version
of the concurrency challenges that ch07 addresses in full, but it is real concurrency
with real consequences: race conditions, memory visibility, and the need for
explicit synchronisation.


### 4. Security at the Hardware Boundary

The 2FA project introduces an important idea: that security properties must be
enforced at every layer of a system, including the hardware layer.

A software-only security protocol is only as secure as the physical device it
runs on. If an attacker can physically access the device, replay traffic on the
wire, or power-cycle it at a critical moment, software guarantees may not hold.

This is not an argument against software security; it is an argument for
*threat modelling*: identifying what an attacker can do and designing defences
accordingly. The threat model for an embedded device is different from the
threat model for a web service. An embedded device may be physically accessible.
Its firmware may be extractable. Its communication channel may be observable.

The formal tools in ch08 — particularly the Alloy models in `ch06/addition/algebra/alloy`
and the session types in `ch07/addition/sessions` — can be used to specify and
check the security properties of protocols like 2FA. The hardware implementation
in ch04 gives those abstractions a concrete referent.


### 5. Resource Management as Design

The most characteristic challenge of embedded programming is resource management
without the safety net of a general-purpose OS. Memory, time, and power are all
explicitly managed by the programmer.

Memory: the heap may not exist, or may be replaced by a pool allocator. Stack
overflow is not caught by a runtime — it silently corrupts memory. Structures
must be sized for the worst case, because dynamic resizing is too expensive or
unavailable.

Time: everything that happens has a cost in CPU cycles. Communication protocols
require precise timing. Violating timing constraints can corrupt data on the wire.

Power: a battery-powered device that does not sleep will die quickly. The program
must explicitly manage when peripherals are active and when the CPU is halted.

These constraints push the programmer toward *defensive design*: allocating
everything statically where possible, bounding all loops, avoiding dynamic dispatch.
The resulting code looks different from idiomatic Python or Java, but the reasons
are grounded in physics, not style.


### 6. From Embedded to Distributed

The blockchain and Raft concepts appear in both ch04 (Pico hardware) and ch07
(distributed systems). This is not a coincidence.

A network of Pico devices, each maintaining a chain of signed blocks and refusing
to accept invalid updates, is a small-scale distributed system. The problems it
faces — consistent state under partial failures, authenticated communication,
Byzantine behaviour from a compromised node — are the same problems addressed
by formal consensus protocols.

The Pico is a useful place to encounter these problems because the system is small
enough to observe completely. There are only a few nodes. The network fits on a desk.
Failures are visible. But the principles that apply are the same ones that govern
systems with thousands of nodes, and the chapter's embedded projects lay the
experiential groundwork for the more abstract treatment that follows.
