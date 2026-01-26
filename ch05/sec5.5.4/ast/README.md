
## AST and Its Role in Compilation

An Abstract Syntax Tree (AST) is a structured, hierarchical representation
of a program where irrelevant syntactic details (such as parentheses, commas,
or exact keywords) are removed, and only the *essential structure* of the
program is preserved. It is the main bridge between parsing (syntax) and
later compilation phases (semantic analysis, optimisation, code generation).

You can think of the AST as:
- More abstract than a parse tree.
- Less abstract than a fully semantic or typed representation.
- The compiler's "working model" of the program.

Its main purposes are:

- Represent program structure in a convenient, manipulable form.
- Serve as input to semantic analysis (type checking, name resolution).
- Act as a basis for optimisations.
- Act as a source for code generation.
- Enable tooling: linters, refactorers, formatters, static analysers.

The AST is not just a data structure. It is a design decision:
* How much meaning do you want in your tree?
* Where do you draw the line between syntax and semantics?
* When does your AST stop being an AST and become an IR?

That boundary is one of the deepest and most educational parts in compiler design.


### What an AST Typically Contains

Minimal AST:
- Node type (e.g. `BinaryExpr`, `IfStmt`, `FunctionDecl`)
- Child nodes
- Source position (line, column, file)

Often added:
- Identifier names
- Literal values
- Operator kinds
- Block structures
- Statement vs expression distinctions

Later phases often extend it with:
- Symbol references (links to symbol table entries)
- Type information
- Scope information
- Control-flow metadata

So an AST often *evolves* during compilation.



### The Zone Between Syntax and Semantics

This is one of the most interesting aspects.

Syntax is about:
- Grammar
- Structure
- Valid token sequences

Semantics is about:
- Meaning
- Types
- Variable binding
- Evaluation rules

The AST sits in between:

Purely syntactic AST:
```
a + b
```
is just:

```
BinaryExpr("+")
  Identifier("a")
  Identifier("b")
```
Semantically enriched AST:
```
BinaryExpr("+", type=int)
  Identifier("a", symbol=Var(a:int))
  Identifier("b", symbol=Var(b:int))
```
This raises design questions:
- Should type info live in the AST?
- Should symbol bindings live in the AST?
- Should the AST be immutable?
- Should you have multiple trees: AST -> Typed AST -> IR?

This “gray zone” is where many compiler designs differ.



### What an AST Can Contain (Depending on Design)

Some compilers keep ASTs minimal and push semantics elsewhere.
Others turn the AST into a semantic graph.

Possible additions:
- Types on every expression
- Constant folding results
- Desugared constructs
- Scope links
- Control-flow edges
- Data-flow information

At some point it stops being an AST and becomes an [IR](./../../sec5.7/IR/).



### Alternatives to ASTs

ASTs are not the only representation:
1. Parse Tree
- Direct grammar structure
- Too verbose for most compiler work
2. Typed AST
- AST + semantic annotations
3. IR (Intermediate Representation)
Examples:
- Three-address code
- SSA form
- LLVM IR
More suitable for optimization and code generation.
4. Graph-based IR
- Control-flow graphs (CFG)
- Data-flow graphs (DFG)
- Used for advanced analysis
5. Concrete Syntax Tree (CST)
- Preserves formatting and tokens
- Used in refactoring tools and formatters



### Project Ideas

All projects assume you implement a tiny language
(expressions + variables + functions are enough).



#### Project 1: From Parse Tree to AST

You implement:
- A parser that builds a parse tree.
- A transformer that converts it into an AST.

Focus:
- Removing syntactic noise.
- Choosing node types.
- Designing a clean tree structure.

Questions you answer:
- What grammar constructs disappear?
- What structure remains essential?



#### Project 2: AST Visualization Tool

You build:
- An AST printer (ASCII tree or Graphviz).

Example:
```
IfStmt
 ├─ Condition
 │   └─ BinaryExpr "<"
 │       ├─ Identifier "x"
 │       └─ Literal 10
 └─ ThenBlock
     └─ ...
```
You learn:
- How structure reflects language semantics.
- How different AST designs look visually.



#### Project 3: Syntax-Only vs Semantic AST

You create two versions:
1. Pure AST
2. Annotated AST

Then you compare:

|Aspect|Pure AST|Annotated AST|
|------|--------|-------------|
|Simplicity|High|Lower|
|Power|Limited|High|
|Mutability|Easy|Harder|

This directly explores the syntax–semantics boundary.



#### Project 4: Name Resolution Pass

You implement:
- A symbol table
- A traversal that:
- Binds identifiers to declarations
- Annotates AST nodes

You experience:
- How AST becomes semantic
- Why many compilers extend AST nodes



#### Project 5: Type Checker on AST

You add:
- Types to expressions
- Error reporting

You answer:
- Is the AST still “syntax”?
- Or has it become semantic IR?



#### Project 6: AST Rewriting and "Desugaring"

You transform:
```
for i in range(0, n):
    body
```
into:
```
i = 0
while i < n:
    body
    i = i + 1
```
You see:
- ASTs are not static.
- They are rewritten to simplify later phases.



#### Project 7: Compare AST with IR

You generate:
- AST
- A simple three-address code IR

Then compare:

AST:
```
a + b * c
```
IR:
```
t1 = b * c
t2 = a + t1
```
You learn:
- Why AST is great for structure.
- Why IR is better for optimisation.



#### Project 8: CST vs AST Tool

You build:
- A CST (Concrete Syntax Tree) that preserves formatting.
- An AST that ignores it.

Then you try:
- Reformatting code from CST
- Type checking from AST

You understand why tools use different trees.



