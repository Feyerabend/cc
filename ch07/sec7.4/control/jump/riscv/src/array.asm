# Sum array elements
    li t0, 1000        # array base address
    li t1, 5           # array size
    
    # Initialise array
    li t2, 10
    sw t2, 0(t0)
    li t2, 20
    sw t2, 4(t0)
    li t2, 30
    sw t2, 8(t0)
    li t2, 40
    sw t2, 12(t0)
    li t2, 50
    sw t2, 16(t0)
    
    # Sum array
    li t3, 0           # sum = 0
    li t4, 0           # i = 0
sum_loop:
    beq t4, t1, print_result
    slli t5, t4, 2     # offset = i * 4
    add t5, t0, t5     # address = base + offset
    lw t6, 0(t5)       # load element
    add t3, t3, t6     # sum += element
    addi t4, t4, 1     # i++
    j sum_loop
    
print_result:
    li a7, 1
    mv a0, t3
    ecall
    li a7, 10
    ecall
