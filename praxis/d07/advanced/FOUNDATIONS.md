## Foundations: Correctness in Complex Systems

### 1. The Problem of Correctness at Scale

A single-threaded program with no external dependencies can, in principle, be
understood completely. Given enough time, you can trace every execution path,
verify every output, and be confident that you understand what the program does.

As soon as you add concurrency, distribution, or interaction with external state,
this complete understanding becomes impossible. The space of possible executions
grows exponentially with the number of concurrent actors. The program's behaviour
depends on timing, scheduling, and network conditions that you cannot control or
fully predict.

This is not a temporary problem to be solved by better tools. It is a consequence
of the nature of concurrent and distributed systems. Dijkstra's remark that
"testing can show the presence of bugs but never their absence" is especially
true here. No test suite can cover the space of possible interleavings of
concurrent operations.

What makes correctness tractable in this setting is *structure*: invariants that
must hold regardless of scheduling, protocols that constrain what messages can be
sent and when, type systems that rule out entire classes of errors at compile time.
The advanced programming concepts in this chapter — algebraic effects, session types,
borrow checking, consensus protocols — are all tools for imposing structure on
complex systems.


### 2. The Memory Model as a Contract

One of the most subtle sources of concurrency bugs is not the program logic but the
memory model: the specification of what a thread is guaranteed to observe about
writes performed by other threads.

On modern hardware, writes are not immediately visible to other threads. CPUs use
caches, write buffers, and out-of-order execution. A write by thread A may not reach
thread B's cache until much later, and memory operations may be reordered by the
hardware in ways that are invisible to any single thread.

A memory model is a specification of the visibility guarantees that a language or
runtime provides. Java's memory model guarantees that a write to a volatile variable
is immediately visible to all threads. Rust's memory model, inherited from C++11,
provides similar guarantees for atomic operations. Without explicit synchronisation,
the program is allowed to behave in ways that appear correct under any single-thread
execution but fail under concurrent execution.

The borrow checker (`ch07/addition/borrow`) is in part a response to this: by
preventing data races at the type level, it ensures that memory access patterns are
sound without requiring the programmer to reason about the underlying memory model.


### 3. Effect Systems: Making Side Effects Explicit

An algebraic effect system is a type-level mechanism for tracking which side effects
a computation may perform. A function with type `() -> Int with IO, State` promises to
return an integer and may perform IO and modify state — but nothing else. A pure
function cannot perform IO accidentally.

This is a stronger property than monadic effect tracking (though the two are related).
In a monad-based system, effects are encoded into the type but the handling is
implicit in the monad's bind operation. In an effect system, effects are described
separately from their handlers. The same computation can be run under different
handlers — one that performs real IO, one that mocks it, one that logs it — without
any change to the computation itself.

The `ch07/addition/effect/` implementations demonstrate this. The `counter` effect
describes "a computation that may read or write a counter." The handlers implement
what "read" and "write" actually do. Swapping handlers is a semantics change, not
a code change.

This is important for testing (substitute mock handlers for real ones), for
optimisation (substitute a batched handler for an immediate one), and for
correctness (substitute a transactional handler for a direct one, to guarantee
atomicity).


### 4. Session Types: Correctness by Protocol

A session type is a specification of the sequence of messages that must be exchanged
on a communication channel. A well-typed program cannot send a message out of order,
cannot forget to send a required message, and cannot receive a message of the wrong type.

This is a form of *protocol compliance by construction*. The alternative — verifying
protocol compliance at runtime — catches violations late, generates unhelpful error
messages, and requires that the protocol be re-specified in each implementation.
Session types move the verification to compile time, where it is cheaper and more
reliable.

The connection to formal verification is direct. A session type is a linear logic
formula. Type-checking a program against a session type is proof search in linear
logic. The theory in `ch07/addition/sessions/THEORY.md` develops this connection.

Session types are related to (but distinct from) the protocols modelled in Alloy
(`ch06/addition/algebra/alloy`) and the state machines verified by CTL model
checking (`ch08/addition/model/ctl`). All three tools are answers to the same
question: how do we ensure that a system follows its intended protocol?


### 5. Consensus and the Impossibility of Distributed Agreement

The Raft consensus protocol is a solution to a problem that sounds simple and
turns out to be remarkably hard: how do a group of nodes with unreliable communication
agree on a sequence of values?

The difficulty is not engineering; it is fundamental. The FLP impossibility result
(Fischer, Lynch, Paterson, 1985) proves that no deterministic protocol can guarantee
both safety (nodes agree) and liveness (nodes make progress) in an asynchronous
network where even one node may fail.

Raft's response is to give up the liveness guarantee during partitions: if the network
is split, the majority partition stops accepting writes rather than risking inconsistency.
This is a deliberate tradeoff. The CAP theorem makes this tradeoff precise: a distributed
system can guarantee at most two of Consistency, Availability, and Partition tolerance.
Raft chooses Consistency and Partition tolerance over Availability.

Understanding why this tradeoff is necessary — not just that it is made — requires
engaging with the impossibility results. The formal verification in `ch08/addition/model/ctl`
can check whether a given protocol satisfies safety properties. It cannot overcome
the FLP bound; it can only verify that a protocol does what it claims to do within
the constraints imposed by the bound.


### 6. The Relationship Between Types, Proofs, and Programs

The advanced type systems in this chapter — linear types, session types, dependent types —
are not merely engineering improvements over simple type systems. They represent a
fundamentally different way of thinking about what a program is.

In the Curry-Howard correspondence, a type is a proposition and a program is a proof
of that proposition. A function of type `A -> B` is a proof that B follows from A.
A linear function of type `A -o B` is a proof that B follows from A and that the
derivation uses A exactly once.

Under this correspondence, type-checking is proof-checking, and a program that
passes the type checker is a certified proof of a logical statement. This is the
theoretical basis for the proof assistants in `ch08/addition/proof`: they are
type-checkers for a very expressive type system, and the programs you write in
them are formal proofs.

The gap between the advanced type systems in this chapter and the proof assistants
of ch08 is narrower than it appears. Session types correspond to linear logic proofs.
Dependent types in Agda or Lean are proof-carrying code. The borrow checker's
lifetime analysis corresponds to an affine logic proof obligation.

This connection suggests a unified perspective on what programming languages are:
they are systems for expressing computational processes, and the type system is the
logical framework within which those processes can be reasoned about. The richer the
type system, the more reasoning can be done statically, and the more confident one
can be that the program does what it is claimed to do.
