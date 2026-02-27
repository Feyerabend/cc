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
