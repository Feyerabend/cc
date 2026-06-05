
## Theory of Virtual Machines

A formal theory of virtual machines expressed as a LaTeX document
(`theory_of_virtual_machines.tex`) together with executable code
illustrations in `code/`.


### The underlying intellectual pattern

#### The abstract-algebra formula

The deepest structural pattern in this project is one that runs across
pure mathematics, logic, philosophy, and theoretical computer science.
It can be stated as a two-part schema:

> *Signature + Axioms -> Models*

In abstract algebra this is entirely concrete.  Fix a *signature*:
symbols for operations and their arities (say, one binary operation `·`
and one constant `e`).  Write down *axioms* over that signature
(associativity, left/right identity).  Every mathematical structure that
satisfies those axioms is a *model*--a monoid.  The signature and
axioms together do not pick out one object; they pick out a whole
*class* of objects, related by the property of satisfying the same
sentences.

This is not an isolated trick.  The same move appears in:

| Domain          | Signature                   | Axioms                            | Models                        |
|-----------------|-----------------------------|-----------------------------------|-------------------------------|
| Group theory    | `·, e, (·)⁻¹`               | associativity, identity, inverses | all groups                    |
| Ring theory     | `+, ·, 0, 1`                | ring axioms                       | ℤ, ℚ, polynomial rings, ..    |
| Boolean algebra | `∧, ∨, ¬, ⊤, ⊥`            | de Morgan, distribution           | powersets, truth-values       |
| Lattice theory  | `∧, ∨`                      | order axioms                      | partial orders, topologie     |
| Category theory | objects, morphisms, `∘, id` | associativity, unit laws          | Set, Grp, Top, ..             |

#### Historical roots

The idea of studying *classes of structures* rather than particular
structures goes back to:

*Dedekind and Hilbert (1880s-1900s).*  Hilbert's axiomatic programme
formalised arithmetic and geometry not as properties of specific objects
but as consequences of axioms.  His model-theoretic insight was that the
*same* axioms can be satisfied by many different structures.

*Tarski (1930s-1950s).*  Alfred Tarski gave the formal definition of
*truth in a structure* (a model) and developed model theory as a
mathematical discipline.  His completeness and compactness theorems
showed the deep relationship between syntactic provability and semantic
satisfiability.

*Birkhoff (1935).*  Garrett Birkhoff's HSP theorem showed that the
class of algebras satisfying a set of equational axioms is exactly the
class closed under homomorphisms, subalgebras, and products--giving a
purely algebraic characterisation of "what an axiom system picks out."

*Lawvere (1963).*  William Lawvere's categorical logic reformulated
the pattern once more: a *theory* (in the categorical sense) is a
category with certain structure; its *models* are structure-preserving
functors into *Set*.  This unified logic, algebra, and type theory in
a single framework.

#### The semantic view of theories

In the philosophy of science, the closest source to my knowledge,
Patrick Suppes argued in the 1960s that scientific theories
are best understood not as sets of sentences (the "syntactic view")
but as *classes of models*--the structures that make the theory's
claims true.  On this *semantic view*, to present a theory
is to present a class of models, not a derivation system.

The Balzer-Moulines-Sneed (BMS) *structuralist* programme in the 1980s
applied this to physics: a physical theory specifies intended
applications by picking out a class of models of a formal structure.
Newtonian mechanics, for example, defines the class of tuples
`(T, S, m, f)`--time, space, mass-function, force-function--satisfying
Newton's laws.  Any physical situation that fits that structure is a
model of the theory.



### How this theory fits the pattern

`theory_of_virtual_machines.tex` applies precisely the same schema to
virtual machines and abstract computation.

#### Signature

The document fixes a *formal language* (inductive syntax, §2) and a
collection of structural components:

- *States*--configurations of abstract machines
- *Transition relations*--one-step reduction `->`
- *Semantic maps*--denotations ⟦·⟧, cost functions κ, simulation
  relations R
- *Composition operators*--layer stacks, compiler composition,
  bisimulation up to context

#### Axioms (definitions and theorems)

Rather than equational axioms, the "axioms" here are *definitions*:

- A *transition system* is a pair (S, ->) (§4)
- A *simulation relation* is a relation R ⊆ S_source × S_target
  satisfying the diagram condition of Theorem 9.3 (§10.2–10.3)
- A *cost model* is a monoid-valued weight function κ : Instr -> M
  (§12.1–12.2)
- A *non-interference property* is the statement
  `low(s) = low(s')  ⟹  low(step(s)) = low(step(s'))` (§11.2)

These definitions play the role of axioms: they constrain which
structures count as models.

#### Models

The models are concrete machines:

| Abstract structure                | Concrete models in this document                 |
|-----------------------------------|--------------------------------------------------|
| Call-by-name evaluator            | Krivine machine (§6.3)                           |
| Call-by-value evaluator           | CEK machine (§6.2)                               |
| Higher-order functional evaluator | SECD machine (§6.1)                              |
| Logic programming evaluator       | Warren Abstract Machine (code/wam)               |
| Hardware virtualisation           | Popek–Goldberg formalisation (§7)                |
| JVM bytecode execution            | JVM interpreter (code/jvm)                       |
| Compiler correctness              | CompCert-style simulation (§10, code/simulation) |

Each machine is a *model* of the general abstract machine theory:
it provides concrete carrier sets and operations that satisfy the
general definitions.

#### Revision and expansion

This is one of the key properties of the abstract-algebra/model-theory
pattern: the theory can be *extended* without breaking existing models.

- Add a new cost monoid (§12): existing machines become models of the
  cost-annotated theory too, by choosing κ = 0.
- Extend the language with concurrency (§17): sequential machines remain
  models by embedding them as single-thread systems.
- Add separation logic (§11.4): the heap isolation property is an
  additional axiom; machines without heap simply satisfy it vacuously.

This modularity is not an accident.  It follows directly from the
model-theoretic structure: new axioms *refine* the class of models
(fewer structures satisfy more axioms), but they never break the old
ones unless they are contradictory.



### Project layout

```
theory_of_virtual_machines.tex   Main LaTeX document (~1400 lines, 17 sections)
refs.bib                         BibTeX bibliography
code/
  secd/       SECD machine (call-by-value, higher-order)      §6.1
  cek/        CEK machine (continuations, call-by-value)      §6.2
  krivine/    Krivine machine (call-by-name, thunks)          §6.3
  simulation/ Simulation witness: source ↔ stack machine      §10.2–10.3
  cost/       Cost monoids, budget enforcement                §12
  hoare/      Hoare logic examples (C and Python)             §3.3, §11.4, §17
  wam/        Warren Abstract Machine (Prolog, backtracking)  §6
  jvm/        JVM bytecode interpreter (pure Python)          §14
```

#### Building the document

```bash
tectonic theory_of_virtual_machines.tex
```

Tectonic is a self-contained LaTeX engine (no separate TeX installation
needed).  Install with `brew install tectonic`.  BibTeX runs
automatically on first pass; re-run once to resolve citations.

#### Running the code examples

Each subdirectory is a standalone Python module (Python 3.10+):

```bash
python code/secd/secd.py          ## SECD: function application, lists
python code/krivine/krivine.py    ## Krivine: call-by-name, Ω, thunks
python code/simulation/simulation.py  ## Simulation: source/target lockstep
python code/cost/cost.py          ## Cost monoids, budget exceeded
python code/wam/wam.py            ## WAM: Prolog ancestor search
```

The JVM interpreter can run compiled `.class` files (pass the class name
without `.class`):

```bash
cd code/jvm
javac Example.java          ## requires OpenJDK: brew install openjdk
python main.py Example .
```

The Hoare logic C examples compile and run standalone:

```bash
cd code/hoare/c
make                        ## or: gcc -Wall -std=c11 -o linked_list linked_list.c
./linked_list
./concurrency               ## requires pthreads (macOS: included)
```



### On the theory as an open project

The document is deliberately structured to be *revisable and expandable*:

1. *Revisable*--The choice of abstract machine, cost model, or
   non-interference criterion can be changed without touching other
   sections.  This mirrors how a mathematician can change the axioms of
   a group to get a monoid or a ring.

2. *Expandable*--New sections can be added by defining new operations
   on the existing abstract structures.  The bisimulation-up-to-context
   section (§13), for example, extends the simulation theory with a
   proof technique; it does not break §10.

3. *Multiply instantiable*--The same abstract theory is instantiated
   in many concrete machines.  This is the defining feature of the
   model-theoretic approach: one theory, many models.

The analogy to philosophy of science is direct.  Just as Newtonian
mechanics defines a class of physical models (any system of bodies with
forces satisfying Newton's laws), this theory defines a class of
computational models (any transition system with a simulation relation
satisfying the compiler-correctness conditions).  What changes between
applications is the carrier set and the concrete transition function —
not the axioms.



### Key references

- Landin, P. (1964). The Mechanical Evaluation of Expressions. *Computer Journal* 6(4).
- Felleisen & Friedman (1986). Control Operators, the SECD-Machine, and the λ-Calculus.
- Popek & Goldberg (1974). Formal Requirements for Virtualizable Third Generation Architectures. *CACM* 17(7).
- Leroy, X. (2009). Formal Verification of a Realistic Compiler. *CACM* 52(7).
- Reynolds, J. (2002). Separation Logic. *LICS 2002*.
- Hoare, C.A.R. (1969). An Axiomatic Basis for Computer Programming. *CACM* 12(10).
- Danvy, O. (2004). A Rational Deconstruction of Landin's SECD Machine. *IFL 2004*.

Full bibliography in `refs.bib`.
