
## Semantics: Analysis and Errors

__Build__

```shell
make clean
make
make samples
make table
make interpret
```

We go back to the *Abstract Syntax Tree* (AST) for use in a preliminary *interpreter*. This gives us
more confidence in the compiler proceeds as expected. It also shows how the meaning and validity of
code. Another part of sematic analysis are error checks. Here they are simplified as print to the console.

__Execute__

First `make interpret` to see the samples executes. In the directory of 'tools' you'll find a Python
file: `ast_interpreter.py`. Run the file to see an execution of the programs.


### Analysis in General

Semantic analysis ensures logical correctness and adherence to program rules:

1. *Scope Management*: Each block or procedure maintains its own environment. Variables declared in one
   scope are isolated from others unless explicitly propagated.

2. *Type Checking*: Expressions are evaluated to ensure correct types (e.g. numeric operations). (Only
   one type here: integers)

3. *Consistency*: Constants and procedures cannot be re-declared. Assignments check for variable existence.

4. *Control Flow*: Ensures proper structure for blocks, calls, and recursion. Detects unreachable or
   malformed code.


### Error Messages in Example

1. *Syntax Errors*: Errors in JSON structure (e.g. invalid node types or unexpected formats).

2. *Semantic Errors*: Logical issues during interpretation, like undefined variables or unsupported
   operations.

3. *Runtime Errors*: Issues encountered while executing the interpreted program, such as division
   by zero or recursive depth limits.


### Parser changes in Example


The following code demonstrates how the parser introduces the concept of a "main" block by marking
certain BLOCK nodes in the Abstract Syntax Tree (AST) based on the context of parsing.

```c
int final = FALSE;
..


ASTNode *block() {
    ASTNode *blockNode = createNode(NODE_BLOCK, final ? "main" : NULL);
    if (final) final = FALSE;
    ..

    while (accept(PROCSYM)) {
        ..
        int wasFinal = final;
        final = FALSE;
        addChild(procNode, block());
        final = wasFinal;
        ..
        addChild(blockNode, procNode);
        ..
    }
    addChild(blockNode, statement());
    final = FALSE;
    return blockNode;
}

ASTNode *program() {
   ..
    final = TRUE;
    addChild(programNode, block());
   ..
}
```

#### Explanation of Changes

`final`variable:

The final variable is a flag that determines whether the current block being parsed should be
marked as the "main" block. It helps differentiate the global main block from nested blocks
within procedures.

Marking the main Block:
- When a BEGIN symbol (BEGINSYM) is encountered, a BLOCK node is created. If final is TRUE,
  the block is labeled as "main".
- In the context of parsing the global scope, final is typically set to TRUE, ensuring the
  top-level executable block is marked as "main".

Nested Blocks:
- For nested blocks, such as those within procedures, the final flag is temporarily reset
  to FALSE to prevent marking them as "main".
- After processing a nested block, the original value of final is restored to ensure the
  parser's state is consistent.


#### Example Output

This setup produces an AST with the following structure:

```
PROGRAM
    BLOCK: main
        .. // the main executable
```

The "main" label distinguishes the primary executable block of the program, allowing the
interpreter or semantic analyzer to enforce rules related to program execution.

#### Semantic Constraint

A semantic constraint ensures that there is exactly one BLOCK: main in the program. If
multiple executable blocks are marked as "main", or if no "main" block exists, the parser
or a subsequent validation step raises an error. This constraint enforces the rule that
a program must have a single entry point, which is beneficial for correctness and execution
consistency.

