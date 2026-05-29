## Projects

### Virtual Machine Construction

The following projects guide you from a minimal interpreter toward a complete stack-based
virtual machine. Each project builds on the previous. The code in `ch02/sec2.2.3` through
`ch02/sec2.5` and the additions under `ch02/addition/vms` provide working reference points,
but you should construct your own version rather than copy them. The learning is in the building.

Before writing any code, trace a small example program by hand. Write down the bytecode,
step through each instruction, and draw the stack state at each point. This manual trace
is your first specification.


#### Project 1: Minimal Stack VM

*Objective:* Build a VM that can evaluate arithmetic expressions stored as bytecode.

Your VM should support: `PUSH <n>`, `ADD`, `SUB`, `MUL`, `DIV`, `PRINT`, `HALT`.

Steps:
- Define an instruction set as constants or an enum.
- Write a `run` function that fetches the next instruction, decodes it, and executes it.
- Test by encoding `(3 + 4) * 2` as bytecode and running it.

*Constraint:* Do not use an AST or parser yet. Write the bytecode by hand.

*Questions to answer:*
- What happens if the stack underflows (you try to pop from an empty stack)?
- What should the VM do on division by zero?
- How do you know when the program has finished?


#### Project 2: Variables and Local State

*Objective:* Extend your VM to support named variables.

Add: `STORE <name>`, `LOAD <name>`, and a simple environment (a dictionary).

Steps:
- Add a store and a load instruction.
- Implement an environment as a flat dictionary mapping names to values.
- Write a bytecode program that calculates `x = 3 + 4; y = x * 2; print y`.

*Extension:* Add `LOAD_CONST` for small integer literals to separate constants from stack values.

*Questions to answer:*
- What is the difference between a variable that is on the stack and one that is in the environment?
- What happens if you try to load a variable that has not been stored?


#### Project 3: Control Flow

*Objective:* Add conditional branching and loops.

Add: `JUMP <addr>`, `JUMP_IF_FALSE <addr>`, `CMP_LT`, `CMP_EQ`.

Steps:
- Implement the program counter as an index into the instruction list.
- `JUMP` sets the PC directly. `JUMP_IF_FALSE` pops a boolean and jumps only if false.
- Write a bytecode program that computes the factorial of 5 using a loop.

*Hand-trace first:* Before coding the loop, write out every instruction and stack state
on paper. This reveals exactly what your implementation must handle.

*Questions to answer:*
- What is the difference between absolute and relative jump addresses?
- How would you implement a `for` loop versus a `while` loop in bytecode?
- What is an infinite loop in bytecode? How would you detect one?


#### Project 4: Functions and the Call Stack

*Objective:* Add function definitions and calls.

Add: `CALL <label>`, `RETURN`, `ENTER <nlocals>`.

Steps:
- Implement a call stack separate from the operand stack, or use stack frames.
- `CALL` saves the return address and jumps to the function's bytecode.
- `RETURN` restores the saved PC.
- Write a bytecode program that defines and calls a function that adds two numbers.

*Extension:* Support recursive calls. Test with a recursive Fibonacci or factorial.

*Questions to answer:*
- What information must be saved when a function is called?
- What is a stack frame, and how does your implementation create and destroy one?
- What happens if a recursive function never reaches its base case?


#### Project 5: Register VM Variant

*Objective:* Re-implement your VM using registers instead of a stack.

Design a register machine with a fixed number of registers (`R0`–`R7`).

Instructions: `MOV R<d> R<s>`, `LOAD_IMM R<d> <n>`, `ADD R<d> R<s1> R<s2>`, `PRINT R<d>`, `HALT`.

Steps:
- Replace the operand stack with an array of registers.
- Rewrite the bytecode for your factorial program in register form.
- Compare the number of instructions needed versus the stack version.

*Questions to answer:*
- Which version was easier to write bytecode for by hand?
- Which version do you think is easier to compile to from a high-level language? Why?
- Which version is more similar to a real CPU?


#### Project 6: Harvard Architecture Experiment

*Objective:* Separate instruction memory from data memory and observe what changes.

Use the files in `ch02/addition/harvard` as a reference.

Steps:
- Modify your VM so that bytecode is stored in one array and all data in another.
- Show that the VM cannot write to the instruction array at runtime.
- Try to construct a program that *would* self-modify under a von Neumann model,
  and show that it is impossible in the Harvard model.

*Questions to answer:*
- What security property does the Harvard separation provide?
- What does it prevent you from doing that a von Neumann machine allows?
- Where in ch04 (embedded systems) does this separation matter in practice?


#### Project 7: Memory Allocator Comparison

*Objective:* Compare three memory allocation strategies: malloc, memory pool, and arena.

Use the files in `ch02/addition/mems` as a starting point (`pool.c`, `memo.c`, `arena.c`).

Steps:
- Write a benchmark that allocates and frees 100,000 small objects using each strategy.
- Measure total time and peak memory usage.
- Intentionally fragment the heap under malloc. Show that pool and arena avoid fragmentation.

*Questions to answer:*
- In what kind of application would you choose a pool allocator over malloc?
- Why does an arena allocator not support freeing individual objects?
- What connection does this have to the lifetime management concepts in ch07?
