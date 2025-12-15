
## Comparison of Simple CPU (scpu) and Enhanced CPU (ecpu)

The Simple CPU ([scpu](./scpu/)) and Enhanced CPU ([ecpu](./ecpu/)) represent
two distinct approaches to CPU emulation, reflecting different stages in processor
design evolution, with parallels somewhat the x86 architecture’s progression from
the 8086 to modern processors, or at least the idea of progression.


### Simple CPU (scpu)

The scpu is an 8-bit processor emulator with a straightforward fetch-decode-execute cycle. It fetches
16-bit instructions, decodes them into an opcode and operands (e.g., register selectors, immediate
values), and executes them via a switch-case structure in `cpu_decode_and_execute`. The ALU supports
arithmetic (ADD, SUB), logical (AND, OR, XOR, NOT), and shift (SHL, SHR) operations, updating flags
for zero, carry, overflow, and negative results. Memory access is handled through basic read/write
functions, with no complex addressing modes. Control flow instructions include jumps (JMP, JZ, JC)
and HALT. A microcode ROM stub exists but is underutilised, suggesting a transitional design. This
mirrors early x86 processors like the 8086, which used hardwired logic for direct instruction execution,
prioritising simplicity but limiting extensibility.


### Enhanced CPU (ecpu)

The ecpu adopts a clearer microcode-based architecture, *breaking instructions* into microinstructions stored
in a `microcode_rom`. Each instruction is executed over multiple micro-steps via `execute_microinstruction`,
with control signals (e.g., `alu_enable`, `reg_write_enable`) defining hardware behaviour. The VM includes
additional state variables (`current_instruction`, `micro_step`, `fetched_byte`) for microcode management.
The `init_microcode` function defines sequences for operations like ADD, SUB, LOAD, and HALT, enabling easy
expansion. The ecpu retains the scpu’s instruction set and `fetch` function for *compatibility* but uses
microcode for flexibility. This resembles later x86 processors (e.g., 80386, Pentium), which use microcode
to translate CISC instructions into ("RISC") micro-operations, supporting complex operations and compatibility.


### Parallels to x86

The scpu’s direct decoding ensures low-latency execution for a small instruction set, akin to the 8086’s
hardwired logic, but adding new instructions requires modifying core logic, a limitation seen in early x86.
The ecpu’s microcode approach, like post-80386 x86 processors, allows complex instructions to be decomposed
into micro-steps, facilitating extensibility and compatibility. The ecpu’s multi-step execution mirrors
x86’s pipelined architectures (e.g., 80486), while its control signals evoke modern x86’s data path management
for features like out-of-order execution. Both CPUs share the same instruction set, ensuring compatibility,
similar to x86’s ability to run legacy code via microcode translation. The scpu suits simple, resource-constrained
environments, while the ecpu’s modularity supports advanced features, reflecting x86’s evolution from
simplicity to complex, scalable designs.

While the parallels to x86 evolution highlight key design trends, they are illustrative, not literal,
as the scpu and ecpu are simplified emulators lacking the full complexity of real-world processors.

