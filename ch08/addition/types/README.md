
## Type Systems - A Survey

A *type system* is a formal mechanism that assigns types to terms in a language
and uses them to rule out certain classes of program errors at compile time.
What counts as "a type" varies widely: a simple tag like `Int`, a logical
proposition, a resource budget, a protocol, or even a proof about program
behaviour.

This document surveys the main families of type systems, from the simply typed
lambda calculus through to homotopy type theory and linear logic. Each section
gives the core grammar or notation, key properties, and representative
languages or proof assistants.

A rough thread runs through all of them: the __Curry-Howard-Lambek
correspondence__, which equates types with propositions, programs with proofs,
and type-checking with proof verification. Different type systems correspond to
different logics--intuitionistic, second-order, linear, modal, homotopy--and
understanding that correspondence is often the fastest way to understand what a
new type system is really doing.


### 1. Basic Type Systems

These define the basic typed computation model.

#### 1.1 Simply Typed Lambda Calculus (STLC)

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



#### 1.2 Polymorphic Type Systems

Generalize functions across types.

##### System F (Parametric Polymorphism)

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



#### 1.3 Rank-N Polymorphism

Extends polymorphism to deeper positions.

Example:

```
f : (∀a. a → a) → Int
```

Used in:

```
Haskell
```



### 2. Subtyping Systems

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



### 3. Structural Type Extensions

These describe *data structure composition*.

#### 3.1 Product Types

```
T × U
```

Example:

```
(Int, Bool)
```



#### 3.2 Sum Types

```
T + U
```

Example:

```
Either Int String
```



#### 3.3 Recursive Types

Define self-referential structures.

Example:

```
List = μX. 1 + (Int × X)
```



#### 3.4 Algebraic Data Types (ADT)

Combines products and sums.

Example:

```
data Tree =
    Leaf
  | Node Tree Tree
```



### 4. Advanced Structural Systems

#### 4.1 Generalized Algebraic Data Types (GADTs)

Allow constructors to refine types.

Example:

```
data Expr a where
  IntLit  :: Int -> Expr Int
  BoolLit :: Bool -> Expr Bool
```

They allow *type-safe interpreters*.



#### 4.2 Existential Types

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



#### 4.3 Higher-Kinded Types

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



### 5. Intersection and Union Types

#### 5.1 Intersection Types

```
T ∧ U
```

Meaning:

```
value satisfies both types
```

Used for:

```
overloaded functions
refinement
```



#### 5.2 Union Types

```
T ∨ U
```

Meaning:

```
value may be either type
```

Used for:

```
nullable values
TypeScript discriminated unions
```



### 6. Dependent Type Systems

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



### 7. Refinement Type Systems

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



### 8. Linear and Resource Type Systems

Control *value usage*.

#### 8.1 Linear Types

```
use exactly once
```

Example:

```
file : File
```

must be consumed once.



#### 8.2 Affine Types

```
use at most once
```

Used in:

```
Rust ownership
```



#### 8.3 Relevant Types

```
use at least once
```



#### 8.4 Graded / Quantitative Types

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



### 9. Linear Logic

Logical foundation for *resource-sensitive* type systems (Girard, 1987).

Structural rules are restricted:

```
no unrestricted weakening
no unrestricted contraction
```

Connectives:

```
multiplicative:  A ⊗ B   (tensor — use both)
                 A ⅋ B   (par — use one in context of other)
                 1        (multiplicative unit)
                 ⊥        (multiplicative false)

additive:        A & B   (with — choose one)
                 A ⊕ B   (plus — provide one)
                 ⊤        (additive true)
                 0        (additive false)

exponentials:    !A       (of course — may be used freely)
                 ?A       (why not — may be discarded freely)
```

Implication (derived):

```
A ⊸ B  ≡  A⊥ ⅋ B    (linear implication)
```

The exponential `!` recovers classical structural rules:

```
!A ⊢ !A ⊗ !A   (contraction)
!A ⊢ 1          (weakening)
```

Correspondence with computation:

```
⊗   →   simultaneous resource consumption
&   →   external choice
⊕   →   internal choice
!   →   unrestricted reuse (ordinary function argument)
⊸   →   function consuming its argument exactly once
```

Connection to type systems:

```
linear types          ←→   multiplicative linear logic
session types         ←→   linear logic + π-calculus
Curry–Howard for LL   ←→   proof nets / sequent calculus
```



### 10. Effect Type Systems

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



### 11. Capability Type Systems

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



### 12. Session Types

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



### 13. Typestate Systems

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



### 14. Temporal and Modal Types

Track *time or modality*.

Modal operators:

```
□T   (necessarily T — always true)
◇T   (possibly T — eventually true)
○T   (next T — true at next time step)
```

Temporal operators model:

```
LTL  (linear temporal logic)
CTL  (computation tree logic)
```

Applications:

```
reactive systems
distributed protocols
stream processing
```

Connection to logic:

```
modal types  ←→  S4 / S5 modal logic
staged types ←→  S4 (code as □T)
```



### 15. Gradual Type Systems

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

Consistency relation replaces subtyping:

```
T ~ U
```

Languages:

```
TypeScript
Racket
Python typing
```



### 16. Row Polymorphism

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



### 17. Path-Dependent Types

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



### 18. Higher Type Theories

These extend dependent types with richer notions of equality.

#### 18.1 Homotopy Type Theory (HoTT)

Interprets types as *topological spaces* and equality as *paths*.

Core idea:

```
identity type  Id_A(x, y)
  ≡ space of paths from x to y in type A
```

Higher paths:

```
level 0  →  contractible types (propositions)
level 1  →  sets (proof-irrelevant equality)
level 2  →  groupoids
level n  →  n-groupoids
∞        →  ∞-groupoids
```

Univalence axiom (Voevodsky):

```
(A ≃ B) ≃ (A = B)
```

Meaning:

```
equivalent types are identical
isomorphism implies equality
```

Higher Inductive Types (HITs):

```
define types by generators and path constructors
example: circle S¹ has a point base and a path loop : base = base
```

Identity type rules:

```
refl  : Id(a, a)          (reflexivity)
J     : eliminator for paths
```

Consequences:

```
function extensionality
proof irrelevance for propositions
univalent foundations for mathematics
```

Used in:

```
Agda (HoTT library)
Coq (HoTT library)
```



#### 18.2 Cubical Type Theory

Provides a *computational* interpretation of the univalence axiom, avoiding it as a mere axiom.

Core idea:

```
paths are functions  I → A
  where I is an interval type [0,1]
```

Faces and boxes:

```
higher-dimensional cubes model higher equalities
```

Composition operation:

```
comp : fills open boxes (cubes with one face missing)
```

Key advantage over book HoTT:

```
univalence is provable, not postulated
all proofs compute
```

Used in:

```
Cubical Agda
Cubical TTT (Cartesian cubical type theory)
```



### 19. Behavioral and Protocol Types

These describe *system interactions*.

Examples:

```
session types
protocol types
actor types
behavioral contracts
```

Actor model typing:

```
Actor<S>  — actor that accepts messages of type S
```

Behavioral contracts specify:

```
liveness properties
safety properties
interaction patterns
```

Used in distributed systems.



### 20. Staged Type Systems

Support *multi-stage programming*.

Example:

```
code<T>
```

Meaning:

```
program fragment producing T
```

Staging levels:

```
⟨e⟩   (quote — defer evaluation)
~e    (splice — insert quoted code)
```

Connection to modal logic:

```
code<T>  ≃  □T  in S4 modal logic
```

Used for:

```
metaprogramming
code generation
partial evaluation
```

Languages:

```
MetaOCaml
```



### 21. Probabilistic Type Systems

Used in probabilistic programming.

Example types track:

```
distributions
random variables
```

Example:

```
sample : Distribution<T> → T
```

Inference preserves:

```
measurability
normalizability
```

Languages:

```
Hakaru
Church
```



### 22. Dimensions of Type System Design

Type systems usually vary along *these axes*.

#### Expressiveness

```
simple → dependent
```



#### Resource Tracking

```
unrestricted → affine → linear → quantitative
```



#### Effect Awareness

```
pure → effect typed
```



#### Behavioral Specification

```
data → protocols → temporal behavior
```



#### Logical Strength

```
propositional
higher-order
dependent
homotopy
```



### 23. Modern Research Combinations

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



### 24. A Rough "Expressiveness Ladder"

This is not strict but roughly shows increasing expressive power.

```
untyped lambda calculus
      |
simply typed lambda calculus
      |
polymorphic types (System F)
      |
subtyping systems
      |
GADTs
      |
effect systems
      |
linear / affine systems
      |
refinement types
      |
dependent types
      |
homotopy type theory
```



### 25. The Deep Theoretical Correspondence

Many type systems correspond to *logical systems*.

```
             STLC <--> intuitionistic logic          (Curry-Howard)
         System F <--> second-order logic
     Linear types <--> multiplicative linear logic   (Girard)
    Session types <--> linear logic + π-calculus
  Dependent types <--> higher-order logic            (Martin-Löf)
             HoTT <--> homotopy theory               (Voevodsky)
       Cubical TT <--> cubical sets                  (Cohen et al.)
      Modal types <--> S4/S5 modal logic
     Staged types <--> S4 (necessity as code)
```

This is part of the *Curry-Howard-Lambek correspondence*:

```
            types <-->  propositions
         programs <-->  proofs
       evaluation <-->  proof normalization
       categories <-->  type theories                (Lambek)
           spaces <-->  types                        (HoTT)
```
