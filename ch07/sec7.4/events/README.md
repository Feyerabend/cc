
### Event-Driven & Reactive

| Mechanism | Description | Use Cases | Related Pattern(s) |
|-----------|-------------|-----------|--------------------|
| [Callback](./callback/) | Function invoked at a later point, usually by a framework | Event handling, async operations, sorting hooks | Observer, Inversion of Control |
| [Signal Handler](./signal/) | Async routine called in response to OS or hardware signals | Interrupt handling, Unix signals, exceptions | Observer, Interrupt Vector Table |
| [Event Loop](./loop/) | Central loop dispatching async events | GUIs, servers, JavaScript runtimes | Reactor, Proactor |

First, let’s consider the Callback mechanism. Imagine a bustling
kitchen where a chef delegates tasks to assistants, not expecting
immediate results but instead providing instructions to be executed
later when the task is complete. This is the essence of a *callback*:
a function passed as an argument to another function or framework,
lying in wait until the right moment arrives to spring into action.
The framework, perhaps a web server or a user interface library,
decides when to invoke this function, often in response to an
event like a user clicking a button or a file finishing its download.
Callbacks shine in scenarios requiring asynchronous operations--think
of a web application fetching data from a server, where the callback
function processes the response once it arrives, or in sorting algorithms
where a custom comparison function dictates the order. This mechanism
ties closely to the Observer pattern, where components listen for
events and react accordingly, and to Inversion of Control, where
the framework, not the developer’s code, dictates the flow of execution.

*Signal handlers* are specialised routines designed to respond to
specific signals, such as a user pressing Ctrl+C to interrupt a
program or a hardware interrupt signaling a device’s readiness.
These signals are often asynchronous, arriving unpredictably, and
the handler must be swift and precise, handling the interruption
without derailing the program’s flow. In Unix systems, for instance,
a signal handler might catch a SIGTERM to gracefully shut down a
process, saving state before exiting. In exception handling, a
similar principle applies, where the handler catches and resolves
unexpected errors. This mechanism is deeply tied to the Observer
pattern, as it listens for specific triggers, and to the Interrupt
Vector Table, a low-level structure mapping interrupts to their handlers.

The *event loop* is a central mechanism that runs continuously,
polling for events—user inputs in a GUI, incoming network requests
in a server, or tasks in a JavaScript runtime—and dispatching them
to the appropriate handlers. It’s the backbone of graphical user
interfaces, where it processes mouse clicks or keyboard presses,
and of web servers, where it manages multiple client connections.
In JavaScript runtimes like Node.js, the event loop is the maestro
orchestrating asynchronous tasks, ensuring non-blocking performance.
This mechanism aligns with the Reactor pattern, which handles
multiple events in a single-threaded environment, and the Proactor
pattern, which extends this for asynchronous I/O operations.

Together, these mechanisms--Callback, Signal Handler, and Event
Loop--form a trio of strategies for managing the unpredictable
nature of asynchronous events. Callbacks offer flexibility,'
letting developers inject custom logic into frameworks. Signal
Handlers provide resilience, catching and managing unexpected
interruptions. Event Loops bring order, orchestrating a continuous
flow of events in dynamic systems.

