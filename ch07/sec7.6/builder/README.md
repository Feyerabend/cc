
## PL/0 Interpreter

To iterate from previously we go through the PL/0 interpreter again.
The PL/0 interpreter is here implemented in both Python and C,
demonstrating the preservation of object-oriented design patterns
(particularly the Builder Pattern) across different programming paradigms.

As you probably already know, the PL/0 is a simple programming language
designed for educational purposes, featuring variables, procedures,
conditionals, loops, and basic arithmetic operations. This
implementation provides a complete interpreter with lexical analysis, parsing,
Abstract Syntax Tree (AST) construction, and execution.

- Variable declarations and assignments
- Procedure definitions and calls
- Input/output operations (?, !)
- Conditional statements (if-then)
- Loops (while-do)
- Basic arithmetic and comparison operations


### Language Syntax

- Keywords: var, procedure, begin, end, if, then, while, do, call, ?, !
- Operators: +, -, *, /, <, >, =, := (assignment)
- Identifiers: Alphanumeric names for variables and procedures
- Numbers: Integer literals
- Punctuation: ;, ,, (, )

A PL/0 program consists of:
1. Optional variable declarations (var x, y;)
2. Optional procedure declarations (procedure p; ...)
3. Main statement block, terminated by end.


```pascal
var x, y;
procedure add;
  x := x + y;
begin
  x := 5;
  y := 3;
  call add;
  !x
end.
```

This program declares variables x and y, defines a
procedure add, assigns values, calls the procedure,
and outputs the result (8).


### Architecture

The interpreter follows a modular design with clear separation of concerns:

```
Source Code
    |
    v
  Lexer (Tokenization)
    |
    v
ASTBuilder (Parsing & AST Construction)
    |
    v
  AST (Abstract Syntax Tree)
    |
    v
Interpreter (Execution via Visitor Pattern)
```

#### Components

1. Lexer
   - Converts input code into a stream of tokens
   - Uses TokenMatchStrategy for pattern matching
   - Manages token iteration via TokenIterator

2. ASTBuilder
   - Parses token stream using recursive descent
   - Constructs Abstract Syntax Tree incrementally
   - Implements the Builder Pattern

3. AST Nodes
   - BlockNode: Variable/procedure declarations and main statement
   - AssignNode: Variable assignment
   - CallNode: Procedure call
   - ReadNode: Input operation
   - WriteNode: Output operation
   - CompoundNode: Statement sequence
   - IfNode: Conditional statement
   - WhileNode: Loop statement
   - OperationNode: Arithmetic/comparison operation
   - VariableNode: Variable reference
   - NumberNode: Integer literal

4. Interpreter
   - Executes AST using the Visitor Pattern
   - Manages variable/procedure scopes
   - Handles nested procedure calls with proper scoping


### The Builder Pattern

The Builder Pattern is a creational design pattern that separates the construction
of a complex object from its representation, allowing step-by-step construction
using a fluent interface.

- Director: Orchestrates the construction process
- Builder: Interface defining construction steps
- Concrete Builder: Implements steps to create specific product
- Product: The complex object being constructed

Use:
- Objects requiring many optional parameters
- Constructing complex objects with multiple parts (e.g., ASTs, UI elements)
- Creating different representations with the same construction process


#### Builder Pattern in PL/0

The ASTBuilder class acts as the Concrete Builder, constructing the Abstract
Syntax Tree by parsing tokens from the lexer.

First a Python builder:

```python
class ASTBuilder:
    def __init__(self, lexer: PL0Lexer):
        self.iterator = lexer.get_iterator()
    
    def build(self) -> ASTNode:
        return self.build_block()
    
    def build_block(self) -> BlockNode:
        variables = []
        procedures = []
        statement = self.build_statement()
        return BlockNode(variables, procedures, statement)
    
    def build_statement(self) -> ASTNode:
        ## Construction logic for various statement types
        return node
```

Then a C implementation:

```c
typedef struct {
    TokenIterator* iterator;
} ASTBuilder;

ASTBuilder* builder_create(PL0Lexer* lexer) {
    ASTBuilder* builder = malloc(sizeof(ASTBuilder));
    builder->iterator = lexer_get_iterator(lexer);
    return builder;
}

ASTNode* builder_build(ASTBuilder* builder) {
    return builder_build_block(builder);
}

ASTNode* builder_build_block(ASTBuilder* builder) {
    char** variables = NULL;
    int var_count = 0;
    ASTNode* statement = builder_build_statement(builder);
    return node_create_block(variables, var_count, ...);
}
```

We have:

1. Encapsulation of Construction Logic
   - Building logic isolated in builder methods
   - Each method responsible for one AST node type

2. Step-by-Step Construction
   - Hierarchical construction: build() -> build_block() -> build_statement()
   - Each level delegates to lower-level builders
   - Recursive structure mirrors grammar rules

3. Separation of Construction from Representation
   - Builder knows HOW to construct
   - Nodes know WHAT they represent
   - Changes to construction don't affect representation

4. Factory Pattern Integration
   - Node creation centralized in factory functions
   - Consistent initialization
   - Implementation details hidden


Benefits:
- Code Organization: Clean separation of tokenisation, parsing, and execution
- Maintainability: Changes localised to specific builder methods
- Extensibility: New node types easily added
- Testability: Builder can be tested independently
- Clarity: Method names reflect intent


### Object-Oriented Design in C

Despite C being procedural, the implementation preserves OOP patterns through
careful design:

#### Polymorphism via Function Pointers

__Visitor Pattern__

```c
struct Visitor {
    void* context;
    void* (*visit_block)(Visitor*, ASTNode*);
    void* (*visit_assign)(Visitor*, ASTNode*);
    // ... more visit methods
};
```

Function pointers achieve polymorphic behavior similar to virtual methods.

__AST Node Accept Method__

```c
struct ASTNode {
    NodeType type;
    void* data;
    void* (*accept)(struct ASTNode*, Visitor*);
};
```

Each node can accept a visitor, enabling double dispatch.

#### Encapsulation

Data structures encapsulate their data with controlled access:

```c
typedef struct {
    char* var_name;
    ASTNode* expression;
} AssignData;
```

#### Abstraction

ASTNode acts as an abstract base with concrete implementations for each node type.


### Design Patterns Used

1. Builder Pattern: `ASTBuilder` constructs complex AST incrementally
2. Visitor Pattern: `Visitor` struct with function pointers for polymorphic traversal
3. Strategy Pattern: `TokenMatchStrategy` for flexible token matching
4. Factory Pattern: `Node` creation functions centralise construction



### Example Programs


Factorial:
```pascal
var n, result;
begin
  ?n;
  result := 1;
  while n > 0 do
    begin
      result := result * n;
      n := n - 1
    end;
  !result
end.
```

Input: 5

Output: 120


#### Math with Procedures

```pascal
var global;

procedure math;
var a, b;
begin
  ? a;
  ? b;
  if a < b then ! a;
  if b < a then ! b;
  global := a + b;
end;

begin
  call math;
  ! global * 2;
end.
```

Input: 5 and 3

Output: 3, 16


### Writing PL/0 Programs

#### Variable Declarations

Use var followed by comma-separated identifiers,
ending with semicolon:

```pascal
var x, y, z;
```

#### Procedure Declarations

Define procedures with procedure followed by name,
semicolon, and body:

```pascal
procedure sum;
  x := x + y;
```

#### Statements

- Assignment: <id> := <expression>
- Procedure call: call <id>
- Input: ? <id>
- Output: ! <expression>
- Compound: begin <statements> end
- Conditional: if <expr> <op> <expr> then <statement>
- Loop: while <expr> <op> <expr> do <statement>

#### Expressions

Support arithmetic (+, -, *, /) and comparisons (<, >, =) with parentheses
for grouping.

#### Program Termination

End the program with 'end.' Period important.


### Extending the Interpreter

#### Adding New Operators

1. Update RegexTokenMatchStrategy to recognize new operator
2. Add operator to OperatorFactory mapping
3. Test with sample programs

Example - Adding Modulo:

```python
## In RegexTokenMatchStrategy
r"(?P<op>[-+*/%()<>=])|"

## In OperatorFactory
"%": operator.mod
```

#### Adding New Statement Types

1. Define AST node class (Python) or data structure (C)
2. Add node type to enum
3. Create factory function (C) or constructor (Python)
4. Add builder method for parsing
5. Integrate into build_statement()
6. Add visitor method for execution

#### Adding Data Types

Extend Scope to support non-integer types and type checking.

#### Improving Error Messages

Track line numbers in lexer and include in error messages.


### Memory Management (C Version)

All dynamically allocated structures have corresponding destroy functions:
- `lexer_destroy()`: Frees lexer resources
- `builder_destroy()`: Frees builder (not AST nodes)
- `node_destroy()`: Recursively frees all AST nodes
- `scope_destroy()`: Recursively frees scope chain
- `interpreter_destroy()`: Frees interpreter resources

Proper cleanup sequence:

```c
// 1. Create builder
ASTBuilder* builder = builder_create(lexer);

// 2. Build AST (allocates nodes)
ASTNode* ast = builder_build(builder);

// 3. Destroy builder (builder lifetime separate from product)
builder_destroy(builder);

// 4. Use AST
interpreter_interpret(interpreter, ast);

// 5. Destroy AST (deallocate all nodes)
node_destroy(ast);
```


### Differences Between Python and C Versions

1. Memory Management
   - Python: Automatic garbage collection
   - C: Explicit malloc/free

2. Polymorphism
   - Python: Native class inheritance and virtual methods
   - C: Function pointers simulate virtual methods

3. Type System
   - Python: Dynamic typing
   - C: Void pointers with manual casting

4. Data Structures
   - Python: Dictionaries for scope variables/procedures
   - C: Linked lists for scope management

5. Error Handling
   - Python: Exceptions
   - C: Direct exit() calls


### Common Errors and Debugging

#### Syntax Errors

- Unexpected Character: Invalid tokens (@, #, etc.)
  Fix: Check for proper keywords and operators

- Expected <token> but got <token>: Syntax mistake
  Fix: Verify statement syntax, check for missing semicolons

#### Semantic Errors

- Variable/Procedure Not Found: Undeclared identifier
  Fix: Ensure declarations before use

#### Debugging Tips

- Print token stream in lexer to verify tokenization
- Add debug output in ASTBuilder to inspect AST structure
- Trace variable values in Interpreter for runtime issues


### Conclusion

The PL/0 interpreter demonstrates how object-oriented design patterns like the
Builder Pattern can be successfully implemented in both Python and C. Despite
the languages' different paradigms, the core architectural principles remain
intact through disciplined design.

Takeaways:
- Builder Pattern separates construction from representation
- Design patterns transcend language paradigms
- C can implement OOP concepts through structs and function pointers
- Clean architecture improves maintainability and extensibility

