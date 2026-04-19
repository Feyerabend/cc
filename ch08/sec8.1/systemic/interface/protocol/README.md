
## Protocols and APIs

At the heart of distributed computing lies a fundamental architectural choice: should two components
communicate via a *protocol* or via an *API* (Application Programming Interface)? This distinction
has shaped the design of operating systems, the architecture of the Internet, and the structure of
modern cloud systems. There are no hard-and-fast rules for when to choose one over the other, leading
to a wide variety of solutions in practice.

A detailed conceptual analysis of this choice--originally written in the late 1990s when the
Internet forced a re-evaluation of these architectural decisions--is preserved in
[protocol1996.md](./protocol1996.md). What follows is a summary of the key ideas.


### Protocols

*Protocols* offer clearly defined, explicit structures for communication. Their key properties are:

* *Language and platform independence:* Programs can communicate regardless of the underlying
  systems or programming languages they are written in. This is what makes the Internet possible.
* *Serial communication:* Communication often happens serially, which necessitates careful handling
  of shared data between sessions to ensure protocol-safe simultaneous processing.
* *Versioning challenges:* Extending or changing communicating programs can pose problems, sometimes
  requiring protocol revisions or replacements.
* *Speed:* Protocols generally do not facilitate the fastest possible communications compared to
  a direct API call.

The Internet is predominantly composed of protocols at different levels within the TCP/IP stack.
Even HTTP and HTML are protocol solutions rather than APIs. Protocols exist at various levels,
making a completely protocol-less alternative unrealistic for distributed systems.


### APIs

*APIs (Application Programming Interfaces)* are characterised by ease of use and greater flexibility,
especially when directly integrated into programming languages without requiring special handling.
Their key properties are:

* *Immediate oversight:* APIs allow more direct control and processing of shared data or resources,
  provided the language or system supports it.
* *Performance:* Contemporary operating systems are extensively built upon API-type interfaces.
  Window management is a prime example where fast, low-latency interaction with program libraries
  is essential, making a protocol solution unsuitable in that context.
* *Tighter coupling:* APIs tend to bind caller and implementer more closely than protocols, which
  can be a strength (more expressive, more efficient) or a weakness (less portable, harder to version).

Yet if window management were structured as a client-server model, a partially protocol-based
solution might actually be preferable--demonstrating that the choice is never absolute, but
always contextual.


### APIs and Protocols Together

APIs and protocols are rarely in direct opposition; they frequently intermingle. A client-side
application may call a REST API (a higher-level convention), which sends data via HTTP (a protocol),
which travels over TCP/IP (lower-level protocols), handled by a kernel driver that writes to a
device register (a hardware interface). The crucial task is to consider thoughtfully how and when
each should be employed.

Elements like Java via the WWW can delegate tasks to interfaces, while underlying layers are managed
by protocols--demonstrating that APIs and protocols are complementary, not competing.


### CORBA: Bridging the Gap

CORBA (Common Object Request Broker Architecture) was an important attempt to provide a unified
framework bridging protocols and APIs. The Object Management Group (OMG) designed CORBA to allow
object-oriented applications to communicate with each other regardless of location, language, or
operating system.

An *Object Request Broker (ORB)* acts as mediating middleware between a server and a client, which
can reside within the same network or on the same machine. The ORB receives client requests, locates
the object, transmits parameters, invokes methods, and returns results--all transparently to the
client. The object's interface is defined via IDL (Interface Definition Language), ensuring its
internal nature is well-encapsulated and its external face is the only thing the client needs to know.

CORBA thus provides independence from the operating system, programming language, and other systemic
dependencies--achieving the universality of a protocol with something close to the convenience of
a direct API call.

CORBA 1.1 (from 1991) defined interfaces for application communication via an ORB. CORBA 2.0 (from
1994) detailed how ORB implementations from different vendors could interoperate. Though specific
technologies like COM/DCOM and CORBA have since been superseded by REST, gRPC, and similar
approaches, the core architectural dilemma they addressed persists.


### A Prescient Observation

One insight from this era stands out as particularly forward-looking: *security must be built into
the foundation of a networked operating system from the outset*, rather than added as an afterthought.
The prospect of reaching an operating system with remote calls from distant locations--which both
Microsoft and third-party developers were attempting through COM/DCOM--was not without significant
challenges, particularly regarding security.

This observation, made in the late 1990s, anticipated a lesson that took the industry considerable
time to fully internalise: secure architecture is not a layer that can be bolted on top of an
insecure foundation. It must be part of the design from the beginning.

The enduring value of these reflections lies not in predictions about specific product successes, but
in their articulation of architectural dilemmas that continue to shape software development today:
where do you draw the boundary between protocol and API, between universality and performance,
between openness and control?
