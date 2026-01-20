
## Symbol Tables

A symbol table is a data structure used in compilers and interpreters to store
information about identifiers (variables, functions, classes, etc.) in a program. It
helps in *semantic analysis*, *scope resolution*, *type checking*, *optimisation*, and
*code generation*.

A symbol table is typically implemented as a hash table, tree, or stack-based structure.
Typically each entry (symbol) in the table stores:
- Name: The identifier's name.
- Type: The data type (e.g. int, float, function).
- Scope: The level of scope where the symbol is valid (e.g. global, local, block).
- Location: Memory address, register, or offset.
- Attributes (optional): Extra details like function parameters, array size, or linkage information.

Example:

|Name	|Type	|Scope	|Memory Location	|Extra Info|
|--|--|--|--|--|
|x	|int	|local	|stack offset -4	|-|
|y	|float	|global	|0x1004	|-|
|add	|function	|global	|code section	|(int, int) -> int|


#### Role of Symbol Tables in Compilation

__1. Lexical Analysis (Tokenisation)__
- The lexer identifies identifiers and passes them to the symbol table.
- Example: Seeing int x = 5; causes x to be entered into the symbol table.

__2. Parsing (Syntax Analysis)__
- The parser ensures correct syntax and updates the symbol table with additional
  structure (e.g. function parameters).
- Example: 'int f(int a, int b) { return a + b; }' adds 'f', 'a', and 'b' to the table.

__3. Semantic Analysis__
- Resolves scope and checks for undeclared variables, type mismatches, or redeclaration errors.
- Example:

```c
int x = 10;
float x = 5.5;  // Error: x redeclared in the same scope
```


__4. Intermediate Code Generation__
- Uses symbol table to generate correct addresses, types, and function calls.

__5. Optimisation__
- Symbol tables help identify constant folding, dead code elimination, and variable inlining.

__6. Code Generation__
- Assigns memory locations to variables and determines correct register allocations.


#### Handling Scope in Symbol Tables

Compilers use nested scopes, where each scope has its own symbol table:
1. *Global Scope:* Stores functions, global variables.
2. *Function Scope:* Stores local variables, function parameters.
3. *Block Scope:* Stores variables inside {} blocks.

To resolve an identifier, the compiler:
1. Checks the current scope.
2. Moves outward (parent scopes) if not found.
3. Reports an error if the identifier is not declared.

Example (Stack-Based Symbol Table):

```
Scope 3 (Block)    -> { x: int }
Scope 2 (Function) -> { y: float, f: function }
Scope 1 (Global)   -> { g: int }
```
Looking up x first checks Scope 3, then moves to Scope 2, etc. moving outwards.

#### Implementation Strategies

1. Hash Table (Most Common)
- Fast lookup and insertion (O(1) on average).
- Collisions handled via chaining or open addressing.

2. Tree-Based (e.g., AVL, Red-Black)
- Ordered for efficient range queries and scoped lookups (O(log n)).

3. Stack-Based (For Block Scope)
- Uses a stack where entering a scope pushes a new table, and leaving pops it.
- Efficient for languages with nested block scopes (C, Java).


#### Example:

```c
int g = 10;
void f() {
    int x = 5;
    { // block
        int y = 20;
        x = y + g;
    }
}
```

*Global Scope*

|Name	|Type	|Scope	|Location|
|--|--|--|--|
|g	|int	|global	|0x1000|
|f	|function	|global	|0x2000|

*Function f Scope*

|Name	|Type	|Scope	|Location|
|--|--|--|--|
|x	|int	|f local	|stack offset -4|

*Block Scope inside f*

|Name	|Type	|Scope	|Location|
|--|--|--|--|
|y	|int	|block	|stack offset -8|
