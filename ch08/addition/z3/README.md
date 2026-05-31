
## Symbolic Register-Based Virtual Machine

This project implements a *symbolic register-based virtual machine (SymRegVM)* that uses
the *Z3 SMT solver* to perform *symbolic execution* and verify properties of programs. It
is a small but concrete example of a much larger field: automated formal verification through
theorem proving and constraint solving.

> *Dependency:* You must have Z3's Python bindings installed to run this.
> Install with: `pip install z3-solver`


### Theorem Provers: Historical and Current Context

To understand what Z3 does and why it matters, it helps to trace where the idea came from
and how the field developed.

#### The Early Foundations (1950s–1970s)

The dream of mechanising mathematical reasoning is almost as old as computing itself. Alan
Turing, Alonzo Church, and others had already shown in the 1930s that some questions about
programs are undecidable in general, yet within bounded domains a machine can be made to
reason rigorously.

The first automated theorem prover of significance was the *Logic Theorist* (1956), built by
Allen Newell, Herbert Simon, and Cliff Shaw at RAND Corporation. It could prove theorems
from Whitehead and Russell's *Principia Mathematica* using heuristic search. Their follow-up,
the *General Problem Solver* (1957), attempted domain-independent reasoning.

The *Resolution principle*, introduced by John Alan Robinson in 1965, gave theorem provers a
much cleaner algorithmic foundation. Instead of heuristic search, resolution reduces proof
to a single, mechanically applicable rule. This underpins most classical logic-based provers
and eventually Prolog. The *DPLL algorithm* (Davis, Putnam, Logemann, Loveland, 1960–1962)
gave us efficient SAT solving — determining whether a propositional formula has any
satisfying assignment — which remains the engine inside virtually every modern SMT solver.

Dedicated *interactive theorem provers* (ITPs) emerged in the late 1960s and 1970s. These
systems require a human to guide the proof, with the machine checking each step. The most
influential early examples are:

- *LCF* (Edinburgh, 1972, Robin Milner): The first system to use a small, trusted *kernel*
  that all proofs must pass through. Its ML metalanguage let users write proof tactics. This
  architecture — a tiny trusted core with a programmable tactic layer — directly influenced
  every major ITP that followed.
- *Automath* (Eindhoven, 1967, de Bruijn): An early dependent-type framework for checking
  mathematical texts, predating by decades the type-theoretic foundations now used in Coq
  and Lean.

#### Interactive Theorem Provers (ITPs)

Interactive provers ask a human to construct a proof step by step; the system only checks
correctness. They are extremely expressive — capable of formalising almost any mathematics —
but require substantial expertise and effort.

*HOL (Higher-Order Logic)* descended from Milner's LCF. The HOL4 and HOL Light variants
remain active today. HOL Light (John Harrison, Intel) was famously used to formally verify
the *Kepler conjecture* proof as part of the Flyspeck project (completed 2014).

*Isabelle/HOL* (Lawrence Paulson, Cambridge, 1986 onward) combines a generic logical
framework with a powerful automation layer called Sledgehammer, which calls external ATPs
and SMT solvers to discharge subgoals. Isabelle has been used to verify the seL4 microkernel
(a complete formal proof of functional correctness of an operating system kernel, 2009) and
the CakeML compiler.

*Coq* (INRIA, France, 1989 onward) is based on the *Calculus of Inductive Constructions*,
a dependent type theory where proofs and programs are the same kind of object. Coq was used
to verify the *four-colour theorem* (Gonthier, 2005), the CompCert C compiler (Xavier Leroy,
proven to produce correct machine code), and large parts of mathematics in the Mathematical
Components library.

*Lean* (Microsoft Research, Leonardo de Moura, 2013; Lean 4 rewrite 2021) is the newest
major ITP and has attracted enormous recent interest, partly through the *Mathlib* project —
a community library formalising a large swath of undergraduate and graduate mathematics.
Recent collaborations with AI researchers (including DeepMind's AlphaProof and the
Terence Tao group) are exploring how large language models can assist with Lean proofs.

#### Automated Theorem Provers (ATPs)

Unlike interactive provers, ATPs attempt to find proofs entirely on their own, given a
first-order formula and background axioms. They excel within their domain but cannot match
the expressiveness of ITPs.

*Vampire* (Manchester/Vienna, Riazanov and Voronkov, 1993 onward) and *E* (Schulz, 1998)
are state-of-the-art resolution- and superposition-based provers. They compete annually at
the *CASC* competition (CADE ATP System Competition). ATPs are widely used as back-ends
inside Isabelle's Sledgehammer and other systems.

*Prover9/Mace4* (McCune, Argonne National Laboratory) proved a long-standing open problem
in combinatory logic (the Robbins conjecture) in 1996 — the first major open mathematical
problem solved by an ATP.

#### SAT Solvers

A *SAT solver* decides whether a propositional formula in conjunctive normal form has a
satisfying assignment. Modern solvers — *MiniSAT* (Sörensson and Eén, 2003), *Glucose*,
*CaDiCaL*, *Kissat* — use the *CDCL* (Conflict-Driven Clause Learning) algorithm, a
dramatic improvement on DPLL. SAT is NP-complete in theory, but practical CDCL solvers
handle industrial instances with millions of variables. Hardware companies such as Intel and
AMD use SAT-based model checking to verify chip designs.

#### SMT Solvers: Z3 and its Peers

*Satisfiability Modulo Theories* (SMT) extends SAT by adding richer background theories:
linear and nonlinear arithmetic, arrays, bit-vectors, strings, algebraic data types, and
more. An SMT solver combines a CDCL SAT engine with theory solvers that handle each domain.
When the SAT engine finds a candidate Boolean assignment, the theory solvers check whether
it is consistent with the underlying mathematics; if not, they generate a *conflict clause*
that rules it out.

*Z3* (Leonardo de Moura and Nikolaj Bjørner, Microsoft Research, 2008) is the dominant
SMT solver in both research and industry. It is used inside:

- *Software verification tools*: Dafny, Boogie, Spec#, VeriFast, Why3, Frama-C
- *Security analysis*: symbolic execution engines like KLEE, angr, and Manticore use Z3
  to solve path constraints when exploring program branches
- *Hardware verification*: as a back-end to model checkers
- *Constraint solving in AI*: planning, synthesis, and test generation

*CVC5* (the successor to CVC4, developed at Stanford, Iowa, and NYU) is Z3's closest
competitor and often outperforms it on specific theory combinations. *Yices 2* (SRI
International) is particularly fast on quantifier-free fragments and bit-vector reasoning.

All three support the *SMT-LIB 2* standard input format, enabling benchmarks and tool
interoperability. Annual *SMT-COMP* competitions drive solver performance forward.

#### Model Checkers

Model checking, pioneered by Clarke, Emerson, and Sifakis (Turing Award 2007), verifies
finite-state systems exhaustively. *SPIN* (Holzmann, Bell Labs) checks concurrent protocol
specifications. *NuSMV* and *nuXmv* check hardware and software models against temporal
logic properties. *CBMC* (Clarke et al.) uses SAT/SMT to bounded-model-check C programs,
finding bugs up to a given depth. *CPAchecker* and *Ultimate Automizer* compete in the
*SV-COMP* (Software Verification Competition) and use SMT solvers as core engines.

#### The Current Landscape

Several trends are shaping the field today:

*AI + Formal Methods.* Large language models are being applied both to *generate* proof
attempts (e.g., OpenAI's work on IMO problems, DeepMind's AlphaProof) and to *synthesise*
programs that are then formally verified. The combination is promising but still nascent.

*Verified software stacks.* CompCert (C), CakeML (ML), and ongoing work on Rust
verification (Verus, Creusot) show that verified compilers are practical. The seL4
microkernel, used in safety-critical aerospace and automotive systems, demonstrates
OS-level verification.

*SMT in everyday development.* Tools like Dafny (Amazon) and F* (Microsoft) let developers
write specifications alongside code, with Z3 discharging proof obligations automatically.
AWS uses Dafny to verify cloud infrastructure code.

*Lean and the formalisation of mathematics.* The Mathlib library for Lean 4 now covers
topology, algebraic geometry, number theory, and more, with hundreds of contributors. This
represents a shift from proof checking as a specialist activity to something approaching
collaborative, machine-checked mathematics.

#### How Z3 Works (in brief)

Z3 implements the *DPLL(T)* framework:

1. A CDCL SAT solver works over a propositional abstraction of the input formula.
2. When a candidate model is found, specialised *theory solvers* (for linear arithmetic,
   arrays, bit-vectors, etc.) check consistency.
3. If a theory contradiction is found, a lemma is added back to the SAT solver to block
   that class of assignments.
4. The process repeats until either a satisfying assignment is found (*sat*) or the search
   space is exhausted (*unsat*).

For quantified formulas, Z3 uses *E-matching* and *model-based quantifier instantiation*
(MBQI) to handle universally and existentially quantified variables.

When the result is *sat*, Z3 can produce a *model* — a concrete assignment of values to
variables satisfying all constraints. When the result is *unsat*, Z3 can optionally produce
an *unsatisfiability proof*.

In this project, we use Z3's integer arithmetic theory. Each VM state (registers, flags,
program counter) at each time step is a Z3 integer variable. Instructions are encoded as
constraints relating consecutive states. Asking "does this property hold for all executions?"
becomes asking whether the negation of the property is *unsat* — that is, that no execution
can violate it.


### Project Overview

#### What SymRegVM Does

The VM models a simple register machine with:

- *Registers*: `A` (accumulator), `B` (auxiliary)
- *Flags*: `Z` (zero flag), `N` (negative flag)
- *Program counter*: `pc` (set to -1 when halted)
- *Instruction set*: `LOAD_A`, `LOAD_B`, `ADD`, `SUB`, `MUL`, `DIV`, `JNZ`, `HALT`

Programs are lists of `(instruction, operand)` pairs. The VM encodes every possible
execution symbolically as Z3 constraints, then uses Z3 to either prove that a property
holds for all executions or find a counterexample.

#### Files

*`simple.py`* — A minimal proof-of-concept. Loads 5 into B, loads 0 into A, multiplies,
and verifies `A == 0` at halt. Shows the basic constraint-encoding pattern with no
distractions.

*`sym_regvm.py`* — The extended VM. Adds out-of-bounds PC handling, a helper for
converting Z3 boolean values to Python booleans, a higher default step limit (50), and
three factorial programs (3!, 4!, 5!) demonstrating multi-step arithmetic verification.
A `run_example()` helper drives all three cases uniformly.

*`verify_rate_limiter.py`* — A practical, self-contained verification example that does
not use the VM's instruction set at all. Instead it encodes a *token bucket rate limiter*
directly as Z3 integer constraints — exactly as a bounded model checker like CBMC would
do internally. See the section below for details.

#### The Rate Limiter Example

A token bucket is the rate-limiting algorithm behind Linux `tc`, nginx `limit_req`, AWS
API Gateway, and Envoy. The rules are straightforward: at the start of each tick add
`REFILL` tokens (capped at `CAPACITY`); each arriving request consumes one token if
available, otherwise it is rejected.

`verify_rate_limiter.py` demonstrates four things in sequence:

*Part 1 — proving the correct implementation.* Four properties are checked over all
possible request sequences simultaneously: the safety throughput bound, the capacity
invariant (tokens never exceed `CAPACITY`), no negative token counts, and a liveness
guarantee that at least one request is accepted when demand is continuous. Each check is
a single Z3 call.

*Part 2 — a real bug with a real counterexample.* Removing the `min(tokens + REFILL, CAPACITY)`
cap is a plausible mistake — easy to forget or accidentally drop in a refactor. Z3 finds
the minimal counterexample immediately: with no requests arriving, tokens grow freely by
`+REFILL` each tick, violating the capacity invariant at tick 1.

*Part 3 — a subtle ordering bug.* Swapping refill and serve seems harmless and produces
identical output when the bucket starts full. Z3 finds that with an initially empty bucket
the serve-first variant rejects the first request (it sees `tokens == 0` before refilling),
while the correct implementation refills first and accepts it. This is precisely the class
of edge-case bug that normal unit tests almost never catch.

*Part 4 — scale.* Over 5 ticks there are 2⁵ = 32 possible request patterns. Over 64
ticks there are 2⁶⁴ ≈ 1.8 × 10¹⁹. Z3 handles either in one solver call because it
manipulates the constraints algebraically rather than enumerating sequences.

#### The Connection Between the VM and the Rate Limiter

`simple.py` and `sym_regvm.py` encode programs as explicit instruction sequences and let
Z3 reason about their execution traces. `verify_rate_limiter.py` skips the instruction
layer entirely and writes the transition relation — the per-tick state update — directly
as Z3 constraints. Both approaches are valid; the choice depends on whether the property
of interest is about a concrete machine program or about an algorithm expressed more
abstractly. Real tools like CBMC translate C source code into the second form automatically.

#### Limitations

- Symbolic execution is computationally expensive; the fixed `max_steps` caps complexity.
- No decrement instruction in the VM makes countdown loops awkward to express.
- Z3's nonlinear integer arithmetic (multiplication) is undecidable in general; the solver
  may time out on large programs that use it heavily.
- Loops must be fully unrolled within `max_steps`; there is no support for loop invariants.

#### Potential Improvements

- Add `DEC_B` (decrement B) and `CMP` (compare) instructions to support loops naturally.
- Support loop invariant annotations to verify loops without full unrolling.
- Develop a small high-level language that compiles down to VM instructions.
- Use Z3's incremental solving (`push`/`pop`) for more efficient property checking across
  multiple related queries (the rate limiter already does this correctly).
- Explore using Lean or Coq to give a fully mechanised proof of the VM's semantics itself,
  rather than just the programs it runs.
