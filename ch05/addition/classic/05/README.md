
## Semantics: Symbol Tables

__Build__

```shell
make clean
make
make samples
make table
```

The provided code fragments illustrate the basic structure for a simple symbol table build in a
language close to PL/0. The symbol table relies on an *Abstract Syntax Tree* (AST) for the extraction
of information, and thus the AST has to be built *before* extraction of the symbol table.

__View__

First `make table` to generate symbol tables for the samples. Then in the directory of 'tools' you'll
find a HTML-file: `table_yaml.html`. Open the file locally, and search for the symbol table representation
in the 'table' folder.


### Overview and Uses

A symbol table is a data structure used in programming languages, particularly in compilers and interpreters.
It stores information about the various symbols (identifiers) in a program, such as variables, constants,
procedures, and functions.

1. Name: The identifier (such as variable name, procedure name).
2. Attributes: Information about the identifier, such as:
	- Type: Integer, real, procedure, etc.
	- Scope: Where the symbol is valid (local, global).
	- Memory location: Address or offset for storage.
	- Other properties: Parameter count, size, modifiers, etc.

Symbol tables essentially maps symbol names and their attributes.

#### Common Uses

1. Compilation and Interpretation: Symbol tables are essential during both compilation and interpretation,
   as they help the compiler/interpreter understand what each symbol represents.
2. Scope Resolution: They help resolve scopes by maintaining separate entries for global, local, and nested blocks.
3. Type Checking: Type information stored in the symbol table allows the compiler to enforce type rules.
4. Code Optimisation: They enable optimisations such as constant folding and register allocation.
5. Error Detection: A symbol table helps identify undeclared variables or mismatched types during semantic analysis.

The importance of symbol tables depends on the task: In compilers, they are indispensable for parsing,
semantic analysis, and code generation. In simple interpreters or one-pass translators, a lightweight
implementation of symbol tables might suffice, or they may not be explicitly constructed if the program
doesn't need complex scoping or type checking.


### Symbol Tables in a PL/0 Compiler

PL/0 is a simple teaching-oriented language, and its compiler typically uses symbol tables for tasks like
handling variables, constants, and procedures.

1. Lexical and Syntactic Analysis:
	- During lexical analysis, tokens representing identifiers are created.
	- In syntactic analysis (parsing), entries in the symbol table are created or updated for each identifier
	  encountered. In this case, the Abstract Syntax Tree (AST) manages the symbols, which are then extracted
	  from the resulting tree.

2. Handling Scopes:
	- PL/0 supports nested procedures, which means the symbol table must manage nested scopes. This is often
      implemented as a stack of symbol tables or a tree structure.
	- When entering a new block, a new table or scope level is created.
	- When exiting a block, the corresponding scope is removed.

3. Type Checking:
	- PL/0's symbol table stores type information for variables and constants. This allows the compiler to
      ensure that expressions are semantically correct.

4. Procedure Management:
	- Information about procedures, such as parameter counts and local variable sizes, can be stored in the symbol table.

5.	Code Generation:
	- The symbol table either provides memory locations or offsets for identifiers, or can help with such tasks,
      allowing the code generator to produce correct machine or intermediate code.


#### Example

Let’s consider a simple PL/0 program:

```pascal
const x = 10;
var y;
procedure square;
    var z;
    begin
        z := y * y
    end;
begin
    y := x + 1;
    call square
end.
```

The symbol table will store:

1. Constants.
    - x: Type const, value 10.

2. Variables.
    - y: Type var, scope global.
	- z: Type var, scope square.

3. Procedures.
	- square: Type procedure, local scope includes z.

At runtime or during code generation:
- The constant x might directly map to a value.
- The variable y and local variable z are assigned memory offsets or registers.
- The procedure square includes metadata to manage calls.


#### Implementation Techniques

1. Data Structures:
	- Hash tables: For fast symbol lookup.
	- Linked lists or trees: To handle nested scopes efficiently.
2.	Nested Scopes:
	- Use a stack of symbol tables, where the top of the stack represents the current scope.
3.	Lifetime Management:
	- When a scope ends, its corresponding table or entries are removed.


### Conclusion

Symbol tables are used in compiling and interpreting PL/0 and other programming languages. They bridge
the gap between the code written by developers and the low-level operations performed by the machine.
While their implementation can vary in complexity, their role in ensuring correct, efficient, but also
optimised program execution is fundamental.
