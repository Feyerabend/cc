
## COOL with Free Monads


```text

        ┌─────────────────────────────┐
        │         Category            │
        │       of Endofunctors       │
        └──────────────┬──────────────┘
                       │
             free monad (Free F)
                       │
         ┌─────────────┼──────────────────┐
         ▼             ▼                  ▼
   ┌─────────┐   ┌─────────────┐   ┌─────────────┐
   │ Console │◄──┤  Telemetry  │◄──┤    Http     │
   └─────────┘   └──────┬──────┘   └──────┬──────┘
                        │                 │
                program description   multiple interpreters
                        │                 │
                        ▼                 ▼
             Pure A | Impure (F k)   Test | Prod | Optimise
```

### What's New in This Iteration?

This file `cat_free.py` advances COOL by introducing *Free Monads*,
which generate monads "for free" from any functor:

- *Free Monads*: `Free F A = Pure A | Impure (F (Free F A))`—build effect descriptions as data structures.
- *Separation*: Program (AST-like) vs. Interpreter (semantics).
- *Functors*: Base ops (e.g., `PrintLine`, `ReadLine`).
- *Interpreters*: F-algebras mapping ops to effects; multiple for testing/optimization.
- *Coproducts*: Combine functors (e.g., Console + Telemetry).
- *DSLs*: Build composable languages (e.g., logging, state, HTTP).
- Demos: Console, logging, state, HTTP; mocks, optimizations.

This iteration enables pure, testable effect systems—perfect for DSLs and flexible interpretations.


### Core Features

- *Free Monad*: `Pure` (values), `Impure` (effects via functors); `bind`/`fmap`.
- *Functors*: Custom ops with `fmap_free`.
- *Interpreters*: Run programs with effects (real/mock/optimized).
- *Coproduct*: `EitherF` for multi-DSLs.
- *Smart Constructors*: Easy ops like `print_line`, `get_state`.
- Categorical Ties:
  - Free = Initial algebra over functor.
  - Interpreter = F-algebra.
  - Coproduct = Extensible effects.


### How It Works

1. *Build Programs*: Chain ops with `bind` (monadic).
2. *Free Structure*: Layers of `Impure` functors ending in `Pure`.
3. *Interpret*: Fold over structure with interpreter's `run`.
4. *Coproduct*: `inject_left`/`inject_right` for combined functors.
5. *Demos*: Hand-built programs interpreted variously.

No parser—manual construction.


### Example Highlights

From the demo:

- *Console DSL*: `print_line("Hello") >> read_line() >> print_line("You said: ")`.
- *Logging DSL*: `log_info("Starting") >> computation >> log_info("Done")`.
- *State DSL*: `get_state >> modify_state(lambda s: s+1) >> put_state(42)`.
- *Coproduct*: Combine logging + state; interpret together.
- *Multiple Interpreters*: Real console vs. mock (logs outputs).
- *Testing*: Pure interpreter checks without I/O.
- *Optimiation*: Fuse/reorder ops before running.
- *Web API DSL*: `http_get("/users") >> http_post("/analytics")`; mock for tests.

These show free monads' flexibility: one program, many meanings.


### Limitations

- Manual programs (no parser).
- Basic functors (no generics/variance here).
- Simplified coproducts (manual injection).
- No full laws checks.
- Missing: Cofree comonads, transformers.


### Next Steps

- Parse free monad DSLs with `cat_parse.py`.
- Integrate monads/applicatives from prior files.
- Add ADTs from `cat_adt.py` as functors.
- Explore free arrows/applicatives.
- Visualise program trees.
- Combine with generics/monoids for richer DSLs.
