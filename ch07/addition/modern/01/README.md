
### A Modernised Compiler

The `compiler.py` is a compiler for a simplified programming language inspired by PL/0
(designed by Niklaus Wirth). This compiler translates the source code into C code, which
can then be compiled and executed using a C compiler. The compiler follows a classic
compilation pipeline: *lexing*, *parsing*, *semantic analysis*, and *code generation*.
It uses a *packrat parser* for efficient parsing and the *Visitor pattern* to traverse
the Abstract Syntax Tree (AST) for code generation.

The input language supports features like variable declarations, procedures, assignments,
conditionals (`if`), loops (`while`), input/output operations (`?` for read, `!` for write),
and basic arithmetic and comparison operations. The output C code includes necessary
headers (e.g., `stdio.h` for I/O) and translates the input program’s constructs into
equivalent C constructs.


### Compilation Process Overview

1. *Lexing*: The `Lexer` class reads the source code and breaks it into a sequence of
   tokens (e.g., keywords, identifiers, numbers, operators).
2. *Parsing*: The `PackratParser` class uses the tokens to build an AST, representing
   the program’s structure hierarchically.
3. *Semantic Analysis and Code Generation*: The `CCompiler` class traverses the AST
   using the Visitor pattern, generating equivalent C code while maintaining a context
   for variable scoping and procedure definitions.
4. *Output*: The generated C code is written to an output file, which can be compiled
   and executed using a C compiler.



#### 1. *Lexer (`Lexer` class)*

The lexer is responsible for *tokenization*, converting the raw source code (a string)
into a list of tokens. Each token is a tuple containing the token’s value (e.g., `begin`,
`:=`, `42`) and its type (e.g., `kw` for keyword, `id` for identifier, `num` for number,
`op` for operator, etc.).

- *Key Features*:
  - Recognizes keywords (e.g., `begin`, `end`, `if`, `while`), operators (e.g., `+`, `-`, `:=`),
    identifiers, and numbers.
  - Handles multi-character tokens like `:=`, `<=`, `>=`, and `end.` (program terminator).
  - Skips whitespace and raises a `SyntaxError` for unexpected characters.
  - Debugging output logs each token produced (e.g., `DEBUG: Lexer produced token: 'begin' (kw)`).

- *How It Works*:
  - The `tokenize` method iterates through the input string, using `read_alpha`, `read_digit`,
    and `read_operator` to extract tokens based on character types (alphabetic, numeric, or operator).
  - Tokens are stored in `self.tokens` as `(value, kind)` pairs.

- *Example*:
  For the input `var x; x := 5;`, the lexer produces tokens like:
  ```
  [("var", "kw"), ("x", "id"), (";", "semi"), ("x", "id"), (":=", "asgn"), ("5", "num"), (";", "semi")]
  ```

#### 2. *Abstract Syntax Tree (AST) (`ASTNode` and derived classes)*

The AST represents the program’s structure as a tree of nodes, where each node corresponds
to a syntactic construct (e.g., a block, assignment, or expression). The `ASTNode` class is
an abstract base class defining the `accept` method for the Visitor pattern. Derived classes
include:

- *`BlockNode`*: Represents a block with variable declarations, procedure definitions, and a main statement.
- *`AssignNode`*: Represents an assignment (e.g., `x := 5`).
- *`CallNode`*: Represents a procedure call (e.g., `call proc`).
- *`ReadNode` and `WriteNode`*: Handle input (`? x`) and output (`! x`) operations.
- *`CompoundNode`*: Represents a sequence of statements (e.g., within `begin ... end`).
- *`IfNode` and `WhileNode`*: Represent conditional and loop constructs.
- *`OperationNode`*: Represents binary operations (e.g., `x + y`, `x < y`).
- *`VariableNode` and `NumberNode`*: Represent variables and numeric literals.

Each node implements the `accept` method, which allows a visitor to process the node.


#### 3. *Packrat Parser (`PackratParser` class)*

The parser uses *packrat parsing*, a memoized recursive descent parsing technique, to
construct the AST from the token list. Packrat parsing is efficient for languages with
complex grammars because it caches intermediate results to avoid redundant computations.

- *Key Features*:
  - Implements a top-down parser with methods like `program`, `block`, `statement`,
    `condition`, `expression`, `term`, and `factor`, each corresponding to a grammar rule.
  - Uses memoization via the `memoize` method to cache parsing results for specific rules
    and positions, reducing time complexity for backtracking.
  - Debugging output logs parsing steps (e.g., `DEBUG: Entering statement at pos 0`).
  - Handles the PL/0-like grammar, including variable declarations (`var`), procedures,
    statements, and expressions.
  - Raises `SyntaxError` for invalid syntax (e.g., missing `;` or `end.`).

- *How It Works*:
  - The `parse` method starts by calling `program`, which expects a `block` followed by
    an optional `end.` token.
  - Each parsing method (e.g., `block`, `statement`) attempts to match tokens against
    grammar rules, building AST nodes and advancing the token position.
  - The parser supports nested constructs like procedures, `if` statements, and `while`
    loops, and handles operator precedence in expressions (e.g., `*` and `/` before `+` and `-`).

- *Example*:
  For the input `var x; x := 5;`, the parser constructs a `BlockNode` containing a
  variable `x` and an `AssignNode` with `VariableNode("x")` and `NumberNode(5)`.


#### 4. *Visitor Pattern (`Visitor` and `CCompiler` classes)*

The *Visitor pattern* is used to traverse the AST and perform actions (in this case, code
generation). The `Visitor` class is an abstract base class defining methods for each AST
node type (e.g., `visit_block`, `visit_assign`). The `CCompiler` class implements these
methods to generate C code.

- *How the Visitor Pattern Works*:
  - Each AST node’s `accept` method calls the appropriate `visit_*` method on the visitor,
    passing itself as an argument.
  - This decouples the AST structure from the operations performed on it, allowing different
    visitors to perform different tasks (e.g., code generation, semantic analysis, or
    optimisation) without modifying the AST classes.
  - In `compiler.py`, the `CCompiler` visitor generates C code by traversing the AST and
    emitting code snippets for each node.

- *Key Features of `CCompiler`*:
  - *Context Management*: Uses a `CompilerContext` to track variables, scopes, procedures,
    and generated code. It supports nested scopes (via `enter_scope` and `exit_scope`) and
    generates temporary variables if needed.
  - *Procedure Handling*: Collects procedure names in `collect_procedures` to generate
    function prototypes, then processes each procedure’s body.
  - *Code Generation*:
    - `visit_block`: Generates variable declarations and procedure definitions, wrapping
      the main block in a `main` function.
    - `visit_assign`: Generates C assignments (e.g., `x = 5;`).
    - `visit_call`: Generates procedure calls (e.g., `proc();`).
    - `visit_read` and `visit_write`: Generate `scanf` and `printf` calls for I/O.
    - `visit_if` and `visit_while`: Generate C `if` and `while` statements.
    - `visit_operation`: Maps PL/0 operators to C operators (e.g., `=` to `==`).
    - `visit_variable` and `visit_number`: Return variable names and numeric literals as strings.

- *Example*:
  For an AST node `AssignNode("x", NumberNode(5))`, the `visit_assign` method generates `x = 5;`.


#### 5. *Compiler Context (`CompilerContext` class)*

The `CompilerContext` class manages state during code generation:

- *Scopes*: Maintains a stack of dictionaries (`scopes`) to track variable declarations in
  different scopes.
- *Code Buffer*: Stores generated C code lines in `generated_code`, with proper indentation.
- *Procedure Tracking*: Stores procedure definitions in `procedures` and tracks the current
  procedure being compiled.
- *Temporary Variables*: Generates unique temporary variable names if needed (though not
  used in this implementation).
- *Methods*:
  - `add_variable`: Registers a variable in the current scope.
  - `variable_exists`: Checks if a variable is defined in any scope.
  - `add_code`: Appends a line of C code with appropriate indentation.
  - `get_code`: Joins all code lines into a single string.


#### 6. *PL0Compiler and Main Function*

The `PL0Compiler` class provides a static method `compile_file` to orchestrate
the compilation process:

- Reads the input file.
- Creates a `Lexer` to tokenize the input.
- Creates a `PackratParser` to build the AST.
- Uses a `CCompiler` to generate C code.
- Writes the output to a `.c` file.
- Handles errors (e.g., file I/O errors, syntax errors) with appropriate messages.

The `main` function parses command-line arguments to specify input and optional
output filenames, calling `PL0Compiler.compile_file`.


### Example Workflow

For an input file `example.pl0`:
```
var x;
x := 5;
! x;
end.
```

1. *Lexing*:
   - Tokens: `[("var", "kw"), ("x", "id"), (";", "semi"), ("x", "id"), (":=", "asgn"), ("5", "num"), (";", "semi"), ("!", "kw"), ("x", "id"), (";", "semi"), ("end.", "kw")]`

2. *Parsing*:
   - AST: `BlockNode(variables=["x"], procedures=[], statement=CompoundNode(statements=[AssignNode("x", NumberNode(5)), WriteNode(VariableNode("x"))]))`

3. *Code Generation*:
   - Output C code:
     ```c
     #include <stdio.h>

     int x;

     int main() {
         x = 5;
         printf("%d\n", x);
         return 0;
     }
     ```

4. *Output*: Written to `example.c`, which can be compiled with a C compiler (e.g., `gcc example.c -o example`).


### Why Use the Visitor Pattern?

The Visitor pattern is ideal for this compiler because:
- *Separation of Concerns*: The AST structure is separate from code generation logic,
  making it easy to add new operations (e.g., type checking, optimization) by creating new visitor classes.
- *Extensibility*: New AST node types can be added with corresponding `visit_*` methods in visitors.
- *Maintainability*: Code generation logic is centralized in the `CCompiler` class,
  with each `visit_*` method handling a specific node type.


### Limitations and Potential Improvements

- *Error Handling*: The compiler raises `SyntaxError` for invalid input but could provide
  more detailed error messages (e.g., line numbers).
- *Semantic Analysis*: The current implementation does not check for semantic errors
  (e.g., undeclared variables, procedure redefinition). Adding a semantic analysis visitor could improve robustness.
- *Optimisation*: The generated C code is straightforward but could be optimised
  (e.g., eliminating redundant assignments).
- *Language Features*: The PL/0-like language is minimal; adding support for arrays,
  functions with parameters, or more complex expressions could enhance its practicality, or utility.


### Conclusion

The `compiler.py` demonstrates compiler concepts like lexing, parsing with packrat parsing,
AST construction, and code generation using the Visitor pattern. The modular design makes
it a foundation for learning about compilers or extending with additional features.
To use it, provide a PL/0-like source file as input, and it will generate a C program
that can be compiled and executed.
