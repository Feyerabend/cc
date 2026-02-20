
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
with languages like *Algol**, *ML*, and *Haskell*, where static
typing was used to improve safety and reasoning about programs.
Modern languages now span a wide spectrum, from dynamically typed
(*Python*, *JavaScript*) to richly statically typed (*Rust*,
*Haskell*, *Scala*).


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

