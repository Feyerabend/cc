# Hello World - prints "Hello, World!" and exits
# Demonstrates: syscall 4 (print string), syscall 10 (exit)

.text
main:
    # Load address of hello string
    la a0, hello_str
    li a7, 4          # syscall 4 = print string
    ecall
    
    # Exit
    li a7, 10         # syscall 10 = exit
    ecall

.data
hello_str:
    .byte 72, 101, 108, 108, 111, 44, 32, 87, 111, 114, 108, 100, 33, 10, 0
    # "Hello, World!\n\0"
