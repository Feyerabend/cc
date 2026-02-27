# Fibonacci sequence (first 10 numbers)
    li t0, 0           # fib(n-2)
    li t1, 1           # fib(n-1)
    li t2, 10         # counter
loop:
    beq t2, zero, done
    add t3, t0, t1     # fib(n) = fib(n-1) + fib(n-2)
    
    li a7, 1           # print
    mv a0, t3
    ecall
    
    mv t0, t1          # shift values
    mv t1, t3
    addi t2, t2, -1
    j loop
done:
    li a7, 10
    ecall
