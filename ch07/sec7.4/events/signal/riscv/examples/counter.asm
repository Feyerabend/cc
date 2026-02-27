# Simple Counter
# Counts from 1 to 20 and prints each number
# Good for basic testing and watching interrupts fire

.text
main:
    # Initialize
    li sp, 0x10000
    li t0, 1          # counter
    li t1, 21         # limit

loop:
    bge t0, t1, done
    
    # Print counter value
    mv a0, t0
    li a7, 1
    ecall
    
    # Print space
    li a0, 32
    li a7, 11
    ecall
    
    addi t0, t0, 1
    j loop

done:
    # Print newline
    li a0, 10
    li a7, 11
    ecall
    
    # Exit
    li a7, 10
    ecall
