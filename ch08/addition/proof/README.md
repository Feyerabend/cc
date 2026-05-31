
## A Proof Checker for Homotopy Type Theory, Written in C

This repository is a programming language laboratory for students studying
dependent type theory and Homotopy Type Theory ([HoTT](./../hott)).
It implements Martin-Löf Type Theory extended with HoTT features--identity types,
univalence, higher inductive types, universe polymorphism, and inductive
families - in around 4 000 lines of C source that you can read, run, and
extend.

The central idea: a term `t : A` is simultaneously a *program* of type `A`,
a *proof* that `A` is inhabited, and a *computation* that the evaluator can
normalise. The type checker is the proof checker. The normaliser is the
operational semantics. These are not analogies--they are the same object
seen from different angles.

The concrete goal of the repository is to write the type soundness proof for
a small typed language *inside the system itself*, as an inhabitant of a
dependent type. Getting there requires indexed inductive families, universe
polymorphism, and implicit arguments--all of which are present.



### Repository layout

```
code/
  core/                   The mathematical kernel: parser, bidirectional type checker,
                          NbE evaluator, elaborator. REPL: lcore.
  lang/                   A call-by-need graph reducer using the same surface syntax
                          and type checker. REPL: llang.
docs/
  01.md                   Orientation: what the system is, how to build it, a quick tour
  02.md                   First read: tracing one expression end to end through the code
  03.md                   Terms and Values: the two-representation design and why it works
  04.md                   Normalisation by Evaluation: eval, quote, eliminators, neutrals
  exercises/
    01_add_lmax.md        Medium exercise: add lmax (maximum of two levels)
    02_quotient_types.md  Large exercise: add quotient types as a HIT
```

Start with [docs/01.md](docs/01.md).



### Building and running

```
cd code/core && make
./lcore
```

The REPL accepts one expression per line:

```
> succ (succ zero)
  normal : succ (succ zero)
> :type Π(A : Type). A → A
  type : Type_1
> :let id : Π(A : Type). A → A = \A x. x
> :type id _ zero
  type : Nat
```

Commands: `:type e` infers and prints the type of `e`. `:conv a b` tests
definitional equality. `:let name : type = term` adds a global definition.

For the graph-reducer layer:

```
cd code/lang && make && ./llang
:load "lib/prelude.lam"
```



### What the system demonstrates

*Types as propositions, terms as proofs.* The same syntax that writes
`plus : Nat → Nat → Nat` also writes `plus_comm : Π(m n : Nat). Id Nat (plus m n) (plus n m)`.
They are checked by the same checker and run by the same evaluator.
`plus_comm 2 3` reduces to `refl 5` - a concrete witness that both sides
compute to the same number.

*Length-indexed vectors.* `head` on an empty vector is a type error, not
a runtime crash. The length is part of the type; the type checker enforces
bounds statically.

```
data Vec (A : Type) : Nat → Type where
  vnil  : Vec A zero
  vcons : Π(n : Nat). A → Vec A n → Vec A (succ n)
```

*Proofs that compute.* Identity type proofs are programs. Run them and they
reduce. `plus_comm (succ (succ zero)) (succ (succ (succ zero)))` normalises
to `refl (succ (succ (succ (succ (succ zero)))))`.

*Universe polymorphism.* Definitions can be quantified over universe
levels so they work at `Type_0`, `Type_1`, or any `Type_ℓ`:

```
:let id : Π(ℓ : Level). Π(A : Type_ℓ). A → A = \ℓ A x. x
id _ Nat zero       -- level inferred as 0
id _ Type Nat       -- level inferred as 1
```

*Implicit arguments.* Underscores `_` are holes the elaborator fills by
unification:

```
id _ zero    -- A inferred as Nat
id _ true    -- A inferred as Bool
```



### How to read the code

The code is structured so that every type-theoretic concept maps to a
specific piece of C. There are no magic numbers, no hidden invariants that
require external documentation. Read the source files in this order:

1. `code/core/term.h` - All `TM_` and `VL_` tags. Skim once, return as reference.
2. `code/core/eval.c` - `nbe_eval`, `nbe_vapp`, the eliminators.
3. `code/core/check.c` - `infer`, `check`, `conv`.
4. `code/core/parse.c` - `parse_term`, `parse_atom`, de Bruijn conversion.
5. `code/core/elab.c` - Hole filling. Only relevant when you write `_`.

The standard library in [code/lang/lib/](./code/lang/lib) shows the system
in use: programs and proofs written in the same language, running through
the same machinery. [code/lang/lib/README.md](./code/lang/lib/README.md)
is a detailed walkthrough of everything in the library.



### The standard library

`code/lang/lib/` contains:

| File          | Contents                                                         |
|---------------|------------------------------------------------------------------|
| `nat.lam`     | `Nat`, `plus`, `mult`, `pred`, `iszero`                          |
| `vec.lam`     | `Vec`, `vlength`, `vmap`, `vconcat`, `head`                      |
| `fin.lam`     | `Fin`, `toNat`, `finWeaken` - bounded natural numbers            |
| `proofs.lam`  | `plus_zero_l`, `plus_zero_r`, `plus_succ_r`, `plus_comm`         |
| `prelude.lam` | Entry point - imports all of the above                           |



### Exercises

The [docs/exercises/](./docs/exercises/) folder contains
guided extensions to the system:

- *Add `lmax`* (`01_add_lmax.md`): Implement the maximum of two universe
  levels. Medium difficulty, around 80 lines across 5 files. Covers the full
  pipeline: parsing, evaluation, type checking, quoting, and conversion.

- *Quotient types* (`02_quotient_types.md`): Add `A / R` as a higher
  inductive type. Large exercise, around 300 lines. Covers path constructors,
  the coherence condition in the eliminator, and the connection between
  quotients and the univalence axiom.
