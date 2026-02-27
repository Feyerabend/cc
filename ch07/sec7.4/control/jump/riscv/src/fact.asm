# Calculate 5! (factorial)
    li a0, 5           # n = 5
    li a1, 1           # result = 1
loop:
    beq a0, zero, done # if n == 0, done
    mul a1, a1, a0     # result *= n
    addi a0, a0, -1    # n--
    j loop
done:
    li a7, 1           # syscall: print int
    mv a0, a1          # move result to a0
    ecall
    li a7, 10          # syscall: exit
    ecall
