# Factorial Calculator
# Calculates factorial of 5 (5! = 120)
# Demonstrates: loops, multiplication

.text
main:
    # Initialize stack pointer
    li sp, 0x10000
    
    # Calculate 5! iteratively
    li t0, 5          # n
    li t1, 1          # result = 1
    li t2, 1          # counter = 1
    
fact_loop:
    addi t3, t0, 1    # t3 = n + 1
    bge t2, t3, fact_done
    mul t1, t1, t2    # result *= counter
    addi t2, t2, 1    # counter++
    j fact_loop
    
fact_done:
    # Print result
    mv a0, t1
    li a7, 1          # syscall 1 = print integer
    ecall
    
    # Print newline
    li a0, 10
    li a7, 11         # syscall 11 = print char
    ecall
    
    # Exit
    li a7, 10
    ecall
