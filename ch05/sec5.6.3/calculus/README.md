
## Lambda Calculus Type Systems Progression

- *[lambda.py](lambda.py)*: Basic simply typed lambda calculus with explicit
  type annotations and type checking (no inference).
- *[hm.py](hm.py)*: Hindley-Milner (HM) type inference, adding polymorphism
  via let-bindings and type schemes (no explicit annotations needed).
- *[generics.py](generics.py)*: Extends HM with parametric polymorphism (generics),
  algebraic data types (e.g., List, Maybe, Pair), constructors, and pattern matching.
- *[recur.py](recur.py)*: Adds support for recursive functions (via `let rec` and
  fixpoints), recursive types (e.g., μ-types for infinite structures
  like lists or trees), and additional term constructs
  (e.g., integers, binary operations, conditionals).

This progression illustrates key concepts in *type theory*:
- *Lambda Calculus Basics*: Untyped lambda calculus is a model of computation
  using functions (abstractions), variables, and applications.
  Adding types prevents errors like applying a function to the wrong argument.
- *Type Checking vs. Inference*: Checking verifies if a term matches
  given types; inference deduces types automatically.
- *Polymorphism*: Allows functions to work on multiple types
  (e.g., a generic `map` function).
- *Recursion*: Enables self-referential definitions, requiring special
  handling in types (recursive types) and terms (fixpoints) to avoid infinite loops or types.
- *Algebraic Data Types (ADTs)*: Sum types (variants like `Maybe`) and
  product types (records like `Pair`), with pattern matching for deconstruction.
- *Unification*: Core algorithm in HM inference to solve type equations
  (e.g., equating `α → β` with `Int → γ` infers `α = Int`, `β = γ`).
- *Type Schemes and Generalisation*: In HM, `let`-bindings generalise
  types (e.g., `∀α. α → α` for identity), enabling polymorphism.
- *Occurs Check*: Prevents infinite types during unification
  (e.g., `α = α → β` is invalid).



### 1. lambda.py: Simply Typed Lambda Calculus

*What is Implemented*:
- Core terms: Variables (`Var`), Abstractions (`Abs` with
  explicit type annotations), Applications (`App`).
- Types: Base types (e.g., `Int`, `Bool`), Function types (`τ₁ → τ₂`).
- Type checking function `typecheck(term, context)` that
  verifies terms against typing rules (variable, abstraction, application).
- Examples: Identity function, constant functions, composition, applications,
  and type errors.

*How it Works*:
- Uses a `TypeContext` (environment Γ) to map variables to types.
- Recursively applies typing rules:
  - Variables: Lookup in context.
  - Abstractions: Extend context with parameter type, check body.
  - Applications: Check function has type `τ₁ → τ₂`, argument has `τ₁`, return `τ₂`.
- Explicit types are required on abstractions; no inference.
- Raises `TypeError` on mismatches (e.g., applying `Int → Int` to `Bool`).

*Key Concepts*:
- Static typing to ensure type safety.
- No polymorphism or recursion--types are monomorphic and finite.
- Demonstrates basic type safety in functional programming
  (e.g., like in typed languages without generics).

*Output Example* (from `main()`):
```
Term: (λx:Int. x)
Type: Int → Int
```


### 2. hm.py: Hindley-Milner Type Inference

*What is Implemented*:
- Builds on lambda.py terms, but removes explicit type annotations
  on abstractions.
- Adds `Let` bindings for polymorphism.
- Type inference via Algorithm W (HM): Infers types automatically,
  supports let-polymorphism.
- Types: Adds type variables (`α`), schemes (`∀α. τ` for polymorphism).
- Examples: Identity, self-application (fails with infinite type), const,
  composition, let-polymorphism (e.g., using `id` at multiple types).

*How it Works*:
- `infer(term, env, gen)` returns a substitution (mappings like `t0 ↦ Int`)
  and inferred type.
- Key steps:
  - Generate fresh type variables for unknowns.
  - Recurse on subterms, collecting constraints.
  - Unify constraints (e.g., equate types via `unify(t1, t2)`).
  - Generalize in `let`: Quantify free variables not in the environment.
  - Instantiate schemes with fresh variables for polymorphic use.
- Handles occurs check to avoid infinite types (e.g., `α = α → β`).
- Environment maps variables to schemes for polymorphism.

*Key Concepts*:
- HM inference: Damas-Milner algorithm (the concrete type inference algorithm
  for HM, or algorithm W), basis for languages like ML/Haskell.
- Let-polymorphism: `let id = λx. x` infers `∀α. α → α`, usable at any type.
- Principal types: Infers the most general type.
- No recursion yet--terms can't be recursive.

*Output Example*:
```
Term: (λx. x)
Type: t0 → t0
```


### 3. generics.py: Parametric Polymorphism (Generics)

*What is Implemented*:
- Extends hm.py with type applications (`TypeApplication` e.g., `List Int`),
  forall types (`∀α. τ`).
- Terms: Adds type abstractions (`TypeAbs` Λα. e for System F-style polymorphism),
  type instantiations (`e [τ]`), constructors (`Construct` e.g., `Cons`), pattern matching (`Match`).
- Supports ADTs: List, Maybe, Pair with constructors (e.g., `Nil`, `Cons`, `Some`, `None`).
- Inference handles generics and matching.
- Examples: Polymorphic identity (System F), lists/maybes/pairs, head functions,
  unwrap, let-polymorphism with generics.

*How it Works*:
- `infer` extended for new terms:
  - Constructors: Lookup polymorphic scheme, instantiate, apply to args.
  - Matching: Infer scrutinee type, unify with constructor return types, infer cases.
  - TypeAbs: Infer body, wrap in `ForallType`.
  - TypeInstantiation: Substitute type arg into forall.
- Environment pre-populated with ADT schemes (e.g., `Cons: ∀α. α → List α → List α`).
- Unification extended for type applications (match constructors and args).

*Key Concepts*:
- Parametric polymorphism: Types parameterized by variables (e.g., generics in Java, templates in C++).
- System F: Explicit type lambdas for polymorphism (beyond HM's implicit).
- ADTs: Data definitions with variants, deconstructed via matching.
- Type-safe generics: Ensures operations like `head` only on matching types.

*Output Example*:
```
Term: (Λα. (λx:α. x))
Type: ∀α. α → α
```


### 4. recur.py: Recursive Types and Functions

*What is Implemented*:
- Extends generics.py with recursion.
- Types: Adds recursive types (`RecursiveType` μα. τ, e.g.,
  `List α = μα. Nil | Cons α α` implicitly).
- Terms: Adds recursive lets (`LetRec`), fixpoints (`Fix`),
  integers (`IntLit`), binary ops (`BinOp` e.g., `+`, `=`),
  conditionals (`IfThenElse`).
- More ADTs: Trees (Leaf/Node).
- Inference supports recursive bindings.
- Examples: Factorial, Fibonacci, list sum/length/map,
  tree depth, foldr, fix-factorial.

*How it Works*:
- `infer` for recursion:
  - LetRec: Assume fresh type for var, infer value
    (unifying with assumed type), generalize, infer body.
  - Fix: Similar, assume type τ, infer body as τ, unify.
  - BinOp/If: Hardcoded rules (e.g., `+` requires Ints, returns Int).
- Unification/apply extended for recursive types (avoid substituting bound vars).
- Handles mutual recursion indirectly (via nested let recs).

*Key Concepts*:
- Recursive types: Self-referential (e.g., lists as infinite unions),
  with μ-operator for equirecursive types.
- Fixpoints: Y-combinator analog for recursion in untyped lambda, typed here.
- Recursive functions: Type-safe loops (e.g., factorial infers `Int → Int`).
- Practical FP: Enables real algorithms like map/fold on recursive structures.

*Output Example*:
```
Term: (let rec fact = (λn. (if (n = 0) then 1 else (n * (fact (n - 1))))) in fact)
Type: Int → Int
```

### Limitations and Extensions
- No evaluation/reduction--focus on typing.
- Simplified: No type classes, effects, or full System Fω.
- Potential extensions: Subtyping, dependent types, or
  go ahead and make a full interpreter!

