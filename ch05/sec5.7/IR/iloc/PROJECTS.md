
## Projects on ILOC

### Extending the RISC-V Compilation Pipeline: Project Ideas

The provided codebase forms a foundation for a toy compiler targeting RISC-V, with
intermediate representations, code generation, assembly, and execution via a virtual machine.
It handles basic arithmetic and assignments in a linear program flow, making it ripe
for *expansions* that introduce real compiler techniques, hardware emulation, or language
features. Below, are several project ideas, each building directly on the existing components
like the AST generator, ILOC IR, RISC-V backend, assembler, and VM. These range from
optimisations to new frontends, with suggestions on how to integrate them--perhaps by
also modifying the Makefile to include new steps or running them via the `compile.py`
pipeline script.


#### ILOC Optimisation Pass: Streamlining Intermediate Code

Introduce a modular optimization "plugin" that processes the ILOC instructions after
they're generated from the AST but before conversion to RISC-V assembly. This could
implement classic compiler optimisations we already tocuhed upon, like constant
propagation (replacing variables with known constants), common subexpression
elimination (avoiding redundant calculations), or dead code removal (eliminating unused
assignments). But this time at a lower level. For clarity, structure it as a separate
class in a new file like `iloc_optimizer.py`, which takes a list of ILOCInstruction
objects, analyses data flow (e.g., via a simple graph), and outputs an optimised list.
Integrate it into the pipeline by calling it in `compile.py` between 'ast_to_iloc'
and 'iloc_to_riscv' steps, then compare before-and-after instruction counts or execution
times in the VM to demonstrate efficiency gains. This project clarifies how mid-level
optimisations reduce code size without altering semantics, and it's extensible for more
advanced passes like loop-invariant code motion if you add control flow later.


#### Enhanced RISC-V Virtual Machine: Adding Realism and Debugging

Upgrade the existing `vm.py` from a basic interpreter to a more sophisticated emulator
by incorporating features like hardware interrupts (e.g., timer-based), memory-mapped
I/O for simulated devices (such as a simple UART for input/output), or support for privileged
instructions from the RISC-V spec. To make debugging easier, add a built-in tracer that
logs register changes, memory accesses, and instruction disassembly at each step, controllable
via command-line flags. For integration, extend the RISCVVM class with new methods for
handling exceptions or peripherals, and update the execute loop to check for interrupts
periodically. This not only makes the VM feel more like real hardware but also allows
testing edge cases, such as division by zero traps, providing a hands-on way to explore
low-level system design and clarifying why emulators are crucial for embedded development.


#### Simple Language Frontend: Parsing to AST

Expand the pipeline's input side by creating a basic parser for a mini programming language
(e.g., a subset of C-like syntax with variables, assignments, and expressions) that generates
the ASTNode structure. Use a library like PLY or write a recursive descent parser in a new
file like `parser.py` to tokenize and build the tree from source code strings. Hook it into
`example_program.py` by replacing 'create_program_ast' with a parse function that reads from
a '.src' file, ensuring compatibility with the existing 'ast_to_iloc' generator. This project
demystifies frontend compilation, showing how source code transforms into an abstract syntax
tree, and opens doors for adding features like error reporting or type annotations, ultimately
making the whole system a more complete compiler, but still, toy.


#### Alternative Backend: Targeting a Different ISA

Diversify the code generation by adding a new backend that translates ILOC to another instruction
set architecture, such as ARM or a simplified x86 subset, instead of RISC-V. Create a parallel
class to RISCVGenerator, say ARMGenerator in a file like `iloc_to_arm.py`, mapping ILOC ops to
equivalent assembly (e.g., ADD to "add r0, r1, r2") and handling register allocation similarly.
Update compile.py to accept a flag for backend selection, generating '.s' files for the chosen ISA,
then use an external assembler (or extend `asm.py`) for binary output. To run it, you'd need a
corresponding VM, but start simple by outputting assembly for manual verification. (An alternative
could be to use a Raspberry Pi Pico.) This highlights architectural differences—like RISC-V's
load/store model versus others' memory operands--and clarifies portability concepts in compilers,
making it a way to compare instruction efficiencies.


#### Control Flow Extensions: Loops and Conditionals

The current pipeline handles only *sequential* code; enhance it by adding support for control
structures like if-else and while loops to the AST, ILOC, and beyond. Introduce new NodeType
enums (e.g., IF, WHILE) with branches in ASTNode, then update `ast_to_iloc.py` to emit ILOC
jumps (add ILOCOp like JUMP, CBR for conditional branch) and labels. In `iloc_to_riscv.py`,
map these to RISC-V branches (e.g., beq, bne), ensuring proper label resolution. Finally,
verify in the VM by adding branch decoding if needed. Integrate via expanded `example_program.py`
with looped examples, like summing an array. This project elucidates how compilers manage
non-linear flow, including challenges like forward references, and transforms the system into
one capable of real programs, with room for optimisations like loop unrolling.


#### Performance Profiler: Analysing Execution Metrics

Build a profiling tool atop the VM to measure and report metrics like instruction counts,
cache misses (simulate a simple cache), or hotspot detection (e.g., most-executed ops).
Extend RISCVVM with counters for each opcode type and memory access, then add a post-execution
report method that outputs stats, perhaps visualised with matplotlib via the `code_execution`
tool. Tie it into the Makefile's run target with a '--profile' flag. For deeper insights,
compare profiles before and after applying an ILOC optimiser from another idea. This clarifies
performance bottlenecks in compiled code, teaching concepts like big-O in practice and why
profiling guides optimisations, while leveraging the pipeline's end-to-end nature for
before/after comparisons.

