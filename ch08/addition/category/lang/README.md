
## Category Theory in Programming Languages

This directory collects a series of experiments applying category theory
to different programming language paradigms, styles, and use cases. Each
subdirectory is self-contained and can be explored independently.


### Overview

| Folder   | Language / Style     | Main Focus                                              |
|----------|----------------------|---------------------------------------------------------|
| `algol/` | C                    | Categorical objects, morphisms, and functors in C       |
| `cool/`  | Python (OOP → FP)    | Progressive COOL language: generics, monads, free monads|
| `cql/`   | Python (relational)  | Categorical Query Language — queries as functors        |
| `lisp/`  | Python (LISP)        | Categorical LISP interpreter with monadic evaluation    |
| `con/`   | Python (concurrent)  | Category theory applied to concurrency and async code   |


### Algol — Categorical Programming in C

[`algol/`](./algol/) implements category theory concepts directly in C:
objects as tagged types, morphisms as typed function descriptors,
composition, and functors. The goal is to show that categorical thinking
applies even at the systems level.


### COOL — Categorical Object-Oriented Language

[`cool/`](./cool/) is a progressive series of Python interpreters, each
adding a new categorical concept on top of the previous one:

- `01/` — Core OOP with subtyping as morphisms (`cat_cool.py`)
- `02/` — Generics as endofunctors + parser combinators (`cat_gen.py`, `cat_parse.py`)
- `02a/` — Generics extended with monoids (`cat_gen2.py`)
- `03/` — Algebraic data types as products and coproducts (`cat_adt.py`)
- `04/` — Monadic effects: Maybe, Either, State, IO, Reader (`cat_monad.py`)
- `05/` — Applicative functors for independent effects (`cat_applicative.py`)
- `06/` — Free monads, effect DSLs, and multiple interpreters (`cat_free.py`)


### CQL — Categorical Query Language

[`cql/`](./cql/) implements a relational query engine in Python where
queries are modelled as functors. Joins are pullbacks, unions are
coproducts, and aggregations are natural transformations — directly
mirroring categorical database theory (Spivak, Rosebrugh, et al.).


### LISP — Categorical LISP

[`lisp/`](./lisp/) is a small LISP interpreter in Python. Evaluation
uses an explicit `EvalMonad` for error handling, closures model
exponential objects in cartesian closed categories, and S-expressions
align naturally with morphism composition.


### Con — Concurrency

[`con/`](./con/) is a five-part series showing how categorical abstractions
structure concurrent Python programs:

- `01/` — Functors for independent async transformations
- `02/` — Natural transformations for switching execution strategies
- `03/` — Applicative functors for parallel composition
- `04/` — Monads for dependent sequential concurrency
- `05/` — Free monads decoupling program description from execution

