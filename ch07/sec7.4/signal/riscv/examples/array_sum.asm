# Array Sum
# Sum an array of integers stored in memory
# Demonstrates: memory loads, loops, data section

.text
main:
    # Initialize stack
    li sp, 0x10000
    
    # Load array address
    la t0, array
    li t1, 10         # array length
    li t2, 0          # sum accumulator
    li t3, 0          # index

loop:
    bge t3, t1, done
    
    # Load array[i]
    slli t4, t3, 2    # t4 = i * 4 (word offset)
    add t5, t0, t4    # t5 = &array[i]
    lw t6, 0(t5)      # t6 = array[i]
    
    # sum += array[i]
    add t2, t2, t6
    
    addi t3, t3, 1
    j loop

done:
    # Print sum
    mv a0, t2
    li a7, 1
    ecall
    
    # Print newline
    li a0, 10
    li a7, 11
    ecall
    
    # Exit
    li a7, 10
    ecall

.data
.align 4
array:
    .word 1
    .word 2
    .word 3
    .word 4
    .word 5
    .word 6
    .word 7
    .word 8
    .word 9
    .word 10
    # Expected sum = 55
