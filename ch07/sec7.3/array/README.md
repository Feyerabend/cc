
## History of the K Programming Language

K is a concise, array-oriented programming language developed by Arthur Whitney
in the early 1990s as a successor to APL (A Programming Language) and A+. It was
designed for high-performance data processing, particularly in finance and big data
applications, emphasising brevity, vector operations, and implicit parallelism.
K's syntax is extremely terse--often using single characters for operations--which
makes it powerful but notoriously hard to read for newcomers
(sometimes called "write-once, read-never" code).

- *Milestones*:
  - *1993*: First version of K released by Whitney at Morgan Stanley.
  - *Mid-1990s*: K2 and K3 evolved, with improvements in database integration
    (leading to kdb+, a time-series database used in finance).
  - *2000s–Present*: Commercial versions like Kx Systems' kdb+ became industry
    standards for real-time analytics. Open-source variants and interpreters
    (like oK, ngn/k) emerged to make K more accessible.
  - K influenced languages like J (by Ken Iverson and Roger Hui) and
    Q (a more readable wrapper around K for kdb+).

K's philosophy prioritises speed and expressiveness: operations are applied to
entire arrays (vectors) at once, avoiding explicit loops. It's used in high-frequency
trading, genomics, and sensor data processing due to its efficiency.


### Overview of K Implementations

These files implement a subset of K in Python, focusing on core array operations,
monadic/dyadic functions, and data structures like lists and dictionaries. They
don't cover the full K language (e.g., no adverbs like `/` for fold or full database
support) but still provide a functional interpreter for learning and experimentation.

- *Core Features Supported*:
  - *Atoms and Vectors*: Scalars (ints, floats, bools, strings) and lists (vectors)
    with rank polymorphism (operations adapt to scalar/vector inputs).
  - *Monadic Operations*: Single-argument functions like `+` (sum), `-` (negate),
    `!` (iota/generate sequence), `#` (length), `|` (reverse), etc.
  - *Dyadic Operations*: Two-argument functions like `+` (add), `*` (multiply),
    `@` (index), `?` (find/unique), etc.
  - *Data Structures*: Nested lists, dictionaries (e.g., `["a":1;"b":2]`),
    and basic lambdas (e.g., `{x+y}`).
  - *Error Handling*: Custom errors for type, rank, domain, etc.
  - *REPL*: Interactive shell for testing expressions.
  - *Parallelism (in parallel version)*: Uses Python's multiprocessing for
    large vector operations (e.g., sum, min/max) when arrays exceed a threshold.

The implementations are educational and not optimized for production-scale performance
like commercial K (which is compiled and runs at near-C speeds).

Here's a table comparing the key files:

| File Name                  | Purpose | Key Differences from Base | Dependencies |
|----------------------------|---------|---------------------------|--------------|
| *k_interpreter.py* | Base interpreter implementation. | N/A (core version). | None (pure Python). |
| *k_interpreter_parallel.py* | Enhanced interpreter with parallel execution for large arrays. | Adds multiprocessing/threading for ops like sum, min, max on vectors > threshold (default: 1000 elements). Configurable (enable/disable, workers, threshold). | Requires `multiprocessing` and `concurrent.futures`. |
| *k_examples.py* | Examples and demo script for the base interpreter. | Runs predefined examples/tests; no parallelism. | Imports from `k_interpreter.py`. |
| *k_tests.py* | Test suite for the parallel interpreter. | Includes serial vs. parallel correctness checks, performance benchmarks, and edge cases. | Imports from `k_interpreter_parallel.py`. |


### Using the K Implementations

#### Running the Interpreter (REPL Mode)
- For base: `python k_interpreter.py`
- For parallel: `python k_interpreter_parallel.py`
- In REPL:
  - Enter expressions like `[3, "+", 4]` (list form) or `(1;2;3)+10` (string form).
  - Assign variables: `x:(1;2;3)` then `+x` (sums to 6).
  - Help: Type `help` for operation list.
  - Vars: Type `vars` to see defined variables.
  - Exit: Type `exit`.
- Parallel-specific commands (in parallel REPL):
  - `parallel` : Show config.
  - `parallel on/off` : Enable/disable parallelism.
  - `parallel threshold N` : Set min array size for parallel (e.g., 1000).
  - `parallel workers N` : Set CPU workers (default: all cores).

#### Running Scripts/Files
- Pass a file as argument: `python k_interpreter.py my_script.k`
  - Script lines are evaluated sequentially (ignores comments with `#`).
- Example script content:
  ```
  x:10
  y:(1;2;3)
  x + y  # Outputs [11, 12, 13]
  ```

#### Running Examples and Tests
- Examples: `python k_examples.py` – Runs demos grouped by category
  (arithmetic, vectors, etc.) and prints results with ✓/✗.
- Tests: `python k_tests.py` – Runs full suite (basic ops, parallel,
  serial vs. parallel, edges). Outputs pass/fail summary and
  performance benchmarks (e.g., speedup for large arrays).

#### Expression Syntax
- *List Form*: Use Python lists, e.g., `[[1,2,3], "+", 10]` --> [11,12,13].
- *String Form (K-like)*: `(1;2;3)+10` --> [11,12,13].
- Dictionaries: `["a":1;"b":2]` (keys can be strings, ints, etc.).
- Nested: `((1;2);(3;4))+10` --> [[11,12],[13,14]].
- Errors: Handled gracefully in REPL (e.g., "type error: cannot add str and int").


### How to Use It in Practice

These interpreters are great for:
- *Learning K/APL Concepts*: Experiment with vector ops without installing full K.
  E.g., compute sum of squares: `+ (!10) * (!10)` --> 285.
- *Prototyping Data Processing*: Handle small-to-medium datasets (e.g., CSV-like lists).
  For large data, parallel version speeds up ops like summing 100k+ elements
  (potential 2-8x speedup on multi-core CPUs).
- *Embedding in Python*: Import and use `evaluate_expression(expr)`
  in your scripts for K-style computations.
  - Example:
    ```python
    from k_interpreter_parallel import evaluate_expression, register_standard_operations
    register_standard_operations()
    result = evaluate_expression(["+", list(range(100000))])  # Parallel sum
    ```
- *Performance Testing*: Use `k_tests.py` to benchmark serial vs. parallel on your hardware.
  Adjust threshold/workers for optimal speedup (e.g., lower threshold for I/O-bound tasks).
- *Extensions*: Add custom operations by registering new `Operation` instances (e.g., for stats or ML primitives).
- *Limitations in Practice*: Not for production (slow compared to native K; no GPU/optimised numerics).
  For real-world, consider ngn/k (fast C impl) or kdb+ trial.

Practical Tip: Start with small expressions in REPL. For parallelism, test with large arrays
(e.g., `+ !100000`) and monitor CPU usage—enable threads for I/O, processes for CPU-bound.


### About Implementations

- *Base (k_interpreter.py)*: ~800 lines. Clean, recursive evaluator with type checks.
  Uses Python's built-ins (e.g., `sum`, `min`) for ops. Focuses on correctness;
  serial execution only. Good for teaching—clear separation of registry, evaluator, and ops.
- *Parallel (k_interpreter_parallel.py)*: ~1000 lines. Builds on base with `parallel_map`,
  `parallel_reduce` using `ProcessPoolExecutor` (default) or threads. Config via `ParallelConfig` class.
  Handles fallbacks (e.g., if pickling fails). Adds utilities like `chunk_list` for workload distribution.
- *Examples (k_examples.py)*: Demo script with 18+ sections (arithmetic to advanced).
  Uses `run_example` to test/print, covering 80%+ of ops. Educational—shows real K idioms
  like "sum of squares" or matrix transpose.
- *Tests (k_tests.py)*: Suite with sections (basic, parallel, serial-vs-parallel, edges).
  Uses `run_test` for assertions; benchmarks speedup (e.g., 100k elements). Covers booleans,
  strings, dicts, and errors. Parallel tests use low threshold (100) for CI-friendly runs.

NOTE: The parallel version shows practical concurrency in Python, but Python's GIL limits
thread speedup for CPU tasks—use processes for true parallelism. Overall, they're a starting
point for forking/extending a K interpreter.

