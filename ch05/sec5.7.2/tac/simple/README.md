
## TAC

Three-Address Code (TAC) is an intermediate representation used in compilers to bridge
the gap between the high-level source code and the low-level assembly or machine code.
It represents the program as a series of simple instructions, each involving at most
three operands. These operands typically include variables, constants, and temporary
variables that store intermediate results.

Parsing transforms a high-level expression (like 'a + (b * c) / 5 - 8') into a structured
representation, such as an abstract syntax tree (AST). TAC is generated as a step in the
translation process, often following the parsing phase.


__1. AST Traversal__

- During parsing, the expression is converted into an AST that reflects the
  precedence and associativity of operators.

- For example, the AST for a + (b * c) / 5 - 8 might look like this:

```text
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
- Generating TAC involves a postorder traversal of this tree, processing nodes
  from the leaves up to the root.


__2. Breaking Complex Expressions into Steps__

- TAC simplifies the expression by breaking it into a series of simple binary operations.

- For example, a + (b * c) / 5 - 8 becomes:

```text
t0 = b * c
t1 = t0 / 5
t2 = a + t1
t3 = t2 - 8
```

- This step-by-step representation is more manageable for the next stages
  of compilation.


__3. Temporary Variables__

- TAC introduces temporary variables (t0, t1, etc.) to store intermediate results.

- These variables are crucial for preserving partial results while respecting
  operator precedence and associativity.


### Generating Assembly Instructions

TAC is a useful intermediary in generating assembly instructions.

__1. Mapping Operations to Assembly__

- Each TAC instruction corresponds to one or more assembly instructions,
  depending on the target architecture.

- For arithmetic operations, TAC maps directly to assembly. For instance:

```text
t0 = b * c  ->  LOAD R1, b
                LOAD R2, c
                MUL R3, R1, R2
                STORE R3, t0
```

- Temporary variables (t0, t1, etc.) are typically mapped to registers or
  memory locations.


__2. Simplifying Register Allocation__

- TAC's explicit use of temporary variables makes it easier for the compiler
  to allocate registers or memory slots.

- For instance, a register allocator can decide which registers to assign to
  t0, t1, etc., ensuring efficient use of CPU resources.


__3. Handling Precedence and Associativity__

- Since TAC respects the operator precedence established during parsing, the
  assembly instructions derived from TAC also adhere to the correct evaluation order.

- This eliminates the need for the assembly generation phase to reanalyze operator
  precedence.


__4. Optimisation__

- TAC is a common target for compiler optimisations, such as constant folding,
  common subexpression elimination, and loop unrolling.

- For example, if b and c are constants, the TAC t0 = b * c can be precomputed
  as t0 = 15 (if b = 3 and c = 5), reducing the number of assembly instructions.


__5. Platform Independence__

- TAC is independent of any specific machine architecture. Once generated, the
  TAC can be converted into assembly for different architectures (x86, ARM, etc.),
  making it highly versatile.


#### Example: Generating Assembly from TAC

Let's translate the TAC for a + (b * c) / 5 - 8 into x86-like assembly instructions:

TAC:

```text
t0 = b * c
t1 = t0 / 5
t2 = a + t1
t3 = t2 - 8
```

Corresponding Assembly:

```assembly
LOAD R1, b        ; Load b into register R1
LOAD R2, c        ; Load c into register R2
MUL R3, R1, R2    ; Multiply R1 and R2, store result in R3 (t0)
LOAD R4, 5        ; Load constant 5 into R4
DIV R5, R3, R4    ; Divide R3 by R4, store result in R5 (t1)
LOAD R6, a        ; Load a into R6
ADD R7, R6, R5    ; Add R6 and R5, store result in R7 (t2)
LOAD R8, 8        ; Load constant 8 into R8
SUB R9, R7, R8    ; Subtract R8 from R7, store result in R9 (t3)
```

Here:
- Registers (R1, R2, etc.) are used to hold operands and intermediate results.
- The temporary variables (t0, t1, etc.) are mapped to registers or memory locations.
