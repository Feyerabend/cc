
## Elementary: Compiling in Practice

We begin with a straightforward implementation of a [mini](./mini/src/MINI.md) compiler designed to
handle basic arithmetic expressions. This simple compiler serves as an introductory example, illustrating
the fundamental components of the compilation process. It encompasses key stages such as lexical analysi
(tokenising the input), parsing (building a syntax tree), semantic analysis (ensuring correctness of operations),
and code generation (translating the syntax tree into executable code). Despite its simplicity, the
mini compiler provides a hands-on foundation for understanding the core principles of compiler construction.

From this starting point, we can systematically build upon our knowledge and skills to tackle more advanced
and complex examples. A natural progression is to explore a more substantial compiler for the educational
programming language [PL/0](./syntax/PL0.md). PL/0 is a well-known minimalist language often used for
teaching compiler construction (at least until some years ago). It introduces additional concepts like
variable declarations, procedures, control flow (such as loops and conditionals), and a more comprehensive
symbol table for managing scopes and identifiers. You might also have a look at a small
[PL/0 interpreter and compiler](./../../code/pl0/) to get a feeling how they work.

By transitioning from the mini compiler to PL/0, we expand our understanding of compiler design, delving
deeper into topics such as abstract syntax trees (ASTs), type checking (as we have only one it is minimal),
nested scopes, and procedural abstraction. Moreover, PL/0 provides an excellent platform to experiment
with optimisation techniques, error handling, and even extending the language's features. This incremental
approach allows learners to solidify their understanding of the compilation process while tackling
increasingly challenging problems in a structured and manageable way.

### Some changes

To begin our exploration of PL/0, we will make some modifications to its [grammar](./syntax/GRAMMAR.md) to
better align it with modern programming practices and simplify its usage. The first change involves
removing the "odd" keyword. In the original grammar, the "odd" keyword was used within conditional
statements to evaluate whether a given numeric expression (on the right-hand side of the condition)
was odd or even. If the expression was odd, the condition would evaluate to true; otherwise, it
would evaluate to false. While this feature is an interesting aspect of the language, its utility
is limited, and removing it streamlines the grammar while reducing potential confusion for learners
encountering it for the first time.

The second adjustment introduces parentheses around conditions, similar to the convention used in
programming languages such as C. For instance, a condition in the original PL/0 might appear without
parentheses, whereas our modified grammar will require conditions to be enclosed within parentheses
e.g. '(x < y)'. This change not only makes the syntax more explicit and visually structured but also
aligns with the familiarity that many programmers already have with conditional syntax in widely-used
languages.

Third, we adapt the handling of statement terminations by introducing semicolons (;) to mark the
end of statements rather than using them as separators. In the original PL/0, semicolons acted as
delimiters between consecutive statements, which differs from the more common convention of treating
semicolons as terminators. For example, instead of writing 'begin a := b; c := d end', the new grammar
would use 'begin a := b; c := d; end' with each semicolon clearly indicating the conclusion of a statement.
This adjustment simplifies the parsing process and aligns PL/0's syntax more closely with modern
programming languages, making it easier for students to grasp and work with.

Limiting procedures to the top level in PL/0 simplifies scoping and improves readability by avoiding the
complexity of managing nested scopes and variable access. This change makes the interpreter or compiler
easier to implement, as it eliminates the need for complex call stacks or environment management. While
it reduces the language's expressiveness by removing the ability to encapsulate helper functions within
procedures, it aligns with PL/0's minimalist and educational focus. The trade-off sacrifices the power
of closures and localised abstractions but keeps the language straightforward for learners and implementers.

Constants can only be declared at the top level. This also simplify handling of constants.

Thus,
- The "odd" keyword is removed to streamline the grammar, as its utility is limited
  and could confuse learners as it is not often represented in languages of today.
- Parentheses are introduced around conditions, improving clarity and aligning syntax
  with familiar conventions in languages like C.
- Semicolons now act as statement terminators instead of separators, simplifying
  parsing and modernising the syntax.
- Procedures are limited to bransching from the top level, avoiding complex scoping,
  simplifying implementation, but still aligning with PL/0's educational focus.
- Constants can't be declared in other places than at the top level.

These changes are not just superficial; they reflect deliberate design choices aimed at making the
language more intuitive and accessible while providing a better foundation for understanding compiler
construction. They also allow learners to focus on core concepts without being bogged down by
idiosyncrasies that may not translate to other programming environments.

To avoid some confusion with PL/0, we will call this new language: *PL/E*.


### Steps in Compiling PL/E ...

A traditional compiler operates in distinct phases: lexical analysis, syntax analysis, semantic analysis,
optimisation, and code generation. Each of these phases can be refined or expanded based on the complexity
of the programming language, the target platform, or optimisation goals.

The refinement of compilers often involves *modular design*, where each phase is implemented as a pipeline,
enabling developers to tweak or replace individual phases for specific goals.
These can be e.g. optimisations for certain hardware: GPUs, or enhanced debugging capabilities.


#### Lexical Analysis

Typically,
- Beyond tokenisation, more sophisticated error detection for malformed tokens can be added.
- Preprocessing steps like comments removal, macro expansion or conditional compilation
  (e.g. in C/C++) can be integrated into this stage.

Specifically,

- Convert the source code into a stream of tokens (e.g., keywords, operators, identifiers).
	- Implementation: Use a finite state machine or a library (like Flex or a custom tokeniser
      in Python/C++). Here: we make our own [tokeniser](./syntax/TOKENS.md).
	- Tokens for PL/E:
        - Keywords: const, var, procedure, call, begin, end, if, then, while, do.
	    - Symbols: '=', '+', '-', '*', '/', '(', ')', ';', '.'.
	    - Identifiers: variable names, procedure names and numbers.

Example:

```pascal
var sum;

begin
    sum := 4 + 2;
end.
```

Could be tokenised to:

```
VARSYM IDENT sum SEMICOLON ENDOFLINE
ENDOFLINE
BEGINSYM ENDOFLINE
IDENT sum BECOMES NUMBER 4 PLUS NUMBER 2 SEMICOLON ENDOFLINE
ENDSYM PERIOD
ENDOFFILE
```


#### Syntax Analysis

Typically,
- Refined with better error recovery strategies, ensuring that the parser continues to analyse
  code even after encountering errors.
- Use of more advanced parsing techniques like Packrat parsing for ambiguous grammars.

Specifically,
- Parse the token stream into a syntax tree based on PL/E grammar. This step ensures the program
  adheres to the language's grammar rules.
- We will use a recursive descent parser, where the parser will build a abstract syntax tree
  (AST) for further stages. See [AST](./syntax/AST.md).

Example:

```pascal
var sum;
begin
    sum := 4 + 2;
end.
```

Output AST:

```
PROGRAM
  BLOCK
    VAR_DECL: sum
    BLOCK
      ASSIGNMENT: sum
        OPERATOR: +
          EXPRESSION
            NUMBER: 4
          NUMBER: 2
```


#### Semantic Analysis

Typically,
- Enrich type checking to include flow-sensitive type inference (e.g. checking variable
  initialisation across branches).
- Add support for advanced features like dependent types or type-driven program synthesis.

Specifically,
- Ensure the program is semantically correct (e.g. no undefined variables, type mismatches).
	- Symbol Table: Track declarations (const, var, procedure) and ensure variables are
    declared before use.
	- Type Checking: PL/E doesn't have complex types, but ensure numbers and variables are
    used correctly.
	- Scope Management: Handle scopes for procedure declarations, simplified by only dividing them
    into local and global (and no nested cases).

Example:

```pascal
var sum;
begin
    sum := 4 + 2 + z;
end.
```

Output:

```
Warning: Identifier 'z' used before declaration.
```

(We have some error checking outside of the core compilation pipeline, to avoid introduce
too many concepts at once. Therefore, the warning can be seen if the Python script for
symbol.py is invoked.)


#### Intermediate Code Generation

Typically,
- Introduce high-level Intermediate Representations (IR) for easier analysis and optimisation.
  For example, SSA (Static Single Assignment) form is widely used for optimisation.
- Multi-level IRs: A high-level IR (close to source) and a low-level IR (close to assembly)
  can provide better optimisation opportunities.

Specifically,
- Translate the AST into an intermediate representation (IR) like three-address code (TAC)
  or a stack-based code (often used for PL/0).
- PL/0 typically targets a stack-based virtual machine (e.g. instructions like
  PUSH, ADD, CALL, etc.). Which we will also do with PL/E.

Example: AST for 'y := x + 1':

```
Assignment
├── LHS: y   -- left hand side
└── RHS: +   -- right hand side 
    ├── x
    └── 1
```

IR for stack machine:

```
LOAD x
PUSH 1
ADD
STORE y
```


#### Optimisation

Typically,
- Refined into high-level optimisations (e.g. loop transformations, constant folding)
  and low-level optimisations (e.g. register allocation, instruction scheduling).
- Profile-guided optimisations (using runtime data to inform compilation) can enhance
  performance.

Specifically,
- Optimise the intermediate code for performance.
    - For PL/0, optimisations can include:
	    - Constant Folding: Replace x := 5 + 3 with x := 8 at compile time.
	    - Dead Code Elimination: Remove unreachable or unused code.
	    - Peephole Optimisation: Simplify redundant instructions
          (e.g. replace PUSH 0; ADD with NOP).
    - For PL/E show in TAC?


#### Code Generation

Typically,
- Refine to support multiple backends, allowing cross-compilation for different architectures.
- Techniques like Just-In-Time (JIT) compilation or Ahead-Of-Time (AOT) compilation can be
  layered on top for different deployment scenarios.

Specifically,
- Generate target code for the PL/0 virtual machine or hardware.
    - PL/0 VM Code Example:

```
PUSH 10     ; Push constant 10 to stack
STORE x     ; Store to variable x
LOAD x      ; Load x to stack
PUSH 1      ; Push constant 1 to stack
ADD         ; Add top two values on the stack
STORE y     ; Store result to variable y
```

PL/E .. LLVM .. WASM



#### Post-Compilation

Typically,
- Tools like linkers and loaders can perform additional optimisations, such as
  dead code elimination and binary rewriting.
- Static analysis tools can further check for issues like memory safety or
  undefined behavior.

Specifically,
- Handle final steps, such as linking (if targeting real hardware) or loading
  the code into a virtual machine.

  For PL/0, this step often involves:
  - Writing the binary or assembly-like code into a file.
  - Providing a virtual machine to execute the generated code.

  PL/E
  - Linking from WASM to browser ..



### Projects for Omitted Steps

From the discussion above, it is evident that certain steps in the compiler
development process have been deliberately omitted. These omissions were made
to maintain clarity and focus on the core concepts, avoiding unnecessary
complexity that might obscure the main learning objectives. Specifically,
the following components have been excluded:

- *Error Handling*: The current implementation provides limited or no
  mechanisms for detecting and reporting errors. This simplifies the
  core implementation but leaves an important aspect of compiler design
  unexplored. See more on [Errors](./semantics/ERRORS.md).

- *Optimisation*: No optimisations are applied to the generated code,
  meaning there is no consideration for improving performance, minimising
  resource usage, or simplifying the final output.

- *Type Checking*: Since this compiler exclusively handles integers, there
  is no type system or semantic checks, eliminating the need for type
  enforcement or verification. See more on [Types](./types/TYPES.md).

To address these omitted topics and provide opportunities for deeper learning,
the following additional projects are proposed to extend and enhance the concepts.


__1. Implement Comprehensive Error Handling__

*Develop a robust error-handling mechanism for the compiler to
detect, report, and guide users through various issues in the
source code.*

- Add support for syntax errors, semantic errors, and warnings.
- Design error messages to be clear, actionable, and contextual
  (e.g. use inclusion of line numbers, offending code snippets,
  and suggestions for fixes).
- Implement a hierarchical error system that distinguishes between
  critical errors (which halt compilation) and warnings (which
  allow compilation to proceed).


*Challenge:* Build a recovery mechanism that enables the compiler to continue
parsing after encountering errors, instead of stopping abruptly.

*Advanced extension:* Make the error system configurable, allowing developers
to customise which warnings/errors are shown or suppressed.


__2. Add Basic and Advanced Optimisations__

Introduce a new phase in the compilation process to optimise the generated
code for performance and efficiency.

- Start with basic optimisations, such as:
  - Constant folding: Evaluate constant expressions at compile-time
    (e.g. replace 2 + 3 with 5).
	- Dead code elimination: Remove unreachable or unnecessary code.
	- Inline expansion: Replace short function calls with their body
    to reduce overhead.
- Progress to more advanced optimisations:
	- Peephole optimisation: Scan small sections of code to simplify
    or replace inefficient instruction sequences.
	- Loop optimisations: Unroll loops, reduce loop overhead, or move
    invariant calculations outside the loop.
	- Register allocation: Minimise memory access by efficiently using
    CPU registers.
	
*Challenge:* Develop a visualisation tool to compare pre- and post-optimisation
code, helping users understand the impact of these transformations.


__3. Introduce a Type System__

Expand the compiler to handle multiple data types and implement type-checking
rules to ensure correctness.
- Add support for data types such as integers, floats, and strings.
- Implement type inference and explicit type annotations in the source language.
- Design and enforce type-checking rules for operations, such as ensuring operands
  in arithmetic expressions are compatible.
- Provide informative error messages for type-related issues (e.g. "Cannot assign
  a string to an integer variable").
- Advanced extension: Add support for user-defined types (e.g. structs or enums)
  and create a mechanism for type equivalence and subtyping.

4. Create a Warning System for Potential Issues

Design a mechanism to detect and report potential problems that don't prevent
compilation but could cause bugs or inefficiencies.
- Examples include:
	- Unused variables: Report variables that are declared but never used.
	- Deprecated constructs: Warn about outdated language features.
	- Potential logical errors: Identify suspicious code patterns, such as
    assignments within conditional expressions, e.g. 'if (x = 0) ..'.
	- Implement a severity system (e.g., low, medium, high) and allow users to
    configure which warnings are displayed or ignored.

*Challenge:* Incorporate machine learning to analyse and predict common coding
mistakes, improving warning accuracy.


__5. Extend the Compiler with Modular Features__

Explore modular extensions to handle omitted components independently or
integrate them into the current compiler.
- Error handling module: Build a standalone library for managing errors,
  which can be plugged into the compiler.
- Optimisation pipeline: Design a framework that supports adding new optimisation
  passes without altering the compiler core.
- Type-checking module: Implement a reusable type-checker that can support
  multiple languages.

This modular approach not only reinforces the core concepts but also demonstrates
how real-world compilers are built with extensibility in mind.


__6. Design a Debugging and Logging Tool__

Develop a debugging tool to trace the compiler's internal processes.
- Add features to log parsing steps, code generation, and any errors
  or warnings encountered.
- Visualise the abstract syntax tree (AST) and intermediate representations
  to aid in understanding the compilation process.
- Provide detailed stack traces for runtime errors, helping users diagnose issues.
- Advanced extension: Build an interactive debugging interface that allows
  users to step through compilation phases and modify inputs dynamically.


### Summary

These projects not only deepen your understanding of compiler design but also provide
practical experience with critical features that are often essential in real-world
applications. By addressing the omitted components, you'll gain a more comprehensive
view of how compilers interact with programming languages and their users.
