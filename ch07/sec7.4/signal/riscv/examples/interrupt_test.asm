# Interrupt Test Program
# Designed to trigger various interrupts in vm_with_ivt
# - Timer interrupt (every 1000 instructions)
# - Instruction count milestone (every 10000 instructions)
# - Memory watchpoint (writes to address 0x100)
# - Can be interrupted with SIGUSR1 for breakpoint

.text
main:
    # Initialize stack at high address
    li sp, 0x10000
    
    # Write to memory location 0x100 to trigger watchpoint
    li t0, 0x100
    li t1, 0xDEADBEEF
    sw t1, 0(t0)
    
    # Print banner
    la a0, banner
    li a7, 4
    ecall
    
    # Initialize counter
    li s0, 0          # outer loop counter
    li s1, 100        # outer loop max
    
outer_loop:
    bge s0, s1, done
    
    # Inner computation loop (generates many instructions)
    li s2, 0          # inner counter
    li s3, 100        # inner max
    li s4, 0          # accumulator
    
inner_loop:
    bge s2, s3, inner_done
    
    # Do some computation
    add s4, s4, s2
    mul s4, s4, s0
    and s4, s4, s1
    or s4, s4, s2
    xor s4, s4, s3
    
    addi s2, s2, 1
    j inner_loop

inner_done:
    # Modify watched memory every 10 iterations
    li t0, 10
    rem t1, s0, t0
    bne t1, zero, skip_write
    
    li t0, 0x100
    add t2, s0, s4
    sw t2, 0(t0)      # Trigger watchpoint
    
skip_write:
    # Print progress every 20 iterations
    li t0, 20
    rem t1, s0, t0
    bne t1, zero, skip_print
    
    mv a0, s0
    li a7, 1
    ecall
    la a0, progress_msg
    li a7, 4
    ecall
    
skip_print:
    addi s0, s0, 1
    j outer_loop

done:
    # Print completion message
    la a0, done_msg
    li a7, 4
    ecall
    
    # Print final value at watchpoint
    li t0, 0x100
    lw a0, 0(t0)
    li a7, 1
    ecall
    
    li a0, 10
    li a7, 11
    ecall
    
    # Exit
    li a7, 10
    ecall

.data
banner:
    .byte 73, 110, 116, 101, 114, 114, 117, 112, 116, 32, 84, 101, 115, 116, 10, 0
    # "Interrupt Test\n\0"

progress_msg:
    .byte 32, 105, 116, 101, 114, 97, 116, 105, 111, 110, 115, 10, 0
    # " iterations\n\0"

done_msg:
    .byte 68, 111, 110, 101, 33, 32, 70, 105, 110, 97, 108, 32, 118, 97, 108, 117, 101, 58, 32, 0
    # "Done! Final value: \0"
