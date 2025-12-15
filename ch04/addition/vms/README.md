
## Simulation of Hardware through Software

The study of computer hardware can be approached from multiple directions. Here, the perspective
is primarily through software. By employing programming, simulation, emulation, and virtual machines,
we obtain an accessible framework for investigating the fundamental mechanisms that underlie computer systems.

This software-centred approach allows us to model and experiment with core ideas such as instruction
execution, memory organisation, and control flow without the immediate need for physical hardware.
A central concept in this exploration is the *state machine*. Understanding how a state machine
functions provides valuable insight into the organisation of hardware, as it captures the structured,
stepwise nature of computation.

From this vantage point, the study can then progress to increasingly detailed levels of abstraction.
Beginning with virtual machines, one can move towards microcode and eventually to the logic gates that
constitute the physical realisation of computation. This progression reveals the layered architecture
of computing systems and clarifies the relationships between software abstractions and hardware implementation.


### Two Different Approaches

We start with a more conceptual approach to the "machine,"
rather than actual hardware.


#### The State Machine VM: An Illustration of Microcoding Principles

This [State Machine VM](./state/) provides a high-level, clear example
of the logic that underlies the execution of instructions within a CPU,
a concept often implemented through *microcode*.

* *What:* This VM's architecture is built as a series of nested state machines.
  There is a top-level VM state machine that governs the overall fetch-decode-execute
  cycle, and a separate, smaller state machine for each individual instruction.
  This is a direct parallel to how a complex instruction in a real CPU is executed.

* *How:* When the VM is in the `VM_EXECUTING` state, it hands control to an `InstructionSM`
  (Instruction State Machine). This instruction state machine then progresses through
  its own states (e.g., `INST_INIT`, `INST_OPERAND`, `INST_EXECUTE`). The VM doesn't 
  just perform the entire operation at once. Instead, it breaks it down into fundamental,
  sequential steps. For instance, an `OP_LOAD` instruction isn't a single action;
  it's a sequence of states that first fetches the operand and then pushes it onto the stack.

* *Why:* This approach is a pedagogical tool for visualising a *microcoded CPU design*.
  In real hardware, a complex instruction like `ADD` might be implemented by a sequence
  of simple control signals (the microcode) that are fetched from a small, internal
  ROM or PLA (Programmable Logic Array) within the CPU. The State Machine VM illustrates
  this exact principle: a complex macro-instruction is reduced to a series of simpler,
  atomic, and observable *micro-operations*, each represented by a state transition.
  This makes the VM's internal workings highly transparent and easy to trace.


#### The SAP VM: An Illustration of CPU-like Architecture and Addressing

This [SAP VM](./sap/) virtual machine illustrates the foundational design
of a classic Central Processing Unit (CPU), complete with registers and
various memory addressing modes.

* *What:* The SAP VM is a simplified model of a register-based computer. It features
  a central `cpu_t` struct with dedicated registers for the accumulator, program counter,
  stack pointer, and index register. Its instruction set is designed to work with
  different ways of accessing data in memory.

* *How:* The VM's instruction word is encoded to contain not only the operation to
  perform (`opcode_t`) but also a specific *addressing mode* (`addressing_mode_t`).
  This allows a single instruction like `OP_LDA` (Load Accumulator) to behave differently
  depending on how the operand is interpreted. For example, `LDA #42` (immediate mode)
  loads the number 42 directly, while `LDA $100` (direct mode) loads the value stored
  at memory address 100.

* *Why:* This design serves as a powerful illustration for understanding how real-world
  CPUs function. It demonstrates the importance of registers for fast, local data manipulation
  and the flexibility provided by different addressing modes to efficiently access data
  from various locations in memory (immediate values, direct locations, or calculated
  addresses via an index register).



### CPU Simulation through Microcode and Logic Gates

The provided code in [scpu](./cpu/scpu/) implements a software-based 8-bit CPU emulator,
simulating a virtual machine (VM) with a microcode-driven architecture. It includes
fundamental logic gates (AND, OR, XOR, NOT, NAND, NOR) that form the basis for half
adders, full adders, and an 8-bit ripple carry adder, enabling arithmetic and bitwise
operations. The Arithmetic Logic Unit (ALU) supports operations like ADD, SUB, AND,
OR, XOR, NOT, SHL, and SHR, with flag support for zero, carry, overflow, and negative
results. Microcode in a ROM defines control signals for each instruction, orchestrating
ALU operations, register updates, and memory accesses. The VM executes instructions by
fetching and processing micro-instructions, fully emulating the CPU's behaviour.
The microcode relies on logic gate-based operations, though implemented in software,
not hardware. Comprehensive tests verify the functionality of gates, adders, ALU,
microcode, and VM, including edge cases and performance scenarios.

Another enhanced version of a CPU in [ecpu](./cpu/ecpu/) illustrates even closer to 
the machine (taking some points from the previous more rudimentary), microcode,
instructions and logical gates. The "evolution" also reimagine the
[parallels](./cpu/README.md) to the x86 line of processors.

A simulation in C at the gate-level of some simple CPU functions can also be found
in [gates](./gates/).


### PIO

The `emu2040pio.py` script in [pio](./pio/) implements a Python-based emulator for
the Raspberry Pi Pico's Programmable I/O (PIO) system, simulating state machines
that execute low-level instructions for hardware control. It defines a set of
instruction types (e.g., JMP, WAIT, IN, OUT, PUSH, PULL, MOV, IRQ, SET, NOP)
with support for delays, side-set pins, and conditional execution. The emulator
includes a `PIOBlock` managing up to four state machines, each with registers
(X, Y, ISR, OSR), FIFOs, and GPIO/IRQ interactions. Instructions are parsed from
a text-based program format, supporting features like conditional jumps and bit
manipulation. The code provides demo programs for LED blinking, WS2812 RGB LED control,
UART transmission, and a counter with conditional jumps. Comprehensive error handling
and state tracking ensure accurate emulation of PIO behaviour. The script can run
specific demos (blink, ws2812, uart, counter) or all demos via command-line arguments.

