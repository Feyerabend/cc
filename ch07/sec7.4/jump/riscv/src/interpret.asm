# interpret.asm
# A minimal bytecode interpreter demonstrating jump tables in practice
# This shows how languages like Python and Java use jump tables for dispatch

.text
main:
    lui sp, 0x10        # Init stack
    
    # Execute a simple bytecode program
    # Program: PUSH 10, PUSH 20, ADD, PRINT, HALT
    la t0, bytecode     # t0 = program counter
    la t1, stack_top    # t1 = stack pointer
    
interpret_loop:
    # Fetch next opcode
    lbu a0, 0(t0)       # Load opcode byte
    addi t0, t0, 1      # Increment program counter
    
    # Check for HALT (opcode 0)
    beq a0, zero, halt
    
    # Save interpreter state
    addi sp, sp, -12
    sw t0, 0(sp)        # Save program counter
    sw t1, 4(sp)        # Save stack pointer
    sw ra, 8(sp)        # Save return address
    
    # Dispatch to opcode handler via jump table
    la t2, opcode_table
    slli a0, a0, 2      # opcode * 4
    add t2, t2, a0
    lw t2, 0(t2)        # Load handler address
    
    # Call handler (a1 = program counter, a2 = stack pointer)
    mv a1, t0
    mv a2, t1
    jalr ra, t2, 0
    
    # Restore state (handler may have modified PC and SP)
    lw t0, 0(sp)        # Restore PC
    lw t1, 4(sp)        # Restore SP
    lw ra, 8(sp)
    addi sp, sp, 12
    
    j interpret_loop

halt:
    li a7, 10
    ecall

# -------------------------------------------------------
# Bytecode Handlers
# Each handler implements one virtual machine instruction
# -------------------------------------------------------

# HALT - opcode 0 (handled inline above)

# PUSH <value> - opcode 1
# Push immediate value onto stack
op_push:
    lbu t3, 0(a1)       # Load immediate value
    addi a1, a1, 1      # Advance PC past immediate
    sw t3, 0(a2)        # Push to stack
    addi a2, a2, 4      # Advance stack pointer
    
    # Update saved state
    sw a1, 0(sp)
    sw a2, 4(sp)
    ret

# ADD - opcode 2
# Pop two values, add them, push result
op_add:
    addi a2, a2, -4     # Pop first operand
    lw t3, 0(a2)
    addi a2, a2, -4     # Pop second operand
    lw t4, 0(a2)
    add t3, t3, t4      # Add
    sw t3, 0(a2)        # Push result
    addi a2, a2, 4
    
    sw a2, 4(sp)        # Update stack pointer
    ret

# SUB - opcode 3
op_sub:
    addi a2, a2, -4
    lw t4, 0(a2)        # Second operand
    addi a2, a2, -4
    lw t3, 0(a2)        # First operand
    sub t3, t3, t4
    sw t3, 0(a2)
    addi a2, a2, 4
    
    sw a2, 4(sp)
    ret

# MUL - opcode 4
op_mul:
    addi a2, a2, -4
    lw t3, 0(a2)
    addi a2, a2, -4
    lw t4, 0(a2)
    mul t3, t3, t4
    sw t3, 0(a2)
    addi a2, a2, 4
    
    sw a2, 4(sp)
    ret

# PRINT - opcode 5
# Pop and print top of stack (destructive - removes value)
op_print:
    addi a2, a2, -4     # Pop value
    lw a0, 0(a2)
    
    # Print integer syscall
    li a7, 1
    ecall
    
    # Print newline
    li a0, 10
    li a7, 11
    ecall
    
    sw a2, 4(sp)        # Update stack pointer
    ret

# -----------------------------------

.data

# Opcode dispatch table
# Maps opcode number to handler function address
opcode_table:
    .word halt          # 0: HALT
    .word op_push       # 1: PUSH
    .word op_add        # 2: ADD
    .word op_sub        # 3: SUB
    .word op_mul        # 4: MUL
    .word op_print      # 5: PRINT

# Sample bytecode program
# Format: [opcode] [immediate] [opcode] ...
# Program: PUSH 10, PUSH 20, ADD, PUSH 5, MUL, PRINT, HALT
# This computes (10 + 20) * 5 = 150
bytecode:
    .byte 1, 10         # PUSH 10
    .byte 1, 20         # PUSH 20
    .byte 2             # ADD (stack: [30])
    .byte 1, 5          # PUSH 5 (stack: [30, 5])
    .byte 4             # MUL (stack: [150])
    .byte 5             # PRINT (prints 150, stack: [])
    .byte 0             # HALT

# Stack space
.align 2
stack:
    .space 256
stack_top:
