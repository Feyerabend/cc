
## COOL with Algebraic Data Types

```text

        ┌─────────────────────────────┐
        │         Category            │
        │          of Types           │
        └──────────────┬──────────────┘
                       │
             morphisms (subtyping, projections, injections)
                       │
         ┌─────────────┼───────────────────┐
         ▼             ▼                   ▼
   ┌─────────┐   ┌─────────────┐   ┌───────────────┐
   │   Bool  │◄──┤   Option<T> │◄──┤      Tree     │
   └─────────┘   └──────┬──────┘   └────────┬──────┘
                        │                   │
                 coproduct (sum)     recursive fixed point
                        │                   │
                        ▼                   ▼
                 None | Some(T)    Leaf | Node(value, left, right)
```


### What's New in This Iteration?

This file `cat_adt.py` extends the COOL framework by incorporating
*Algebraic Data Types (ADTs)*, interpreted through category theory lenses:

- *Sum Types*: As categorical coproducts (A + B), modeling choices/alternatives.
- *Product Types*: As categorical products (A × B), modeling structured data.
- *Pattern Matching*: As catamorphisms (folds over initial algebras).
- *Recursive Types*: As fixed points of functors (μF), for structures like lists and trees.
- *Constructors & Projections*: Injections into sums and projections from products.
- Demonstrations include Option, Either, Tuples, Binary Trees, Lists, Result, Bool (as sum), and Peano Naturals.

This iteration shifts focus from OOP/classes to functional-style data types,
showing how categories unify both paradigms.


### Core Features

- *Sum Types (Coproducts)*: Tagged unions like `Option = None | Some(T)`.
- *Product Types (Products)*: Named tuples like `(name: String, age: Int)`.
- *Recursive ADTs*: Self-referential types like `Tree = Leaf | Node(Int, Tree, Tree)`.
- *Pattern Matching*: Exhaustive case analysis with binding.
- *Runtime Values*: Immutable structures with evaluation.
- *Type Checking*: Basic subtyping and morphism checks.
- Categorical Mappings:
  - Constructors -> Injections (ι₁, ι₂).
  - Projections -> π₁, π₂.
  - Matching -> Universal morphism from coproduct.


### How It Works

1. *Type Environment*: Registers types as category objects; subtyping as morphisms.
2. *Sum/Product Definitions*: Explicit constructors for variants/fields.
3. *Expressions*: Literals, constructors, accessors, matches.
4. *Evaluation*: Recursive descent interpreter with environment.
5. *Matching*: Checks exhaustiveness; binds variables per case.
6. *Recursion*: Types reference themselves (e.g., `Tree` in `Node`).

No full parser yet—ASTs are hand-built for demos.


### Example Highlights

From the demo:

- *Option<Int>*: `None | Some(42)` with matching to extract value.
- *Either<String, Int>*: Error handling with `Left("Error") | Right(100)`.
- *Product (Tuple)*: `(name="Alice", age=30, active=true)` with field access.
- *Binary Tree*: Recursive structure; manual construction.
- *List<Int>*: As fixed point `μX. 1 + (Int × X)`; cons and literals.
- *Result<Int, String>*: Like Rust's error type; matching for handling.
- *Bool as Sum*: `True | False` ≅ `Unit + Unit`; if-then-else via match.
- *Peano Nats*: `Zero | Succ(Nat)`; recursive numbers.

These show ADTs as "data algebras" with categorical universals.


### Limitations

- Hand-constructed ASTs (no parser integration yet).
- Basic type checking; no variance in generics here.
- No automatic exhaustiveness checks in code (simulated).
- Immutable values only; no mutable state in ADTs.
- Simplified recursion (no cycle detection).
- Missing: Full folds/anamorphisms, GADTs, dependent types.


### Next Steps

- Merge with `cat_parse.py` for ADT syntax parsing.
- Add generics to ADTs (e.g., `Option<T>` as functor).
- Implement full catamorphisms (folds) for recursion.
- Explore monads over ADTs (e.g., `List` as monad).
- Visualize ADT structures as category diagrams.
- Combine with monoids from `cat_gen2.py` for algebraic ops.

