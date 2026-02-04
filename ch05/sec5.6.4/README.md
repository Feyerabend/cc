
### Use of AST

Abstract Syntax Trees (ASTs) are a powerful representation of code structure,
enabling a wide range of analyses and transformations. ASTs are commonly used for:

- *Optimisations*: Transforming the AST to make the code faster, smaller, or
  more efficient (e.g., constant folding, constant propagation, expression
  simplification, loop optimisations).
- *Static Analysis*: Checking for errors or properties without running the
  code (e.g., type checking, reachability analysis, linting for style or bugs).
- *Code Generation/Transformation*: Converting the AST to another form (e.g.,
  transpiling to another language, minifying code, or generating bytecode).
- *Refactoring Tools*: Automated code changes like renaming variables or extracting methods.
- *Security Analysis*: Detecting vulnerabilities like potential overflows or injection risks.
- *Metrics and Visualisation*: Computing complexity metrics (e.g., cyclomatic complexity)
  or generating code diagrams.

To keep things simple we provide examples of AST-based optimisations and analyses.
Each example includes a new analyser or transformer class, runs it on a slightly
modified or similar AST, and prints results.

You can combine them (e.g., propagate constants then fold then simplify). For more
advanced uses, ASTs power tools like ESLint (JS linter), Clang (C++ optimiser), or
Python's ast module for meta-programming.


#### 1. Constant Folding

This traverses the AST to evaluate expressions that are purely constant (no variables),
replacing them with their computed value. This reduces runtime computations. For example,
`10 + 20` becomes `30`. It's a transformer that modifies the AST.
In a real compiler, you'd then generate code from the folded AST. The benefits are fewer
operations at runtime.


#### 2. Constant Propagation

This analysis propagates constant values through the code, replacing variables with their
constant values where possible. It's similar to liveness but forward-propagating.
Combined with folding, it can simplify more code. This code replaces variables with
constants where known, enabling further optimisations like folding. It's a sample of forward dataflow
analysis.


#### 3. Expression Simplification

Simplify expressions using rules like `x + 0 = x`, `x * 1 = x`, or `x - x = 0`.
This is another transformer, focusing on binary operations. This applies algebraic
rules recursively. It's lightweight and can be extended with more identities.


#### 4. Reachability Analysis

Similar to e.g. dead code, but for control flow: Identify statements that can never
be executed (e.g., code after an infinite loop or false condition).
This is *analysis*, not transformation.
This sample detects code that can't be reached due to control flow. In practice, pair it
with constant propagation for better detection of always-true/false conditions.

#### 5. Type Checking

Type checking is a static analysis technique that verifies the compatibility of types
in a program without executing it. Using an AST, we can traverse the nodes to infer types
for expressions and variables, check operations (e.g., ensuring operands for + are integers),
validate conditions (e.g., if/while expect booleans), detect undefined variables, and ensure
consistent variable usage (e.g., no assigning a bool to an int-typed variable).

The checker here detected the undefined variable, the mismatch when reassigning a bool to an
int-typed var, and the int used as a while condition (should be bool). It *inferred types*
for valid variables. Note that 'early_use' isn't in inferred types because the error prevented
type assignment, and 'z' is inferred as int from both branches. This is a basic monomorphic type
checker. For real languages, you'd handle more types (e.g., functions, polymorphism) or
use Hindley-Milner inference. Read up on this inference, as we will return to it many times.

