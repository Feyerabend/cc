
## Description of the Gate-Level CPU and ALU Simulator

This simulator represents a simplified, yet detailed, model of a central processing unit (CPU) and
its arithmetic logic unit (ALU), constructed entirely from basic logic gates and derived circuits,
all implemented in C code to mimic hardware behaviour at a low level. The design draws inspiration
from classic computer architecture principles, such as those found in von Neumann machines, but
scaled down to a 4-bit word size for manageability while still capturing the essence of gate-level
operations. By building everything from fundamental gates like NOT, AND, OR, and XOR, the simulator
demonstrates how complex computational structures emerge from simple binary logic, providing insight
into how real hardware functions without relying on high-level abstractions. The entire system operates
on a simulated clock, with state changes occurring on rising edges, and it includes components like
registers, memory, and a control unit, all interconnected to perform fetch-decode-execute cycles on
a small set of instructions.

At the core of the simulator are the basic logic gates, which serve as the atomic building blocks
for all higher-level circuits. The NOT gate inverts a single bit, turning a 0 into 1 or vice versa,
implemented simply as a bitwise complement operation restricted to one bit. The AND gate outputs 1
only if both inputs are 1, effectively performing a logical multiplication. The OR gate outputs 1
if at least one input is 1, acting as a logical addition. The XOR gate, crucial for addition and
other operations, outputs 1 if the inputs differ, which is equivalent to addition modulo 2 in binary.
These gates are defined as functions that operate on single bits, ensuring that every subsequent
component is composed purely from these primitives, maintaining the gate-level fidelity throughout
the simulation.

Building upon these gates, the simulator constructs more complex arithmetic circuits, starting with
adders. A half adder combines XOR for the sum bit and AND for the carry bit, handling two input bits
without an incoming carry. A full adder extends this by incorporating an additional carry-in input,
using two half adders in sequence: the first processes the two data bits, and the second adds the
result to the carry-in, with an OR gate combining any carries generated. For multi-bit addition, a
ripple-carry adder chains full adders together, propagating the carry from the least significant
bit to the most significant across the 4-bit word, detecting overflow if a carry remains after the
last bit. Subtraction is simulated via 2's complement, where the subtrahend is inverted bit-by-bit
using NOT gates, then incremented by 1 using the adder, before adding it to the minuend. Bitwise
operations like AND, OR, and XOR are applied across the entire word by iterating over each bit
and using the corresponding gate, resulting in efficient parallel-like simulation of hardware logic.

The ALU integrates these arithmetic and logical operations into a single unit, selectable via control
signals. It accepts two 4-bit inputs (typically from the accumulator and an operand) and two operation
select bits (op0 and op1) to choose between ADD (00), AND (01), OR (10), or a pass-through for
LOAD (11). The ALU computes the result using the appropriate circuit, sets a zero flag if the output
is all zeros, and an overflow flag based on carry-out from addition. This modular design allows the
ALU to act as the computational heart of the CPU, handling data manipulation in response to
instructions, with all internal workings traceable back to gate operations.

Registers form the next layer, providing storage for data and state. Each register is an array of
D flip-flops (DFFs), one per bit, where a DFF captures its input on the rising clock edge if enabled,
simulating edge-triggered behaviour. The DFF itself is modelled behaviourally but could be expanded to
full NAND-based master-slave latches for even deeper gate purity. Reading a register aggregates the
bits from each DFF into a 4-bit value, while loading writes new data by clocking each bit individually.
Key registers include the program counter (PC) for tracking the current instruction address, the
accumulator (ACC) for holding computation results, the instruction register (IR) for the fetched
opcode and operand, the memory address register (MAR) for holding addresses during memory access,
and the memory data register (MDR) as a buffer, though less used in this simple design.

The random access memory (RAM) is fully gate-level, treating it as an array of 16 registers (each 4-bit),
simulating a small address space. An address decoder uses gates to match the input address against each
possible location, generating a one-hot enable signal for the selected word. Reading involves selecting
the enabled register's output, while writing loads data into the chosen register on the clock edge
if the write signal is active. This approach, while computationally intensive due to iterating over
all locations for decoding, accurately emulates hardware multiplexers and demultiplexers built from
gates, making the memory volatile and stateful like real SRAM.

The control unit orchestrates the entire system using hardwired combinational logic derived from gates.
It decodes the 2-bit opcode from the IR, generating signals like ALU operation selects, register load
enables, memory read/write, ALU source (immediate or memory), and halt. For example, an ADD instruction
(opcode 00) sets ALU ops to 00, enables ACC load, and selects immediate operand, all computed via AND,
OR, and NOT gates on the opcode bits. This microarchitecture ensures deterministic behaviour without
microcode, keeping the design straightforward yet illustrative of how control paths drive data flow.

The CPU operates in cycles, each simulating a clock tick to advance the state. In the fetch phase,
the PC's value loads into the MAR, the instruction at that address reads from RAM into the IR, and
the PC increments using the adder. The decode-execute phase interprets the opcode to produce control
signals, selects the ALU operand (immediate from IR or data from RAM), performs the ALU operation,
updates flags, and loads the result into the ACC if enabled. Memory writes, if singled, store the
ACC back to RAM at the operand address. The cycle repeats until a HALT instruction (opcode 11) is
encountered, which sets the halt signal to stop execution. This multi-phase approach, while simplified
to one function call per cycle in code, mirrors real pipelined or non-pipelined CPUs, with all
transitions governed by the clock to prevent race conditions.

To illustrate, the sample program loaded into RAM demonstrates basic execution: at address 0,
ADD 1 (binary 0001) adds 1 to the initial ACC of 0, resulting in 1; at 1, AND 3 (0111) bitwise-ANDs with 3,
keeping 1; at 2, OR 2 (1010) bitwise-ORs with 2, yielding 3; at 3, HALT (1100) stops. The simulation
runs this, capturing states after each cycle in JSON format, showing progressive changes in registers
and flags, with memory remaining static since no stores occur.

