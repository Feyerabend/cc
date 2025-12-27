
## COOL with Applicative Functors

```text

        ┌───────────────────────────────┐
        │           Category            │
        │        of Endofunctors        │
        └────────────────┬──────────────┘
                         │
             applicative apply (<*>)
                         │
         ┌───────────────┼─────────────────┐
         ▼               ▼                 ▼
   ┌─────────┐   ┌───────────────┐   ┌─────────────┐
   │  Maybe  │◄──┤  Validation   │◄──┤    List     │
   └─────────┘   └───────┬───────┘   └──────┬──────┘
                         │                  │
                 independent effects   cartesian product
                         │                  │
                         ▼                  ▼
                    None | Some(a)    [1,2] <*> [3,4] = [3,4,3,4]
```


### What's New in This Iteration?

This file `cat_applicative.py` extends COOL by introducing *Applicative Functors*,
positioned as a bridge between Functors and Monads:

- *Applicatives*: Lax monoidal functors enabling independent effect composition.
- *Key Ops*: `pure` (lift values), `apply` (<*>) (apply wrapped functions).
- *Independent Effects*: Unlike Monads (sequential/dependent), applicatives
  handle static, parallelisable structures.
- Implemented Applicatives:
  - *Maybe*: Optional apply (fails if any missing).
  - *Either*: Fails fast (first error).
  - *Validation*: Accumulates all errors (key for forms).
  - *List*: Cartesian product (all combinations).
  - *ZipList*: Pointwise apply (zip-like).
  - *Const*: Accumulates monoids (ignores values).
- Laws verification: Identity, composition, homomorphism, interchange.
- Demos: Lifting, products, validation, parsers, traverse.

This iteration highlights applicatives' power for static computations, complementing monads' dynamic ones.


### Core Features

- *Applicative Interface*: `pure`, `apply`, `fmap`, `lift_a2` for binary lifts.
- *Expressions*: Literals, vars, ops, lambdas, applications, applicative constructs.
- *Runtime*: Eval with environments; applies use function values.
- Categorical Ties:
  - Applicative = Functor + monoidal structure.
  - Laws ensure composability.
  - Between Functor (map) and Monad (bind).


### How It Works

1. *Applicative Values*: Subclasses with `pure`/`apply`/`fmap`.
2. *Expressions*: AST for applicative ops (e.g., `AFmap`, `AApply`).
3. *Evaluation*: Recursive; applies extract/call functions.
4. *Lifts*: `lift_a2` for binary; extendable to n-ary.
5. *Demos*: Hand-built ASTs in `demo()`.

No parser—manual ASTs.


### Example Highlights

From the demo:

- *Maybe Apply*: `pure (+) <*> Some(3) <*> Some(4) → Some(7)`.
- *List Cartesian*: `[λx.x+1, λx.x-1] <*> [5, 6] → [6,7,4,5]`.
- *Validation*: Collects all form errors: `Failure(["Username too short", "Invalid email"])`.
- *ZipList*: Pointwise: `zipWith (+) [1,2,3] [4,5,6] → [5,7,9]`.
- *Const*: Accumulates sums: `Const(2) <*> Const(3) → Const(5)`.
- *Laws*: Verified for Maybe (e.g., homomorphism: `pure f <*> pure x = pure (f x)`).
- *Applicative vs Monad*: Shows dependency limitation in applicatives.
- *Form Validation*: All errors at once for better UX.
- *Parser Combinators*: Independent parsing for efficiency.
- *Traverse*: Validates list elements, collects failures.

These demonstrate applicatives for parallel/independent ops.


### Limitations

- Manual ASTs (no parser).
- Basic implementations (no full instances, no effects in Const).
- No monad integration yet.
- Simplified laws checks (manual).
- Missing: Full traverse/sequence, applicative do-notation.


### Next Steps

- Parse applicative syntax with `cat_parse.py`.
- Combine with monads from `cat_monad.py` (applicative-monad relation).
- Add traversables for structures like trees from `cat_adt.py`.
- Explore monoidal aspects more (e.g., Day convolution).
- Visualize applicative compositions.
- Integrate generics from `cat_gen.py` for parametric applicatives.
