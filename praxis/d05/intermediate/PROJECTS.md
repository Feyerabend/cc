## Projects

### Compilers, Parsers, and Language Implementation

These projects guide you through building a complete language implementation,
from grammar to execution. The additions under `ch05/addition/` provide reference
material — especially `classic/`, `parsers/`, `interpreter/`, `prolog/`, and `vtable/`.

The pedagogy of this chapter reverses the usual order: you build first, then you
compare your construction against theory. Each project should be accompanied by
a short written reflection connecting what you built to a theoretical concept
encountered during the work.


#### Project 1: Expression Language Pipeline

*Objective:* Build a complete pipeline from source text to evaluated result for a
small arithmetic and variable language. This is the central project of chapter 5.

Work through these stages, keeping each as a separate, testable module:

*Stage 1 — Lexer:* Input is a string; output is a list of tokens (number literals,
identifiers, operators, parentheses). Write tests for each token type before implementing.

*Stage 2 — Parser:* Input is a token list; output is an AST. Use recursive descent.
Handle operator precedence and parentheses. Write tests for valid and invalid input.

*Stage 3 — Evaluator:* Input is an AST; output is a value. Handle variables with
an environment dictionary. Write tests for expressions with and without variables.

*Stage 4 — REPL:* Combine the three stages into a read-eval-print loop.

*Extension 1:* Add `if-then-else` as an expression (not a statement).
*Extension 2:* Add anonymous functions (`fun x -> expr`) and closures.
*Extension 3:* Add a type checker between the parser and evaluator.

See `ch05/addition/classic/PROJECT.md` for the full language grammar and
`ch05/addition/interpreter/` for a reference progression.

*Questions:*
- At which stage did you catch the most bugs in your design?
- What was the hardest part of implementing closures? What does a closure need to capture?
- How would you add `let x = expr in expr` without breaking existing features?


#### Project 2: Parser Comparison

*Objective:* Implement the same grammar using three different parsing strategies.
Compare the implementations by complexity, capability, and error quality.

Choose a grammar that is non-trivial but bounded: arithmetic with functions,
a simple configuration format, or a subset of a real language.

Implement it using:
1. *Recursive descent* (write by hand from the grammar).
2. *PEG / packrat* (see `ch05/addition/parsers/packrat/`).
3. *Earley* (see `ch05/addition/parsers/earley/`).

For each implementation:
- Count the lines of code.
- Test against 10 valid inputs and 5 invalid inputs.
- Compare the error messages produced for each invalid input.
- Measure parse time on a large (1000-token) input.

*Questions:*
- Which parser handles ambiguous grammars? Which does not?
- Which was easiest to write? Which produced the best error messages?
- What does the Earley parser give you that recursive descent does not?


#### Project 3: Mini Prolog Engine

*Objective:* Build a small Prolog-like inference engine that supports unification
and backtracking.

See `ch05/addition/prolog/mprolog.py` and `sprolog.py` as references. Build your own.

*Stage 1:* Implement unification. Two terms unify if they can be made identical by
substituting variables. Implement this as a function `unify(t1, t2, bindings) -> bindings | None`.

*Stage 2:* Implement a database of facts and rules. A fact is `parent(tom, bob).`
A rule is `grandparent(X, Z) :- parent(X, Y), parent(Y, Z).`

*Stage 3:* Implement backward chaining with backtracking. Given a query,
search the database for matching clauses and recursively prove their bodies.

*Test queries:*
- Family relationships: who are Tom's grandchildren?
- Reachability: which cities are reachable from city A?
- Sudoku: encode a 4x4 puzzle as constraints; solve by inference.

*Questions:*
- What is the difference between unification and equality testing?
- What causes the Prolog engine to backtrack? What is a "choice point"?
- What query causes your engine to loop forever? Can you detect this?


#### Project 4: SECD Machine Compiler

*Objective:* Compile a lambda calculus expression to SECD bytecode and execute it.

See `ch05/addition/am/secd/` for the SECD machine implementation.

*Stage 1:* Understand the SECD machine. Trace the execution of `(λx. x + 1) 5`
by hand: what are the Stack, Environment, Control, and Dump at each step?

*Stage 2:* Write a compiler that translates lambda calculus expressions into SECD
instruction sequences. The compiler is a recursive function over the AST.

*Stage 3:* Test with: identity function, addition, factorial (via recursive let),
and a higher-order function (e.g. `twice = λf. λx. f (f x)`).

*Questions:*
- Why does the SECD machine need four components rather than just a stack?
- What does the Dump hold? When is it used?
- How does environment lookup work in the SECD machine? What is the environment structure?


#### Project 5: OOP Compiler with Vtables

*Objective:* Extend the vtable-based OOP compiler in `ch05/addition/vtable/` with
one new feature: either inheritance or interfaces.

Study the existing pipeline: `lexer.py` → `parser.py` → `vtable_builder.py` →
`vtable.py` → `codegen.py`.

Choose one:

*Option A — Inheritance:*
- A class can extend another: `class Dog extends Animal`.
- `Dog` inherits all of `Animal`'s methods and can override them.
- The vtable for `Dog` starts with `Animal`'s entries and replaces overridden ones.
- Test that calling an overridden method dispatches to the right implementation.

*Option B — Interfaces:*
- An interface declares method signatures without implementations: `interface Drawable`.
- A class implements an interface: `class Circle implements Drawable`.
- The compiler checks that all interface methods are implemented.
- Test that calling an interface method on any implementing class works correctly.

*Questions:*
- How does the vtable structure change when you add inheritance?
- What is dynamic dispatch? What makes it "dynamic"?
- What would a *static* dispatch look like in the vtable model?
