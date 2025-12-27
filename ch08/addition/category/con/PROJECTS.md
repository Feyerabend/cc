
## Project Ideas

### 1. *Async Task Library*
Build a small library that provides `Async[A]` with functor, applicative, and monad interfaces.

*What you'll learn:*
- Implementing the type class hierarchy in your favourite language
- Managing thread pools and execution contexts
- Handling errors in async contexts

*Features to implement:*
- `map`, `flatMap`/`bind`, `pure`
- `map2`, `map3` for parallel composition
- `timeout`, `retry`, `race` combinators
- Error handling with `Result[A]` or `Either[E, A]`

*Languages:* Python (asyncio), JavaScript (Promises), Rust (futures), Scala (cats-effect)



### 2. *Form Validation Framework*
Create a parallel form validation library using applicative functors.

*What you'll learn:*
- Why applicatives are perfect for independent validations
- Accumulating errors (not just failing fast)
- Real-world performance benefits of parallelism

*Features:*
```python
email = validate_email(form.email)      # async check
username = validate_username(form.user)  # async check
password = validate_password(form.pass)  # async check

# All run in parallel!
result = validate_all(email, username, password)
```

*Bonus:* Compare performance against sequential validation



### 3. *Pipeline DSL*
Design a fluent API for data processing pipelines using monadic composition.

*What you'll learn:*
- Builder pattern meets category theory
- Method chaining with type safety
- Lazy evaluation strategies

*Example API:*
```python
Pipeline()
  .read("data.csv")
  .filter(lambda row: row['age'] > 18)
  .map(lambda row: process(row))
  .write("output.csv")
  .run()  # Nothing executes until .run()!
```

*Extensions:* Add parallel stages, error handling, progress tracking




### 4. *Multi-Strategy Executor*
Build a task execution system with pluggable interpreters (sync, async, parallel, mock).

*What you'll learn:*
- Free monad pattern in practice
- Strategy pattern meets functional programming
- Writing testable concurrent code

*Core idea:*
```python
# Define tasks (description)
task = (
  fetch_user(123)
  .then(lambda user: fetch_posts(user.id))
  .then(lambda posts: aggregate(posts))
)

# Choose execution strategy
SyncExecutor().run(task)      # Sequential
AsyncExecutor().run(task)     # Threaded
ParallelExecutor().run(task)  # Max parallelism
MockExecutor().run(task)      # For tests
```

*Real-world use case:* ETL pipelines, data processing workflows



### 5. *Concurrent Web Scraper*
Build a web scraper that uses applicative functors for parallel requests and monads for sequential dependencies.

*What you'll learn:*
- When to use applicative vs monad
- Rate limiting and backpressure
- Dependency graphs in scraping

*Architecture:*
```python
# Independent pages - use Applicative (parallel)
pages = fetch_many([url1, url2, url3])

# Dependent requests - use Monad (sequential)
detail = (
  fetch_list_page(url)
  .bind(lambda items: fetch_details(items[0]))
  .bind(lambda detail: fetch_related(detail.id))
)
```

*Extensions:* Add caching, respect robots.txt, implement retry logic



### 6. *Effect System*
Create a simple effect system that tracks side effects in types.

*What you'll learn:*
- Algebraic effects and handlers
- Type-level programming
- Effect polymorphism

*Example:*
```python
def fetch_user(id: int) -> Effect[IO | Network, User]:
    # Type says: "I do IO and Network effects"
    ...

def pure_logic(user: User) -> Effect[None, Report]:
    # Type says: "I'm pure, no effects!"
    ...
```

*Goal:* Make effects explicit, testable, and composable




### 7. *Distributed Task Scheduler*
Build a distributed task execution system using free monads.

*What you'll learn:*
- Free monads for distributed systems
- Serialising computation descriptions
- Remote execution and result gathering

*Architecture:*
1. Client builds task AST (free monad)
2. Serialise AST, send to coordinator
3. Coordinator analyses dependencies
4. Distribute independent tasks to workers
5. Gather results, continue execution

*Technologies:* gRPC, message queues, distributed tracing



### 8. *Stream Processing Library*
Create a reactive stream processing library with backpressure.

*What you'll learn:*
- Combining push and pull models
- Backpressure and flow control
- Transducers and stream fusion

*API design:*
```python
Stream.from_file("data.csv")
  .map_parallel(expensive_transform, concurrency=10)
  .filter(is_valid)
  .batch(100)
  .write_to("output.db")
```

*Key features:*
- Functor/Applicative/Monad for streams
- Natural transformations (hot ↔ cold streams)
- Resource safety (bracket pattern)



### 9. *Optimising Interpreter*
Build an interpreter that analyses free monad programs and optimises them.

*What you'll learn:*
- Program analysis and optimisation
- Detecting parallelisable operations
- Rewriting rules and AST transformations

*Optimisations to implement:*
- Detect independent operations → parallelise
- Batch similar operations (read multiple files at once)
- Reorder operations when safe
- Eliminate redundant operations (read same file twice)

*Example:*
```
Before:  read(A) → read(B) → process(A, B)
After:   read(A) ∥ read(B) → process(A, B)  [parallel!]
```



### 10. *Concurrency Framework*
Build a full concurrent programming framework inspired by the concepts you've learned.

*What you'll learn:*
- Everything! This is your magnum opus

*Features to include:*
- *Functor/Applicative/Monad* hierarchy for tasks
- *Natural transformations* between execution strategies
- *Free monads* for effect description
- *Resource management* (bracket, finalisers)
- *Error handling* (typed errors, recovery)
- *Cancellation* (cooperative and forced)
- *Scheduling* (fairness, priority)
- *Observability* (tracing, metrics)

*Inspiration:* Look at Cats Effect (Scala), ZIO (Scala), Tokio (Rust)



### 11. *Arrows for Dataflow*
Explore *arrows* (generalisation of monads) for dataflow programming.

*Why arrows?*
- Monads force linear composition
- Arrows allow more flexible composition
- Perfect for circuits, signal processing, UI frameworks

*Project:* Build a visual dataflow editor where nodes are arrows



### 12. *Algebraic Effects System*
Implement algebraic effects and handlers for concurrency.

*Concepts:*
- Effects as operations with handlers
- Effect polymorphism
- Delimited continuations

*Languages to explore:* OCaml (native support), Koka, Eff



### 13. *Category Theory Visualiser*
Build an interactive tool to visualise category theory concepts in concurrent programs.

*Features:*
- Visualize functor mappings
- Show monadic bind as graph composition
- Animate natural transformations
- Display free monad ASTs
- Interactive interpreter comparison

*Technologies:* D3.js, React, visualisation libraries

