
## COOL — Categorical Object-Oriented Language .. continued

```text
        ┌─────────────────────────────┐
        │         Category            │
        │          of Types           │
        └──────────────┬──────────────┘
                       │
             subtyping morphisms
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
   ┌─────────┐   ┌─────────────┐   ┌──────────-───┐
   │  Animal │◄──┤   Box<T>    │◄──┤ Comparator<T>│
   └─────────┘   └──────┬──────┘   └──────┬────-──┘
                        │                 │
                   covariant         contravariant
                    functor             functor
                       ▼                   ▼
             Box<Dog> <: Box<Animal>   Comparator<Animal> <: Comparator<Dog>

```


### Evolution

This repository contains several progressive iterations of *COOL*.

Current main branches / files (most mature -> newest):

| File                  | Main Idea                              | Generics? | Parser? | Runtime? | Maturity | Main contribution                          |
|-----------------------|----------------------------------------|-----------|---------|----------|----------|--------------------------------------------|
| `cat_cool.py`         | First version — basic OOP + categories | ✗         | ✗       | ✓        | ★★★★     | Core concept, subtyping as morphisms       |
| `cat_parse.py`        | Standalone **parser combinator** library | —         | ✓       | ✗        | ★★★★     | Clean, mutual-recursion-safe combinators   |
| `cat_gen.py`          | **Generics** as endofunctors           | ✓         | ✗       | ✓        | ★★★☆     | Variance, type substitution, bounds        |
| (future) full version | parser + generics + runtime + typeck   | ✓         | ✓       | ✓        | ★★☆☆     | The real goal (still under construction)   |


Main ideas implemented:

- *Generics as endofunctors* `F : Type -> Type`
- Three kinds of *variance* (categorical properties of functors)
  - covariant (`+T`)
  - contravariant (`-T`)
  - invariant (default)
- *Bounded polymorphism* (`T extends Animal`)
- *Type parameter substitution* (functorial action)
- *Instantiated generic classes* created at "compile-time" (simulation)
- *Subtyping rules respect variance* (the heart of safe generic subtyping)
- Demonstration of classical examples:
  - `Box<T>` -> covariance
  - `Comparator<T>` -> contravariance
  - `Pair<T,U>` -> product type / binary functor
  - `Optional<T>` -> simplified monad-like
  - `List<T>` -> covariant collection


### Parser

A implementation of *parser combinators* with these notable features:

- *Categorical style* naming & operations
  - `>>=` (bind)
  - `>>` (then/ignore left)
  - `<<` (then/ignore right)
  - `|` (choice / coproduct)
- *Delayed* combinator for *mutual recursion* (essential for expr <-> stmt)
- Very robust error propagation
- Nice token handling (`token()`, `keyword()`, `symbol()`)
- Supports generic syntax: `Box<Int>`, `new Box<String>()`, etc.

Many people consider this parser combinator implementation one of the
cleaner ones written in pure Python.


### What are we trying to express?

We are trying to build a (very small) language where almost every
major concept has a direct categorical counterpart:

```text
OOP concept                 c  Category Theory concept
────────────────────────────┼───────────────────────────────
Class                       ->  Object in category
Inheritance                 ->  Morphism
Subtyping                   ->  Existence of morphism
Polymorphism                ->  Natural transformation
Method override             ->  Different impl. of same NT
Generic class F<T>          ->  Endofunctor F : Type -> Type
Variance                    ->  Preservation of arrows
Type parameter substitution ->  Functorial action map
Bounded quantification      ->  Dependent product / slice category
Interface                   ->  Universal property / specification
```


### Current Limitations

- No real parser -> interpreter (everything still hand-constructed ASTs)
- Type checking is partial (especially for generics)
- No full statement language in parser yet
- No proper error reporting pipeline
- Runtime is very naive (no real dispatch tables, no JIT, etc.)
- Missing: traits, multiple inheritance, higher-kinded types, effect system…


### Possible Future Directions

```
1. Connect cat_parse.py with cat_gen.py -> real AST -> typecheck -> eval
2. Add kind system (higher-kinded types)
3. Experiment with monadic effects (IO, State, Maybe)
4. Try to model traits as colimits / Kan extensions
5. Add visualization of type category + morphisms
6. Minimal standard library with generic collections
7. Maybe.. very tiny dependent types? (probably too ambitious)
```
