
## Property-Based Testing Framework in C

A modular C implementation of property-based testing concepts:

- Property-based testing concepts in systems programming
- Strategy pattern in C using function pointers
- Manual memory management in testing frameworks
- Exception handling without C++ exceptions
- Compositional design with type-safe (ish) generics


### Project Structure

```
property-testing-c/
├── src/
│   ├── core/              # Core testing framework
│   │   ├── property_test.h
│   │   └── property_test.c
│   ├── strategies/        # Strategy implementations (modular)
│   │   ├── integer_strategy.{h,c}
│   │   ├── list_strategy.{h,c}
│   │   ├── tuple_strategy.{h,c}
│   │   ├── string_strategy.{h,c}
│   │   └── oneof_strategy.{h,c}
│   └── types/            # Shared data structures
│       ├── types.h
│       └── types.c
├── examples/             # Numbered examples showing progression
│   ├── 01_algebraic_properties.c
│   ├── 02_sorting_properties.c
│   ├── 03_compositional_generation.c
│   └── 04_string_properties.c
|       ...
├── build/               # Build artifacts (generated)
├── docs/                # Documentation
│   ├── README.md
│   └── ROADMAP.md
└── Makefile
```

### Quick Start

```bash
make              ## Build library and all examples
make test         ## Run all examples
make structure    ## Show project structure
make clean        ## Clean build artifacts
```

### Implemented Components

#### Core Framework (`src/core/`)
- Strategy pattern interface
- Test execution engine
- Shrinking algorithm
- Exception handling (setjmp/longjmp)
- Test result reporting

#### Data Types (`src/types/`)
- **IntList**: Dynamic integer arrays
- **String**: Dynamic strings with append operations
- **Tuple2/Tuple3**: Generic tuples for composition

#### Strategies (`src/strategies/`)

| Strategy  | Purpose                                  | Book Section                |
|-----------|------------------------------------------|-----------------------------|
| *Integer* | Random integer generation                | Implementation Architecture |
| *List*    | List generation with element shrinking   | Implementation Architecture |
| *Tuple*   | Compose multiple strategies into tuples  | Compositional Generation    |
| *String*  | String generation with 3-phase shrinking | Custom Shrinking Strategies |
| *OneOf*   | Choose randomly between strategies       | Compositional Generation    |

#### Examples (`examples/`)

| Example                       | Tests                                       | Book Concepts            |
|-------------------------------|---------------------------------------------|--------------------------|
| *01_algebraic_properties*     | Integer addition properties                 | Algebraic Properties     |
| *02_sorting_properties*       | Sorting invariants                          | Properties vs. Examples  |
| *03_compositional_generation* | Geometric shapes (Point, Rectangle, Circle) | Compositional Generation |
| *04_string_properties*        | String concatenation monoid                 | Algebraic Properties     |

### Example Output

```
$ make test

Running Example 1: Algebraic Properties
---------------------------------------
Running: Integer Addition Associativity
  OK PASSED (100 examples in 0.000s)

Running: Integer Addition Commutativity
  OK PASSED (100 examples in 0.000s)

..
```

### Design Principles

#### Modularity
- Each strategy is a separate, independently compilable module
- Core framework is stable and doesn't change as strategies are added
- Strategies can be composed freely

#### Scalability
- New strategies go in `src/strategies/`
- New examples go in `examples/` with sequential numbering
- Each component has a clear, single purpose

#### Conceptual Clarity
- Numbered examples show progression from simple to complex
- Directory structure mirrors conceptual organization
- Each strategy maps to a specific book section

### Adding New Components

#### Adding a Strategy

1. Create header: `src/strategies/my_strategy.h`
2. Create implementation: `src/strategies/my_strategy.c`
3. Add to `Makefile` SRC_STRATEGIES
4. Create example in `examples/NN_my_example.c`
5. Add example to `Makefile` EXAMPLES

#### Adding an Example

1. Create `examples/NN_description.c` (use next number)
2. Include relevant strategy headers
3. Define property functions
4. Add target to Makefile
5. Add to `make test` sequence


### Key Differences from Python

| Aspect               | Python (Hypothesis) | C (This Implementation)    |
|----------------------|---------------------|----------------------------|
| Memory               | Automatic GC        | Manual management          |
| Types                | Dynamic             | Static with void*          |
| Exceptions           | try/except          | setjmp/longjmp             |
| Iteration            | Lazy generators     | Eager allocation           |
| Strategy Composition | @given decorator    | Explicit constructor calls |



