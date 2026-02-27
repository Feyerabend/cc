# M Extension Test
# Tests multiply and divide instructions
# Demonstrates: MUL, DIV, REM operations

.text
main:
    # Initialize stack
    li sp, 0x10000
    
    # Test 1: Multiplication
    la a0, test1_msg
    li a7, 4
    ecall
    
    li t0, 12
    li t1, 7
    mul t2, t0, t1    # 12 * 7 = 84
    
    mv a0, t2
    li a7, 1
    ecall
    li a0, 10
    li a7, 11
    ecall
    
    # Test 2: Division
    la a0, test2_msg
    li a7, 4
    ecall
    
    li t0, 100
    li t1, 7
    div t2, t0, t1    # 100 / 7 = 14
    
    mv a0, t2
    li a7, 1
    ecall
    li a0, 10
    li a7, 11
    ecall
    
    # Test 3: Remainder
    la a0, test3_msg
    li a7, 4
    ecall
    
    rem t2, t0, t1    # 100 % 7 = 2
    
    mv a0, t2
    li a7, 1
    ecall
    li a0, 10
    li a7, 11
    ecall
    
    # Test 4: High multiply (upper 32 bits)
    la a0, test4_msg
    li a7, 4
    ecall
    
    lui t0, 0x10      # t0 = 0x10000 (use upper immediate)
    lui t1, 0x10      # t1 = 0x10000
    mulh t2, t0, t1   # Upper 32 bits of 0x10000 * 0x10000 = 1
    
    mv a0, t2
    li a7, 1
    ecall
    li a0, 10
    li a7, 11
    ecall
    
    # Exit
    li a7, 10
    ecall

.data
test1_msg:
    .byte 49, 50, 32, 42, 32, 55, 32, 61, 32, 0
    # "12 * 7 = \0"

test2_msg:
    .byte 49, 48, 48, 32, 47, 32, 55, 32, 61, 32, 0
    # "100 / 7 = \0"

test3_msg:
    .byte 49, 48, 48, 32, 37, 32, 55, 32, 61, 32, 0
    # "100 % 7 = \0"

test4_msg:
    .byte 77, 85, 76, 72, 32, 116, 101, 115, 116, 58, 32, 0
    # "MULH test: \0"
