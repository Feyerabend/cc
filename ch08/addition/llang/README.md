
## llang: A HoTT/MLTT Research Kernel — Beta Release

Samples have for a natural departure point been of a toy character throughout:
simple programs to illustrate how the system works. But learning also connects
to research, discovery, curiosity. Here is an attempt to go much further than
simple examples, into research territory.
  
The subject, Homotopy Type Theory and Martin-Löf Type Theory, can be hard to
grasp because it is a genuinely different way of thinking about computation,
in relation to classical computer science. It is worth pausing on why it is
different, rather than diving directly into syntax.

*The classical picture*. In most of what we call computer science, a program
and a proof of correctness are two separate things. You write fib in Python or
OCaml; you test it; if you want a proof, you go to a separate tool--a model
checker, a theorem prover, a verification framework. Types help catch errors early,
but they are erased when the program runs. The compiler does not know, and does
not need to know, what the function is supposed to compute. The gap between
running correctly on a few inputs and provably correct on all inputs is papered
over by testing. This is not a criticism--it is an extremely pragmatic and
productive approach that has built the modern software world. But the gap remains.

A shorter [example](./lang/samples/FIBONACCI.md) of this.

*The MLTT shift*. Martin-Löf Type Theory collapses this gap. A type is a specification,
and a term of that type is the proof that the specification is met. There is no
separate proof step. If you write a function `f : Vec Nat n → Nat` that extracts
the first element of a non-empty vector, the type `Vec Nat (succ n)` in the argument
is the proof that the vector is non-empty--there is no runtime bounds check because
there cannot be an empty vector at that type. The type checker and the proof checker
are the same thing, running on the same term, at the same moment. The example
explores this concretely: what is the kernel actually checking when it accepts a
definition, what is it not checking, and what guarantees does it issue?

*The HoTT leap*. Homotopy Type Theory goes one step further and asks a question that
classical logic does not even pose: when are two proofs of the same thing the same?
In ordinary mathematics, if I prove a theorem by two different routes, those two
proofs are both proofs of the same statement--and that is the end of the discussion.
HoTT says: the two proofs are themselves mathematical objects, and they may or may
not be equal. Two proofs of A = B can be different paths from A to B. Two proofs
that those two paths are the same can themselves be different--a surface connecting
two routes on a torus. This is not wordplay. It is borrowed directly from algebraic
topology, where a space's identity is shaped by how its paths relate to each other.
Equality, in this framework, is not a binary yes/no verdict but a structured object
with geometry.

*Why it matters for computer science*. This has practical consequences. It leads to
a model of computation in which the distinction between data and proof dissolves,
in which the question "are these two programs equivalent?" becomes a first-class
mathematical object you can reason about, and in which types can encode not just
what a function accepts and returns but the full correctness statement of the
computation it performs.

The kernel in this repository implements a complete cubical homotopy type theory kernel
written in C. Implements Martin-Löf Type Theory extended with cubical primitives
(interval, path types, transport, composition, Glue types, univalence), higher inductive 
types including 2-cells, universe polymorphism, implicit arguments, pattern matching
with structural termination checking, and a surface language with module system.

*1261 tests, 0 failures.*

That model are, in a precise sense, proofs rather than tests.


### Building

```
make            ## builds core/lcore (NbE REPL) and lang/llang (surface REPL)
make test       ## runs the full test suite
```

Requires a C11 compiler (`cc`). No other dependencies.

It builds on code from [proof](./../proof/).


### Architecture

Two layers, cleanly separated:

```
core/           NbE kernel — type checker, evaluator, elaborator
  term.h/c      Term AST and Val (semantic values) with all TM_/VL_ tags
  eval.h/c      NbE evaluator: nbe_eval, nbe_quote, all eliminators
  check.h/c     Bidirectional type checker: infer, check, conv
  parse.h/c     Surface-syntax parser for the core REPL
  elab.h/c      Hole elaboration (first-order pattern unification)
  defs.h/c      Global definition table + inductive family registry
  termcheck.h/c Structural termination checker for let rec
  main.c        Core REPL + 1261-test suite

lang/           Graph-reducer surface language (built on top of core)
  node.h/c      Heap graph nodes, printing
  bridge.h/c    Val ↔ ND_CORE bridge (round-trips through NbE)
  reduce.h/c    Graph reduction + REPL commands (:load, :conv, :let, etc.)
  main.c        Surface REPL entry point
  lib/          Standard library (.lam files)
  samples/      Example programs
```

The core is self-contained: `main.c term.c eval.c parse.c check.c defs.c elab.c termcheck.c`
compiles to a complete system. The lang layer links the same core files and adds a graph-reduction surface language.



### What is implemented

#### Type theory

| Feature | Notes |
|---------|-------|
| Π, Σ, W-types | Full dependent function, pair, well-founded trees |
| Martin-Löf Id | J eliminator with CORE-1 fix (non-trivial paths via transp) |
| Bool, Nat | Built-in with eliminators; qualified ctor names (Bool.true etc.) |
| Universe polymorphism | `Level`, `lzero`, `lsuc`, `lmax`, `Type_ℓ` |
| Sum types | `inl`/`inr`/`case` |
| Quotient types | `Quot A R`, `qin`, `qeq` (stuck), `quotrec` |
| Implicit arguments | `_` holes solved by first-order pattern unification |
| `let rec` / `fix` | Structural termination checker enforces well-foundedness |
| Pattern matching | `match scrut of \| ctor args => body`; supports IH sugar in succ arm |  

#### Cubical HoTT

| Feature | Notes |
|---------|-------|
| Interval `II`, `i0`, `i1` | Sentinel neutrals |
| Path type `Path A a b` | `⟨i⟩ body`, `p @ r` |
| PathP (heterogeneous) | `PathP fam a b`; cross-tag conv with `Path` |
| `transp` | Structural rules for Π, Σ, PathP, Glue; non-closed → stuck |
| `hcomp` | Structural rules for Π, Σ, Path, PathP, Glue |
| `comp` / `fill` | Heterogeneous composition and fill-at-variable-point |
| `primSub` | Face-bounded element (CCHM §5); enables transp-PathP |
| Interval ops | `imin`, `imax`, `ineg`; full lattice tautology via 2^n enumeration |
| Partial elements | `IsOne φ`, `Partial φ A`, `[φ ↦ u]` surface syntax |
| Glue types | `Glue A φ T e`; `Equiv T A`; `ua` computation; η-rule |
| `funext` | Computes: `funext A B f g h = ⟨i⟩ λx. h x @ i` |

#### Higher inductive types

| Feature | Notes |
|---------|-------|
| General 1-cell HITs | `data T where c : Path T l r`; sentinel approach |
| Dependent HIT eliminator | Indexed families: motive `P : Π(i:I). T i → Type` |
| 2-cell HITs | `data T where s : Path (Path T l r) p q`; full endpoint equations and indrec |
| `Susp`, `Circle`, `Torus` | All defined as user data types (no hard-coding) |

#### Surface language (lang/)

| Feature | Notes |
|---------|-------|
| Module system | `module NAME where … end`, `open`, `import "file"` |
| Where clauses | `let f = body where helper = rhs` |
| Qualified ctors | `Nat.zero`, `Bool.true`, `MyType.ctor` |
| `rfl` tactic | Resolves `refl _` by unification |
| REPL commands | `:let`, `:load`, `:conv`, `:i`, `:t` |



### Running examples

#### Core REPL
```
cd core && ./lcore
λ> :i (λA. λx. x : Π(A : Type). A → A)
  type: Π(A : Type). Π(_ : A). A
λ> :t        -- run full test suite
```

#### Surface REPL
```
cd lang && ./llang
> :load "samples/stlc.lam"
> :load "samples/torus.lam"
> :load "samples/hit.lam"
```

#### Sample programs

| File | What it demonstrates |
|------|----------------------|
| `samples/factorial.lam` | Structural recursion via `match … ih` |
| `samples/fibonacci.lam` | Accumulator-style fibonacci |
| `samples/stlc.lam` | Certified STLC interpreter (type soundness by construction) |
| `samples/modules.lam` | Module system with nested modules |
| `samples/hit.lam` | Circle, Suspension, Two-Point space as general HITs |
| `samples/torus.lam` | Torus as a 2-cell HIT with endpoint equations and eliminator |
| `samples/where.lam` | Where-clause local helpers |
| `samples/quotient.lam` | Quotient types and setoid equality |
| `samples/implicit.lam` | Implicit argument elaboration |
| `samples/polymorphism.lam` | Universe polymorphism |
| `lib/nat.lam` | Arithmetic library |
| `lib/vec.lam` | Sized vectors |
| `lib/fin.lam` | Bounded naturals |
| `lib/proofs.lam` | Basic HoTT lemmas |



### Design notes

**Sound incompleteness over unsound computation.** Non-closed `transp`, neutral faces,
failed `unglue` — all stay stuck as `VL_TRANSP`/`VL_HCOMP` neutrals. The kernel never guesses.

**Sentinel-based HIT representation.** Each path constructor `c` of family `F` gets a
permanent sentinel level `-(1000 + fam_idx*64 + ctor_idx)`. Neutrals with these levels
carry their ctor args in the spine; endpoint equations fire when `SP_PATHAPP` nodes at
i0/i1 are detected. 2-cells extend this: two leading `SP_PATHAPP` nodes trigger second-dimension
endpoint equations and the 2-cell `nbe_vindrec` branch.

**NbE + bidirectional checking.** Evaluation is always to full normal form (no lazy thunks).
Conversion checking normalises both sides and compares structurally. The bidirectional checker
threads a type downward (`check` mode) and synthesises it upward (`infer` mode).



### Three directions for expansion

__The kernel is feature-complete for standard HoTT and is ready to serve as a platform.__
Three directions are viable:

#### 1. Program verification

Add `theorem` keyword (forces type annotation), `sorry`/`admit` escape hatch, and a minimal
tactic layer (`rfl`, `exact`, `apply`, `rewrite`). The kernel already handles everything theoretically;
the gap is ergonomic. The STLC demo in `samples/stlc.lam` shows the target feel: intrinsically-typed
programs whose type is a machine-checked correctness proof.

**Near-term steps:** tactic parser in `lang/main.c`; `theorem` as a checked `let`; `sorry : Π(A:Type). A`
axiom with a warning flag; `rewrite` as a `J`-application macro.

#### 2. Type system experimentation lab

The `TM_`/`VL_` tag pattern makes adding a new type former straightforward: add tags to `term.h`,
evaluation cases to `eval.c`, checking cases to `check.c`, and parsing to `parse.c`. The `core/lang`
split lets experiments live in the surface language without touching the kernel.

Tractable experiments: graded/linear types (add a usage annotation to Π), modal type theory
(□/◇ comonadic modalities), effect systems (algebraic effects as W-type signatures), session types.

**Near-term steps:** pick one type former; follow the existing TM_FILL / TM_PRIMSUB / TM_GLUE pattern
as a template; add test cases alongside the implementation.

#### 3. Embedded language showcase

Use the surface language and module system to build shallow embeddings: a Hoare-logic layer for a small
imperative language, a session-typed π-calculus, a dependently-typed assembly. The `samples/stlc.lam`
file already demonstrates intrinsically-typed object languages with type soundness by construction.

**Near-term steps:** extend `stlc.lam` with references/state (Σ-type store); add a certified interpreter
for a small imperative language with an axiomatic semantics; write a tutorial notebook showing the embedding pattern step by step.



### Known limitations

- `transp` over non-closed families stays `VL_TRANSP` stuck (intentional).
- `infer ⟨i⟩ body` yields `Path` not `PathP`; use annotation for `PathP`.
- Termination checker accepts only `match`-arm binders as decreasing; `natrec`-step args and `pred` are rejected. Use `match … ih` sugar.
- `qeq` coherence stays stuck (correct for the semisimplicial model).
- HIT path ctor point-endpoints must be `VL_INDCON`; neutral approximation used otherwise.
- User-defined HITs are not universe-polymorphic (type params fixed at `Type_0`).
- EL-1 step 4 (threading `SrcLoc` through checker signatures) deferred: error messages show sub-term locations, not outer-expression locations.



### Test suite

Run `echo ":t" | core/lcore` to execute all 1261 tests. Test categories:

| Series | Count | What is tested |
|--------|-------|----------------|
| Basic reduction 1–14 | 14 | NbE correctness |
| Type formation T1–T9 | 9 | Universe, Π, Σ |
| Lambda η/β | 15 | Conversion |
| Id/J | 10 | Identity type |
| Nat/Bool eliminators | 20 | natrec, boolrec |
| Universe polymorphism M1-* | 21 | Level, lmax |
| Implicit arguments M2-* | 9 | Hole elaboration |
| Pattern matching PM-* | 18 | match + IH sugar |
| Termination TC-* | 17 | Structural check |
| Cubical L2-* | 70+ | Path, transp, comp, fill, Glue, funext, etc. |
| HITs HG-*, SU-*, HIT2-*, HIT3-* | 60+ | General HITs, 2-cells |
| Quotients | 12 | Quot, qin, quotrec |
| Modules QN-*, LW-*, MC-* | 20 | Qualified names, where, match resolution |
| Error rejection | 40+ | Type errors correctly diagnosed |




### Where does llang sit?

*Not a programming language.*

It produces no binary, has no IO, no effects, no compilation target. You cannot write a web server or a sorting
library you'd ship. Idris, F*, and ATS are all dependently-typed languages that still aim at programming as their
primary output. This kernel does not. The surface language in lang/ is a proof-and-normalisation environment, not a
compiler frontend.
 
*Not a production theorem prover.*

Coq, Lean 4, Agda, and Isabelle are the production systems. They have: a tactic language (hundreds of thousands of
lines), a curated standard library (millions of lines), universe cumulativity, unification heuristics, and years of
ergonomics work. This kernel has none of that. You cannot use it to certify a compiler or verify a cryptographic
protocol in any practical sense today--the ergonomics are too thin.
 
*What it actually is.*

The most precise positioning is: a research-complete, small-trusted-core implementation of CCHM Cubical Type Theory 
with 2-cell HITs, written in C.

Cubical Agda is the closest in terms of theory implemented. But Agda is written in itself (bootstrapped Haskell), has
a 200,000+ line trusted core by some counts, and its cubical extension is layered onto an older system not designed
for it from the ground up. This kernel implements the same CCHM theory from scratch, in a simpler, auditable way. The
core/ is roughly 5,000 lines of C with no external dependencies--loser to what the de Bruijn criterion actually
demands. 

cooltt and redtt (research systems from the CMU groups) are philosophically similar--small, correct-by-design,
focused on cubical computing. They implement Cartesian cubical type theory rather than CCHM, and neither has 2-cell
HITs. This kernel is closer to CCHM (the Agda/Voevodsky/Cohen/Coquand/Huber/Mörtberg family) and extends it further in
the HIT direction.
 
miniTT (Coquand, Kinoshita, Nordström, Takeyama, 2009) established the tradition of small reference implementations.
This kernel is what miniTT would look like after extending through cubical structure, Glue/univalence, HITs, 2-cells,
a surface language, and 1,261 tests.


__The specific claim it makes__

The unusual thing about this kernel is not what it covers, but the combination:
1. CCHM cubical (not just MLTT, not just HoTT-via-axiom--actual computing transport and composition)
2. 2-cell HITs (the torus, S², where the 2-cell eliminator type-checks and computes)
3. Written in C, ~5K lines trusted core (not bootstrapped, not Haskell, auditable)
4. Surface language and module system (not just a type-checking API)
5. 1,261 tests (not a prototype--a tested, stable system)

Very few systems have all five. Cubical Agda comes closest but fails on (3). cooltt has (3) but not (2) or (4). Most
research kernels stop at (1) and (3).


__The honest gap__

What it lacks, compared to production proof assistants, is:
- A tactic language. You write full proof terms by hand. At ~20 lines a proof is already painful. Coq's rewrite, simp,
  auto close this gap. Without tactics, only small-scale proofs are ergonomic.
- Universe cumulativity. Agda and Coq allow terms of Type_k to appear where Type_{k+1} is expected. This kernel
  requires explicit universe lifting.
- Large-library integration. There is no equivalent of Mathlib. The standard library in lang/lib/ covers Nat, Vec,
  Fin, and a handful of proofs.

These are not theoretical limits--they are engineering work. The kernel is the foundation on which any of the three
expansion directions (verification platform, type system lab, embedded language showcase) would be built. The theory
is done. The ergonomics are the remaining distance.


__The two liner answer__

It occupies the position of a reference-quality CCHM cubical kernel--more complete theoretically than any other
system of comparable size, less ergonomic than any production proof assistant, and more concrete than a pure research
paper. The right comparison is not Coq or Agda in their current form, but what Coq's kernel looked like in 1989, or
Agda's before the ecosystem grew around it: the essential computational core, proven correct, waiting for a language
to be built on top. God speed!

