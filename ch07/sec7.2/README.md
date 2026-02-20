
## Type Systems

Type systems emerged from the intersection of mathematical logic
and the theory of computation. Early influences include the work
of *Bertrand Russell* on logical paradoxes and *Alonzo Church*'s
typed lambda calculus (1940s), which introduced types as a way to
prevent nonsensical expressions. Later, *Haskell Curry* and others
formalised connections between logic and computation, culminating
in the *Curry–Howard correspondence*, where types are viewed as
logical propositions and programs as proofs.

In programming languages, type systems became practically important
with languages like *Algol*, *ML*, and *Haskell*, where static
typing was used to improve safety and reasoning about programs.
Modern languages now span a wide spectrum, from dynamically typed
(*Python*, *JavaScript*) to richly statically typed (*Rust*,
*Haskell*, *Scala*).

Type systems are not just about safety; they influence program design,
optimisation, and documentation. Advanced type systems can express
invariants, encode protocols, and even reason about effects like
state or exceptions.


### Formal Introduction

A *type system* classifies program expressions according to the kinds of values they compute,
ensuring certain correctness properties. Typing judgments are written as:

```math
\Gamma \vdash e : \tau
```

where:
- $\Gamma$ is the typing context (variables and their types)
- $e$ is an expression
- $\tau$ is the type
- $\Gamma \vdash e : \tau$ reads: "under context $\Gamma$, expression $e$ has type $\tau$"


#### Example: Variable Typing

```math
\frac{x:\tau \in \Gamma}{\Gamma \vdash x : \tau} \quad (\text{Var})
```

If a variable $x$ has type $\tau$ in the context, it is assigned type $\tau$.



#### Example: Addition

```math
\frac{\Gamma \vdash e_1 : \text{Int} \quad \Gamma \vdash e_2 : \text{Int}}{\Gamma \vdash e_1 + e_2 : \text{Int}} \quad (\text{Add})
```

If $e_1$ and $e_2$ are integers, then $e_1 + e_2$ is also an integer.



#### Simply-Typed Lambda Calculus

*Abstraction:*

```math
\frac{\Gamma, x:\tau_1 \vdash e : \tau_2}{\Gamma \vdash (\lambda x.e) : \tau_1 \to \tau_2} \quad (\text{Abs})
```

*Application:*

```math
\frac{\Gamma \vdash e_1 : \tau_1 \to \tau_2 \quad \Gamma \vdash e_2 : \tau_1}{\Gamma \vdash e_1 \, e_2 : \tau_2} \quad (\text{App})
```

These formal rules allow reasoning about programs rigorously
and form the foundation for modern type theory.  


### Type System Dimensions

Type systems can be categorised along several axes:

1. *Static vs Dynamic Typing*
   * *Static typing* checks types at compile time,
     enabling early error detection and optimisation.
   * *Dynamic typing* defers checks until runtime,
     allowing more flexibility but potentially runtime errors.

2. *Strong vs Weak Typing*
   * *Strongly typed* languages prevent implicit type coercions
     that can lead to unexpected behaviour.
   * *Weakly typed* languages allow more implicit conversions,
     trading safety for convenience.

3. *Nominal vs Structural Typing*
   * *Nominal typing* requires explicit type declarations and
     matches by name (*Java*, *C#*).
   * *Structural typing* matches by the shape or structure of
     data (*TypeScript*, *OCaml*).

4. *Polymorphism*
   * *Parametric polymorphism* lets functions operate on any
     type uniformly (generics).
   * *Ad-hoc polymorphism* (overloading) allows different
     behaviour for different types.
   * *Subtype polymorphism* enables treating objects of
     different types under a common interface.

5. *Dependent and Refinement Types*

   * *Dependent types* allow types to depend on values,
     enabling precise specifications (*Agda*, *Idris*).
   * *Refinement types* constrain existing types with
     predicates, encoding invariants directly in the type system.


### Beyond Safety

Advanced type systems can encode complex program invariants:
* *Effect systems* track side effects (e.g., state, exceptions, I/O).
* *Linear types* ensure resources are used exactly once, preventing leaks or double frees.
* *Gradual typing* allows mixing static and dynamic typing in the same program.

These extensions make types a tool for reasoning, verification,
and program documentation, not just error prevention.

Type systems thus bridge theory and practice: they formalise
computation while shaping real-world programming language design.


