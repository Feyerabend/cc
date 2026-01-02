
## A COOL Compiler: Free-Monad–Based Compiler Skeleton

This repository is *not a language implementation* and not even *a finished compiler*.
It is vhat could be called a *semantic skeleton*: a rigorously separated pipeline that
starts with *meaning-free program descriptions* and ends with *target-agnostic code generation*.

The core idea is simple but non-negotiable:
> Programs are data. Meaning is supplied later.

Everything in this repository follows from that premise.

If you want to proceed as a project, you might have to defer your instincts on
buolding a compiler too soon. This will become clearer in the below.


### 1. Motif and Design Intent

This project explores a compiler architecture based on *Free Monads* and
*algebraic interpretation*, with the explicit goal of:
- separating *description* from *execution*
- separating *program structure* from *target semantics*
- enabling multiple interpretations, including compilation
- making optimisation and analysis first-class

This is *not* about functional programming aesthetics.
It is about *semantic control*.

If you are used to:
- interpreters that execute immediately
- compilers that traverse ASTs directly to text
- languages where effects are intrinsic

then this design deliberately does *not* do that.


### 2. Conceptual Overview

The system is structured into *three semantic layers*:

```
Free Monad Program -> Linear Intermediate Representation (IR) -> Code Algebra (target semantics)
```

Each layer is:
- pure
- inspectable
- independently testable
- replaceable without affecting the others

This is not accidental. It is the central invariant.


### 3. The Free Monad Layer (existing Code in above folder)

The Free monad layer defines:
- DSL operations as *functors*
- programs as *pure trees*
- sequencing via `bind`
- no execution, no side effects

A program at this level:
- does not run
- does not allocate
- does not print
- does not "mean" anything yet

It is a *symbolic description of intent*.

This layer is intentionally unaware of e.g.:
- C
- LLVM
- runtime models
- memory layouts
- optimisation strategies

That ignorance is a feature.



### 4. The IR Layer (Step 1)

#### Purpose

The IR exists to answer one question:
*In what order do effects occur?*

It deliberately ignores:
- values
- types
- runtime representation

The IR is *linear*, explicit, and "boring".
That is correct.


#### Files


__`ir.py`__

Defines the IR data structures:
- `IRInstr`: one effectful step
- `IRProgram`: a list of steps
No semantics. No logic.


__`ir_lowering.py`__

Defines the lowering pass:
```
Free -> IRProgram
```
This pass:
- is structural, not interpretive
- follows continuations via `run_step`
- preserves order exactly
- introduces no new meaning

This is the point where nested trees become a flat program.
If something breaks later, this is the first place to look.



### 5. The Code Algebra Layer (Step 2)

#### Purpose

A *code algebra* answers a different question:

> *What does this sequence of operations mean in a given target world?*

This is where:
- C
- LLVM
- WASM
- analysis traces
- optimisers

will eventually live.

Crucially, this layer does *not* see `Free` at all.
It only sees IR.


#### Files

__`codegen_core.py`__

Defines the abstract interface:
- `begin()`
- `emit(IRInstr)`
- `end()`

This is an *algebra*, not a printer.
If you are tempted to add string concatenation here, please stop and wait.


__`codegen_state.py`__

Defines a generic `CodeState`.
This is intentionally under-specified.

It exists to:
- accumulate structure
- delay textual commitment
- support multiple backends

Think of it as a *semantic buffer*, not output.


__`trace_algebra.py`__

This is the *correctness oracle*.

The `TraceAlgebra`:
- emits no code
- performs no effects
- records only *what happened*

It exists solely to prove:
- IR lowering is correct
- sequencing is preserved
- no instructions are lost
- no interpretation leaked in

If this algebra breaks, everything breaks.



__`codegen_driver.py`__

The simplest possible driver:
```
IRProgram -> CodeAlgebra -> CodeState
```
* No branching.
* No logic.
* No "cleverness".

This file should remain as "boring" as it can be, forever.



### 6. Testing and Correctness

__`test_pipeline.py`__
This is not a unit test.
It is a *semantic sanity check*.

It proves that:
1. A Free program lowers to the correct number of IR instructions
2. The IR preserves order
3. The algebra sees exactly what it should
4. No side effects occur during compilation

This is the compiler equivalent of checking that:
- parsing preserves structure
- evaluation order is stable

If this test fails, do *not* proceed, until debugging and checking all things.


### 7. Makefile

The `Makefile` exists to enforce discipline:
- all files present
- pipeline runnable
- no hidden dependencies

Running `make` must always mean: "The compiler pipeline is structurally sound."
Nothing more. Really.


### 8. What This Is Not

This repository is not:
- an interpreter
- a language runtime
- a complete compiler
- a teaching exercise
- an optimisation framework (yet)

Trying to turn it into any of those prematurely will break its core idea.


### 9. How to Proceed (In Order)

If you want to continue without collapsing the architecture,
the next steps should be taken in this order:

1. Enrich the IR
- introduce temporaries
- make value flow explicit
- still no target assumptions

2. Add control flow
- labels
- conditional jumps
- loops as structure, not syntax

3. Define a runtime contract
- how Value lowers
- ownership model
- memory representation

4. Add a real backend
- C algebra
- LLVM algebra
- or both

Skipping steps will force target assumptions too early.



### 10. Mental Model to Keep

If you keep only one invariant in mind, keep this one:

* Free describes what happens.
* IR describes when it happens.
* Algebra decides what it means.

As long as those three remain separate, the system stays honest.
Once they collapse, it becomes just another code generator.



### 11. Closing Note

This project is intentionally quiet.

* There are no clever tricks.
* No metaprogramming.
* No magic decorators.

What it offers instead is semantic leverage.

If you respect that, it will scale naturally into:
- a compiler
- an analyser
- a transformer
- or all three at once.

If not, it will fight you.
That is by design.
Good Luck!

