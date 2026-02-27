# jump_table.asm
# Demonstrates jump table pattern for operation dispatch
# This is the fundamental pattern used in interpreters and VMs

.text
main:
    # Initialize stack pointer
    lui sp, 0x10        # sp = 0x10000
    
    # Test all operations
    li a0, 0            # operation 0: ADD
    li a1, 15
    li a2, 7
    jal perform_operation
    li a7, 1            # syscall: print result
    ecall
    
    li a0, 10           # print newline
    li a7, 11
    ecall
    
    li a0, 1            # operation 1: SUB
    li a1, 15
    li a2, 7
    jal perform_operation
    li a7, 1
    ecall
    
    li a0, 10
    li a7, 11
    ecall
    
    li a0, 2            # operation 2: MUL
    li a1, 15
    li a2, 7
    jal perform_operation
    li a7, 1
    ecall
    
    li a0, 10
    li a7, 11
    ecall
    
    li a0, 3            # operation 3: DIV
    li a1, 15
    li a2, 7
    jal perform_operation
    li a7, 1
    ecall
    
    li a0, 10
    li a7, 11
    ecall
    
    # Exit
    li a7, 10
    ecall

# ============================================================================
# perform_operation: Jump table dispatcher
# 
# This function demonstrates the jump table pattern:
# 1. Bounds check the operation code
# 2. Multiply by 4 (size of address) to get table offset
# 3. Load function address from table
# 4. Jump to the function
#
# Inputs:  a0 = operation code (0-3)
#          a1 = first operand
#          a2 = second operand
# Outputs: a0 = result
# ============================================================================
perform_operation:
    # Save return address
    addi sp, sp, -4
    sw ra, 0(sp)
    
    # Bounds check: operation must be 0-3
    sltiu t0, a0, 4     # t0 = 1 if a0 < 4, else 0
    beq t0, zero, error # if t0 == 0, invalid operation
    
    # === JUMP TABLE LOOKUP ===
    # This is the core of the jump table pattern
    
    # Step 1: Load base address of jump table
    la t0, jump_table   # t0 = &jump_table
    
    # Step 2: Calculate offset (operation_code * 4 bytes)
    slli a0, a0, 2      # a0 = a0 << 2 (multiply by 4)
    
    # Step 3: Add offset to base address
    add t0, t0, a0      # t0 = &jump_table + offset
    
    # Step 4: Load the function address from the table
    lw t0, 0(t0)        # t0 = *t0 (dereference to get function address)
    
    # Step 5: Jump to the function (indirect jump)
    jalr ra, t0, 0      # Jump to address in t0, save return to ra
    # === END JUMP TABLE LOOKUP ===
    
    j done

error:
    li a0, -1           # Return -1 for invalid operation

done:
    # Restore return address and return
    lw ra, 0(sp)
    addi sp, sp, 4
    ret

# ============================================================================
# Arithmetic operation functions
# Each function follows the calling convention:
# - Inputs in a1, a2
# - Output in a0
# - Must preserve all other registers
# ============================================================================

add_func:
    add a0, a1, a2      # a0 = a1 + a2
    ret

sub_func:
    sub a0, a1, a2      # a0 = a1 - a2
    ret

mul_func:
    mul a0, a1, a2      # a0 = a1 * a2
    ret

div_func:
    div a0, a1, a2      # a0 = a1 / a2
    ret

# ============================================================================
# Jump Table Data Structure
# This is an array of function pointers (addresses)
# Each entry is 4 bytes (one word) on RISC-V
# ============================================================================

.data
jump_table:
    .word add_func      # Index 0
    .word sub_func      # Index 1
    .word mul_func      # Index 2
    .word div_func      # Index 3
