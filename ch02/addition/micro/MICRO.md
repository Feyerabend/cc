## Microcode and Machine Code

### What is Machine Code?

Machine code consists of binary instructions that the CPU executes directly. These instructions are
hardware-specific and control operations such as arithmetic, data movement, or branching. Each
instruction corresponds to an operation the CPU can perform, defined in its Instruction Set
Architecture (ISA). Examples include ADD, SUB, or JMP (as we show in the many variants of VMs).

### What is Microcode?

Microcode is a layer beneath machine code. It provides a mechanism for implementing complex machine
instructions as sequences of simpler, predefined micro-instructions. These micro-instructions manipulate
low-level hardware components such as registers, arithmetic units, or control signals.

Microcode serves as the *firmware layer* within a CPU, sitting between the hardware gates and the
machine code. When a machine code instruction is fetched and decoded, the control unit uses microcode
to orchestrate the detailed steps required to execute that instruction.

Thus:

A *machine code instruction* is mapped to a sequence of *microcode instructions* stored in a special
control memory. For example, a single ADD instruction might require a microcode sequence to load
operands, activate the ALU, and store the result.

Microcode directly interacts with *hardware components*, sending signals to gates, triggering specific
operations such as addition or subtraction in the ALU, or moving data between registers.

The relationship can be thought of as:

1. High-Level Language: Human-readable code like C or Python is compiled into machine code.

2. Machine Code: CPU-readable binary instructions.

3. Microcode: A firmware layer interpreting machine code into hardware-level actions.

4. Hardware (Gates): Logic gates (AND, OR, XOR) perform the final operations dictated by microcode.


#### But Why Use Microcode?

1. Flexibility: Microcode allows CPUs to support complex instructions without redesigning hardware.

2. Abstraction: It abstracts low-level operations, simplifying the design of machine instructions.

3. Upgradability: Manufacturers can update or patch microcode to fix hardware bugs or enhance
   functionality without altering physical components.


### Historical Perspective

1. In the early days there was no Microcode:
    - In the 1940s and 50s, early computers like the ENIAC executed hardwired instructions directly.
    - Changes in functionality required rewiring the machine.

2. Microcode introduction (1950s–60s):
    - IBM introduced microcode in its System/360 series, allowing multiple ISAs to be implemented on the same hardware.
    - Maurice Wilkes is credited with pioneering the concept of microprogramming.

3. Modern use:
    - Today, CPUs from Intel and AMD use microcode for managing complex instructions, debugging, and optimisation.
    - Microcode remains crucial in *backward compatibility*, enabling modern processors to execute older machine code.

You might notice here that CPUs such as ARM is not mentioned. Microcode is not always needed, and its use depends
largely on the type of CPU architecture. Reduced Instruction Set Computing (RISC) processors generally do *not*
rely on microcode in the same way that Complex Instruction Set Computing (CISC) processors, like those in the x86
family, do.

Instead of microcode, RISC processors (e.g. ARM) often use hardwired control logic to execute instructions.
This approach directly connects control signals to the hardware, eliminates the need for a microcode interpreter,
and optimises speed and efficiency at the cost of flexibility.

Microcode is crucial for the flexibility and functionality of CISC processors, but is largely unnecessary for
RISC architectures due to their simplicity and efficiency. RISC achieves its goals through hardwired control,
providing a trade-off of speed and power efficiency over the flexibility offered by microcode.


#### Python Example

In the example:
- Machine Code Instructions: High-level commands like ADD and SUB.
- Microcode Instructions: Internal operations such as LOAD_A, LOAD_B, MICRO_ADD, and OUTPUT_ACC.
- Hardware (Simulated): Registers (A, B, ACC) and operations simulate the gates' behavior.

This setup reflects how a single machine code instruction (e.g. ADD) triggers a sequence of detailed microcode steps,
mimicking how real CPUs execute complex operations. For instance:
- ADD 7, 3 translates into:
    1.	Load 7 into Register A.
    2.	Load 3 into Register B.
    3.	Perform addition using the ALU (via microcode).
    4.	Store the result in ACC.


### Conclusion

Microcode is an elegant solution to the challenge of bridging the high-level complexity of machine instructions
with the simplicity of hardware gates. It optimizes flexibility and functionality in CPU design, ensuring both
backward compatibility and the ability to handle intricate operations efficiently. While largely hidden from
software developers, microcode plays a certain role in the invisible layers that power modern computing.
