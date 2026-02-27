
## Jump Table in ARM Thumb-2

Thumb-2 is an instruction set architecture introduced by ARM for Cortex-M3 and later processors.
It extends the original Thumb instruction set with:
- Support for both 16-bit and 32-bit instructions.
- Support for richer operations (e.g., full LDR rX, =label, MOVW, MOVT, etc.).
- More powerful conditional execution and control-flow.

Thumb-2 keeps code compact (like Thumb) but also powerful (like full ARM).


### Subroutine

Assumptions
- r0 contains the operation selector: 0 = add, 1 = sub, 2 = mul, 3 = div
- r1 and r2 contain the operands
- Result will be in r0

```asm
.syntax unified
.thumb

.global main
.type main, %function

main:
    // assume r0 = op, r1 = a, r2 = b

    // bounds check (if needed), we skip it here for brevity

    // calculate offset and branch via table
    LDR     r3, =jump_table       // Load address of jump table
    LDR     r3, [r3, r0, LSL #2]  // Load function pointer from table
    BX      r3                    // Jump to selected function


add_func:
    ADD     r0, r1, r2
    BX      lr

sub_func:
    SUB     r0, r1, r2
    BX      lr

mul_func:
    MUL     r0, r1, r2
    BX      lr

div_func:
    // naive division assuming r2 != 0
    MOV     r3, r1
    MOV     r0, #0
div_loop:
    CMP     r3, r2
    BLT     div_done
    SUB     r3, r3, r2
    ADD     r0, r0, #1
    B       div_loop
div_done:
    BX      lr


.align 2
jump_table:
    .word add_func
    .word sub_func
    .word mul_func
    .word div_func
```

Notes
1. The jump table is built using .word entries pointing to the label of each function.
   The jump table thus uses function pointers.
2. LDR r3, =jump_table (pseudo instruction) loads the address of the table into r3.
3. LDR r3, [r3, r0, LSL #2] indexes into the jump table (each address is 4 bytes).
   It uses r0 (the operation index) to calculate the address.
   Uses the LSL #2 (logical shift left by 2) to multiply the index by 4
   (since each address is 4 bytes).
4. BX r3 branches (jumps) to the handler.
