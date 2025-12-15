
## Introduction to the SAP Virtual Machine (SAP VM)

The SAP Virtual Machine (SAP VM) is a low-level, educational virtual machine designed to emulate
the behaviour of a simple processor with a focus on direct memory manipulation, explicit addressing
modes, and a minimal instruction set architecture (ISA). Unlike higher-level virtual machines that
abstract away memory management (e.g., through memory allocation functions like `malloc` or
object-oriented constructs), the SAP VM operates closer to the hardware, directly addressing memory
locations and managing registers, a stack, and program flow in a manner akin to real microprocessors.
It is implemented in C and provides a robust debugging and testing environment, making it an
excellent tool for learning about computer architecture, assembly programming, and low-level system
operations.


### Features

1. *Memory Model*:
   - The SAP VM has a fixed memory size of 1024 16-bit words, as defined in `sap_vm_config.h`
     (`MEMORY_SIZE 1024`). Memory is addressed directly using 16-bit addresses (0x000 to 0x3FF),
     providing a flat, linear address space.
   - Specific memory regions are designated for different purposes:
     - `PROGRAM_START` (0x000): Where program code begins.
     - `DATA_MEMORY_START` (0x100): Typically used for data storage.
     - `STACK_TOP` (0x3FF): The top of the stack, which grows downward.
   - Unlike higher-level VMs that use abstract memory allocation (e.g., `alloc`),
     the SAP VM requires explicit memory address manipulation, mirroring how real hardware
     manages memory.

2. *Instruction Set Architecture (ISA)*:
   - The SAP VM supports a small but versatile set of 16 instructions, including:
     - Arithmetic: `ADD`, `SUB`, `MUL`, `DIV`
     - Logical: `AND`, `OR`, `XOR`
     - Control flow: `JMP`, `JZ`, `JNZ`, `JSR`, `RTS`
     - Data movement: `LDA` (load accumulator), `STA` (store accumulator)
     - Comparison: `CMP`
     - No-op: `NOP`
   - Instructions are encoded in 16-bit words, with 4 bits for the opcode, 2 bits for the
     addressing mode, and 10 bits for the operand, as defined by `OPCODE_SHIFT`, `ADDR_MODE_SHIFT`,
     and `OPERAND_MASK` in `sap_vm.h`.
   - Four addressing modes are supported: immediate, direct, indirect, and indexed, allowing
     flexible memory access patterns.

3. *CPU and Registers*:
   - The VM’s CPU (`cpu_t` in `sap_vm.h`) includes:
     - *PC* (Program Counter): Points to the next instruction.
     - *SP* (Stack Pointer): Manages the stack for subroutine calls and returns.
     - *ACC* (Accumulator): Holds results of arithmetic and logical operations.
     - *X* (Index Register): Used for indexed addressing.
     - *IR* (Instruction Register): Holds the current instruction.
     - *Flags*: Zero, negative, carry, and overflow flags for conditional operations.
   - This structure closely resembles a simple microprocessor, emphasising low-level control
     over hardware resources.

4. *Execution Model*:
   - The VM operates in a fetch-decode-execute cycle, implemented in `vm_step` (in `sap_vm.c`).
     Each instruction is fetched from memory, decoded into opcode, addressing mode, and operand,
     and then executed.
   - Execution can be controlled via `vm_run` (runs for a specified number of cycles) or
     `vm_run_until_halt` (runs until a halt condition, typically an `RTS` instruction with
     a non-zero operand).
   - The VM supports breakpoints, tracing, and debugging, making it ideal for educational purposes.

5. *Debugging and Testing*:
   - The `sap_vm_debug.c` file implements an interactive debugger with commands like `step`,
     `run`, `memory`, `disasm`, `breakpoint`, and `trace`, allowing users to inspect and control
     the VM’s state.
   - The test suite in `sap_vm_test.c` verifies core functionality (basic operations, memory
     operations, control flow) and sample programs like Fibonacci, factorial, and loops.
   - Sample programs in `sap_vm_samples.c` demonstrate practical use cases, such as iterative
     Fibonacci and factorial calculations, memory tests, and subroutine calls, all written in
     the VM’s assembly-like instruction set.

6. *Low-Level Nature*:
   - The SAP VM directly manipulates memory addresses. For example, instructions like `LDA`
     and `STA` operate on specific memory locations (e.g., 0x100 for data storage), and the
     programmer must explicitly manage these addresses.
   - The stack is implemented as a fixed region in memory, with the stack pointer (`SP`) directly
     referencing memory addresses, similar to real hardware like the 6502 or early Intel processors.
   - Subroutines (`JSR` and `RTS`) use the stack for return addresses, and memory access is constrained
     by the 1024-word limit, forcing careful resource management.


### Comparison to Higher-Level VMs

The SAP VM is significantly closer to the machine than the VMs described in your book. For example:
- *Memory Management*: The SAP VM uses fixed, addressable memory locations, requiring programmers
  to specify exact addresses (e.g., `STA 0x100` to store a value at address 0x100).
- *Instruction Set*: The SAP VM’s ISA is minimalist and assembly-like, with direct control over
  registers and memory, unlike higher-level VMs that might use interpreted bytecode or high-level
  constructs (e.g., method calls, garbage-collected objects).
- *Proximity to Hardware*: The SAP VM’s explicit handling of registers, flags, and a stack pointer
  mimics real CPU behaviour, while your book’s VMs likely abstract these details, focusing on
  portability or ease of use.
- *Debugging*: The SAP VM’s debugger provides low-level insights (e.g., inspecting memory,
  registers, and disassembled instructions), whereas higher-level VMs might offer debugging at
  the source code or object level.


### Practical Usage

To use the SAP VM, you can:
1. *Run the Debugger*: Execute `sap_vm_debug` to enter the interactive debugger, where you can
   load sample programs (e.g., `load fib`), run them (`run`), step through instructions (`step`),
   or inspect memory (`memory 0x100 0x10F`).
2. *Run Tests*: The `sap_vm_test.c` suite verifies the VM’s functionality and runs sample programs
   like Fibonacci (F(10) = 55) and factorial (5! = 120).
3. *Write Programs*: Create programs by encoding instructions using `vm_encode_instruction` and
   loading them into memory, either manually or via `vm_load_program`.


### Example: Fibonacci Program

The `load_fibonacci_program` function in `sap_vm_samples.c` illustrates the low-level nature of
the SAP VM. It calculates the 10th Fibonacci number iteratively by:
- Storing initial values (n=10, a=0, b=1) in memory at `DATA_MEMORY_START`.
- Using direct addressing to load and store values (e.g., `LDA 0x100` to load n).
- Implementing a loop with `JNZ` to iterate n-1 times, updating Fibonacci values in memory.
- Handling edge cases (n=0, n=1) with conditional jumps (`JZ`).

This program directly manipulates memory addresses and uses the VM’s instruction set, contrasting
with a high-level VM that might use variables or objects.


### Conclusion

The SAP VM is primarily an educational tool for understanding low-level computing concepts, including
memory addressing, instruction encoding, and CPU operations. Its design bridges the gap between high-level
programming and hardware, making it ideal for learning about assembly programming and computer architecture.
By directly manipulating memory addresses and using a simple ISA, it provides some contrast to the
abstracted VMs previously, offering a hands-on experience with the mechanics of a "real" processor.

To explore further, try running the debugger (`./sap_vm_debug`), loading a sample program like `fib`,
and stepping through its execution to see how the VM processes instructions and manages memory.
