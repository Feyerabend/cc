
## Hindley-Milner Type Inference

Hindley-Milner (HM), also known as Damas--Milner or Damas--Hindley--Milner, is a classical type
system for the lambda calculus that supports parametric polymorphism. It allows for automatic
type inference in functional programming languages, enabling programs to be written without
explicit type annotations while still ensuring type safety. HM is foundational to languages
like ML, Haskell, OCaml, and F#, where it deduces types for variables, expressions, and functions
from untyped code.


#### History

The system was first described by J. Roger Hindley in 1969, who proved that his algorithm
could infer the most general type for expressions in the simply typed lambda calculus.
It was independently rediscovered by Robin Milner in 1978 through his Algorithm W. Luis
Damas later provided a formal proof in his 1982 PhD thesis and a joint paper with Milner,
extending it to handle polymorphic references. The origins trace back to earlier work on
type inference for the simply typed lambda calculus by Haskell Curry and Robert Feys in 1958.
As of recent developments, HM continues to influence modern type systems, with extensions
incorporating features like type classes in Haskell, higher-kinded types, and integration
with dependent types in experimental languages.


#### Key Properties

- *Completeness*: HM can infer types for any typable program without needing hints or annotations.
- *Principal Typing*: It always deduces the *most general* (principal) type for a program, which
  is the broadest polymorphic type that fits all uses. All other valid types are instances of
  this principal type.
- *Parametric Polymorphism*: Supports generic functions (e.g., `forall a. a -> a` for the identity
  function), but restricts it to "let-polymorphism" where polymorphic types are only allowed for
  let-bound variables, not lambda-bound parameters, to maintain decidability.
- *Efficiency*: Inference is near-linear time in practice, using algorithms like Algorithm W (formal)
  or Algorithm J (practical).
- *Scope-Sensitivity*: Types are derived from complete programs or modules, ensuring context-aware
  inference.

HM distinguishes between *monotypes* (simple types like `Int` or `T -> T`) and *polytypes*
(type schemes with universal quantifiers, e.g., `forall α. α -> α`).


#### How Type Inference Works

HM inference "runs typing rules backwards": it traverses the program's abstract syntax tree (AST),
assigns fresh type variables to expressions, generates constraints based on usage, and solves them
via unification to find consistent types. If successful, it generalises the result to a polymorphic
type scheme.

1. *Constraint Generation*: During AST traversal, rules are applied to collect type equalities
   (constraints).
   - *T-Var*: Lookup a variable's type scheme in the environment and instantiate it with fresh variables.
   - *T-Lam* (Abstraction): For `λx.e`, assign a fresh type `tv` to `x`, infer type `t` for `e`,
     and return `tv -> t`.
   - *T-App* (Application): For `e1 e2`, infer `t1` for `e1` and `t2` for `e2`; introduce fresh `tv`
     and unify `t1` with `t2 -> tv`.
   - *T-Let*: For `let x = e1 in e2`, infer `t1` for `e1`, generalise it to a scheme, bind it to `x`,
     then infer `t2` for `e2`.
   - Additional rules handle conditionals (e.g., `if` requires `Bool` condition and matching branch types),
     fixed points (for recursion), and primitives (e.g., `+` unifies to `Int -> Int -> Int`).

2. *Unification*: Solves constraints by finding substitutions that make types equal, using a
   union-find structure for efficiency.
   - Rules: Match identical types; substitute variables if they don't occur in the target
     type (occurs check prevents infinite types like `a = a -> b`); recursively unify function arrows.
   - If unification fails, the program is ill-typed.

3. *Generalisation and Instantiation*:
   - *Generalisation*: At let-bindings, quantify free type variables not in the environment
     (e.g., turn `a -> a` into `forall a. a -> a`).
   - *Instantiation*: When using a polymorphic type, replace quantified variables with
     fresh ones for each use.
   This ensures the principal type is the most general, allowing flexible reuse
   (e.g., identity function works for any type).


#### Examples

- *Identity Function*: For `id = \x -> x`, inference assigns fresh
  `a` to `x`, returns `a -> a`, and generalizes to `forall a. a -> a`.
- *Addition*: For `\x y z -> x + y + z`, constraints unify to `Int -> Int -> Int -> Int`.
- *Composition*: For `compose f g x = f (g x)`, infers `forall c d e. (d -> e) -> (c -> d) -> c -> e`.


#### Extensions and Limitations

HM has been extended for type classes (Haskell), overloading, higher-kinded types (with kinds),
and subtyping, though full inference becomes harder with subtyping. Limitations include no support
for ad-hoc polymorphism without extensions and challenges with mutable references (solved by Damas).
In practice, it's implemented in compilers via monadic inference, separating constraint collection
from solving. For implementations, see resources on building HM systems in Haskell or similar languages.

