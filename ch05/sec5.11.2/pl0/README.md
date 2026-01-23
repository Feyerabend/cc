
## PL/0 Interpreter and Compiler

This code consists of a compiler and an interpreter for a really small, simple
programming language similar to PL/0 (or at the start of building PL/0). The
compiler translates a high-level program (with variable declarations and
arithmetic expressions) into a sequence of low-level instructions, while the
interpreter executes those instructions step by step.


### How the Compiler Works

The compiler takes a simple program written in a custom language and converts it into
a list of instructions that the interpreter can execute. The process happens in two
main passes:

1. First Pass: Collect Variables
The compiler scans the program and finds all variable declarations (var x). It assigns
each variable a memory location in a symbol table.

2. Second Pass: Compile Assignments
When the compiler encounters an assignment (x = 3 + 5), it:
- Translates expressions like 3 + 5 into load (LIT) and operation (OPR) instructions.
- Stores the result in the memory location assigned to the variable (STO).

For example, x = 3 + 5 is compiled into these instructions:

```assembly
LIT 0 3   # Push 3 onto the stack  
LIT 0 5   # Push 5 onto the stack  
OPR 0 2   # Add the top two values  
STO 0 3   # Store result in memory address 3  
```

### How the Interpreter Works

The interpreter takes the compiled instructions and executes them using a stack-based machine.
It keeps track of execution using:
- A stack (`s[]`) to store values and variables.
- A program counter (`p`) to track the current instruction.
- A base pointer (`b`) for function calls (not used here).
- A stack pointer (`t`) for memory allocation.

The interpreter reads each instruction and performs the corresponding operation. For example:
- `LIT 0 3` --> Push 3 onto the stack.
- `LIT 0 5` --> Push 5 onto the stack.
- `OPR 0 2` --> Pop two values, add them, push the result.
- `STO 0 3` --> Store the top value into memory at address 3.


### Running a Sample Program

Consider this small program:
```assembly
var x  
var y  

x = 3 + 5  
y = x + 2  
```

The compiler first assigns memory locations (x → 3, y → 4). It then translates the program into
machine instructions. When executed, the interpreter follows the instructions and calculates:

```assembly
x = 8  
y = 10  
```

Finally, the interpreter prints these values from memory.


### Opcodes

From: https://raw.githubusercontent.com/adamdunson/pl0-compiler/master/doc/PL0%20User's%20Manual.pdf

| Op Code | Syntax   | Description |
|---------|---------|-------------|
| 1       | LIT 0, M  | Push constant value (literal) M onto the stack |
| 2       | OPR 0, M  | Operation to be performed on the data at the top of the stack |
|         | OPR 0, 0  | Return; used to return to the caller from a procedure. |
|         | OPR 0, 1  | Negation; pop the stack and return the negative of the value |
|         | OPR 0, 2  | Addition; pop two values from the stack, add and push the sum |
|         | OPR 0, 3  | Subtraction; pop two values from the stack, subtract second from first and push the difference |
|         | OPR 0, 4  | Multiplication; pop two values from the stack, multiply and push the product |
|         | OPR 0, 5  | Division; pop two values from the stack, divide second by first and push the quotient |
|         | OPR 0, 6  | Is odd? (divisible by two); pop the stack and push 1 if odd, 0 if even |
|         | OPR 0, 7  | Modulus; pop two values from the stack, divide second by first and push the remainder |
|         | OPR 0, 8  | Equality; pop two values from the stack and push 1 if equal, 0 if not |
|         | OPR 0, 9  | Inequality; pop two values from the stack and push 0 if equal, 1 if not |
|         | OPR 0, 10 | Less than; pop two values from the stack and push 1 if first is less than second, 0 if not |
|         | OPR 0, 11 | Less than or equal to; pop two values from the stack and push 1 if first is less than or equal to second, 0 if not |
|         | OPR 0, 12 | Greater than; pop two values from the stack and push 1 if first is greater than second, 0 if not |
|         | OPR 0, 13 | Greater than or equal to; pop two values from the stack and push 1 if first is greater than or equal to second, 0 if not |
| 3       | LOD L, M  | Load value to top of stack from the stack location at offset M from L lexicographical levels down |
| 4       | STO L, M  | Store value at top of stack in the stack location at offset M from L lexicographical levels down |
| 5       | CAL L, M  | Call procedure at code index M |
| 6       | INC 0, M  | Increment the stack pointer by M (allocate M locals); by convention, this is used as the first instruction of a procedure and will allocate space for the Static Link (SL), Dynamic Link (DL), and Return Address (RA) of an activation record |
| 7       | JMP 0, M  | Jump to instruction M |
| 8       | JPC 0, M  | Pop the top of the stack and jump to instruction M if it is equal to zero |
| 9       | SIO 0, 1  | Start I/O; pop the top of the stack and output the value |
| 10      | SIO 0, 2  | Start I/O; read input and push it onto the stack |

9, 10 not impl.
