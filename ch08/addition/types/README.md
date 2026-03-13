
## 1. Basic Type Systems

These define the basic typed computation model.

### 1.1 Simply Typed Lambda Calculus (STLC)

Foundation of most typed languages.

Types:

```
T ::= Bool | Int | T → T
```

Judgment:

```
Γ ⊢ e : T
```

Properties:

```
progress
preservation
strong normalization
```

Logical interpretation:

```
intuitionistic propositional logic
```



### 1.2 Polymorphic Type Systems

Generalize functions across types.

#### System F (Parametric Polymorphism)

Types:

```
∀α. T
```

Example:

```
id : ∀α. α → α
```

Properties:

```
uniform behavior across types
```

Also called:

```
second-order lambda calculus
```



### 1.3 Rank-N Polymorphism

Extends polymorphism to deeper positions.

Example:

```
f : (∀a. a → a) → Int
```

Used in:

```
Haskell
```



## 2. Subtyping Systems

Introduce *type hierarchies*.

Subtyping rule:

```
S <: T
```

Meaning:

```
S can be used wherever T is expected
```

Key mechanisms:

```
covariance
contravariance
invariance
```

Variants include:

```
structural subtyping
nominal subtyping
bounded quantification
```

Example system:

```
System F<
```



## 3. Structural Type Extensions

These describe *data structure composition*.

### 3.1 Product Types

```
T × U
```

Example:

```
(Int, Bool)
```



### 3.2 Sum Types

```
T + U
```

Example:

```
Either Int String
```



### 3.3 Recursive Types

Define self-referential structures.

Example:

```
List = μX. 1 + (Int × X)
```



### 3.4 Algebraic Data Types (ADT)

Combines products and sums.

Example:

```
data Tree =
    Leaf
  | Node Tree Tree
```



## 4. Advanced Structural Systems

### 4.1 Generalized Algebraic Data Types (GADTs)

Allow constructors to refine types.

Example:

```
data Expr a where
  IntLit  :: Int -> Expr Int
  BoolLit :: Bool -> Expr Bool
```

They allow *type-safe interpreters*.



### 4.2 Existential Types

Hide type information.

Example:

```
∃α. T
```

Use case:

```
abstract data types
modules
```



### 4.3 Higher-Kinded Types

Types parameterized over *type constructors*.

Example:

```
Functor f
```

where

```
f : * → *
```

Common in:

```
Haskell
Scala
```



## 5. Intersection and Union Types

### Intersection Types

```
T ∧ U
```

Meaning:

```
value satisfies both types
```



### Union Types

```
T ∨ U
```

Meaning:

```
value may be either type
```



## 6. Dependent Type Systems

Types may depend on *values*.

Example:

```
Vector(n)
```

Function example:

```
append :
Vector(n) →
Vector(m) →
Vector(n + m)
```

Features:

```
proof-carrying programs
theorem proving
program verification
```

Used in:

```
Agda
Idris
Coq
Lean
```



## 7. Refinement Type Systems

Attach predicates to types.

Example:

```
{x : Int | x > 0}
```

Meaning:

```
x is an integer greater than zero
```

Verification uses:

```
SMT solvers
```

Languages:

```
Liquid Haskell
F*
Dafny
```



## 8. Linear and Resource Type Systems

Control *value usage*.

### Linear Types

```
use exactly once
```

Example:

```
file : File
```

must be consumed once.



### Affine Types

```
use at most once
```

Used in:

```
Rust ownership
```



### Relevant Types

```
use at least once
```



### Graded / Quantitative Types

Track *how many times* something is used.

Example:

```
x : A [k]
```

meaning

```
x used k times
```

Used in:

```
quantitative type theory
```



## 9. Effect Type Systems

Track *side effects* in types.

Example:

```
readFile : File → IO String
```

Effect systems track:

```
IO
state
exceptions
nondeterminism
concurrency
```

Variants:

```
effect rows
algebraic effects
handlers
```

Languages:

```
Koka
Eff
Haskell
```



## 10. Capability Type Systems

Types encode *permissions*.

Example:

```
File<read>
File<write>
```

Used to enforce:

```
security
access control
resource ownership
```

Used in:

```
Pony
Capsicum
```



## 11. Session Types

Describe *communication protocols*.

Example protocol:

```
!Int.?Bool.end
```

Meaning:

```
send Int
receive Bool
terminate
```

Guarantees:

```
protocol safety
deadlock freedom
```

Derived from:

```
π-calculus
linear logic
```



## 12. Typestate Systems

Types represent *program state transitions*.

Example:

```
File<Closed>
File<Open>
```

Functions:

```
open  : File<Closed> → File<Open>
close : File<Open> → File<Closed>
```

Ensures correct usage of resources.



## 13. Temporal and Modal Types

Track *time or modality*.

Example:

```
□T
◇T
```

Meaning:

```
always true
eventually true
```

Applications:

```
reactive systems
distributed protocols
```



## 14. Gradual Type Systems

Combine static and dynamic typing.

Unknown type:

```
?
```

Example:

```
x : ?
```

Runtime checks enforce safety.

Languages:

```
TypeScript
Racket
Python typing
```



## 15. Row Polymorphism

Used for *extensible records and variants*.

Example:

```
{ name : String | r }
```

Meaning:

```
record with field name plus other fields
```

Languages:

```
PureScript
OCaml variants
Elm
```



## 16. Path-Dependent Types

Types depend on *object paths*.

Example:

```
x.A
```

Used heavily in:

```
Scala
DOT calculus
```



## 17. Higher Type Theories

These extend dependent types.

### Homotopy Type Theory

Adds topology-inspired equality.

Concepts:

```
identity types
paths
univalence
```



### Cubical Type Theory

Provides computational interpretation of equality.

Used in:

```
Cubical Agda
```



## 18. Behavioral and Protocol Types

These describe *system interactions*.

Examples:

```
session types
protocol types
actor types
behavioral contracts
```

Used in distributed systems.



## 19. Staged Type Systems

Support *multi-stage programming*.

Example:

```
code<T>
```

Meaning:

```
program fragment producing T
```

Used for:

```
metaprogramming
code generation
```

Languages:

```
MetaOCaml
```



## 20. Probabilistic Type Systems

Used in probabilistic programming.

Example types track:

```
distributions
random variables
```

Languages:

```
Hakaru
Church
```



## 21. Dimensions of Type System Design

Type systems usually vary along *these axes*.

### Expressiveness

```
simple → dependent
```



### Resource Tracking

```
unrestricted → affine → linear → quantitative
```



### Effect Awareness

```
pure → effect typed
```



### Behavioral Specification

```
data → protocols → temporal behavior
```



### Logical Strength

```
propositional
higher-order
dependent
homotopy
```



## 22. Modern Research Combinations

Many research systems combine multiple ideas.

Examples:

```
linear dependent types
session dependent types
effect polymorphism
graded modal types
quantitative dependent types
```

Example research systems:

```
Granule
F*
Idris
Koka
```



## 23. A Rough "Expressiveness Ladder"

This is not strict but roughly shows increasing expressive power.

```
untyped lambda calculus
      │
simply typed lambda calculus
      │
polymorphic types (System F)
      │
subtyping systems
      │
GADTs
      │
effect systems
      │
linear / affine systems
      │
refinement types
      │
dependent types
      │
homotopy type theory
```



## 24. The Deep Theoretical Correspondence

Many type systems correspond to *logical systems*.

```
STLC              <--> intuitionistic logic
System F          <--> second-order logic
Linear types      <--> linear logic
Dependent types   <--> higher-order logic
Session types     <--> linear logic + π-calculus
HoTT              <--> homotopy theory
```

This is part of the *Curry–Howard–Lambek correspondence*.




