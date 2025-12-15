
## Projects


### SAP VM

These projects leverage the SAP VM's robust CPU model, register set, and addressing
modes to build upon a more "traditional" computer architecture.

* *Assembler and Disassembler:* Create a program that takes a text-based assembly
  file (e.g., `program.asm`) and converts it into the numeric instruction format
  the SAP VM understands. The disassembler would do the reverse, taking the numeric
  memory contents and generating a human-readable assembly listing. This would
  solidify your understanding of instruction encoding.

* *Extend the Instruction Set:* Add new instructions to the SAP VM. You could implement:
    * Logical shift and rotate instructions (`SHL`, `SHR`, `ROL`, `ROR`).
    * Conditional branching instructions based on flags (`JGT`, `JLT`, `JLE`, `JGE`).
    * A multiplication instruction that handles a 32-bit result.

* *Memory Management Unit (MMU) Simulation:* Add a new layer to the SAP VM that
  simulates an MMU. You would introduce concepts like virtual vs. physical addresses,
  page tables, and protection bits. The VM would then need to translate virtual
  addresses to physical addresses on every memory access.

* *Build a Simple Compiler:* Design a very simple language (e.g., one with basic
  arithmetic and loops) and write a compiler that translates it directly into SAP VM
  instructions. You could even use a simple parser generator like Lex/Yacc or
  Flex/Bison for this. (You can also return to this when reading up on compilers in
  [ch05](./../../ch05/)).


### State Machine VM

These projects focus on the elegant, step-by-step nature of the state machine design.

* *Add a Call Stack and Subroutines:* The existing `new_vm.c` has a simple stack but
  lacks explicit subroutine support. Implement `OP_CALL` and `OP_RET` instructions
  that push the return address onto a separate call stack and then pop it back off.
  This would make the VM Turing-complete and allow for modular programming.

* *Build a Graphical State Visualizer:* Create a simple tool that displays the VM's
  state as it steps through a program. This would be a great way to visualize the
  microcode-like execution. You could show the current state of the main VM and the
  instruction state machine, highlight the program counter, and show the stack contents.

* *Instruction Pipeline Simulation:* Modify the VM to simulate a simple pipeline.
  You could introduce stages like `FETCH`, `DECODE`, and `EXECUTE` that operate in
  parallel. You would then need to handle *pipeline hazards*, such as data
  dependencies between instructions, and figure out how to stall the pipeline
  when necessary.


### Cross-VM Projects

These projects could be adapted for either VM, allowing you to compare and contrast
the implementation approach.

* *A "High-Level" Assembly Language:* Create a more programmer-friendly assembly
  language that supports labels, variables, and macros. Write a preprocessor that
  takes this language and converts it into the simpler, direct instruction format
  for either VM.

* *Performance Comparison:* Instrument both VMs to measure and compare their
  performance. You could write a series of identical programs for both architectures
  (e.g., calculating Fibonacci numbers) and then track metrics like the number of
  cycles or instructions executed. This would highlight the performance trade-offs
  of the different designs.

* *Self-Modifying Code:* Write a program for either VM that modifies its own
  instructions in memory as it runs. This is an advanced concept that would
  test your understanding of the VM's memory and execution model.

