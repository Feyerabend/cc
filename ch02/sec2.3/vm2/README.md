
## VM2

The inpiration of this VM version comes from stack-absed programming languages such as FORTH.
Moreover, this program implements a simple virtual machine (VM) that interprets and executes
a predefined sequence of instructions for calculating and printing Fibonacci numbers. The main
C file initializes the VM with a Fibonacci sequence-generating program, runs it, and measures
its execution time. The VM operates on a stack-based architecture, executing operations like
arithmetic, jumps, and stack manipulation, with custom commands such as TWODUP, ROT, and PRINT.

The C program is divided into a header file and a source file, demonstrating the typical
organization of these components. A separate file (`main.c`) is the starting point for
running the program. Also a `Makefile` is introduced to show how interaction between compiler
and source can be handled.


### Features

The provided code is a minimal implementation of a stack-based virtual machine (VM) in C,
designed to interpret a custom bytecode for generating Fibonacci numbers.

1. Main function (`main.c`):
	* The main function initializes a VM with a hardcoded sequence of bytecode instructions
      stored in the code[] array. This sequence calculates and prints the first few Fibonacci numbers.
	* The `program()` function creates a new VM, runs the bytecode, and prints the execution
      time. It uses functions from the `vm2.h` header, such as `newVM()` to create the VM2
      and `run()` to execute the program.

2. VM Implementation (`vm2.c`):
	* The VM operates by executing instructions on a stack, where each instruction manipulates
      the stack in some way, such as pushing or popping values, performing arithmetic operations,
      and branching logic.
	* Functions like `push()`, `pop()`, and `nextcode()` handle stack operations and instruction
      fetching.
	* The `run()` function implements the VM's instruction cycle, which continuously fetches and
      executes instructions from the `code[]` array until a HALT instruction is encountered.
	* Instructions include basic arithmetic (ADD, SUB, etc.), stack manipulation (DUP, ROT, TWODUP),
      conditional jumps (JPZ, JPNZ), and I/O (PRINT).
3.	VM Data Structures (`vm2.h`):
	* A VM struct stores the state of the virtual machine, including a stack, a program counter
      (`pc`), and global variables (`vars`).
	* Constants such as `STACK_SIZE` define the size of the stack, and an enumeration lists all
      supported opcodes for instructions like ADD, HALT, PRINT, etc.

The Fibonacci sequence generation works by:
* Starting with two initial values (0 and 1).
* Repeatedly adding the last two values on the stack and printing the result.
* Using control flow instructions (JPNZ) to loop until a predetermined limit is reached.
