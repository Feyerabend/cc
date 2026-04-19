
## Interfaces

An interface is a defined boundary or shared surface between systems, components, or entities that
enables interaction or communication in a predictable and structured way. An interface defines how
two sides exchange data, control, or resources -- but *not* how either side is implemented internally.
It specifies the form, meaning, and rules of interaction; it enables components to collaborate despite
internal differences; and it acts as a contract: as long as both sides respect the interface, they
can interact successfully.

This principle applies across all technical layers, from transistors to user interfaces.


### What an Interface Does

1. *Enables communication:* Defines how information flows between components.
2. *Encapsulates complexity:* Hides internal details behind a stable interaction point.
3. *Supports modularity:* Components can be developed independently as long as the interface is
   preserved.
4. *Facilitates interoperability:* Allows independently-built systems -- often in different languages
   or domains -- to work together.

| *Characteristic*      | *Meaning*                                                                  |
|-----------------------|----------------------------------------------------------------------------|
| *Explicitness*        | Clearly specified, documented, and understood by both sides                |
| *Stability*           | Interfaces evolve more slowly than implementations                         |
| *Abstraction*         | Hides internal mechanisms, exposing only what is necessary                 |
| *Bidirectionality*    | Some interfaces are one-way (API calls); others are negotiated (protocols) |
| *Semantics*           | Defines not just syntax but also meaning and expected behaviour            |
| *Composability*       | Interfaces enable reuse and reassembly into larger systems                 |

A wall socket illustrates the concept well: it specifies shape, voltage, and electrical protocol,
allows diverse devices to connect without knowing how power is generated or distributed, and provides
a stable contract that enables safe interaction despite internal heterogeneity.


### Interface Types and Examples

Interfaces take many forms in computing -- from low-level machine integration to human-facing systems.

| *Interface Type*          | *Description*                              | *Example*                       | *Layer*                    |
|---------------------------|--------------------------------------------|---------------------------------|----------------------------|
| *User Interfaces (UI)*    | Boundary between human and system          | GUI buttons, CLI, touch events  | Application / Presentation |
| *Data formats / Schemas*  | Structured data exchange                   | JSON, XML, Protocol Buffers     | Application                |
| *File formats*            | Persistent data structures                 | CSV, SQLite, PDF                | Application                |
| *APIs*                    | Callable program functions                 | POSIX, REST                     | Application                |
| *Protocols*               | Agreed communication rules                 | HTTP, TCP/IP, MQTT              | Network / Transport        |
| *Message queues*          | Asynchronous pub/sub model                 | Kafka, RabbitMQ                 | Middleware                 |
| *Event loops / Callbacks* | Async control handoffs                     | JS event loop, GUI events       | Application                |
| *Function signatures*     | Invocation contract between code units     | `int f(int)` in C               | Language / Compiler        |
| *Shared libraries / ABIs* | Binary compatibility between binaries      | libc.so, x86 calling convention | OS / Compiler              |
| *Shared memory*           | Low-level memory access sharing            | mmap, POSIX shm                 | OS / Kernel                |
| *Signals / Interrupts*    | Async system-level notifications           | IRQs, UNIX signals              | OS / Hardware              |
| *State machines*          | Defined transition models                  | TCP handshake, parser automaton | Application / Protocol     |
| *Command line*            | Text-based interaction contract            | UNIX pipes, CLI arguments       | Application / OS           |
| *Types / Contracts*       | Declarative interface specifications       | TypeScript types, CORBA IDL     | Language / Application     |
| *Hardware interfaces*     | Software <-> hardware interaction          | GPIO, PCI bus                   | Hardware                   |


### User Interfaces

A *user interface* (UI) is the direct interaction surface between a human and a system. Like any
interface, it hides implementation details and exposes a consistent interaction contract: input
modalities (clicks, gestures, keystrokes) and output formats (visuals, sounds). From this perspective,
a UI is not separate from interface theory -- it is simply a human-facing interface, governed by the
same principles of abstraction, encapsulation, explicit structure, and predictable semantics.

The main types of user interfaces are:

* *Command-line interfaces (CLI):* The user types commands as text. Powerful and precise, but
  requiring prior knowledge. The terminal model offers a clarity and minimalism that remains
  compelling, and has returned in a new form through AI chat interfaces -- structured, sequential,
  and calm.

* *Graphical user interfaces (GUI):* The user interacts through windows, icons, buttons, and menus.
  Introduced widely through the Xerox Star and Apple Macintosh in the early 1980s, this model
  brought accessibility and visual clarity. However, it also introduced clutter and complexity
  over time, as menus and icons eventually became as overloaded and cryptic as earlier keyboard
  controls.

* *Touch interfaces:* Used in smartphones and tablets, relying on finger gestures. Dominant in
  mobile design, they forced a reset of interface conventions toward simplicity and single-purpose
  screens.

* *Voice interfaces:* Systems using speech recognition (Siri, Alexa). Natural language interaction
  reduces the learning curve but introduces ambiguity.

* *Natural language interfaces:* Allow users to communicate using ordinary language, often using AI
  to interpret intent.

Good interfaces share core properties: they are *clear* (the user understands what they see and what
actions are possible), *consistent* (similar actions look and behave similarly), *efficient* (common
tasks are quick), *forgiving* (mistakes are easy to undo), and *responsive* (the system gives
feedback when an action is taken).

For a detailed exploration of UI history, design thinking, and the tension between power and
simplicity, see [User Interfaces](./ui/).


### Protocols and APIs

At the heart of distributed computing lies a fundamental architectural choice: should two components
communicate via a *protocol* or an *API*? This distinction has shaped the design of operating
systems, the Internet, and modern cloud systems.

*Protocols* offer clearly defined structures and enable programs to communicate regardless of the
underlying systems or programming languages they are written in. Communication often happens serially,
and extending or changing communicating programs can require protocol revisions. The significant
benefit of protocols lies in their universality -- they are what makes the Internet possible.

*APIs (Application Programming Interfaces)* are characterised by ease of use and greater flexibility,
especially when directly integrated into programming languages without requiring special handling.
APIs allow more immediate oversight and processing of shared data or resources, provided the language
or system supports it. Contemporary operating systems are extensively built upon API-type interfaces --
window management is a prime example where fast, low-latency interaction with program libraries is
essential, making a protocol solution unsuitable.

The Internet is predominantly composed of protocols at different levels within the TCP/IP stack.
Even HTTP and HTML are protocol solutions rather than APIs. Yet APIs and protocols are rarely in
direct opposition -- they frequently intermingle. A client-side JavaScript application may call a
REST API (a higher-level convention), which sends data via HTTP (a protocol), which travels over
TCP/IP (lower-level protocols), which is handled by a kernel driver that writes to a device register
(a hardware interface).

CORBA (Common Object Request Broker Architecture) was an important attempt to provide a unified
framework bridging the two: object-oriented applications could communicate via an Object Request
Broker (ORB) that handled location, parameter passing, method invocation, and result return --
all with the client unaware of the object's location, language, or operating system. The object's
interface was defined via IDL (Interface Definition Language), ensuring its internal nature was
well-encapsulated and system-independent.

One insight from this history stands out as particularly prescient: security must be built into
the foundation of a networked operating system from the outset, rather than added as an afterthought.
A lesson that took the industry considerable time to internalise.

For a detailed historical and conceptual analysis of protocols vs. APIs, see
[Protocols and APIs](./protocol/).


### Layered Interface Model

Interfaces stack and interact across system layers:

1. *Hardware:* GPIO, buses, voltage levels
2. *Kernel/OS:* Signals, shared memory, ABIs
3. *Language/Compiler:* Function signatures, types, linking
4. *Middleware/Application:* APIs, event loops, protocols, queues
5. *Presentation/Interaction:* UIs, file formats, data schemas

A cross-layer example: a user clicks a button (UI), which calls a JavaScript function (API), which
sends a REST request over HTTP (protocol), routed via TCP/IP (network stack), handled by a kernel
driver (OS), that writes to a device register (hardware). Each step uses a specific interface,
layered but interdependent.


### Interface Design Principles

Good interfaces -- whether for machines or humans -- share fundamental properties. They should be
*stable* over time, changing less frequently than the implementations behind them; *minimal* in
what they expose, hiding complexity rather than revealing it; *explicit* in their semantics, not
just their syntax; and *composable*, enabling systems to be assembled from independently-developed
parts.

The tension in interface design is always between expressiveness and stability. A richer interface
enables more powerful interactions but is harder to maintain across versions and implementations.
A minimal interface is easier to preserve but may force awkward workarounds. Good interface design
navigates this tension thoughtfully, resisting the urge to expose too much while ensuring that
what is exposed is genuinely useful.

Interfaces are contracts that enable interaction between components, regardless of their
implementation. Whether machine-to-machine or human-to-machine, interfaces enable modularity,
abstraction, and communication across technological boundaries.
