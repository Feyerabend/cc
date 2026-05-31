## Foundations: The Formal Basis of Computation

### 1. What Formal Methods Are (and Are Not)

Formal methods are mathematical techniques for specifying and verifying properties
of systems. The goal is certainty: not "this passed all my tests" but "this is
provably correct with respect to this specification."

This goal is not always achievable, and it is always expensive. The practice of
formal methods is therefore a discipline of choosing what to verify and how precisely.

Formal methods include a wide spectrum:
- *Lightweight formal methods:* type checking, model checking with small models,
  abstract interpretation, static analysis. Fast, automated, applicable broadly,
  but give weaker guarantees.
- *Interactive theorem proving:* proof assistants (Coq, Lean, Agda, Isabelle).
  Can verify essentially any mathematical property. Requires significant human effort
  and expertise. Used where the cost of failure is extremely high.
- *Automated theorem proving and SMT:* Z3, CVC5, Vampire. Push-button for many
  problems within bounded domains. Require careful encoding.

The choice between these is always a tradeoff between cost and strength of guarantee.
A type system is a form of formal verification that is so cheap and automated that
we no longer think of it as "formal methods." An Agda proof of a cryptographic
protocol is at the other extreme.

What all these approaches share is the requirement of a *specification*: a formal
statement of what "correct" means. Without that, there is nothing to verify against.
Writing a good specification is often harder than writing the program, and it is the
step most often omitted in practice.


### 2. Types as a Logical Foundation

The Curry-Howard correspondence, developed independently by Haskell Curry and
William Howard in the mid-twentieth century, identifies a deep structural equivalence
between type systems and logical systems.

On one side: propositions, proofs, and logical deduction. On the other: types, programs,
and type-checking. The correspondence maps:
- A type corresponds to a proposition.
- A program that inhabits a type corresponds to a proof of that proposition.
- Type-checking corresponds to proof verification.
- Reduction (computation) corresponds to proof normalisation.

This is not a metaphor. For the relevant type systems and logics, it is a precise
isomorphism. A function type `A -> B` corresponds to logical implication A ⊃ B.
A product type `A × B` corresponds to conjunction A ∧ B. A sum type `A + B`
corresponds to disjunction A ∨ B. The empty type corresponds to falsehood.

The correspondence extends as the type system becomes richer. Linear types correspond
to linear logic. Dependent types correspond to first-order predicate logic. The type
theory underlying Coq and Lean corresponds to a constructive higher-order logic.
HoTT extends this with homotopy theory, interpreting identity types as paths in a
topological space and the univalence axiom as the statement that equivalent types
are identical.

The practical consequence is that proof assistants are just type checkers for very
expressive type systems. Writing a proof in Agda is writing a program of a specific
type. The type checker verifies the proof.


### 3. Martin-Löf Type Theory and Its Descendants

MLTT (`ch08/addition/hott/mltt/`) is the logical foundation for most modern
proof assistants. Its central feature is *dependent types*: types that depend on
values. This allows the type system to express not just "this is a list" but
"this is a list of exactly n elements" or "this function returns a value greater
than its input."

MLTT is *constructive*: every proof must be a construction, not just an argument
from contradiction. This has philosophical implications — excluded middle and the
axiom of choice are not available without explicit addition — and practical ones:
proofs in MLTT are programs, and those programs can be extracted and run.

The core constructs of MLTT:
- *Π-types* (dependent function types): the type of functions from a type A to
  a type family B that depends on the input.
- *Σ-types* (dependent pair types): the type of pairs where the type of the
  second component depends on the value of the first.
- *Identity types*: the type of *witnesses* that two terms are identical. This
  is where HoTT begins: identity types can have non-trivial structure.

HoTT adds the *univalence axiom*: equivalent types are identical. This allows
mathematical structures to be transported along equivalences, making large
areas of abstract mathematics tractable in the type-theoretic framework.


### 4. Model Checking and the State Explosion Problem

Model checking (`ch08/addition/model/ctl`) is a technique for automatically verifying
that a finite-state system satisfies a temporal logic property. Given a model of the
system (a set of states and transitions) and a property (expressed in CTL, LTL, or
a similar logic), the model checker exhaustively explores all reachable states and
verifies the property at each one.

The power of model checking is its completeness within the model: if the property fails,
the checker produces a counterexample trace. This trace is a concrete execution showing
how the system reaches a bad state. It is often more informative than a failed test.

The limitation is the state explosion problem: the number of states grows exponentially
with the number of concurrent components. A system with ten independent threads, each
with ten states, has up to 10^10 combined states. Modern model checkers address this
with symbolic representation (representing sets of states as boolean formulas),
abstraction (grouping states that are indistinguishable for the property being checked),
and bounded model checking (checking only executions up to a fixed length).

The tools in `ch08/addition/model/` demonstrate model checking on small systems.
The connection to ch07's Raft implementation is direct: Raft's safety and liveness
properties are temporal logic formulas, and a simplified model of the protocol
can be checked against them.


### 5. Decidability and the Limits of Automation

Formal verification is constrained by the fundamental limits of computation.

The halting problem is undecidable: no algorithm can, in general, determine whether
an arbitrary program terminates. By reduction, most interesting properties of programs
are also undecidable. Rice's theorem states that every non-trivial semantic property
of programs is undecidable.

This means that every formal analysis tool must either:
- *Be incomplete:* it may fail to verify correct programs (false positives in bug finding,
  or inability to prove true properties).
- *Be unsound:* it may verify incorrect programs or miss real bugs.
- *Restrict its domain:* it operates only on a class of programs for which the property
  is decidable.

Presburger arithmetic is complete for linear arithmetic over integers — every true
formula is provable and every false formula is disprovable — but it cannot express
nonlinear arithmetic. Z3 is complete for some theories but not for all; in practice
it is a best-effort tool that may time out on hard instances.

Type systems are a particularly successful example of the third approach: they verify
a restricted class of properties (type safety, linearity, protocol compliance) exactly
and efficiently, at the cost of rejecting some programs that would actually behave
correctly (false positives). The art of type system design is choosing what to check
and what to leave undecidable.


### 6. The Verified Stack: Connecting All Chapters

The formal methods of ch08 are not isolated from the rest of the book. They are the
deepest level of a stack of techniques that reaches back to ch01.

At the bottom: representation. The correctness of a Hamming code (ch01) can be proved
in Z3. The correctness of a virtual machine's memory model (ch02) can be verified
with a model checker.

Above that: specification. The testing discipline of ch03 is informal specification.
TDD makes the specification executable. Formal methods make it mathematical.

Above that: implementation. The type systems of ch05 and ch07 enforce properties
of implementations. The session types ensure protocols are followed. The borrow checker
ensures memory is managed safely.

At the top: verification. The proof assistants of ch08 allow the full stack to be
formally certified: this VM, running this program, satisfies this specification,
proved by this proof, checkable by this checker.

In practice, this complete chain is rare and expensive. But its existence is not
merely academic. The CompCert compiler (a formally verified C compiler), the seL4
microkernel (a formally verified operating system kernel), and the Fiat cryptography
library (formally verified cryptographic implementations) show that the full chain
is possible for real, deployed software. The cost is high; the benefit is a level
of assurance that no amount of testing can provide.

The goal of this chapter is not to produce formally verified software, but to
understand what formal verification offers, what it costs, and where it sits
in relation to the other tools and techniques in the book.
