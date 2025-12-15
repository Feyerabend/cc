
## SAP Instruction Set

This document describes the instruction set for the SAP Virtual Machine (VM),
a simple 16-bit virtual machine designed for educational purposes. Each instruction
is encoded as a 16-bit word, with the following structure:

- *Opcode*: 4 bits (bits 12-15)
- *Addressing Mode*: 2 bits (bits 10-11)
- *Operand*: 10 bits (bits 0-9)

The VM supports four addressing modes and a variety of instructions for arithmetic,
memory operations, logical operations, and control flow.

16-bit Instruction Format:
```
+------------------+----------------+----------------------------+
| Opcode (4 bits)  | Addr Mode (2)  | Operand (10 bits)          |
| Bits 15-12       | Bits 11-10     | Bits 9-0                   |
| 15 14 13 12      | 11 10          | 9 8 7 6 5 4 3 2 1 0        |
+------------------+----------------+----------------------------+
```

*Example*

Instruction: LDA #42

- Opcode: LDA (0x1)
- Addressing Mode: Immediate (0x0)
- Operand: 42 (0x02A in 10 bits)
- Encoded: (0x1 << 12) | (0x0 << 10) | 0x02A = 0x102A

Example: LDA #42
```
+-------------------+-----------------+--------------------------+
| 0 0 0 1           | 0 0             | 0 0 0 0 1 0 1 0 1 0      |
| Opcode: LDA (0x1) | Mode: Imm (0x0) | Operand: 42 (0x02A)      |
+-------------------+-----------------+--------------------------+
```



### Addressing Modes

The SAP VM supports the following addressing modes:

1. *Immediate (#)*: The operand is a literal value, sign-extended to 16 bits.
   - Example: `LDA #42` loads the value 42 directly into the accumulator.
2. *Direct*: The operand is a memory address from which the value is read or written.
   - Example: `LDA 0x100` loads the value stored at memory address 0x100.
3. *Indirect (@)*: The operand is a memory address that contains another address,
   from which the value is read or written.
   - Example: `LDA @0x100` loads the value from the address stored at 0x100.
4. *Indexed (,X)*: The operand is a memory address offset by the value in the X register.
   - Example: `LDA 0x100,X` loads the value from the address 0x100 + X.


### Instruction Set

Below is the complete instruction set for the SAP VM, including opcodes, descriptions,
affected flags, and examples.

| Opcode | Name | Description | Affected Flags | Example |
|--------|------|-------------|----------------|---------|
| 0x0 | NOP | No operation | None | `NOP` |
| 0x1 | LDA | Load accumulator | Z, N | `LDA #42` |
| 0x2 | STA | Store accumulator | None | `STA 0x100` |
| 0x3 | ADD | Add to accumulator | Z, N, C, O | `ADD #5` |
| 0x4 | SUB | Subtract from accumulator | Z, N, C, O | `SUB #3` |
| 0x5 | MUL | Multiply accumulator | Z, N, C, O | `MUL #2` |
| 0x6 | DIV | Divide accumulator | Z, N, C, O | `DIV #2` |
| 0x7 | AND | Logical AND with accumulator | Z, N | `AND #0xFF` |
| 0x8 | OR | Logical OR with accumulator | Z, N | `OR #0x0F` |
| 0x9 | XOR | Logical XOR with accumulator | Z, N | `XOR #0xFF` |
| 0xA | CMP | Compare with accumulator | Z, N, C | `CMP #10` |
| 0xB | JMP | Unconditional jump | None | `JMP 0x200` |
| 0xC | JZ | Jump if zero | None | `JZ 0x200` |
| 0xD | JNZ | Jump if not zero | None | `JNZ 0x200` |
| 0xE | JSR | Jump to subroutine | None | `JSR 0x300` |
| 0xF | RTS | Return from subroutine or halt | None | `RTS #1` |

#### Flags
- *Z*: Zero flag (set if result is zero)
- *N*: Negative flag (set if result is negative)
- *C*: Carry flag (set if arithmetic operation results in a carry or borrow)
- *O*: Overflow flag (set if arithmetic operation overflows)


### Details and Examples

#### 1. NOP (No Operation)
- *Opcode*: 0x0
- *Description*: Does nothing, increments the program counter (PC).
- *Affected Flags*: None
- *Example*:
  ```
  NOP
  ```
  - *Effect*: Advances the PC to the next instruction without changing any registers or memory.
  - *Use Case*: Used for timing delays or as a placeholder.

#### 2. LDA (Load Accumulator)
- *Opcode*: 0x1
- *Description*: Loads a value into the accumulator based on the addressing mode.
- *Affected Flags*: Z, N
- *Example*:
  ```
  LDA #42
  ```
  - *Effect*: Loads the value 42 into the accumulator. Sets Z=0, N=0 (since 42 is positive).
  - *Use Case*: Initialize the accumulator with a constant or value from memory.

#### 3. STA (Store Accumulator)
- *Opcode*: 0x2
- *Description*: Stores the accumulator value to a memory location based on the addressing mode.
- *Affected Flags*: None
- *Example*:
  ```
  LDA #123
  STA 0x100
  ```
  - *Effect*: Stores the value 123 at memory address 0x100.
  - *Use Case*: Save the accumulator value to memory for later use.

#### 4. ADD (Add to Accumulator)
- *Opcode*: 0x3
- *Description*: Adds a value to the accumulator based on the addressing mode.
- *Affected Flags*: Z, N, C, O
- *Example*:
  ```
  LDA #10
  ADD #5
  ```
  - *Effect*: Adds 5 to the accumulator (10 + 5 = 15). Sets Z=0, N=0, C=0, O=0.
  - *Use Case*: Perform addition operations.

#### 5. SUB (Subtract from Accumulator)
- *Opcode*: 0x4
- *Description*: Subtracts a value from the accumulator based on the addressing mode.
- *Affected Flags*: Z, N, C, O
- *Example*:
  ```
  LDA #10
  SUB #3
  ```
  - *Effect*: Subtracts 3 from the accumulator (10 - 3 = 7). Sets Z=0, N=0, C=0, O=0.
  - *Use Case*: Perform subtraction operations.

#### 6. MUL (Multiply Accumulator)
- *Opcode*: 0x5
- *Description*: Multiplies the accumulator by a value based on the addressing mode.
- *Affected Flags*: Z, N, C, O
- *Example*:
  ```
  LDA #5
  MUL #3
  ```
  - *Effect*: Multiplies the accumulator by 3 (5 * 3 = 15). Sets Z=0, N=0, C=0, O=0.
  - *Use Case*: Perform multiplication operations.

#### 7. DIV (Divide Accumulator)
- *Opcode*: 0x6
- *Description*: Divides the accumulator by a value based on the addressing mode.
- *Affected Flags*: Z, N, C, O
- *Example*:
  ```
  LDA #15
  DIV #3
  ```
  - *Effect*: Divides the accumulator by 3 (15 / 3 = 5). Sets Z=0, N=0, C=0, O=0.
  - *Use Case*: Perform division operations.

#### 8. AND (Logical AND with Accumulator)
- *Opcode*: 0x7
- *Description*: Performs a bitwise AND between the accumulator and a value.
- *Affected Flags*: Z, N
- *Example*:
  ```
  LDA #0xFF
  AND #0x0F
  ```
  - *Effect*: Performs bitwise AND (0xFF & 0x0F = 0x0F). Sets Z=0, N=0.
  - *Use Case*: Mask bits in the accumulator.

#### 9. OR (Logical OR with Accumulator)
- *Opcode*: 0x8
- *Description*: Performs a bitwise OR between the accumulator and a value.
- *Affected Flags*: Z, N
- *Example*:
  ```
  LDA #0xF0
  OR #0x0F
  ```
  - *Effect*: Performs bitwise OR (0xF0 | 0x0F = 0xFF). Sets Z=0, N=0.
  - *Use Case*: Set bits in the accumulator.

#### 10. XOR (Logical XOR with Accumulator)
- *Opcode*: 0x9
- *Description*: Performs a bitwise XOR between the accumulator and a value.
- *Affected Flags*: Z, N
- *Example*:
  ```
  LDA #0xFF
  XOR #0xFF
  ```
  - *Effect*: Performs bitwise XOR (0xFF ^ 0xFF = 0x00). Sets Z=1, N=0.
  - *Use Case*: Toggle bits in the accumulator.

#### 11. CMP (Compare with Accumulator)
- *Opcode*: 0xA
- *Description*: Compares the accumulator with a value, setting flags based on the result (accumulator - value).
- *Affected Flags*: Z, N, C
- *Example*:
  ```
  LDA #10
  CMP #10
  ```
  - *Effect*: Compares accumulator with 10 (10 - 10 = 0). Sets Z=1, N=0, C=0.
  - *Use Case*: Used before conditional jumps to test conditions.

#### 12. JMP (Unconditional Jump)
- *Opcode*: 0xB
- *Description*: Sets the program counter to the specified address.
- *Affected Flags*: None
- *Example*:
  ```
  JMP 0x200
  ```
  - *Effect*: Sets PC to 0x200, continuing execution from there.
  - *Use Case*: Implement loops or unconditional branches.

#### 13. JZ (Jump if Zero)
- *Opcode*: 0xC
- *Description*: Jumps to the specified address if the zero flag is set.
- *Affected Flags*: None
- *Example*:
  ```
  LDA #0
  CMP #0
  JZ 0x200
  ```
  - *Effect*: Since accumulator equals 0, zero flag is set, so PC is set to 0x200.
  - *Use Case*: Conditional branching based on zero result.

#### 14. JNZ (Jump if Not Zero)
- *Opcode*: 0xD
- *Description*: Jumps to the specified address if the zero flag is not set.
- *Affected Flags*: None
- *Example*:
  ```
  LDA #5
  CMP #0
  JNZ 0x200
  ```
  - *Effect*: Since accumulator is not 0, zero flag is not set, so PC is set to 0x200.
  - *Use Case*: Conditional branching based on non-zero result.

#### 15. JSR (Jump to Subroutine)
- *Opcode*: 0xE
- *Description*: Pushes the current PC onto the stack and jumps to the specified address.
- *Affected Flags*: None
- *Example*:
  ```
  JSR 0x300
  ```
  - *Effect*: Saves the current PC on the stack, sets PC to 0x300.
  - *Use Case*: Call a subroutine, allowing return via RTS.

#### 16. RTS (Return from Subroutine or Halt)
- *Opcode*: 0xF
- *Description*: If operand is 0, pops the return address from the stack and sets PC to it.
  If operand is non-zero, halts the VM with the operand as the exit code.
- *Affected Flags*: None
- *Example*:
  ```
  RTS #1
  ```
  - *Effect*: Halts the VM with exit code 1.
  - *Use Case*: Return from a subroutine or terminate the program.


### Example Program

Below is a short example program that calculates the sum of numbers from 1 to 5 using a loop,
similar to the `simple_loop` sample in `sap_vm_samples.c`.

```asm
; Initialize: sum = 0, i = 1, limit = 5
0x000: LDA #0          ; Load 0 into accumulator
0x001: STA 0x100       ; Store to sum (at 0x100)
0x002: LDA #1          ; Load 1 into accumulator
0x003: STA 0x101       ; Store to i (at 0x101)
0x004: LDA #5          ; Load 5 into accumulator
0x005: STA 0x102       ; Store to limit (at 0x102)

; Loop: sum += i; i++; while i <= limit
0x006: LDA 0x100       ; Load sum
0x007: ADD 0x101       ; Add i
0x008: STA 0x100       ; Store sum
0x009: LDA 0x101       ; Load i
0x00A: ADD #1          ; Increment i
0x00B: STA 0x101       ; Store i
0x00C: SUB 0x102       ; i - limit
0x00D: JZ 0x010        ; If i > limit, jump to done
0x00E: JMP 0x006       ; Loop back
0x00F: NOP             ; (padding)
0x010: LDA 0x100       ; Load final sum
0x011: RTS #1          ; Halt
```

- *Effect*: Computes 1 + 2 + 3 + 4 + 5 = 15, storing the result in the accumulator and memory address 0x100.
- *Execution*: Run with `./sap_vm_debug`, then use `load` to load a similar program (e.g., `loop`) and `run` to execute.


### Notes
- *Instruction Encoding*: Each instruction is encoded using `vm_encode_instruction(opcode, mode, operand)`.
  For example, `LDA #42` is encoded as `(0x1 << 12) | (0x0 << 10) | 42`.
- *Flags*: Arithmetic and logical instructions update flags based on the result. The CMP instruction sets
  flags based on the difference (accumulator - value).
- *Memory*: The VM has a 1024-word memory (16-bit signed integers), with addresses from 0x000 to 0x3FF.
- *Stack*: The stack grows downward from address 0x3FF (STACK_TOP). JSR pushes the return address, and RTS pops it.

This instruction set provides a foundation for writing simple programs while supporting debugging and testing
through the provided debugger and test suite.

