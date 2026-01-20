
## An Excerpt from PL/0 User Manual: Op Codes and the Syntax / Mnemonics

An educational compiler typically outputs final machine or intermediate code after processing source code.
As a project, you could develop a code generator for PL/E that produces code resembling the example below,
specifically designed for execution by a PL/0 virtual machine. This exercise will deepen your understanding
of compiler back-end processes, including code generation and optimisation, while giving you practical
experience in translating high-level constructs into lower-level instructions suitable for PL/0’s architecture.

More on PL/0 you can find in:
https://raw.github.com/adamdunson/pl0-compiler/master/doc/PL0%20User%27s%20Manual.pdf

The following table is an excerpt from this manual.

| Op&nbsp;Code | Syntax&nbsp;Menmonics     | Description                                                                                          |
|---------|----------------------|------------------------------------------------------------------------------------------------------|
| 1       | LIT 0, M             | Push constant value (literal) M onto the stack                                                       |
| 2       | OPR 0, M             | Operation to be performed on the data at the top of the stack                                          |
|         | OPR 0, 0             | Return; used to return to the caller from a procedure                                                |
|         | OPR 0, 1             | Negation; pop the stack and return the negative of the value                                          |
|         | OPR 0, 2             | Addition; pop two values from the stack, add and push the sum                                        |
|         | OPR 0, 3             | Subtraction; pop two values from the stack, subtract second from first and push the difference        |
|         | OPR 0, 4             | Multiplication; pop two values from the stack, multiply and push the product                          |
|         | OPR 0, 5             | Division; pop two values from the stack, divide second by first and push the quotient                 |
|         | OPR 0, 6             | Is odd? (divisible by two); pop the stack and push 1 if odd, 0 if even                              |
|         | OPR 0, 7             | Modulus; pop two values from the stack, divide second by first and push the remainder                 |
|         | OPR 0, 8             | Equality; pop two values from the stack and push 1 if equal, 0 if not                                |
|         | OPR 0, 9             | Inequality; pop two values from the stack and push 0 if equal, 1 if not                              |
|         | OPR 0, 10            | Less than; pop two values from the stack and push 1 if first is less than second, 0 if not          |
|         | OPR 0, 11            | Less than or equal to; pop two values from the stack and push 1 if first is less than or equal second, 0 if not |
|         | OPR 0, 12            | Greater than; pop two values from the stack and push 1 if first is greater than second, 0 if not     |
|         | OPR 0, 13            | Greater than or equal to; pop two values from the stack and push 1 if first is greater than or equal second, 0 if not |
| 3       | LOD L, M             | Load value to top of stack from the stack location at offset M from L lexicographical levels down   |
| 4       | STO L, M             | Store value at top of stack in the stack location at offset M from L lexicographical levels down    |
| 5       | CAL L, M             | Call procedure at code index M                                                                       |
| 6       | INC 0, M             | Increment the stack pointer by M (allocate M locals); by convention, this is used as the first instruction of a procedure and will allocate space for the Static Link (SL), Dynamic Link (DL), and Return Address (RA) of an activation record |
| 7       | JMP 0, M             | Jump to instruction M                                                                                 |
| 8       | JPC 0, M             | Pop the top of the stack and jump to instruction M if it is equal to zero                             |
| 9       | SIO 0, 1             | Start I/O; pop the top of the stack and output the value                                              |
| 10      | SIO 0, 2             | Start I/O; read input and push it onto the stack                                                     |
