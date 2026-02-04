
## System F Type System

System F, also known as the polymorphic lambda calculus or second-order lambda calculus,
is a typed lambda calculus that extends the simply typed lambda calculus by introducing
universal quantification over types. This allows for parametric polymorphism, where functions
can operate uniformly over different types without knowing them in advance. It serves as
a theoretical foundation for type systems in functional programming languages such as
Haskell and ML, enabling generic programming while maintaining strong type safety.


#### History

System F was independently discovered by logician Jean-Yves Girard in 1972 as part of his
work on proof theory and by computer scientist John C. Reynolds around the same time, who
explored it in the context of polymorphic typed lambda calculus. It builds on the simply
typed lambda calculus, adding mechanisms for type abstraction and application, which mirror
term-level lambda abstraction but at the type level. As of 2026, System F remains a cornerstone
of type theory, influencing modern extensions like dependent types and higher-kinded
polymorphism, though its core has seen no fundamental changes since its inception.


#### Key Properties

- *Parametric Polymorphism*: System F supports universal types (e.g., ∀α. α → α for
  the identity function), allowing functions to be polymorphic over types. This is
  more expressive than ad-hoc polymorphism (e.g., overloading) or subtype polymorphism.
- *Strong Normalisation*: All well-typed terms in System F terminate (no infinite
  reductions), making it suitable for total functional programming and proofs of program correctness.
- *Type Safety*: System F is type-safe, with theorems for progress (well-typed terms
  can reduce) and preservation (reduction preserves types).
- *Expressiveness*: It can encode data types like booleans, integers, pairs, lists,
  and even Church numerals using only lambda terms and type polymorphism, without needing built-in primitives.
- *Undecidability of Type Inference*: Unlike Hindley-Milner (a decidable subset),
  full type inference in System F is undecidable, requiring explicit type annotations for polymorphic functions.
- *Second-Order Logic Connection*: System F corresponds to second-order intuitionistic
  logic via the Curry-Howard isomorphism, where types are propositions and terms are proofs.


#### How the Type System Works

System F adds two constructs to the simply typed lambda calculus:
- *Type Abstraction (Λ)*: Introduces a binder for type variables, e.g., Λα. λx:α. x (the polymorphic identity).
- *Type Application*: Applies a term to a type, e.g., (Λα. λx:α. x) Int (instantiates to int → int).

*Syntax* (simplified):
- Types: τ ::= α (type variable) | τ → τ (function) | ∀α. τ (universal)
- Terms: e ::= x (variable) | λx:τ. e (abstraction) | e e (application) | Λα. e (type abstraction) | e [τ] (type application)

*Typing Rules* (key ones):
- *T-Var*: Γ ⊢ x : τ if x:τ ∈ Γ
- *T-Abs*: If Γ, x:τ1 ⊢ e : τ2, then Γ ⊢ λx:τ1. e : τ1 → τ2
- *T-App*: If Γ ⊢ e1 : τ1 → τ2 and Γ ⊢ e2 : τ1, then Γ ⊢ e1 e2 : τ2
- *T-TAbs*: If Γ ⊢ e : τ (with α not free in Γ), then Γ ⊢ Λα. e : ∀α. τ
- *T-TApp*: If Γ ⊢ e : ∀α. τ, then Γ ⊢ e [τ'] : τ[τ'/α] (substitution)

Reduction follows beta-reduction for both terms and types, preserving types.


#### Examples

- *Polymorphic Identity*: Λα. λx:α. x has type ∀α. α → α.
  Applying to int: (Λα. λx:α. x) [int] reduces to λx:int. x.
- *Self-Application*: In System F, self-application like (λx. x x) is
  typable as (Λα. λx:α → α. x x) [∀β. β → β], showcasing its expressiveness beyond simply typed lambda calculus.
- *Church Booleans*: true = Λα. λt:α. λf:α. t; false = Λα. λt:α. λf:α. f; both have type ∀α. α → α → α.
- *Lists*: Can be encoded as ∀α. ∀β. (α → β → β) → β → β (fold-like), demonstrating definable data types.


#### Extensions and Limitations

System F has been extended to System Fω, which adds quantification over type
constructors (higher kinds), enabling more advanced type-level programming like
functors and monads in Haskell. Limitations include the undecidability of type
inference, which led to practical subsets like [Hindley-Milner](HM.md)
(with let-polymorphism for decidability) used in real languages.
It lacks features like recursion (added in extensions like PCF) or effects,
focusing purely on total functions. In modern type theory, System F influences
systems with dependent types (e.g., in Coq or Agda), but requires additions
for full dependently typed programming.

