
## A Minimal Scheme (improved of the improved): Schem

### Map and Reduce in a Functional Context

The `builtin_map` and `builtin_reduce` functions implement higher-order functions similar to
those found in Scheme or Common Lisp.

- `map` applies a given function to each element in a list and returns a new list of results.
  It ensures the function is evaluated correctly, either as a built-in function or an interpreted Lisp function.
- `reduce` folds a list using an accumulator. It recursively applies a function to the current
  accumulator and the next element, updating the accumulator each step.

These implementations mirror functional languages but use explicit memory management and linked
lists instead of native array operations.


### Dynamic Scope and Environment Handling

Variable scoping is implemented using an environment chain (Environment). Each function call can
introduce a new environment, linked to its parent. This allows for lexical scoping of variables,
meaning functions can access bindings from outer scopes. The function `env_lookup` traverses
this chain to find the variable binding.


### Lisp as a Meta-Language

This interpreter allows Lisp functions to be defined dynamically, including lambda expressions.
The example in `run_tests` demonstrates defining a square function using lambda and then applying
it using map. This ability to define functions at runtime showcases Lisp's homoiconicity, where
code is data and can be manipulated at runtime.


### Interpreted vs Built-in Functions

The interpreter distinguishes between built-in and interpreted functions:
- Built-ins, such as + and *, are defined in C (builtin_add, builtin_mul).
- Interpreted functions (e.g. lambda expressions) are stored as LispFunction
  objects with an associated environment.

When evaluating an interpreted function, the interpreter creates a new environment with the
function's parameters bound to arguments before executing the body.


### Going Further ..

While the Scheme/Lisp interpreter demonstrates fundamental Lisp concepts, it has several
fragile aspects and areas for improvement.

__1. Fragile Memory Management__
- Manual Garbage Collection: The mark-and-sweep garbage collector, while functional, lacks
  automatic triggering. If `gc_collect` isn't called at the right time, memory leaks or
  excessive memory consumption can occur. Ideally, garbage collection should be triggered
  automatically when a memory threshold is reached.
- No Reference Counting: Some Lisp implementations use reference counting to reduce the
  need for full garbage collection sweeps. This would prevent unnecessary heap usage between
  full GC cycles.

__2. Lack of Proper Error Handling__
- Many functions assume valid input and do not check for NULL pointers or malformed Lisp
  expressions. A malformed list (e.g. (1 . 2 3)) could cause undefined behavior.
- The interpreter should have explicit error reporting, returning structured error messages
  instead of crashing. Right now, errors might be caught implicitly by the system (segfaults)
  rather than gracefully handled.
- Example: `env_lookup` should return an explicit "unbound variable" error rather than
  returning NULL and causing a crash later.

__3. Missing Tail-Call Optimisation (TCO) for All Recursive Cases__
- While `eval_tail_recursive` attempts tail-call optimisation, it might not handle all cases.
  Specifically, nested recursive calls `((define (fact n) (if (= n 0) 1 (* n (fact (- n 1))))))`
  may still overflow the stack.
- A proper TCO implementation would rewrite recursive calls into iteration, rather than just
  avoiding extra stack frames.

__4. Limited Standard Library and Built-ins__
The interpreter lacks essential Lisp functions such as:
- List manipulation (filter, foldr, reverse)
- String handling (there's no string?, string-length, concat)
- Input/Output support (reading/writing files, interacting with the OS)
Without these, writing non-trivial Lisp programs is difficult.

__5. Lexical Scope is Limited__
- While environments support function scoping, closures may not work fully if variables are
  captured outside their original scope. For example:
```lisp
(define (make-adder x) (lambda (y) (+ x y)))
```
If x is not retained in the closure, the function may not behave as expected.

__6. No Macro System__
- Lisp's power comes from macros, which allow modifying code before evaluation. The interpreter
  lacks a macro system (define-macro), limiting metaprogramming abilities.

__7. Performance Issues__
- Linked lists for everything: Lists are dynamically allocated and traversed linearly, making
  operations like map and reduce inefficient. Using a vector-based representation or optimising
  cons allocation could help.
- Interpreter overhead: Every function call involves dictionary lookups in Environment, making
  execution slower than it could be.


### Making the Code More Robust

__1. Improve Garbage Collection__
- Introduce automatic GC triggering based on heap usage.
- Implement reference counting for frequently used objects.
- Optimize mark phase by using a worklist instead of recursion (avoids stack overflow in deep graphs).

__2. Better Error Handling__
- Add an explicit LispError type with structured error messages.
- Ensure all functions check for NULL pointers or invalid syntax before processing.

__3. Implement a Proper Closure System__
- Modify LispFunction to store captured variables.
- Ensure closures can be passed around and invoked properly.

__4. Add a Macro System__
- Implement define-macro to allow AST transformations.
- Use Lisp itself to expand macros before evaluation.

__5. Implement Core Library__
- Add basic list operations (reverse, filter, assoc).
- Include string handling.
- Provide basic file I/O functions.

__6. Performance Optimisations__
- Use hash tables for environment lookups instead of linked lists.
- Cache frequently used built-in functions.
- Introduce bytecode compilation instead of interpreting raw lists.


### Projects That Build on This Code

Here are possible projects to expand the interpreter into a more powerful Lisp dialect.

__1. JIT-Compiling Lisp Interpreter__

Instead of interpreting expressions directly, compile them into bytecode or native machine
code using LLVM. This would make execution much faster. Example: implement a JIT compiler
that translates Lisp expressions into x86 instructions.

__2. Add a Standard Library__

Expand the Lisp environment to include a real stdlib. Functions like:
- Higher-order functions (filter, ..)
- Mathematical functions (trigonometry, logarithms)
- File I/O (open-file, read-line, write-line)

__3. Implement a REPL (Read-Eval-Print Loop)__

A proper interactive Lisp shell with:
- History and auto-completion
- Pretty-printing of results
- Debugger support (inspect stack frames, step through evaluation)

__4. Lisp-to-C Compiler__

Instead of interpreting Lisp expressions, generate C code from Lisp and compile it.
- Writing Lisp programs that compile to native executables.
- Using Lisp as an embedded scripting language in C projects.

__5. Multi-Threading and Concurrency__

Implement threading using green threads or C pthreads:
- Support parallel evaluation (pmap instead of map).
- Introduce message-passing concurrency.

__6. Implement a Full Lisp Dialect (Scheme or Common Lisp)__

Expand the interpreter into a full-fledged Lisp dialect, such as Scheme, by adding:
- First-class continuations (call/cc).
- Full numeric tower (integers, floats, rationals).
- Proper hygienic macros.


### Advice

While the current interpreter provides a good foundation, it is limited by memory management issues,
lack of lexical closures, poor error handling, and missing built-in functions.

For further development, a Lisp-to-C compiler, JIT compilation, macro system, and a richer standard
library would turn it into a usable language rather than just a toy interpreter.
