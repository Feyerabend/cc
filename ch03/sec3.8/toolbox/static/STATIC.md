
## Static Analyser

The REGVM program implements a simple register-based virtual machine that processes a
series of instructions, such as MOV, ADD, SUB, MUL, CMP, and control flow commands like
JMP and JZ. It operates with four registers (A, B, C, D), supports conditional flags
(zero and negative), and a program counter to manage execution flow. The instructions
are decoded and executed sequentially, allowing the simulation of small programs,
like the included example for factorial calculation.


### Description

Static analysis is a method of examining code *without executing* it, focusing on
detecting errors, inconsistencies, or potential issues. In this context, the static
analyzer for REGVM validates the program before it runs. It performs checks to ensure:

* All opcodes are valid and match the expected number of arguments.
* Registers and operands used in the instructions are defined and appropriate.
* Jump targets are correctly specified, either as valid line numbers or defined labels.
* Logical errors, such as invalid operations or unresolvable references, are flagged.

The analyzer aims to catch mistakes early, preventing runtime errors and improving
the program's reliability.
