
## CEK Machine: A Lambda Calculus Interpreter

The *CEK machine* is an abstract machine for evaluating
lambda calculus expressions. It's named after its three main components:

- *C* (Control): The term currently being evaluated
- *E* (Environment): A mapping from variable names to their values
- *K* (Kontinuation): The stack of pending computations

The CEK machine is a *small-step operational semantics*--it breaks down
evaluation into individual atomic steps, making the evaluation process
explicit and observable.


### Why Does It Exist?

#### Historical Context

The CEK machine was introduced by Matthias Felleisen and Daniel P. Friedman
in the 1980s as part of their work on semantic engineering and programming
language theory. It emerged from a lineage of abstract machines designed to model computation:

1. *SECD Machine* (1964): Peter Landin's stack-based machine for lambda calculus
2. *CEK Machine* (1986): Felleisen & Friedman's refinement using explicit continuations
3. *CESK Machine*: Extended version adding a Store component for modeling mutable state

#### Purpose and Applications

The CEK machine serves several important purposes:

*1. Pedagogical Tool*
- Makes evaluation order explicit and observable
- Helps students understand closures, environments, and continuations
- Demonstrates tail-call optimization naturally

*2. Semantic Foundation*
- Provides a rigorous mathematical model for lambda calculus evaluation
- Forms the basis for proving correctness of compilers and optimizations
- Helps reason about program equivalence

*3. Implementation Technique*
- Many interpreters and compilers use CEK-like structures internally
- The continuation component naturally handles control flow
- Explicit environments model lexical scoping precisely

*4. Research Platform*
- Easy to extend with new language features (state, exceptions, delimited continuations)
- Clear separation of concerns makes modifications straightforward
- Useful for exploring different evaluation strategies


### How Does It Work?

#### Core Components

*Control (C)*: The term being evaluated
```
Term = Variable(name)
     | Lambda(param, body)
     | Application(function, argument)
```

*Environment (E)*: Maps variables to values
```
Environment = { variable_name -> Value }
```

*Kontinuation (K)*: Represents "what to do next"
```
Kont = Halt                                    // Done!
     | Arg(argument_term, saved_env, next_k)   // Need to eval argument
     | Fun(function_value, next_k)             // Need to apply function
```

#### Evaluation Steps

The machine transitions between states `⟨Control | Environment | Kontinuation⟩`:

*1. Variable Lookup*
```
⟨x | E | K⟩  ->  apply_kont(K, E[x])
```
Look up the variable in the environment and pass its value to the continuation.

*2. Lambda Abstraction*
```
⟨λx.body | E | K⟩  ->  apply_kont(K, Closure(x, body, E))
```
Create a closure capturing the current environment.

*3. Function Application*
```
⟨(f a) | E | K⟩  ->  ⟨f | E | Arg(a, E, K)⟩
```
Evaluate the function first, saving the argument for later.

*4. Continuation Application*

When we have a value and need to continue:

- *Halt*: Return the value (done!)
- *Arg(a, E', K')*: Now evaluate the argument: `⟨a | E' | Fun(value, K')⟩`
- *Fun(closure, K')*: Apply the function by extending its environment: `⟨body | E'[param->value] | K'⟩`

#### Example Trace

Let's trace `(λx.x) 7`:

```
⟨(λx.x) 7 | {} | Halt⟩
-> ⟨λx.x | {} | Arg(7, {}, Halt)⟩
-> apply_kont(Arg(...), <λx.x>)
-> ⟨7 | {} | Fun(<λx.x>, Halt)⟩
-> apply_kont(Fun(...), 7)
-> ⟨x | {x->7} | Halt⟩
-> apply_kont(Halt, 7)
-> 7  ✓
```

### Key Features

#### Tail Call Optimization

The CEK machine naturally implements tail-call optimization. When a function call is in tail position, no new continuation frame is added--the current continuation is reused. This means infinite loops like `(λf.f f)(λf.f f)` won't overflow the stack.

#### Closures and Lexical Scoping

Closures capture their defining environment, ensuring variables are resolved according to lexical scope:

```scheme
((λx. (λy. x)) 42)  ; Returns a closure that remembers x=42
```

#### Explicit Control Flow

Unlike evaluators that use the host language's call stack, the CEK machine makes all control flow explicit through the continuation component. This makes it easy to:
- Add exception handling
- Implement first-class continuations (call/cc)
- Support coroutines and generators

### Implementation Details

#### Python Version (`cek.py`)

- Pure functional implementation using immutable dataclasses
- Step-by-step tracing for educational purposes
- Church encoding examples (numerals, booleans, pairs)
- Pretty-printing of Church-encoded values

*Run it:*
```bash
python cek.py
```

#### C Version (`cek.c`)

- Imperative implementation with explicit memory management
- Custom garbage collector using mark-and-sweep
- Optimized for performance
- Test suite with lambda calculus examples

*Compile and run:*
```bash
gcc -std=c99 -O2 cek.c -o cek
./cek
```

### Extensions and Variations

The basic CEK machine can be extended to support:

- *Primitive operations* (arithmetic, comparisons)
- *Mutable state* (CESK machine with Store component)
- *Exception handling* (additional continuation constructors)
- *First-class continuations* (call/cc operator)
- *Lazy evaluation* (modify continuation handling)
- *Type checking* (annotate values with types)

### Further Reading

*Foundational Papers:*
- Felleisen, M., & Friedman, D. P. (1986). "Control operators, the SECD-machine, and the λ-calculus"
- Felleisen, M. (1987). "The Calculi of Lambda-v-CS Conversion: A Syntactic Theory of Control and State in Imperative Higher-Order Programming Languages"

*Modern Treatments:*
- Dybvig, R. K. (2009). "The Scheme Programming Language" (Chapter on implementation)
- Friedman, D. P., & Wand, M. (2008). "Essentials of Programming Languages" (EOPL)

*Related Concepts:*
- Abstract machines (SECD, Krivine, ZAM)
- Continuation-passing style (CPS)
- Operational semantics
- Lambda calculus evaluation strategies
