# Fibonacci Sequence
# Prints first 10 Fibonacci numbers
# Demonstrates: loops, memory operations

.text
main:
    # Initialize stack
    li sp, 0x10000
    
    # Setup: fib[0] = 0, fib[1] = 1
    li t0, 0          # fib[n-2]
    li t1, 1          # fib[n-1]
    li t2, 10         # counter
    
    # Print fib[0] = 0
    li a0, 0
    li a7, 1
    ecall
    li a0, 32         # space
    li a7, 11
    ecall
    
    # Print fib[1] = 1
    li a0, 1
    li a7, 1
    ecall
    li a0, 32
    li a7, 11
    ecall
    
    li t3, 2          # start at index 2
    
loop:
    bge t3, t2, done
    
    # fib[n] = fib[n-1] + fib[n-2]
    add t4, t0, t1
    
    # Print fib[n]
    mv a0, t4
    li a7, 1
    ecall
    li a0, 32         # space
    li a7, 11
    ecall
    
    # Shift: fib[n-2] = fib[n-1], fib[n-1] = fib[n]
    mv t0, t1
    mv t1, t4
    
    addi t3, t3, 1
    j loop

done:
    # Print newline
    li a0, 10
    li a7, 11
    ecall
    
    # Exit
    li a7, 10
    ecall
