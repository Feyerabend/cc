
| # | Monad / Effect type | Base category C | Kleisli category Kl(m) is basically.. | The "carrier" of the monoid | Multiplication in Kleisli | Unit of the monoid | What it really means in practice |
|---|---|---|---|---|---|---|---|
| 1 | `Maybe` | Hask | "partial functions" / functions that may fail | `1 → Maybe 1` | `(>=>)` = try first, if succeeds try second | `return` | "best-effort chaining of possibly-failing computations" |
| 2 | `[]` (List) | Hask | "non-deterministic functions" / multi-valued funcs | `1 → [1]` | `(>=>)` = try left, collect all, try right on each | `return = pure = singleton` | "collect all possible results from all branches" |
| 3 | `IO` | Hask | "actions that do side-effects before returning" | `1 → IO 1` | `(>=>)` = sequence two actions | `return` | Classic "do this, then do that" with real-world effects |
| 4 | `State s` | Hask | "functions that carry hidden state" | `1 → s → (1, s)` | `(>=>)` = run first, feed output state to second | `return` | "state is threaded through via composition" |
| 5 | `Writer w` (when w is monoid) | Hask | "functions that accumulate a log/side-output" | `1 → (1, w)` | `(>=>)` = run both, combine logs with `<>` | `return = (x, mempty)` | Log / audit trail / accumulated value grows via monoid op |
| 6 | `Reader r` | Hask | "functions that require an environment" | `1 → r → 1` | `(>=>)` = pass the same environment to both | `return = const id` | "dependency injection via function composition" |
| 7 | `Cont r` (continuation) | Hask | "functions that never really return" | `1 → (1 → r) → r` | CPS-style composition | `return` | Extremely powerful — basis of call/cc, coroutines, etc. |
| 8 | Free monad over signature F | Sets (or any cat) | "syntax trees of F-instructions" | `1 → Free F 1` | `(>=>)` = sequential composition of programs | `return` / `Pure` | The foundation of algebraic effects / handlers |
| 9 | `Either e` | Hask | "functions that can short-circuit with error e" | `1 → Either e 1` | `(>=>)` = fail fast on Left | `return = Right` | Classic error-handling monad (fail-stop semantics) |
|10 | Tagless-final style m | Hask (or any cat) | "abstract programs in algebra m" | `1 → m 1` | `(>=>)` = program sequencing | `return` / `pure` | "the monad is whatever interpretation you choose later" |

