
## RISC-V Jump Tables: Theory and Practice

A comprehensive guide to jump table implementation in RISC-V assembly,
demonstrating one of the most fundamental patterns in systems programming.

A *jump table* is a programming technique that uses an array of function
pointers or addresses to implement efficient multi-way branching.
Instead of cascading if-else statements or switch cases, you use an index
to directly look up and jump to the appropriate code segment.

```
Traditional approach:          Jump table approach:
if (op == 0) func0();         jump_table[op]();
else if (op == 1) func1();    
else if (op == 2) func2();    
...
```

### Why Jump Tables Matter

#### Performance Benefits

- *Constant-time dispatch*: O(1) lookup regardless of number of cases
- *Predictable execution*: Single indirect branch vs. multiple conditional branches
- *Cache-friendly*: Sequential memory access pattern for the table
- *Branch predictor friendly*: Single indirect jump vs. multiple conditional branches

#### Real-World Applications

Jump tables are fundamental to:

1. *Virtual Machines & Interpreters*
   - Python's bytecode interpreter dispatch loop
   - Java Virtual Machine (JVM) instruction decode
   - JavaScript engine bytecode execution

2. *Operating Systems*
   - System call dispatch tables
   - Interrupt vector tables (IVT)
   - Device driver dispatch

3. *Embedded Systems*
   - State machine implementations
   - Protocol handlers (TCP/IP, USB, etc.)
   - Real-time event processing

4. *Compilers*
   - Switch statement optimization
   - Pattern matching dispatch


### RISC-V Implementation

#### The Basic Pattern

```asm
## Input: a0 = operation code (0-3)
## Table lookup and dispatch:

la t0, jump_table       ## 1. Load table base address
slli a0, a0, 2          ## 2. Scale index by 4 (word size)
add t0, t0, a0          ## 3. Calculate entry address
lw t0, 0(t0)            ## 4. Load function pointer
jalr ra, t0, 0          ## 5. Jump to function

## Jump table in .data section:
jump_table:
    .word func0
    .word func1
    .word func2
    .word func3
```

#### Key RISC-V Instructions

| Instruction | Purpose | Example |
|-------------|---------|---------|
| `LA` (Load Address) | Get table base address | `la t0, jump_table` |
| `SLLI` (Shift Left Logical Imm) | Multiply index by 4 | `slli a0, a0, 2` |
| `LW` (Load Word) | Fetch function address | `lw t0, 0(t0)` |
| `JALR` (Jump And Link Register) | Indirect jump | `jalr ra, t0, 0` |



### Examples Included

#### 1. Basic Jump Table (`jump.asm`)

Demonstrates the fundamental pattern with arithmetic operations.

*Features:*
- Bounds checking for safety
- Standard calling convention
- Clear documentation of each step

*Expected Output:*
```
22    # 15 + 7
8     # 15 - 7
105   # 15 * 7
2     # 15 / 7
```

#### 2. Mini Interpreter (`interpret.asm`)

A working bytecode interpreter showing practical jump table use.

*Architecture:*
- Stack-based virtual machine
- 6 opcodes (HALT, PUSH, ADD, SUB, MUL, PRINT)
- Opcode dispatch via jump table

*Sample Program:*
```
PUSH 10
PUSH 20
ADD      # Stack: [30]
PRINT    # Output: 30
PUSH 5
MUL      # Stack: [150]
PRINT    # Output: 150
HALT
```

#### 3. State Machine (`state.asm`)

Traffic light controller demonstrating state-based jump tables.

*States:*
- 0 = RED
- 1 = YELLOW
- 2 = GREEN

*Events:*
- 0 = TIMER
- 1 = EMERGENCY
- 2 = RESET



### Tools

#### Assembler (`asm.py`)

*Features:*
- Full RV32IM support (Base + Multiply/Divide)
- Two-pass assembly with label resolution
- Pseudo-instruction expansion
- Verbose mode for debugging
- Hex dump capability

*Command-line Options:*
```bash
python3 asm.py input.asm output.bin          # Basic assembly
python3 asm.py input.asm output.bin -v       # Verbose output
python3 asm.py input.asm output.bin -d       # Hex dump
```

#### Virtual Machine (`vm.py`)

*Features:*
- Complete RV32IM instruction set
- Instruction tracing
- Register state inspection
- Memory dumping
- Syscall support

*Command-line Options:*
```bash
python3 vm.py program.bin                    # Execute program
python3 vm.py program.bin -t                 # Trace execution
python3 vm.py program.bin -d                 # Debug mode
python3 vm.py program.bin -r                 # Print final registers
python3 vm.py program.bin -m 0x100:0x40      # Dump memory region
```


### Performance Analysis

#### Jump Table vs. Conditional Chain

For N cases:

| Approach | Time Complexity | Branch Count | Cache Behavior |
|----------|-----------------|--------------|----------------|
| If-else chain | O(N) average | Up to N branches | Poor (code scattered) |
| Jump table | O(1) | 1 indirect branch | Good (data locality) |

#### Instruction Count Comparison

*Conditional chain (worst case):*
```asm
# For 4 operations, worst case = 7 instructions
beq a0, zero, case0    # Compare and branch
beq a0, 1, case1       # Compare and branch
beq a0, 2, case2       # Compare and branch
j case3                # Default
```

*Jump table (constant):*
```asm
# Always exactly 5 instructions
la t0, jump_table      # Load address
slli a0, a0, 2         # Scale index
add t0, t0, a0         # Compute address
lw t0, 0(t0)           # Load pointer
jalr ra, t0, 0         # Jump
```

### Memory Layout

#### Typical Program Structure

```
Memory Map:              low address
┌----------------------┐ 0x00000
│  Text Segment        │  (Code)
│  - main              │
│  - perform_operation │
│  - func0, func1...   │
├----------------------┤ 
│  Data Segment        │
│  - jump_table:       │
│    [addr0]           │ <-- Table entries
│    [addr1]           │
│    [addr2]           │
│    [addr3]           │
│  - Other data        │
├----------------------┤
│       ^              │
│    Stack             │
└----------------------┘ 0x10000
                         high address
```

#### Address Calculation Example

```
Given: operation code = 2
       jump_table at 0x200
       Each entry = 4 bytes

Calculation:
1. offset = 2 * 4 = 8 bytes
2. address = 0x200 + 8 = 0x208
3. Load word at 0x208 → function address
4. Jump to that address
```

### RISC-V Calling Convention

All examples follow the standard RISC-V calling convention:

#### Register Usage

| Register | ABI Name | Purpose | Saved By |
|----------|----------|---------|----------|
| x0 | zero | Hardwired zero | N/A |
| x1 | ra | Return address | Caller |
| x2 | sp | Stack pointer | Callee |
| x8 | s0/fp | Saved/Frame pointer | Callee |
| x10-x11 | a0-a1 | Arguments/Return values | Caller |
| x12-x17 | a2-a7 | Arguments | Caller |
| x18-x27 | s2-s11 | Saved registers | Callee |
| x5-x7, x28-x31 | t0-t6 | Temporary registers | Caller |

#### Function Call Pattern

```asm
function:
    ## Prologue: save registers
    addi sp, sp, -4
    sw ra, 0(sp)
    
    ## Function body
    ...
    
    ## Epilogue: restore and return
    lw ra, 0(sp)
    addi sp, sp, 4
    ret
```


### Advanced Techniques

#### Bounds Checking

Always validate indices before table lookup:

```asm
sltiu t0, a0, TABLE_SIZE    ## t0 = (a0 < TABLE_SIZE)
beq t0, zero, error         ## if t0 == 0, out of bounds
```

#### Nested Jump Tables

For multi-dimensional dispatch:

```asm
# First level: state
la t0, state_table
slli s0, s0, 2
add t0, t0, s0
lw t0, 0(t0)

# Second level: event within state
slli a0, a0, 2
add t0, t0, a0
lw t0, 0(t0)
jalr ra, t0, 0
```

#### Sparse Tables

For sparse operation codes, use a hash or perfect hash function:

```asm
# Hash function to compress sparse opcodes
andi a0, a0, 0x7            ## Reduce to 0-7 range
la t0, sparse_table
...
```

### Common Pitfalls

#### 1. Forgetting to Scale Index

*WRONG:*
```asm
add t0, t0, a0              # Missing multiply by 4
```

*Correct:*
```asm
slli a0, a0, 2              # a0 *= 4
add t0, t0, a0
```

#### 2. Missing Bounds Check

*DANGER:*
```asm
la t0, jump_table
slli a0, a0, 2              # No validation!
...
```

*Safe:*
```asm
sltiu t0, a0, 4             # Check bounds first
beq t0, zero, error
...
```

#### 3. Incorrect Table Alignment

*WRONG:*
```asm
jump_table:                 # No alignment
    .word func0
```

*Correct:*
```asm
.align 2                    # Word alignment
jump_table:
    .word func0
```

### Comparison with Other Architectures

#### x86-64

```asm
; x86 uses similar pattern
lea rax, [jump_table]       ; Load table address
mov rdx, [rax + rcx*8]      ; Index with scale
jmp rdx                     ; Indirect jump
```

#### ARM

```asm
; ARM Thumb-2
LDR r3, =jump_table         ; Load table address
LDR r3, [r3, r0, LSL #2]    ; Load with shifted offset
BX r3                       ; Branch exchange
```

#### Key Difference

RISC-V requires explicit index scaling (`slli`),
while x86 and ARM can scale in the addressing mode.

### Building and Running


```bash
# Assemble with verbose output
python3 asm.py src/interpret.asm bin/interpret.bin -v

# Output shows:
# === First Pass: Label Collection ===
# Label 'main' @ 0x0000
# Label 'interpret_loop' @ 0x0008
# ...
# 
# === Second Pass: Code Generation ===
# 0x0000: lui sp, 0x10 => 0x00010137
# ...

# Run with instruction trace
python3 vm.py interpret.bin -t

# Output shows each instruction execution:
# 0x0000: 00010137  LUI    sp, 0x10
# 0x0004: ...
```

### Reference

#### RISC-V Specifications

- [RISC-V ISA Specification](https://riscv.org/technical/specifications/)
- [RISC-V ABI Specification](https://github.com/riscv-non-isa/riscv-elf-psabi-doc)

#### Related Techniques

- Threaded code interpretation
- Direct threaded code
- Computed goto (GCC extension)
- Perfect hashing for dispatch

#### Books

- Patterson, D. A., & Hennessy, J. L. (2017). *Computer organization and design: RISC-V edition*. Morgan Kaufmann.
- Patterson, D. A., & Waterman, A. (2017). *The RISC-V reader: An open architecture atlas*. Strawberry Canyon LLC.

![RISCV Reader](./../../../assets/image/reader.png)

