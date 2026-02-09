
## Modern Functional Basis for Programming Languages

In an era where software complexity demands robust, composable, and error-resilient code,
functional programming (FP) emerges as a foundational paradigm. One that prioritises immutability,
pure functions, and declarative structures over mutable state and imperative control flow.
This codebase establishes a modern functional basis by implementing core FP abstractions in
Python, drawing inspiration from languages like Haskell and Scala while leveraging Python's
dynamic nature and type hints for accessibility. Key constructs such as the Maybe monad for
handling optional values, Result for error propagation, and IO for managing side effects.
It facilitate composability through operations like map and flat_map. Extending to advanced
monads like State for threaded computations and Reader for dependency injection,
it provides tools for stateful yet pure programming, ensuring that effects are
explicit and controllable.

Building on these primitives, the framework incorporates algebraic data types (ADTs) with
pattern matching for expressive data modeling, and type classes like Functor, Applicative,
and Monad. Asynchronous variants, such as AsyncMaybe and AsyncIO, address modern concurrency
needs. Utilities like lenses for immutable updates and do-notation simulations bring "ergonomic"
FP idioms to Python. This synthesis not only bridges FP with object-oriented or imperative
styles--mapping monads to fluent interfaces or try-catch blocks--but also paves the way
for extensions like algebraic effects or domain-specific languages, fostering scalable,
maintainable code in diverse applications from web services to data pipelines.


### 1. Some Projects to Extend From This Codebase

This codebase ([01](./01/), [02](./02/), [03](./03/)) could evolve into a full FP library
like `toolz` or `funcy` in Python, but with more emphasis on monads and type safety.
Here are a few project ideas, ordered from simple to more involved. Each builds on existing
concepts like `Maybe`, `Result`, `IO`, `State`, or type classes (`Functor`, `Monad`, etc.).

- *Project: FP-Style Data Validation Library* (Beginner-Friendly Extension)
  - *Why?* Builds on `Maybe` and `Result` for safe data handling, common in real-world
    apps like form validation or API parsing.
  - *How to Extend:*
    - Add a `Validation` monad (similar to `Result` but accumulates errors instead of short-circuiting).
    - Example: In `functional.py`, create a `Validation` class that extends `Result`
      but allows collecting multiple `Err`s (e.g., for validating user input with multiple rules).
    - Code Sketch:
      ```python
      from typing import List
      from functional_core import Result, Ok, Err

      class Validation(Result[A, List[E]]):
          # Override flat_map to accumulate errors
          def flat_map(self, f: Callable[[A], 'Validation[B, E]']) -> 'Validation[B, E]':
              if self.is_err():
                  return Validation(Err(self.error))  # Use a list for errors
              result = f(self.value)
              if result.is_err():
                  return Validation(Err(result.error))
              return Validation(Ok(result.value))

      # Usage: Validate user data
      def validate_age(age: int) -> Validation[int, str]:
          return Validation(Ok(age)) if age >= 18 else Validation(Err(["Age too low"]))

      def validate_name(name: str) -> Validation[str, str]:
          return Validation(Ok(name)) if name else Validation(Err(["Name required"]))

      # Chain with error accumulation
      result = validate_name("Alice").flat_map(lambda n: validate_age(20).map(lambda a: (n, a)))
      ```
    - *Extension Potential:* Integrate with `Reader` for config-based validation rules.
      Test with real data (e.g., JSON parsing).

- *Project: Immutable Data Structures with Lenses* (Intermediate)
  - *Why?* The codebase already has basic `Lens` in `functional_types.py`. Extend it for
    immutable collections like trees or graphs, which are FP staples.
  - *How to Extend:*
    - Build an immutable `Tree` ADT using the `adt` decorator from `functional_types.py`.
    - Add lenses for traversing/updating nested structures without mutation.
    - Code Sketch:
      ```python
      from functional_types import adt, Lens

      @adt('Tree')
      @dataclass(frozen=True)
      class Node:
          value: A
          children: List['Tree[A]']

      @adt('Tree')
      @dataclass(frozen=True)
      class Leaf:
          value: A

      # Lens for children
      children_lens = Lens(
          getter=lambda node: node.children if isinstance(node, Node) else [],
          setter=lambda node, new_children: Node(node.value, new_children) if isinstance(node, Node) else node
      )

      # Usage: Update deeply nested value immutably
      tree = Node(1, [Leaf(2), Node(3, [Leaf(4)])])
      updated = children_lens.modify(tree, lambda kids: [kid.map(lambda v: v + 1) for kid in kids])  # Assuming Tree has map
      ```
    - *Extension Potential:* Add `Traversable` instances for trees,
      or integrate with `State` for stateful traversals.

- *Project: FP Web Server or CLI Tool* (More Ambitious)
  - *Why?* Use `IO` and `AsyncIO` from `functional.py` for side-effectful apps,
    like a simple HTTP server or command-line parser.
  - *How to Extend:* Combine `Reader` for config injection, `State` for app state,
    and `IO` for I/O. Use `asyncio` for async endpoints.
    - Example: A CLI tool that reads files, processes them functionally, and writes
      outputs using `io_read_file` and `io_write_file`.
  - *Related Projects to Inspire:* Look at `dry-python/returns` (GitHub: dry-python/returns)
    for FP error handling, or `effect` (GitHub: python-effect/effect) for effect systems.

- *Other Ideas:* 
  - Add parser combinators (build on `Result` for safe parsing).
  - Integrate with external libs like `pydantic` for FP-style data models.
  - Create a testing framework using `State` for mock environments.

These are practical, testable, and showcase FP benefits like composability and safety.


### 2. Simpler Extension: Relating FP Concepts to OO/Imperative Constructs

Many developers come from OO/imperative backgrounds (e.g., Java, C#, or vanilla Python), so bridging the
gap reduces the learning curve. You could add this as docstrings, a README section, or even a new module
like `functional_bridge.py` with examples.

Here's how key concepts from your codebase map to common OO/imperative patterns:

- *Maybe (from `functional_core.py`)*:
  - *Imperative/OO Equivalent:* Null checks or `Optional` types in Java/Python.
    Instead of `if x is not None: do_something(x)`, use `maybe(x).map(do_something).get_or_else(default)`.
    This avoids null pointer exceptions (the "billion-dollar mistake").
  - *Relation:* In OO, this is like the Null Object Pattern--treat absence as a valid case without crashes.
  - *Example Bridge:*
    ```python
    # Imperative
    if user:
        greet = f"Hello, {user.name}"
    else:
        greet = "Hello, Guest"

    # FP (using Maybe)
    greet = maybe(user).map(lambda u: f"Hello, {u.name}").get_or_else("Hello, Guest")
    ```

- *Result (from `functional_core.py`)*:
  - *Imperative/OO Equivalent:* Try-catch blocks for error handling. Instead of
    `try: result = func(); except: handle_error()`, use `safe_func().map(process).get_or_else(default)`.
  - *Relation:* Similar to checked exceptions in Java or error codes in C. Encourages explicit error paths,
    unlike exceptions which can jump unpredictably.
  - *Example:* Your `safe_divide` is like wrapping division in try-except.

- *Monads like IO/State/Reader (from `functional.py`)*:
  - *Imperative/OO Equivalent:* Method chaining (e.g., fluent interfaces in OO like Java's Stream API)
    or imperative loops with variables. `IO` is like deferring side effects (e.g., lazy evaluation in OO via lambdas).
  - *Relation:* In imperative code, state is mutated globally; `State` threads it explicitly
    like passing parameters in OO dependency injection. `Reader` is pure DI (e.g., like Spring's @Autowired but functional).
  - *Example Bridge:*
    ```python
    # Imperative (mutable state)
    counter = 0
    def increment():
        global counter
        counter += 1
        return counter

    # FP (using State monad)
    increment_state = state_get().map(lambda c: c + 1).flat_map(state_put)  # Threads state safely
    ```

- *Type Classes (Functor, Monad from `functional_types.py`)*:
  - *Imperative/OO Equivalent:* Interfaces or abstract classes (e.g., Java's Iterable for foldable structures).
    `map` is like LINQ in C# or stream operations.
  - *Relation:* OO polymorphism via inheritance; FP uses protocols for ad-hoc polymorphism without modifying classes.

- *ADTs and Pattern Matching (from `functional_types.py`)*:
  - *Imperative/OO Equivalent:* Enums or sealed classes with switch/if-else chains.
    Pattern matching replaces visitor patterns in OO.
  - *Relation:* Safer than OO downcasting; exhaustiveness checks prevent missed cases.

This mapping could be a blog post or tutorial extending the project--super accessible!


### 3. Advanced Extension: Algebraic Effects

Algebraic effects aren't native to Python--they're more common in research languages like Eff or Koka.
They generalise exceptions: effects (e.g., "read file" or "log") are declared and handled separately,
allowing resumable computations.

- *Why Extend Here?* Your codebase has monads like `IO` for effects; algebraic effects build on this
  by making handlers composable and allowing multiple effect types in one computation.
- *Challenges:* Python lacks continuations, so we'd simulate with monads or generators.
  Performance might suffer for large apps.
- *How to Extend:*
  - Add an `Effect` monad in `functional.py` that supports handlers for custom effects (e.g., IO, State).
  - Use a free monad pattern to represent effects as data.
  - Code Sketch (Basic Simulation):
    ```python
    from functional_types import Functor, Monad  # For type classes

    @dataclass
    class Effect(Generic[A]):  # Base effect
        kind: str  # e.g., 'IO', 'Log'
        args: Any

    class FreeMonad(Monad[A]):  # Simulate algebraic effects with free monad
        def __init__(self, value: Union[A, Effect[A]]):
            self.value = value

        def bind(self, f: Callable[[A], 'FreeMonad[B]']) -> 'FreeMonad[B]':
            if isinstance(self.value, Effect):
                return FreeMonad(Effect(self.value.kind, lambda cont: self.value.args(cont).bind(f)))  # Resume
            return f(self.value)

    # Handler interprets effects
    def handle_io(effect: Effect):
        if effect.kind == 'IO':
            return effect.args()  # Perform actual IO

    # Usage
    def read_file_eff(path): return FreeMonad(Effect('IO', lambda: open(path).read()))
    program = read_file_eff('file.txt').bind(lambda content: FreeMonad(content.upper()))
    result = handle_io(program.value)  # Interpret
    ```
  - *Extension Potential:* Add multi-effect support (e.g., IO + Logging). Inspire from libs
    like `python-effect` or research papers on free monads.

Going even further, build a compiler which implements some of the concepts from modern
functional languages .. start with e.g. the [funlang vm](./vm/).


#### Reading


- Hudak, P. (2000). *The Haskell school of expression: Learning functional
  programming through multimedia*. Cambridge University Press.
  - A practical introduction to functional programming using Haskell, this
  book emphasizes clear development of core FP concepts alongside hands‑on
  examples. It guides readers from basic functional techniques to more advanced
  topics, showing how Haskell’s type system and abstraction mechanisms support
  robust and expressive software design.

- Thompson, S. (1999). *Haskell: The craft of functional programming* (2nd ed.).
  Addison‑Wesley.
  - A foundational text on Haskell and functional programming, this book presents
  the language’s syntax and semantics with a focus on developing correct, elegant
  programs. It covers functional abstractions, types, and data structures, and
  integrates detailed examples that illustrate how functional design leads to
  modular and maintainable code.

- Tran, M. Q. (2019). The art of functional programming. Wiley.
  - A deep dive into functional programming, this book explores the underlying
  principles and practices of FP, while addressing real-world challenges and
  solutions. It introduces functional programming in an accessible way, focusing
  on techniques for writing modular and reusable code.

![Hudak](./../../assets/image/hudak.png)
![Thompson](./../../assets/image/thompson.png)
