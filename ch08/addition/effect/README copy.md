
## The Interpreter Connection

An effect system is essentially an *interpreter pattern at the type level*.
Just like how an interpreter separates:
- *Abstract Syntax Tree* (what to do) from
- *Evaluation* (how to do it)

Effect systems separate:
- *Effect descriptions* (what effects to perform) from
- *Effect handlers* (how to interpret those effects)

This is the *free monad* pattern in disguise.


### Deep Dive: The Theory

#### 1. *Algebraic Effects = Free Monads*

An effect system can be understood through algebraic effects, which have two parts:

*Operations (signatures)*: Declared effects
```
effect State {
  get : () -> int
  put : int -> ()
}

effect Error {
  throw : string -> empty
}
```

*Handlers (algebras)*: Interpretations of those effects
```
handle {
  computation_with_effects()
} with {
  get() -> resume(current_state)
  put(new_state) -> resume((), new_state)
}
```

This is mathematically an *algebra* (in the universal algebra sense):
- Operations are abstract
- Handlers provide concrete implementations
- Different handlers = different interpretations of the same program

#### 2. *Delimited Continuations*

The real power comes from *delimited continuations* (the `resume` function).
When you perform an effect:
1. Execution *pauses*
2. Control transfers to the handler
3. Handler can:
   - Resume once (normal)
   - Resume multiple times (non-determinism, backtracking)
   - Never resume (exceptions)
   - Resume with different values (state)

This is more powerful than exceptions (which can only abort) or
async/await (which must resume exactly once).

[effects.c]


### Key Insights

#### 1. *Separation of Concerns*
- *Business logic* (the counter computation) doesn't know about state storage
- *Handler* decides how to implement state (could be global variable, database, network call)
- Same computation, different interpretations

#### 2. *Composability*
You can stack handlers:
```
handle {
  handle {
    computation()
  } with StateHandler
} with ErrorHandler
```

Each handler interprets its effects and passes unknown effects up.

#### 3. *Effect Polymorphism*
A function can be polymorphic over effects:
```c
// Works with ANY effect that provides "choose"
Effect compute<E>(void) where E: Choice {
    int x = perform choose([1,2,3]);
    int y = perform choose([10,20]);
    return x + y;
}
```

Different handlers give different behaviors:
- `ListHandler` → all combinations: [11, 21, 12, 22, 13, 23]
- `MaybeHandler` → first result: 11
- `RandomHandler` → random pick

#### 4. *Relationship to Monads*

Effect systems generalize monads:
- *Monad*: single effect type, handlers baked in
- *Effect system*: multiple effects, handlers chosen at use-site

```
IO monad ≈ Effect system with fixed IO handler
State monad ≈ Effect system with fixed State handler
```

But effect systems let you *mix and match* handlers, while monads require monad transformers (which don't compose cleanly).

### Real-World Applications

#### 1. *Testing*
```c
// Production: uses real IO
handle { app() } with RealIOHandler

// Testing: uses mock IO
handle { app() } with MockIOHandler
```

#### 2. *Async/Await*
Effect systems can model async as an effect:
```c
Effect async_get(char* url, Continuation* k) {
    return eff_async(http_get, url, k);
}

// Handler spawns threads/fibers
handle { async_computation() } with ThreadPoolHandler
```

#### 3. *Transactions*
```c
handle {
    db_write("key", "value");
    if (error()) {
        perform rollback();
    }
    db_write("key2", "value2");
} with TransactionHandler  // All-or-nothing semantics
```

#### 4. *Backtracking Search*
The non-determinism handler above shows this: explore all branches of search space.



### Comparison to Other Approaches

| Approach          | Power     | Type Safety | Composability         |
|-------------------|-----------|-------------|-----------------------|
| Callbacks         | Low       | None        | Poor                  |
| Monads            | Medium    | High        | Medium (transformers) |
| Effect Systems    | High      | High        | Excellent             |
| Algebraic Effects | Very High | High        | Excellent             |

*Algebraic effects* (OCaml 5, Koka, Eff) add multi-shot continuations,
making them Turing-complete for control flow.


## The Bottom Line

Effect systems are *interpreters for side effects*:
- Programs describe effects (AST)
- Handlers interpret effects (evaluator)
- Same program, multiple meanings
- Type system ensures effects are handled

This gives you the power of dependency injection, the safety of types, and the flexibility of choosing how effects run at the call site rather than at definition site.
