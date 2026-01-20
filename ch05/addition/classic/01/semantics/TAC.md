
## Three-Address Code (TAC)

Generating Three-Address Code (TAC) from an AST and symbol table for a simple language like
PL/0 can be broken into several steps.


### AST and Symbol Table

- The AST represents program structure (e.g. expressions, statements, blocks).
- The Symbol Table keeps track of variables, constants, and procedures, ensuring
  you can map identifiers to memory locations or attributes.


### Understanding TAC

TAC represents the intermediate steps of program execution in the form of:
- Instructions: op x, y, z, where op is an operator and x, y, z are variables,
  constants, or temporary variables.
- Examples of TAC instructions:
    - t1 = a + b (binary operation)
    - if t1 < 10 goto L1 (conditional jump)
    - param x (function call arguments)
    - call proc_name (procedure invocation)


### AST to TAC: The General Process

The key is post-order traversal of the AST, where you recursively process
child nodes and generate TAC instructions for each node.

a. Expressions
- For binary operations like a + b (from an EXPRESSION node):
    - Recursively process a and b to generate their TAC (if needed).
    - Allocate a temporary variable (e.g. t1) and emit a TAC instruction:

```
t1 = a + b
```

- For constants or identifiers:
	- Look up the symbol in the symbol table.
	- Return the constant/variable name as it appears in TAC.

b. Assignments
- For x := a + b (from an ASSIGNMENT node):
	- Process the right-hand side (a + b) and get its result (e.g. t1).
	- Emit the TAC instruction for the assignment:

```
x = t1
```

c. Control Flow
- 1. If Statements
	- For an IF node:
	- Process the condition (e.g., a < b) and emit a TAC instruction:

```
if a < b goto L1
goto L2
L1:
.. (true block TAC)
L2:
```

- 2. While Loops
	- For a WHILE node:
	- Emit labels for the loop start and end.
	- Process the condition and body:

```
L1: 
if a < b goto L2
goto L3
L2:
.. (body TAC)
goto L1
L3:
```

d. Procedure Calls
- For CALL nodes:
    - Emit instructions to push arguments onto a stack:
```
param a
param b
call proc_name
```
	- Handle procedure entry and exit using dedicated labels and stack management.

e. Block Structure
- Each BLOCK (or BEGIN/END) node:
	- Simply traverse the child statements, emitting their corresponding TAC instructions in order.

4. Managing Temporary Variables
	- Use a counter to generate unique temporary variable names (t1, t2, ..).
	- Example:
	    - Process a + b -> generate t1 = a + b.
	    - Use t1 in subsequent TAC instructions.

5. Code Generator Algorithm (High-Level)

Generating TAC in pseudo-code:

```c
int temp_counter = 0;

char* generateTemp() {
    char* temp = malloc(10);
    sprintf(temp, "t%d", temp_counter++);
    return temp;
}

void generateTAC(ASTNode* node) {
    if (!node) return;

    switch (node->type) {

        case NODE_ASSIGNMENT: {
            char* rhs = generateTAC(node->children[1]); // process RHS
            char* lhs = node->children[0]->value;       // variable name
            printf("%s = %s\n", lhs, rhs);
            break;
        }

        case NODE_EXPRESSION: {
            char* left = generateTAC(node->children[0]);
            char* right = generateTAC(node->children[1]);
            char* temp = generateTemp();
            printf("%s = %s %s %s\n", temp, left, node->value, right);
            return temp;
        }

        case NODE_IF: {
            char* cond = generateTAC(node->children[0]); // condition
            printf("if %s goto L1\n", cond);
            printf("goto L2\n");
            printf("L1:\n");
            generateTAC(node->children[1]); // true block, recurse
            printf("L2:\n");
            break;
        }
        //  cases for other node types...
    }
}
```

6. Final Output

Using this approach, you’ll generate TAC for a given AST. For example, given:

```tac
x := 5;
if x < 10 then
    y := x + 1;
```

The corresponding AST might look like:

```
ASSIGNMENT
  IDENTIFIER: x
  NUMBER: 5
IF
  CONDITION: <
    IDENTIFIER: x
    NUMBER: 10
  BLOCK
    ASSIGNMENT
      IDENTIFIER: y
      EXPRESSION: +
        IDENTIFIER: x
        NUMBER: 1
```

The generated TAC:

```tac
t1 = 5
x = t1
if x < 10 goto L1
goto L2
L1:
t2 = x + 1
y = t2
L2:
```

This can then be fed into machine-specific backend or interpreted directly by a virtual machine.
