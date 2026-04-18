
## Combinations of Systemic Concepts

The systemic concepts described in the [systemic](../systemic/) section do not exist in isolation.
They interact, collide, and reinforce each other. When two or three of them act simultaneously
on a design problem, they often leave only one rational architectural response--a structure that
*must* exist given those forces, even if the designer had never heard of it by name.

This section explores those interactions. Each entry begins not with a solution but with forces:
systemic pressures that any engineer would recognise from the problem at hand. The task is to
*derive* the emergent concept from those pressures, rather than to receive it as a definition.

The form of each entry is:
```
Force A + Force B + Force C  ->  Emergent Concept
```

This is not metaphor. It is the claim that if you accept the three forces as real constraints,
the emergent concept follows as a logical necessity. The goal is to arrive at the concept
through reasoning, so that when you encounter it in practice you recognise not just its name
but *why it has to exist*.

This approach to understanding is sometimes called *first-principles thinking*: instead of
learning a catalogue of solutions, you learn the forces that generate solutions. The same forces
appear again and again across different layers of computing--hardware, software, distributed
systems, security--producing different emergent structures that are, at root, responses to the
same underlying pressures.


### Guided Derivations

The following entries are fully worked. Each takes you through a sequence of thought experiments,
simulations, and observations that lead step by step to the emergent concept. You are expected
to run the code, observe the results, and answer the reflection questions.

| Forces                                     | Emergent Concept    | Entry                                 |
|--------------------------------------------|---------------------|---------------------------------------|
| Latency + Cost + Locality                  | Cache               | [locality](./locality/)               |
| Concurrency + State + Determinism          | Synchronisation     | [synchronisation](./synchronisation/) |
| Scalability + Cost + Latency               | Distributed Systems | [distributed](./distributed/)         |
| Determinism + Time + Latency               | Real-Time Systems   | [realtime](./realtime/)               |
| Security + Randomness + Complexity         | Cryptography        | [cryptography](./cryptography/)       |
| Fault Tolerance + Scalability + Resilience | Redundancy          | [redundancy](./redundancy/)           |
| Abstraction + Interface + Complexity       | Modularity          | [modularity](./modularity/)           |
| Noise + Errors + Fault Tolerance           | Error Correction    | [errorcorrection](./errorcorrection/) |
| State + Time + Concurrency                 | Consistency         | [consistency](./consistency/)         |


### Exercises

The following entries are open-ended. A brief orientation is provided--the forces involved
and the direction of the derivation--but the working-through is yours. You have already seen
how the guided derivations proceed. Apply the same reasoning here: start with the forces,
ask what they demand, and build toward the concept without being told what it is.

| Forces                           | Emergent Concept | Entry                                 |
|----------------------------------|------------------|---------------------------------------|
| Time + Concurrency + Determinism | Scheduling       | [scheduling](./scheduling/)           |
| Energy Use + Optimisation + Cost | Power Management | [powermanagement](./powermanagement/) |
| Security + State + Interface     | Authentication   | [authentication](./authentication/)   |

These exercises are placed here because they are close enough to the guided derivations that
a careful reader should be able to reconstruct them independently. The synchronisation and
real-time entries give you the tools for scheduling. The cryptography entry gives you the
tools for authentication. Power management is the energy dimension of the cost-optimisation
tension that runs through several guided entries.


### Relations Between Combinations

The emergent concepts are not independent of each other. They form their own web of interactions:

*Synchronisation* and *consistency* address the same underlying problem--shared state under
concurrency--at different scales. Synchronisation is the local mechanism (a lock on a data
structure); consistency is the system-level model (what guarantees the whole distributed system
makes about its state). Building a consistent distributed system typically requires synchronisation
internally.

*Distributed systems* immediately produces a need for *consistency*. The moment data lives on
more than one machine and concurrent actors write to it, you must choose a consistency model.
The distributed entry shows you how you arrive at distribution; the consistency entry shows you
what distribution immediately demands of you.

*Redundancy* is the structural response to the reliability demands that distributed systems face.
A distributed system with no redundancy is fragile in proportion to its scale--more components
means more failure probability. Redundancy reduces per-component failure to per-system failure.
But redundancy with mutable state requires consistency: which copy is authoritative when they
diverge?

*Error correction* and *redundancy* are the same principle at different layers. Error correction
adds redundant bits to data so that noise-induced corruption can be detected and reversed.
Redundancy adds redundant machines so that hardware failure can be tolerated. The mathematical
structure--adding structured extra copies so that the original can be recovered from a subset--
is identical.

*Modularity* and *distributed systems* reinforce each other. A well-modularised system, where
components interact only through defined interfaces, is easier to distribute across machines
because the interfaces become network boundaries. A poorly modularised system is very hard to
distribute because its components are entangled in ways that cross-machine communication cannot
accommodate.

*Real-time systems* and *scheduling* are directly connected. Real-time guarantees are made
possible by a scheduler that gives priority to time-critical tasks. The real-time entry derives
why timing must be a correctness criterion; the scheduling exercise asks you to derive what
structure meets that criterion.

*Cryptography* is a precondition for *authentication* in any system where the channel between
client and server is not trusted. If a password travels in plaintext, any observer on the
network can steal it. Authentication without cryptography is security theatre.


### How to Use This Section

Each guided entry can be read and worked in isolation. However, the most valuable experience
is to work through them in sequence, because later entries build on intuitions established by
earlier ones. A suggested order:

1. *Locality* - the simplest derivation; establishes the method.
2. *Synchronisation* - introduces the cost of concurrency with shared state.
3. *Distributed Systems* - shows why single-machine limits force a fundamental architectural change.
4. *Consistency* - shows what distributed systems immediately demand.
5. *Redundancy* - shows how reliability is maintained at scale.
6. *Real-Time Systems* - introduces time as a correctness criterion.
7. *Error Correction* - shows the principle of structured redundancy at the data level.
8. *Modularity* - shows how complexity forces structural discipline.
9. *Cryptography* - shows how security, randomness, and hardness combine.

Then attempt the exercises before moving on.

The reflection questions at the end of each entry are not optional. They are where the
understanding is consolidated. An entry read without answering its questions is a concept
encountered, not learned.
