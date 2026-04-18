
## Systemic Concepts in Computing

Beyond the specific algorithms, architectures, or programming languages, there exists a set of systemic concerns
that permeate nearly *every* aspect of computing. These concepts are not tied to a single layer of abstraction--they
cross boundaries between hardware and software, between design and implementation, between local computation
and distributed systems.

Systemic concepts like abstraction, latency, concurrency, error, and state shape how we think about, build, and
interact with computer systems. They are the "forces" that govern complexity, performance, reliability, and usability,
whether we're designing a low-level device driver, a high-level API, or a fault-tolerant distributed protocol.

Some of these concerns reflect inherent tensions: we optimise for speed but must manage energy; we aim for determinism
but accept concurrency; we abstract for clarity but must still respect physical limits. Others help us reason more
clearly about system behaviour, especially when building or debugging layered, modular, or asynchronous systems.

Here is an overview of some of these systemic dimensions of computing--concepts that every practitioner will
eventually engage with, whether explicitly or implicitly.


| Concept | Systemic |
|--------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| [*Noise*](./noice/)                              | Affects communication, sensing, and even logic gates                                                              |
| [*Randomness*](./random/)                        | Critical in simulation, cryptography, testing, protocols                                                          |
| [*Optimisation*](./optimal/)                     | Present in compilers, algorithms, hardware, energy use                                                            |
| [*Security*](./security/)                        | Requires attention at every layer: physical to logical                                                            |
| [*Interface*](./interface/)                      | Defines component interaction everywhere                                                                          |
| [*Abstraction*](./abstract/)                     | Central to all software and hardware design                                                                       |
| [*Scalability*](./scale/)                        | Applies to data, computation, architecture                                                                        |
| [*Latency*](./latency/)                          | Matters in networks, UI, hardware timing                                                                          |
| [*Concurrency*](./../../ch07/models/concurrent/) | Appears from CPU pipelines to distributed systems                                                                 |
| [*Fault tolerance*](./fault/)                    | From ECC memory to retry loops in software                                                                        |
| [*Determinism*](./determinism/)                  | Affects debugging, simulation, and predictability                                                                 |
| [*Time*](./time/)                                | Scheduling, clocks, profiling, causality in distributed systems                                                   |
| [*Complexity*](./complex/)                       | Measured algorithmically, but also felt in UX and architecture                                                    |
| [*State*](./state/)                              | Core to both computing and modelling; managed differently across layers                                           |
| [*Energy use*](./energy/)                        | Crucial from battery devices to datacenters                                                                       |
| [*Cost*](./cost/)                                | Not just economic, but computational, spatial, or temporal                                                        |
| [*Errors*](./errors/)                            | Arise from hardware faults, logic bugs, bad input, or user misunderstanding                                       |
| [*Resilience*](./resilience/)                    | Ensures systems degrade gracefully and recover from faults, attacks, or overload                                  |
| [*Locality*](./locality/)                        | The tendency of programmes to reuse the same data and instructions in clusters of time and space                  |
| [*Throughput*](./throughput/)                    | The rate at which a system completes work; distinct from and often in tension with latency                        |
| [*Observability*](./observability/)              | The ability to understand internal system state from external signals; precondition for debugging and reliability |
| [*Feedback*](./feedback/)                        | Using information about a system's output to adjust its future behaviour; the mechanism of self-regulation        |
| [*Availability*](./availability/)                | The fraction of time a system is operational; related to but distinct from fault tolerance and resilience         |
| [*Privacy*](./privacy/)                          | Individuals' control over information about themselves; related to but distinct from security                     |
| [*Fairness*](./fairness/)                        | Equitable distribution of resources or decisions across parties; has multiple incompatible formal definitions     |
| [*Correctness*](./correctness/)                  | The property that a system does what its specification says; precondition of all other systemic properties        |


This workbook does not attempt to provide an exhaustive catalogue of all systemic concerns in
computing. Instead, it aims to introduce a selection of foundational and cross-cutting ideas
that recur across many layers of hardware, software, and theory. These topics are not isolated;
they connect and reappear in varied forms, from the architecture of a CPU to the design of a
secure web protocol.

The purpose here is to spark curiosity and cultivate awareness. Some of these systemic concepts
are explored in detail, while others are only touched on briefly--or left open for you to
investigate further. By now, you may already have formed your own questions, project ideas,
or conceptual goals. Discuss them with your peers--what might the future hold in these areas?

That's exactly the point: systemic thinking isn't about memorizing a list, but about recognising
patterns, tensions, and principles that shape systems across domains.

This workbook invites you to follow those threads--to explore, test, and build with these concepts
in mind. Take security, for example: it's not a problem you solve once and for all, but an ongoing
effort--one that will persist as long as computers behave even remotely like they do today.

*To become a good programmer, it is not enough to master syntax or tools.
One must also recognise and internalise these systemic concepts--they appear
across all layers of computing and shape how systems behave, succeed, or fail.*


#### Noise

Noise affects all real-world systems. In computing, it appears in analog signals, sensor inputs,
transmission lines, and even in low-level digital logic (e.g., thermal noise, crosstalk). Robust
systems account for it using filtering, error correction, shielding, or redundant design. Even
high-level abstractions sometimes must accommodate noise, such as in signal processing or sensor fusion.


#### Randomness

Randomness plays a fundamental role in cryptography, simulation, testing, and distributed protocols.
It underpins Monte Carlo methods, probabilistic algorithms, randomised load balancing, and key generation.
True randomness (e.g., from hardware) is often approximated with pseudorandom generators, whose properties
are critical to system security and unpredictability.


#### Optimisation

Optimisation permeates software and hardware design--from loop unrolling in compilers to energy-aware
scheduling in CPUs. It seeks to reduce time, space, energy, or other resources. Often guided by cost
models or heuristics, optimisation balances competing priorities like performance vs. clarity, or
generality vs. specialisation.


#### Security

Security spans from physical protection (tamper resistance, secure boot) to software-level controls
(authentication, memory safety). Threats emerge at all levels: bugs, side-channels, protocol flaws,
misconfigured permissions. Systemic security requires layered defences and assumptions that are
valid across abstraction boundaries.


#### Interface

An interface defines how components interact. It shapes design choices, modularity, and compatibility.
Interfaces may be formal (function signatures, protocols) or implicit (file formats, shared memory).
Good interfaces abstract internal complexity and promote reuse, while bad ones can leak details or
create coupling.


#### Abstraction

Central to all software and hardware design, abstraction allows systems to be built in layers,
hiding implementation details and exposing only essential behaviour. From hardware instruction
sets to object-oriented programming, abstraction is the foundation of scalability and maintainability.


#### Scalability

The ability of a system to handle increasing amounts of work or data. Scalability appears in
storage systems (e.g., from local files to distributed databases), computation (single-threaded
vs. parallel processing), and infrastructure (from one server to cloud clusters).


#### Latency

The delay between cause and effect in a system. Important in user interfaces (responsiveness),
network protocols (RTT), and hardware operations (cache misses, interrupt handling). Latency
directly affects usability and throughput.


#### Concurrency

Involves multiple computations happening at once, which may or may not interact. Concurrency
is present in CPU instruction pipelines, multithreaded programming, operating systems, and
distributed applications. It introduces complexity in synchronisation and correctness.


#### Fault Tolerance

The system's ability to continue operating correctly despite failures. Found in ECC memory
(hardware level), RAID (storage), retry mechanisms (software), and consensus protocols
(distributed systems). Fault tolerance is essential for resilience.


#### Determinism

A system is deterministic if the same inputs always produce the same outputs. Determinism is
critical for debugging, testing, simulations, and safety-critical systems. However, it often
conflicts with performance optimisations and concurrency.


#### Time

Time governs system scheduling, real-time guarantees, clock synchronisation (e.g., NTP, logical
clocks), and profiling. In distributed systems, understanding causality and ordering events
(e.g., Lamport timestamps) depends on reasoning about time.


#### Complexity

Can refer to algorithmic complexity (Big O), code complexity (maintainability), or system-level
complexity (emergent behaviour). Complexity impacts performance, reliability, and usability. It’s
often the root cause of bugs and poor design.


#### State

The configuration of a system at a given moment. Managing state is a key concern in UI frameworks,
databases, networking protocols, and CPU design. State introduces challenges like consistency,
synchronisation, and side effects.


#### Energy Use

From battery-powered sensors to energy-hungry datacenters, power consumption affects performance,
thermal design, and sustainability. Software can influence energy use via algorithm choices, polling
frequency, or instruction efficiency.


#### Cost

Broader than monetary cost: includes computational (CPU cycles), spatial (memory/disk usage),
and temporal (latency) dimensions. Cost-benefit tradeoffs drive design decisions across hardware,
software, and system architecture.


#### Errors

Errors are inherent in computing--from flipped bits in memory to logic bugs and invalid inputs.
Handling them involves detection, containment, reporting, and recovery. Some errors are transient
(e.g., hardware glitches), others persistent (e.g., design flaws). Resilient systems embrace error-aware
design, with graceful degradation or corrective strategies.


#### Resilience

The ability of a system to maintain acceptable service in the face of faults, overloads, or unexpected
conditions. Resilience spans hardware (e.g., redundant circuits), software (e.g., retries, fallbacks),
and distributed systems (e.g., failover, partition tolerance), focusing not just on preventing failure
but on graceful degradation and recovery.


### Relations

*Abstraction*, *Interface*, and *State* form a conceptual core around how systems are structured and composed.
Abstraction allows us to hide complexity by defining layers of meaning or functionality, which in turn rely
on interfaces to define the boundaries and protocols for communication between those layers. State is what
these abstractions often manage or transform. For instance, a file system abstracts disk blocks and manages
persistent state, while an API abstracts internal behaviour and exposes a controlled interface to clients.
State is fundamental because it anchors behaviour in time, memory, and identity, which both abstraction and
interface are mechanisms for organising and controlling.

*Time*, *Latency*, and *Concurrency* are inseparable in systems where operations span time and resources are
shared. Time underpins everything from scheduling to causality, especially in distributed systems where clocks
may not agree. Latency arises when components wait--for I/O, communication, or scheduling--making it a temporal
cost that must be optimised or hidden. Concurrency is a structural response to these temporal constraints,
allowing systems to make progress while waiting or to exploit parallelism. These concepts directly influence
how systems behave in real time, how responsive they are, and how well they utilise hardware.

*Noise*, *Randomness*, and *Errors* all describe deviations from ideal behaviour but differ in origin and
function. Noise refers to uncontrolled variation, often physical or environmental, which can corrupt signals
or data. Randomness can be harnessed deliberately, as in cryptography or simulation, but it also models uncertainty
or lack of control. Errors arise when outcomes diverge from expectations, often due to noise or bugs. While noise
is (often regarded as) physical and randomness can be both a tool and a problem, errors are logical or semantic
failures that require detection and recovery mechanisms. Their interplay affects reliability and trustworthiness.

*Optimisation*, *Cost*, *Energy Use*, and *Complexity* are all about managing constraints. Optimisation is the
discipline of navigating trade-offs within these constraints, often minimising cost, energy, or time. Cost is not
merely financial--it encompasses memory, computation, bandwidth, and even human effort. Energy use, though physical,
has computational implications, especially in battery-bound or large-scale systems. Complexity arises when the
interactions among parts become difficult to predict or manage, and it can be both a result of and a barrier to
effective optimisation. These concepts together define the pressures that shape system design.

*Security*, *Fault Tolerance*, *Resilience*, and *Determinism* are about predictability and robustness. Security
demands systems behave predictably in the presence of adversaries, while fault tolerance ensures they remain
functional despite faults. Resilience extends this to include graceful degradation and recovery--going beyond
tolerating faults to actively adapting to and recovering from them. Determinism supports all of these by ensuring
repeatability, which simplifies reasoning and testing. However, in practice, non-determinism is often unavoidable,
making resilience and fault tolerance even more critical. These properties define a system's ability to handle
the unexpected.

*Scalability* and *Resilience* are particularly relevant at the system and network level. While scalability is
about a system's ability to grow without performance collapse, resilience ensures that the system can sustain
functionality as conditions change. These are not just performance issues--they are design philosophies that
emphasise system behaviour under load and stress. A scalable system may still be fragile; a resilient one
prioritises survival and recovery.

*Locality*, *Throughput*, *Observability*, and *Feedback* each deepen the picture drawn by the
original eighteen concepts. Locality explains *why* caches work--it is a property of programme
behaviour, not hardware. Throughput completes the picture alongside latency: latency is the cost
of one operation; throughput is the capacity of the system. Observability is the precondition for
managing any of the other concepts in production--without signals, no other property can be
monitored, debugged, or improved. Feedback is the mechanism by which systems become self-regulating:
it appears in TCP congestion control, CPU frequency scaling, garbage collection, circuit breakers,
and load balancers. These four are fully documented entries.

*Availability*, *Privacy*, *Fairness*, and *Correctness* are left as open explorations. Availability
completes the trio with fault tolerance and resilience, making the outcome metric explicit. Privacy
extends security from "can unauthorised parties access this?" to "should authorised parties have
this in the first place?"--a question that is as much ethical as technical. Fairness asks what
equitable treatment means when resources are shared--a question with multiple incompatible formal
definitions and no single correct answer. Correctness is the deepest of the four: it is the
property that a system does what it should, which requires first having said what it should do.

For an indepth analysis of systemic concept within AI/ML, see [AI/ML](AIMLCONCEPTS.pdf).

