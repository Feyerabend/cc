
## RISC-V Instructions Manual (RV32I Subset + M Extension)

This is a concise tutorial/manual for the RISC-V instructions supported
in the provided assembler and virtual machine. It covers the base integer
set (RV32I) subset, plus the multiplication/division extension (M).
Instructions are grouped by type, with syntax, description, and notes.
All operations are 32-bit, with wrap-around for arithmetic
(no traps except memory bounds).


### Key Conventions
- Registers: `x0`-`x31` or ABI names (e.g., `a0`, `sp`, `ra`). `x0`/`zero` is always 0.
- Immediates: Decimal or hex (e.g., `0x10`), sign-extended where applicable.
- Offsets: For loads/stores, format like `12(sp)` (offset(register)).
- Labels: For branches/jumps, use defined labels (e.g., `loop:`).
- Pseudo-instructions: Convenience wrappers for real instructions.

### R-Type (Register-Register Arithmetic/Logic)
Format: `op rd, rs1, rs2`  
These perform operations between two registers and store in `rd`.

- *ADD*: Add `rs1 + rs2` -> `rd`.
- *SUB*: Subtract `rs1 - rs2` -> `rd`.
- *AND*: Bitwise AND `rs1 & rs2` -> `rd`.
- *OR*: Bitwise OR `rs1 | rs2` -> `rd`.
- *XOR*: Bitwise XOR `rs1 ^ rs2` -> `rd`.
- *SLL*: Logical left shift `rs1 << (rs2 & 0x1F)` -> `rd`.
- *SRL*: Logical right shift `rs1 >>> (rs2 & 0x1F)` -> `rd` (zero-fill).
- *SRA*: Arithmetic right shift `rs1 >> (rs2 & 0x1F)` -> `rd` (sign-fill).
- *SLT*: Set `rd = 1` if `rs1 < rs2` (signed), else 0.
- *SLTU*: Set `rd = 1` if `rs1 < rs2` (unsigned), else 0.

### M Extension (Multiply/Divide)
Format: `op rd, rs1, rs2`  
Handles 32-bit multiplication/division.
Division by zero returns special values (e.g., -1 for signed div).

- *MUL*: Lower 32 bits of `rs1 * rs2` (signed) -> `rd`.
- *MULH*: Upper 32 bits of `rs1 * rs2` (signed) -> `rd`.
- *MULHSU*: Upper 32 bits of `rs1 (signed) * rs2 (unsigned)` -> `rd`.
- *MULHU*: Upper 32 bits of `rs1 * rs2` (unsigned) -> `rd`.
- *DIV*: Signed divide `rs1 / rs2` -> `rd` (quotient; -1 if div by 0).
- *DIVU*: Unsigned divide `rs1 / rs2` -> `rd` (quotient; all 1s if div by 0).
- *REM*: Signed remainder `rs1 % rs2` -> `rd` (rs1 if div by 0).
- *REMU*: Unsigned remainder `rs1 % rs2` -> `rd` (rs1 if div by 0).

### I-Type (Register-Immediate Arithmetic/Logic/Shifts)
Format: `op rd, rs1, imm` (imm is 12-bit signed, except shifts: 5-bit unsigned).  
Shifts use `shamt` (0-31).

- *ADDI*: Add `rs1 + imm` -> `rd`.
- *ANDI*: Bitwise AND `rs1 & imm` -> `rd`.
- *ORI*: Bitwise OR `rs1 | imm` -> `rd`.
- *XORI*: Bitwise XOR `rs1 ^ imm` -> `rd`.
- *SLTI*: Set `rd = 1` if `rs1 < imm` (signed), else 0.
- *SLTIU*: Set `rd = 1` if `rs1 < imm` (unsigned), else 0.
- *SLLI*: Logical left shift `rs1 << shamt` -> `rd`.
- *SRLI*: Logical right shift `rs1 >>> shamt` -> `rd`.
- *SRAI*: Arithmetic right shift `rs1 >> shamt` -> `rd`.

### Load Instructions (I-Type)
Format: `op rd, offset(rs1)` (offset: 12-bit signed).  
Loads from address `rs1 + offset` into `rd`. Signed/unsigned extension to 32 bits.

- *LB*: Load signed byte -> `rd`.
- *LH*: Load signed halfword (16 bits) -> `rd`.
- *LW*: Load word (32 bits) -> `rd`.
- *LBU*: Load unsigned byte -> `rd`.
- *LHU*: Load unsigned halfword -> `rd`.

### Store Instructions (S-Type)
Format: `op rs2, offset(rs1)` (offset: 12-bit signed).  
Stores from `rs2` to address `rs1 + offset`.

- *SB*: Store byte (lower 8 bits of `rs2`).
- *SH*: Store halfword (lower 16 bits of `rs2`).
- *SW*: Store word (32 bits of `rs2`).

### Branch Instructions (B-Type)
Format: `op rs1, rs2, label` (or offset; 13-bit signed, even).  
Branches to `pc + offset` if condition true; else `pc + 4`.

- *BEQ*: Branch if `rs1 == rs2`.
- *BNE*: Branch if `rs1 != rs2`.
- *BLT*: Branch if `rs1 < rs2` (signed).
- *BGE*: Branch if `rs1 >= rs2` (signed).
- *BLTU*: Branch if `rs1 < rs2` (unsigned).
- *BGEU*: Branch if `rs1 >= rs2` (unsigned).

### Jump Instructions
- *JAL*: Format `jal rd, label` (or `jal label` for `rd=ra`;
  offset: 21-bit signed, even). Stores `pc + 4` in `rd`, jumps to `pc + offset`.
- *JALR*: Format `jalr rd, offset(rs1)` (or `jalr rd, rs1` for offset=0;
  offset: 12-bit signed). Stores `pc + 4` in `rd`, jumps to `(rs1 + offset) & ~1`
  (clears least bit for alignment).

### U-Type (Upper Immediate)
Format: `op rd, imm` (imm: 20-bit, shifted left by 12).

- *LUI*: Load upper immediate `imm << 12` -> `rd`.
- *AUIPC*: Add upper immediate to PC: `pc + (imm << 12)` -> `rd`.

### System Instructions
- *ECALL*: Environment call (syscall). Uses `a7` for syscall number:
  - 1: Print integer (`a0`).
  - 4: Print string (null-terminated at `a0` address).
  - 10: Exit program.
  - 11: Print character (`a0` & 0xFF`).
- *EBREAK*: Breakpoint (stops execution, prints message).

### Pseudo-Instructions (Assembled to Real Ones)
These are syntactic sugar; no direct encoding.

- *NOP*: `addi zero, zero, 0` (do nothing).
- *MV*: `addi rd, rs, 0` (move `rs` to `rd`).
- *LI*: `addi rd, zero, imm` (load small immediate; error if |imm| >= 2048).
- *J*: `jal zero, label` (jump, no link).
- *RET*: `jalr zero, ra, 0` (return from subroutine).

### Usage Tips
- *Assembler*: Reads from file (e.g., `input.s`), outputs binary (`output.bin`).
  Supports labels, comments (`#`), and inline labels/instructions.
- *VM*: Loads binary, executes from PC=0.
  Memory: 64KB.
  Syscalls print to console.
  Debug mode prints PC/instr/regs.
- *Examples*: See code for factorial, Fibonacci, array sum.
  Assemble with `python assembler.py input.s output.bin`;
  run with `python vm.py output.bin [-d]`.
- *Limitations*: No floating-point, atomic, or compressed instructions.
  Immediates limited by type. No hardware interrupts.


