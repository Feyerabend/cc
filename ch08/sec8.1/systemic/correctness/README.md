
## Correctness

*This entry is an open exploration. A starting framework is provided below, but you are
expected to investigate, extend, and form your own understanding.*

Correctness is the property that a system does what it is supposed to do. It sounds obvious--surely
all systems are supposed to be correct. But correctness is surprisingly subtle, because it has a
precondition: correctness is only meaningful *relative to a specification*. A system cannot be
correct or incorrect in isolation; it can only be correct or incorrect with respect to some stated
description of what it should do.

This precondition is where most of the difficulty lies. In practice, specifications are often
informal, incomplete, or wrong. A system can be a faithful implementation of a flawed specification,
perfectly correct with respect to what was written down but wrong with respect to what was intended.
Or the system can be an imperfect implementation of a correct specification, correct in intent but
faulty in execution. These are different problems requiring different remedies.

Correctness is related to *determinism* (a correct system must produce the right answer, not
just a consistent one) and to *testing* (one way to gain evidence of correctness), but it is
broader than either. A system can be deterministic and consistently wrong. A system can pass
every test and still fail on untested inputs.


### Starting Points for Exploration

*Specification and verification:*

Formal verification proves that a system satisfies its specification using mathematical logic.
The specification is written in a formal language (TLA+, Coq, Isabelle) and the proof is
mechanically checked. This is expensive and requires significant expertise, but it provides
the strongest possible correctness guarantee. It is used for critical systems: CPU microcode,
cryptographic protocols, file system kernels.

Explore TLA+, developed by Leslie Lamport. What kind of properties can it express? What has
it found in real systems?

*Testing as evidence:*

Testing cannot prove correctness--it can only find bugs. A programme that passes all tests
is not correct; it is untested on the inputs that failed. Dijkstra's observation: "Testing
can show the presence of bugs, but never their absence." Despite this limitation, testing
is the dominant correctness strategy in industry, because it is practical. What makes a
test suite high-confidence? What is the relationship between test coverage and correctness?

*Invariants and assertions:*

An invariant is a property that must be true at all times (or at defined points) in a programme's
execution. Writing invariants explicitly--as assertions in code, as preconditions and postconditions
on functions, as class invariants in an object--is a form of lightweight specification. When an
invariant is violated, the programme fails immediately at the violation site rather than silently
continuing to a confusing failure later. What invariants are implicit in a programme you have
written? What would it mean to make them explicit?

*Type systems as correctness tools:*

A type system is a form of mechanical specification. By declaring that a function takes an integer
and returns a string, you have specified (in a limited way) part of its contract, and the compiler
enforces it. Stronger type systems (dependent types, refinement types) can express richer properties:
"this function takes a non-empty list" or "this value is in the range 0-100". Explore the
relationship between expressiveness of a type system and the correctness it can guarantee.

*Correctness in concurrent systems:*

Correctness in a single-threaded programme means: for this input, the output is right.
Correctness in a concurrent programme also means: the output is right regardless of the
interleaving of threads. This is much harder. Properties like *linearisability* (concurrent
operations appear to happen in some sequential order) and *serializability* (concurrent
transactions appear to execute one at a time) are formal correctness criteria for concurrent
systems. Look up one of these. What does it guarantee? What does it cost?

*The cost of correctness:*

Stronger correctness guarantees cost more: in development time, in runtime overhead (assertions,
runtime checks), in system complexity. A formally verified file system may have 10x the
development effort of an unverified one. Is it worth it? For what systems? Who decides?


### Questions to Answer

1. What is the difference between correctness and reliability?
2. What does it mean for a specification to be "wrong"? Give an example.
3. Can a programme be proven correct? Under what conditions? With what limitations?
4. What is the relationship between correctness and testing? Why can testing not prove correctness?
5. Find a real-world software failure caused by a correctness bug (not a performance or security
   bug). What was specified? What was implemented? What was the gap?
6. What role do types play in correctness? What can they guarantee and what can they not?
7. Is "it works on my machine" a correctness claim? What is it missing?

Write your answers carefully. Correctness is one of the oldest and hardest problems in
computer science. The goal is not to solve it but to understand why it is hard.
