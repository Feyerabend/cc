
## State Machines and VMs 

A state machine-based virtual machine (VM) is an abstract model of a computer that operates by
transitioning between a finite number of states. This approach is conceptually similar to how
a physical computer processes instructions, making a state machine VM a good low-level representation
of a real machine.

A state machine VM, like the one in `new_vm.c`, mirrors the fundamental components and execution
cycle of a physical CPU. This is because both systems are driven by a continuous cycle of fetching,
decoding, and executing instructions.

* *Fetch-Decode-Execute Cycle*: A physical CPU continuously performs the fetch-decode-execute cycle.
  The VM orchestrates this same cycle using its primary state machine. The VM transitions from a
  *`VM_READY`* state to *`VM_FETCHING`* to load an instruction from memory, then to *`VM_DECODING`*
  to identify the instruction, and finally to *`VM_EXECUTING`* to carry it out. This sequential,
  state-driven process is a direct abstraction of the real hardware's operation.

* *Instruction-Level State Machines*: In the `new_vm.c` and `vm_sm.c` examples, each individual
  instruction is also implemented as its own state machine. For instance, the *`OP_LOAD`* instruction
  has states like *`INST_INIT`*, *`INST_OPERAND`*, and *`INST_EXECUTE`*. This multi-state approach
  for a single instruction, especially one with an operand, mimics a microprogrammed CPU design,
  where complex instructions are broken down into a series of simpler micro-operations. A real
  processor might take multiple clock cycles to complete a single instruction, which is analogous
  to how an instruction state machine might need several *`INST_EV_STEP`* events to transition to
  the *`INST_COMPLETE`* state.

* *Explicit State Management*: The VM's explicit state variables (`VMState` and `InstState`) and
  event-driven transitions (`VMEvent`, `InstEvent`) make the entire process transparent and
  deterministic. This contrasts with a traditional, more procedural VM implementation where the
  program counter and other registers are just incremented or modified in a linear flow. The state
  machine approach forces a clear, well-defined progression, which is how a hardware circuit
  operates at its core--each logical gate's output is a function of its current state and input.


### Abstractions in a Simple Programming Language VM

A simple programming language virtual machine, such as the *Python VM* or the *Java Virtual Machine (JVM)*,
is a higher-level abstraction than a state machine VM. While still built on the principles of a
virtual machine, they are intentionally designed to hide the low-level details of the underlying
hardware to provide a more convenient environment for developers.

* *Opcode Complexity*: Instructions in a high-level VM are often much more complex and abstract than
  those in the provided C examples. For instance, a JVM instruction might be something like
  `invokevirtual` to call a method, which involves complex operations like looking up the method
  in a class table and managing the call stack. The state machine VM's opcodes like *`OP_ADD`* and
  *`OP_SUB`* are much closer to the single, atomic operations a CPU performs, like integer addition
  or subtraction.

* *Memory and Stack Management*: High-level VMs include sophisticated features like automatic garbage
  collection and dedicated heap memory for objects, which are completely absent in the state machine
  VM examples. The provided VMs only manage a simple, fixed-size stack and an array for memory.

* *Turing Completeness*: The `new_vm.c` example introduces instructions like `OP_JMP`, `OP_BEZ`, and
  `OP_CALL`. These instructions for branching and function calls are what make the VM "more Turing
  complete," allowing it to perform any computable task. While a high-level VM is also Turing complete,
  it achieves this through more abstract, high-level constructs (e.g., `if-then-else` statements, loops,
  and function calls) that are compiled down to its bytecode, which is then interpreted by the VM.

In summary, a state machine VM's explicit state transitions and multi-step instructions align closely
with the low-level, sequential nature of hardware operation. In contrast, a simple programming language
VM abstracts away these details, providing a higher-level, more user-friendly execution environment that
is further removed from the physical machine's core logic.


### Higher Functions (Opcodes) in the VM

| Opcode   | Description |
|----------|-------------|
| OP_NOP   | No operation |
| OP_LOAD  | Loads an immediate value to the stack |
| OP_STORE | Stores the top of the stack to memory at a specific address |
| OP_FETCH | Loads a value from a memory address to the stack |
| OP_ADD   | Pops two values, pushes their sum |
| OP_SUB   | Pops two values, pushes their difference (`b - a`) |
| OP_MUL   | Pops two values, pushes their product |
| OP_DIV   | Pops two values, pushes their quotient (`b / a`) |
| OP_MOD   | Pops two values, pushes their remainder (`b % a`) |
| OP_DUP   | Duplicates the top of the stack |
| OP_SWAP  | Swaps the top two stack elements |
| OP_POP   | Pops and discards the top element |
| OP_JMP   | Unconditional jump to an address |
| OP_BEZ   | Branches if the top of the stack is zero |
| OP_BNZ   | Branches if the top of the stack is non-zero |
| OP_BLT   | Branches if the second value is less than the top value (pops both) |
| OP_BGT   | Branches if the second value is greater than the top value (pops both) |
| OP_CALL  | Calls a subroutine by pushing the return address to a call stack and jumping |
| OP_RET   | Returns from a subroutine by popping the address from the call stack |
| OP_PRINT | Prints the value on the top of the stack |
| OP_HALT  | Stops execution |


### States in the VM

| State VM      | Description |
|---------------|-------------|
| VM_UNINIT     | The VM is uninitialised |
| VM_READY      | The VM is ready to fetch the next instruction |
| VM_FETCHING   | The VM is fetching an instruction from memory |
| VM_DECODING   | The VM is decoding the fetched instruction |
| VM_EXECUTING  | The VM is executing an instruction via its dedicated state machine |
| VM_HALTED     | The program has completed normally |
| VM_ERROR      | The VM is in an error state |


### Lower-Level States in a State Machine

| State SM      | Description |
|---------------|-------------|
| INST_UNINIT   | The instruction state machine is uninitialised |
| INST_INIT     | The instruction is initialised |
| INST_OPERAND  | The instruction is fetching its operand from memory |
| INST_EXECUTE  | The instruction is performing its core operation |
| INST_COMPLETE | The instruction has finished executing successfully |
| INST_ERROR    | An error occurred during the instruction's execution |



### Conceptual Translation: How does it Work?

The core idea is *decomposition and hierarchy*. Instead of a single, monolithic state machine
that manages the entire VM and every instruction, the design breaks the problem into two distinct layers:

1. *Low-Level: Instruction State Machines*: Each instruction, like `OP_LOAD` or `OP_ADD`, is implemented
   as its own state machine (`InstructionSM`). These are simple, single-purpose machines that handle a
   specific task and its sub-steps. For example, a `LOAD` instruction must first fetch its operand from
   memory before performing the stack push. The `InstructionSM` handles this by transitioning from
   `INST_INIT` to `INST_OPERAND`, and then to `INST_EXECUTE`. This state-by-state execution is a
   low-level, atomic process.

2. *High-Level: VM State Machine*: The VM's state machine (`VirtualMachine`) acts as the conductor.
   Its states (`VM_READY`, `VM_FETCHING`, `VM_DECODING`, `VM_EXECUTING`) represent the major phases
   of the classic fetch-decode-execute cycle. Crucially, when the VM enters the `VM_EXECUTING` state,
   it delegates the work to the lower-level `InstructionSM`. The VM simply calls the `instruction_step`
   function, effectively handing control to the instruction's state machine until that machine reaches
   the `INST_COMPLETE` state.

This hierarchy allows the VM to be general and reusable, while the specific logic for each instruction
is cleanly separated. The VM doesn't really need to know the internal steps of an `OP_ADD` or `OP_JMP`;
it just knows to "run" the instruction's state machine until it's done.


### Sample Translation: OP_LOAD

Let's examine how the low-level `InstructionSM` for `OP_LOAD` supports the high-level VM.

| VM State Machine | Instruction State Machine | Description |
| :--- | :--- | :--- |
| *`VM_READY`* | `INST_UNINIT` | The VM is ready for the next instruction. |
| *`VM_FETCHING`* | `INST_UNINIT` | The VM fetches `OP_LOAD` from memory. |
| *`VM_DECODING`* | `INST_UNINIT` | The VM initializes the `InstructionSM` with `OP_LOAD`. The `InstructionSM` transitions to `INST_INIT` and determines that it needs an operand. |
| *`VM_EXECUTING`* | `INST_INIT` | The VM steps the `InstructionSM`. The instruction SM transitions to `INST_OPERAND` to get the value to be loaded. |
| *`VM_EXECUTING`* | `INST_OPERAND` | The `InstructionSM` fetches the operand from `memory[vm->pc + 1]`. It then transitions to `INST_EXECUTE`. |
| *`VM_EXECUTING`* | `INST_EXECUTE` | The `InstructionSM` pushes the fetched operand onto the VM's stack (`vm_push`). It then transitions to `INST_COMPLETE`. |
| *`VM_EXECUTING`* | `INST_COMPLETE` | The VM detects that the instruction is complete. It then increments the program counter (`vm->pc`) and transitions back to `VM_READY` for the next instruction. The `InstructionSM` is reset to `INST_UNINIT`. |



### Sample Translation: OP_ADD

To explain the "add" operation, we can follow the same upward translation model. The low-level `InstructionSM`
for `OP_ADD` is a simple state machine that encapsulates the logic for adding two numbers, while the high-level
VM's state machine orchestrates the entire process.

| VM State Machine | Instruction State Machine | Description |
| :--- | :--- | :--- |
| *`VM_READY`* | `INST_UNINIT` | The VM is ready for the next instruction. |
| *`VM_FETCHING`* | `INST_UNINIT` | The VM fetches `OP_ADD` from memory. |
| *`VM_DECODING`* | `INST_UNINIT` | The VM initializes the `InstructionSM` with `OP_ADD`. The `InstructionSM` transitions to `INST_INIT` and determines that it *does not* need an operand. |
| *`VM_EXECUTING`* | `INST_INIT` | The VM steps the `InstructionSM`. Since no operand is needed, the instruction SM immediately transitions to `INST_EXECUTE`. |
| *`VM_EXECUTING`* | `INST_EXECUTE` | The `InstructionSM` performs the core addition operation: it calls `vm_pop` twice to get the two top values from the stack, adds them, and then calls `vm_push` to place the sum back on the stack. If either pop or the push fails, the instruction SM transitions to `INST_ERROR`. The instruction SM then transitions to `INST_COMPLETE`. |
| *`VM_EXECUTING`* | `INST_COMPLETE` | The VM detects that the instruction is complete. It then increments the program counter (`vm->pc`) and transitions back to `VM_READY` for the next instruction. The `InstructionSM` is reset to `INST_UNINIT`. |



### What is Microcode?

The architecture described in `new_vm.c` and `vm_sm.c` is very close to the conceptual model of *microcode*,
but it's an abstract software implementation rather than a direct hardware one.

Microcode is a layer of instructions below the instruction set architecture (ISA) of a CPU. It's a low-level
program stored in a special control memory inside the processor. A single machine language instruction, like
`ADD` or `LOAD`, is typically executed by a sequence of these simpler micro-instructions. Each micro-instruction
controls specific hardware components, such as opening a data bus, enabling a register, or activating an
arithmetic logic unit (ALU) operation.


### Similarities to the State Machine VMs

The state machine VMs from the files mirror this concept precisely.

* *Decomposition*: The VM instruction (`OP_ADD`, `OP_LOAD`) corresponds to a high-level machine language
  instruction.
* *Micro-operations*: The individual states within the `InstructionSM` (`INST_INIT`, `INST_OPERAND`,
  `INST_EXECUTE`) are analogous to micro-instructions. Each state transition performs a small, atomic task.
  For example, the `INST_OPERAND` state in `OP_LOAD` is a step to fetch a single value, and the `INST_EXECUTE`
  state is a step to perform the push operation.
* *Orchestration*: The main VM state machine (`VM_FETCHING`, `VM_DECODING`, `VM_EXECUTING`) acts like the
  control unit in a real CPU. It reads the high-level instruction, then triggers the appropriate sequenceof micro-operations (state transitions) to execute it.

In essence, the `InstructionSM` functions as the software equivalent of a microcode sequencer, breaking down
a single VM instruction into a series of smaller, more granular steps, much like how a hardware control unit
uses microcode to execute a CPU instruction. The key difference is that this is all implemented in C code
and runs on a real machine, while microcode is embedded directly into a processor's hardware.


### Summary

The virtual machine (`new_vm.c`, `vm_sm.c`) is designed with a layered state machine architecture that
closely resembles the low-level operation of a physical CPU. This design makes the VM more transparent
and conceptually closer to hardware than a typical high-level VM for a programming language, as we have
gone through earlier.

* *The VM as a State Machine*: At the highest level, the VM itself is a state machine that cycles through
  the classic *fetch-decode-execute* loop. Its states (`VM_READY`, `VM_FETCHING`, `VM_DECODING`, `VM_EXECUTING`)
  represent the major phases of instruction processing. This top-level machine orchestrates the entire program
  flow.

* *Instructions as State Machines*: At a lower level, each individual instruction (opcode), such as `OP_ADD`
  or `OP_LOAD`, is implemented as its own distinct state machine (`InstructionSM`). These instruction-level
  state machines handle the granular steps required to complete a single operation. For example, a `LOAD`
  instruction is broken down into states like `INST_OPERAND` and `INST_EXECUTE`, each performing a simple,
  atomic task.

* *A Conceptual Bridge to Microcode*: This layered design is a direct conceptual parallel to *microcode*
  in a real CPU. The high-level VM instruction (`OP_ADD`) is analogous to a machine code instruction, while
  the sequence of states within the `InstructionSM` (`INST_INIT` -> `INST_EXECUTE` -> `INST_COMPLETE`) is
  the software equivalent of a microcode routine. This allows a complex operation to be built from simpler,
  well-defined state transitions, making the VM's internal workings transparent and deterministic, much
  like the logic gates and control signals of a physical processor.
