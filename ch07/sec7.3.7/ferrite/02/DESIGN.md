

## Design of Programming Languages

### 1. The What

A programming language exists when there is a shared agreement on, what
1. .. programs look like
2. .. programs mean
3. .. programs are allowed to do
4. .. cannot go wrong when programs run

These correspond, respectively, to:
- syntax
- semantics
- static constraints
- soundness guarantees

A compiler or interpreter is not the language.
It is merely one realisation of the language.
In best case a reference implementation.


### 2. Syntax


#### 2.1 Concrete Syntax

Concrete syntax defines how programs are written.

Examples:
- keywords
- punctuation
- layout rules
- textual representation

Typically specified using:
- BNF or EBNF grammars
- lexer rules
- precedence tables

Concrete syntax answers:

Is this a well-formed program text?

It does not answer what the program does.



#### 2.2 Abstract Syntax

Abstract syntax removes irrelevant surface details.

For example:
- parentheses become tree structure
- precedence is implicit
- whitespace disappears

Usually represented as:
- abstract syntax trees (ASTs)
- algebraic data types

Abstract syntax answers:

What is the structural form of this program?



### 3. Static Semantics

Static semantics define constraints on programs
that can be checked without running them.

Examples:
- type systems
- scope rules
- ownership rules
- borrow rules
- name resolution

Static semantics are typically expressed as judgements:
```math
\Gamma \vdash e : \tau
```
They answer:

Is this program meaningful?

Static semantics are where language design choices live.



### 4. Dynamic Semantics: What Programs Do

Dynamic semantics define how programs execute.

There are three classical approaches.



#### 4.1 Operational Semantics

Defines execution as a step-by-step relation.

Example:
```math
\langle e, \sigma \rangle \rightarrow \langle e', \sigma' \rangle
```
Used when:
- building interpreters
- reasoning about execution order
- modelling resources (memory, ownership)

Ferrite uses operational semantics.



#### 4.2 Denotational Semantics

Maps programs to mathematical objects.

Example:
```math
\llbracket e \rrbracket : Env \rightarrow Value
```

Used when:
- reasoning about equivalence
- abstract interpretation
- compositional reasoning

Harder to use for low-level features.



#### 4.3 Axiomatic Semantics

Defines execution by logical assertions.

Example:
```math
\{P\}\ e\ \{Q\}
```

Used for:
- program verification
- reasoning about correctness
- Hoare logic



### 5. The Relationship Between Static and Dynamic Semantics

A well-designed language ensures:
- static semantics prevent bad dynamic behaviour
- dynamic semantics never encounter undefined states

This relationship is formalised through soundness theorems.




### 6. Type Soundness: The Central Proof

The classical result is due to Wright and Felleisen.

Type soundness consists of two theorems.


#### 6.1 Progress

A well-typed program does not get stuck.

Formally:
- either it is a value
- or it can take a step

This rules out runtime errors caused by ill-formed operations.


#### 6.2 Preservation

Evaluation preserves types.

Formally:
- stepping does not change the type of an expression

This ensures execution respects static reasoning.



#### 6.3 Consequence

Together, progress and preservation imply:

Well-typed programs do not go wrong.

This is the formal meaning of safety.



### 7. Proofs as Part of the Language

In modern language design:
- the proofs are part of the language definition
- they are not optional
- they guide implementation

A compiler that violates the proof assumptions is incorrect, not just buggy.



### 8. Refinement and Extension

Languages evolve by:
- extending syntax
- refining static semantics
- strengthening invariants
- re-proving soundness

Examples:
- adding borrowing
- adding effects
- adding concurrency

Each extension requires:
- new typing rules
- new operational rules
- updated proofs



### 9. From Specification to Implementation

The usual pipeline:
1. Formal specification
2. Reference semantics
3. Interpreter or type checker
4. Compiler backend
5. Optimisation (proved correct or restricted)

Good implementations follow the spec.
Bad ones redefine the language accidentally.



### 10. Why This Matters

Without formal semantics:
- compilers become the specification
- bugs become features
- reasoning becomes folklore

With formal semantics:
- languages become teachable
- implementations become replaceable
- correctness becomes meaningful



### 11. Ferrite in Context

What you have done with Ferrite is:
- defined a core language
- formalised ownership
- specified evaluation
- proved safety properties

This is language design, not tooling.

From here, Ferrite can grow deliberately, rather than accidentally.



### 12. How to Build Your First Language (Roadmap)

1. *Decide purpose* (scripting? systems? teaching? effects? safe memory?)
2. *Start extremely small* (arithmetic + variables + if is enough)
3. *Choose syntax* -> s-expressions are easiest for beginners
4. *Write a parser* -> build AST
5. *Write an interpreter* (big-step at first, then small-step)
6. *Add very simple static check* (even just "variables must be defined")
7. *Add types* -> prove progress & preservation (even on 3-4 pages)
8. *Iterate*: add one feature -> break & fix soundness

Popular first extensions:
- Functions + closures
- References + simple ownership (like Ferrite)
- Algebraic data types + pattern matching
- Effects/continuations


### 13. Why All This Formality?

Without formal rules:
- To repeat: The compiler *becomes* the language (C, early Rust, Zig pitfalls)
- Bugs become features
- You cannot teach it reliably (a sort of abstraction / generalisation fails)
- Multiple implementations diverge

With formal rules (even simple ones):
- You *understand* what you built
- You can *prove* safety properties
- You can grow the language *deliberately* (not accidentally)
- You join the tradition of serious language design

Ferrite is already an example:
*tiny core + ownership + proved safety properties -> the right starting point*.

