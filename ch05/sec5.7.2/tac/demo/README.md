
## Three-Address Code (TAC)

Three-Address Code (TAC) is an intermediate representation used in compilers
to bridge the gap between high-level source code and low-level machine code.
It's called "three-address" because each instruction involves at
most three operands (addresses).

Think of TAC as the "universal translator" of programming languages--it's
low-level enough to be close to machine code, yet high-level enough to be
platform-independent and easy to optimise.

TAC represents programs as a sequence of simple instructions,
where each instruction has at most three operands:
```
x = y op z    # Binary operation
x = op y      # Unary operation
x = y         # Assignment
```

#### Components

1. *Operands*: Variables, constants, or temporary variables
2. *Operators*: Arithmetic (+, -, *, /), logical (&&, ||), relational (<, >, ==)
3. *Temporary Variables*: Store intermediate results (t0, t1, t2, ...)
4. *Labels*: Mark locations for jumps and branches


#### Simple Example

High-level expression:
```c
result = a + b * c
```

Equivalent TAC:
```
t0 = b * c
result = a + t0
```


#### 1. *Simplification*
Complex expressions are broken down into simple,
atomic operations that are easier to analyse and translate.

#### 2. *Optimisation Target*
TAC is ideal for easy compiler optimisations:
- Constant folding
- Dead code elimination
- Common subexpression elimination
- Register allocation

#### 3. *Platform Independence*
TAC is architecture-neutral. The same TAC can generate code
for x86, ARM, RISC-V, or any other architecture.

#### 4. *Analysis Friendly*
The simple structure makes it easy to perform:
- Data flow analysis
- Control flow analysis
- Type checking
- Security analysis


### From Source to TAC

#### Step 1: Parsing and AST Construction

High-level expression:
```
a + (b * c) / 5 - 8
```

Abstract Syntax Tree (AST):
```
        -
       / \
      +   8
     / \
    a   /
       / \
      *   5
     / \
    b   c
```

#### Step 2: AST Traversal

Using *postorder traversal* (visit children before parent),
we process the tree from leaves to root.

#### Step 3: TAC Generation

Each node generates TAC instructions:

```
t0 = b * c    # Multiply b and c
t1 = t0 / 5   # Divide result by 5
t2 = a + t1   # Add a to result
t3 = t2 - 8   # Subtract 8 from result
```

The final result is in `t3`.


### TAC Instruction Types

#### 1. Arithmetic Operations

```
t1 = a + b    # Addition
t2 = x - y    # Subtraction
t3 = p * q    # Multiplication
t4 = m / n    # Division
```

#### 2. Assignments

```
x = 42        # Constant assignment
y = x         # Variable copy
```

#### 3. Conditional Branching

```
t1 = x < 10
if t1 goto label_true
y = 0
goto label_end
label_true:
y = 1
label_end:
```

#### 4. Unconditional Jumps

```
goto label_start
```

#### 5. Loops

*While Loop:*
```
label_start:
t1 = i < 10
if not t1 goto label_end
body_of_loop
i = i + 1
goto label_start
label_end:
```

*For Loop:*
```
i = 0
label_loop:
t1 = i < n
if not t1 goto label_end
## loop body
i = i + 1
goto label_loop
label_end:
```

#### 6. Function Calls

```
param x         # Push parameter
param y
call func, 2    # Call with 2 parameters
result = t0     # Capture return value
```

#### 7. Arrays and Memory

```
t1 = arr[i]     # Array read
arr[i] = t2     # Array write
t3 = *ptr       # Pointer dereference
ptr = &x        # Address-of
```


### Generating TAC from Expressions

#### Example: Complex Expression

Expression: `(a + b) * (c - d) / e`

*Step-by-step TAC generation:*

```
t0 = a + b      ## Evaluate first parenthesis
t1 = c - d      ## Evaluate second parenthesis
t2 = t0 * t1    ## Multiply the results
t3 = t2 / e     ## Final division
```

#### Respecting Operator Precedence

Expression: `a + b * c`

Without parentheses, multiplication has higher precedence:

```
t0 = b * c      ## Multiplication first (higher precedence)
t1 = a + t0     ## Then addition
```


### Advanced TAC Features

#### Object-Oriented Constructs

*Member Access:*
```
t1 = obj.field
```

*Method Calls:*
```
param obj
call obj.method, 1
t2 = result
```

#### Exception Handling

```
label_try:
t1 = x / y
goto label_end
label_catch:
print "Division by zero"
goto label_end
label_end:
```

#### Complete Program Example

*C Source Code:*
```c
int factorial(int n) {
    if (n <= 1) 
        return 1;
    return n * factorial(n - 1);
}
```

*TAC Representation:*
```
label factorial:
param n
t1 = n <= 1
if t1 goto label_base_case
t2 = n - 1
param t2
call factorial, 1
t3 = returnval * n
return t3
label_base_case:
return 1
```

#### Iterative Factorial Example

*Plain TAC:*
```
label start:
n = 5
result = 1
label loop:
if n <= 0 goto end
result = result * n
n = n - 1
goto loop
label end:
print result
halt
```


### From TAC to Assembly

TAC serves as an excellent intermediate step
for generating assembly code.

#### Example Translation

*TAC:*
```
t0 = b * c
t1 = t0 / 5
t2 = a + t1
t3 = t2 - 8
```

*x86-like Assembly:*
```assembly
LOAD R1, b        ; Load b into R1
LOAD R2, c        ; Load c into R2
MUL R3, R1, R2    ; R3 = R1 * R2 (t0)
LOAD R4, 5        ; Load constant 5
DIV R5, R3, R4    ; R5 = R3 / R4 (t1)
LOAD R6, a        ; Load a into R6
ADD R7, R6, R5    ; R7 = R6 + R5 (t2)
LOAD R8, 8        ; Load constant 8
SUB R9, R7, R8    ; R9 = R7 - R8 (t3)
```

#### Register Allocation

Temporary variables (t0, t1, etc.) are mapped to:
- *Registers*: For frequently used variables (fast access)
- *Memory*: For less frequently used variables
  or when registers are exhausted

#### Optimisation Opportunities

*Constant Folding:*
```
Before: t0 = 3 * 5
After:  t0 = 15
```

*Common Subexpression Elimination:*
```
Before: t0 = a + b
        t1 = a + b
After:  t0 = a + b
        t1 = t0
```


### Implementation Examples

This repository includes two implementations of a
TAC generator for arithmetic expressions:

#### 1. Python Implementation (`tac.py`)
- Clean, readable code ideal for learning
- Step-by-step debugging output
- Handles operator precedence and parentheses
- Uses a stack-based approach

*Features:*
- Regular expression-based tokenization
- Infix expression parsing
- Interactive debugging output

#### 2. C Implementation (`tac.c`)
- Efficient, low-level implementation
- Shows memory management considerations
- Similar algorithm to Python version
- Good for understanding performance aspects

*Features:*
- Manual tokenisation
- Fixed-size arrays for simplicity
- Detailed stack state visualisation

#### Running the Examples

*Python:*
```bash
python3 tac.py
```

*C:*
```bash
gcc -o tac tac.c
./tac
```

Both programs convert the expression `a + (b * c) / 5 - 8` to TAC.

*Expected Output:*
```
t0 = b * c
t1 = t0 / 5
t2 = a + t1
t3 = t2 - 8
```


### Takeaways

1. *TAC is a bridge* between high-level code and machine code
2. *Simple structure* makes optimisation and analysis easier
3. *Platform independent* representation enables cross-compilation
4. *Temporary variables* store intermediate results explicitly
5. *Labels and jumps* handle control flow
6. *Foundation for modern compilers* used in GCC, LLVM, and others


### Further Reading

#### Compiler Design Topics
- *Static Single Assignment (SSA)*: An advanced form of IR
- *Control Flow Graphs (CFG)*: Graph representation of program flow
- *Data Flow Analysis*: Analysing how data moves through a program
- *Register Allocation*: Efficiently mapping variables to registers

#### Related Concepts
- *Abstract Syntax Trees (AST)*: Tree representation of source code
- *Intermediate Representations (IR)*: Various forms beyond TAC
- *LLVM IR*: A widely-used modern intermediate representation
- *Assembly Language*: The next step after TAC

