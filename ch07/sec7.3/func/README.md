

## λ-Lisp: Recursive Interpretation & Homoiconicity

This implementation uses rather obsolete functional
programming constructions. But many of them are easy
to follow. It is a study in programming language theory
featuring a Python-based Lisp host and a meta-circular
Lisp-in-Lisp interpreter.

| Layer | Implementation | Description |
|-------|----------------|-------------|
| *Host* | `lisp.py` (Python) | Provides the runtime, memory management, and core primitives. |
| *Guest* | `mini-lisp.l` (Lisp) | A meta-circular evaluator defining Lisp within Lisp. |
| *Test* | `demo.py` (Python) | Orchestrates the two layers to demonstrate complex evaluations. |


### The Architecture of Reflection

The project demonstrates how a language can be defined using its own primitives,
a concept known as *Meta-Circular Evaluation*.

1. *Level 0 (The Metal):* Python's runtime environment.

2. *Level 1 (The Host - `lisp.py`):* An interpreter providing the foundational "physics" of Lisp:
   Lexical scoping, Tail Call Optimisation (TCO), and an environment for S-expressions.

3. *Level 2 (The Guest - `mini-lisp.l`):* A Lisp implementation that
   defines `eval` and `apply` using the Host’s primitives.
   This is where the true logic of Lisp lives.


### Functional Purity

* *Lexical Closures:* Functions "remember" the scope in which they were created.

* *Recursion Safety:* Includes recursion depth tracking to prevent host-level
  stack overflows during deep meta-evaluations.

* *Higher-Order Logic:* Full support for passing procedures as values.


### Functional Programming Concepts

This project is a sandbox for some pure functional paradigms:

#### 1. Lexical Closures & Higher-Order Logic

The Host implements *Lexical Scoping*. When a function is defined,
it doesn't just store code; it captures the current environment.

*Project Insight:* You can see this in action in `mini-lisp.l`,
where environments are passed as explicit association lists
`((var1 val1) (var2 val2))`.

#### 2. Tail Call Optimisation (TCO)

Functional languages rely on recursion rather than loops.
To prevent the Python stack from exploding, `lisp.py` utilizes
a *Trampoline* pattern (see low level constructs .. MISSING NOW ..).
This allows the Meta-Lisp layer to perform infinite recursion safely.

#### 3. Homoiconicity (Code as Data)

Lisp is *homoiconic*: its source code is structured as a
native data type (the List). This allows the `mini-eval`
function to treat a piece of code like a list that can be
mapped, filtered, or restructured before execution.
(On homoiconicity see [sec7.3.5](./../../sec7.3.5/)).


NOTE: For aspects on some more modern functional
language constructions implemented,
see [multi](./../multi/),
or [con](./../../../ch08/addition/category/lang/con/)
and [cool](./../../../ch08/addition/category/lang/cool/).

