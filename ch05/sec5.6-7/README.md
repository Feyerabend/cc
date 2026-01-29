
## Semantic Analysis and Intermediate Code Generation

After syntactic analysis has been completed by the lexer and parser,
and possibly after an Abstract Syntax Tree (AST) has been constructed,
the next stage is semantic analysis and Intermediate Representation
(IR) generation. At this point, the compiler pipeline branches into
several possible directions depending on design choices and optimisation
goals. Common transformations include building graph-based representations
such as a Control Flow Graph (CFG), as well as converting the program
into forms like Static Single Assignment (SSA) or Three-Address Code (TAC)
for analysis and optimisation. There is no single mandatory path:
*different compilers follow different pipelines*, and code may pass
through several representations before final code generation.
Below are some details of these stages and representations.


### Core Representations

*Control Flow Graph (CFG)*
A CFG represents the flow of execution through a program. Each node is a
basic block (a sequence of instructions with one entry and one exit), and
edges represent possible control flow paths.

- *When to use*: Essential for almost all optimisation passes.
  Built early in compilation after parsing.
- *Pros*: Makes control flow explicit, enables dataflow analysis,
  straightforward to construct
- *Cons*: Doesn't capture data dependencies directly, can be
  complex for exception handling

*Three-Address Code (TAC)*
Each instruction has at most three operands: `result = operand1 op operand2`.
Example: `t1 = a + b`

- *When to use*: Common intermediate representation after parsing,
  before machine code generation
- *Pros*: Simple, uniform structure; easy to generate from ASTs;
  close to assembly but machine-independent
- *Cons*: Introduces many temporary variables; doesn't make data
  dependencies explicit

*Static Single Assignment (SSA)*
Each variable is assigned exactly once. Uses φ-functions at control flow
merge points to handle multiple definitions: `x3 = φ(x1, x2)`

- *When to use*: For sophisticated optimisations (constant propagation,
  dead code elimination, register allocation)
- *Pros*: Simplifies many optimisations; makes def-use chains explicit;
  enables sparse analysis algorithms
- *Cons*: More complex to construct and maintain; φ-functions don't directly
  correspond to machine instructions; conversion back from SSA adds complexity

*Abstract Syntax Tree (AST)*
Tree representation of the syntactic structure of source code, directly from parsing.

- *When to use*: First representation after parsing; good for source-level transformations
- *Pros*: Close to source code; natural for language-specific optimisations;
  preserves high-level structure
- *Cons*: Too high-level for many optimisations; inefficient for analysis


### Analysis Structures

*Dominator Tree*
Shows dominance relationships: node A dominates B if every path from entry to B goes through A.

- *When to use*: Computing SSA form, loop detection, code motion optimisations
- *Pros*: Captures structural properties efficiently; O(n) construction algorithms exist
- *Cons*: Doesn't capture all control dependencies

*Dependence Graph (DDG - Data Dependence Graph)*
Nodes are instructions/statements, edges represent data dependencies
(read-after-write, write-after-read, write-after-write).

- *When to use*: Instruction scheduling, parallelisation, vectorisation
- *Pros*: Makes data flow explicit; essential for reordering optimisations
- *Cons*: Can be large and complex; doesn't capture control flow

*Program Dependence Graph (PDG)*
Combines control and data dependencies in a single graph.

- *When to use*: Advanced optimisations like program slicing, partial evaluation
- *Pros*: Unified representation of both control and data flow; enables sophisticated transformations
- *Cons*: Complex to construct; large memory footprint; not needed for many common optimisations

*Call Graph*
Nodes are functions/procedures, edges represent function calls.

- *When to use*: Interprocedural analysis, inlining decisions, whole-program optimisation
- *Pros*: Essential for understanding program structure across functions
- *Cons*: Dynamic dispatch and function pointers make it imprecise;
  may need conservative approximations


## Specialised Representations

*Sea of Nodes*
Used in compilers like HotSpot JVM and GraalVM. Represents computation
as a graph where nodes are operations and edges are dependencies (data and control).

- *When to use*: Modern JIT compilers, when you want aggressive optimisation
- *Pros*: Very flexible; enables global code motion; natural representation for many optimisations
- *Cons*: Complex to implement; harder to map to machine code; less intuitive than CFG

*Continuation Passing Style (CPS)*
All control flow is made explicit through function calls with continuations.

- *When to use*: Functional language compilers, advanced control flow transformations
- *Pros*: Uniform representation of control flow; simplifies some optimizations
- *Cons*: Can explode code size; not natural for imperative languages

*LLVM IR*
The intermediate representation used by LLVM, which is in
SSA form but also includes type information and high-level constructs.

- *When to use*: When targeting LLVM infrastructure
- *Pros*: Well-documented; extensive optimisation passes available; strong ecosystem
- *Cons*: Still relatively low-level; LLVM-specific


### How They Work Together

A typical compilation pipeline might look like:

1. *Source Code -> AST* (parsing)
2. *AST -> TAC/IR* (lowering to simpler representation)
3. *Build CFG* from TAC
4. *Compute Dominator Tree* from CFG
5. *Convert to SSA* using dominators and CFG
6. *Build Dependence Graphs* for specific optimisations
7. *Optimisation passes* using SSA, CFG, and analysis structures
8. *Convert out of SSA* 
9. *Code generation* using CFG and possibly new analyses

For example:
- You might build a *call graph* for the whole program first to decide what to inline
- Then convert each function to *SSA* form for optimisation
- Use the *CFG* and *dominator tree* during SSA construction
- Build a *DDG* to schedule instructions optimally
- Use *def-use chains* (implicit in SSA) for dead code elimination


### Choosing Between Techniques

*Use CFG when*: You need basic flow analysis,
almost always constructed

*Use SSA when*: You want powerful optimisations
(constant propagation, dead code elimination, register allocation).
The overhead is worth it for optimising compilers.

*Use TAC when*: You want simplicity and are doing
straightforward compilation without heavy optimisation

*Use AST when*: Doing source-to-source transformations
or high-level language-specific optimisations

*Use PDG when*: Doing program slicing, security analysis,
or very sophisticated transformations

*Use dependence graphs when*: Scheduling instructions,
parallelising code, or vectorising loops


### Key Tradeoffs

*Precision vs. Cost*: More sophisticated representations (PDG, SSA) enable
better optimisations but cost more to construct and maintain.

*Generality vs. Optimisation*: Simple IRs (TAC, basic CFG) work for many
languages but limit optimisation potential. SSA and advanced graphs enable
aggressive optimisation.

*Construction complexity vs. Analysis simplicity*: SSA is harder to build
but makes many analyses trivial. TAC is easy to generate but requires more
complex analysis algorithms.

Most production compilers use a combination: they'll use AST for high-level
passes, convert to SSA for optimisation (relying on CFG, dominator trees,
and def-use chains), then lower to a machine-specific representation for code
generation. The exact combination depends on optimisation goals,
compilation speed requirements, and language characteristics.


