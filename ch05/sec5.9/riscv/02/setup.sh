#!/bin/bash
# setup.sh - Setup RISC-V toolchain and create sample files

echo "=== RISC-V Toolchain Setup ==="
echo ""

# Create samples directory
mkdir -p samples

# Create hello.asm
cat > samples/hello.asm << 'EOF'
# Simple hello world program
# Uses syscall to print

.global _start

_start:
    li a7, 1           # syscall 1: print integer
    li a0, 42          # print 42
    ecall
    
    li a7, 11          # syscall 11: print char
    li a0, 10          # newline
    ecall
    
    li a7, 10          # syscall 10: exit
    ecall
EOF

# Create factorial.asm
cat > samples/factorial.asm << 'EOF'
# Calculate factorial of 5

.global _start

_start:
    li a0, 5           # n = 5
    jal ra, factorial  # call factorial
    
    # Print result
    mv a0, a1          # move result to a0
    li a7, 1           # print integer
    ecall
    
    li a7, 11          # print newline
    li a0, 10
    ecall
    
    li a7, 10          # exit
    ecall

factorial:
    # Input: a0 = n
    # Output: a1 = n!
    li a1, 1           # result = 1
    li t0, 1           # counter = 1
    
fact_loop:
    bgt t0, a0, fact_done
    mul a1, a1, t0     # result *= counter
    addi t0, t0, 1     # counter++
    j fact_loop
    
fact_done:
    ret
EOF

# Create fibonacci.asm
cat > samples/fibonacci.asm << 'EOF'
# Print first 10 Fibonacci numbers

.global _start

_start:
    li s0, 0           # fib(n-2)
    li s1, 1           # fib(n-1)
    li s2, 10          # counter
    
    # Print first number
    li a7, 1
    mv a0, s0
    ecall
    li a7, 11
    li a0, 32          # space
    ecall
    
    # Print second number
    li a7, 1
    mv a0, s1
    ecall
    li a7, 11
    li a0, 32
    ecall
    
    li s3, 2           # count = 2
    
fib_loop:
    bge s3, s2, fib_done
    
    add t0, s0, s1     # fib(n) = fib(n-1) + fib(n-2)
    mv s0, s1          # shift
    mv s1, t0
    
    # Print number
    li a7, 1
    mv a0, t0
    ecall
    li a7, 11
    li a0, 32          # space
    ecall
    
    addi s3, s3, 1
    j fib_loop
    
fib_done:
    li a7, 11
    li a0, 10          # newline
    ecall
    
    li a7, 10
    ecall
EOF

# Create sum_array.asm
cat > samples/sum_array.asm << 'EOF'
# Sum an array of numbers

.global _start

_start:
    # Initialize array in memory
    li t0, 0x1000      # array base address
    
    li t1, 10
    sw t1, 0(t0)       # array[0] = 10
    
    li t1, 20
    sw t1, 4(t0)       # array[1] = 20
    
    li t1, 30
    sw t1, 8(t0)       # array[2] = 30
    
    li t1, 40
    sw t1, 12(t0)      # array[3] = 40
    
    li t1, 50
    sw t1, 16(t0)      # array[4] = 50
    
    # Sum the array
    li a0, 0x1000      # array address
    li a1, 5           # array length
    jal ra, sum_array
    
    # Print result
    li a7, 1
    ecall
    li a7, 11
    li a0, 10
    ecall
    
    li a7, 10
    ecall

sum_array:
    # Input: a0 = array address, a1 = length
    # Output: a0 = sum
    li t0, 0           # sum = 0
    li t1, 0           # index = 0
    
sum_loop:
    bge t1, a1, sum_done
    
    slli t2, t1, 2     # offset = index * 4
    add t2, a0, t2     # address = base + offset
    lw t3, 0(t2)       # load element
    add t0, t0, t3     # sum += element
    
    addi t1, t1, 1     # index++
    j sum_loop
    
sum_done:
    mv a0, t0          # return sum
    ret
EOF

# Create multifile_main.asm
cat > samples/multifile_main.asm << 'EOF'
# Main program that calls external functions

.global _start
.extern add_numbers
.extern multiply

_start:
    li a0, 7
    li a1, 5
    jal ra, add_numbers   # result in a0
    
    mv t0, a0             # save result
    
    # Print sum
    li a7, 1
    ecall
    li a7, 11
    li a0, 32             # space
    ecall
    
    # Multiply the sum by 2
    mv a0, t0
    li a1, 2
    jal ra, multiply
    
    # Print product
    li a7, 1
    ecall
    li a7, 11
    li a0, 10             # newline
    ecall
    
    li a7, 10
    ecall
EOF

# Create multifile_math.asm
cat > samples/multifile_math.asm << 'EOF'
# Math library functions

.global add_numbers
.global multiply

add_numbers:
    # Add two numbers
    # Input: a0, a1
    # Output: a0 = a0 + a1
    add a0, a0, a1
    ret

multiply:
    # Multiply two numbers
    # Input: a0, a1
    # Output: a0 = a0 * a1
    mul a0, a0, a1
    ret
EOF

# Create README
cat > README.md << 'EOF'
# RISC-V Toolchain

A complete RISC-V RV32I assembler, linker, and virtual machine written in Python.

## Components

- **asm.py** - Simple assembler (single file to binary)
- **asm_obj.py** - Object file assembler (produces relocatable .o files)
- **linker.py** - Linker (combines multiple .o files into executable)
- **vm.py** - Virtual machine (executes RISC-V binary code)

## Quick Start

1. Run setup:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. Build and run all samples:
   ```bash
   make all
   ```

3. Build individual programs:
   ```bash
   make hello
   make factorial
   make fibonacci
   make sum_array
   make multifile
   ```

## Features

### Supported Instructions
- RV32I base instruction set
- M extension (multiply/divide)
- Pseudo-instructions (nop, mv, li, j, ret)

### Syscalls
- syscall 1: Print integer (a0)
- syscall 4: Print string (a0 = address)
- syscall 10: Exit
- syscall 11: Print character (a0)

## Sample Programs

### hello.asm
Prints the number 42 and exits.

**Expected output:** `42`

### factorial.asm
Calculates factorial of 5 (5! = 120).

**Expected output:** `120`

### fibonacci.asm
Prints the first 10 Fibonacci numbers.

**Expected output:** `0 1 1 2 3 5 8 13 21 34`

### sum_array.asm
Sums an array of 5 numbers (10+20+30+40+50=150).

**Expected output:** `150`

### multifile (main + math)
Demonstrates linking multiple object files. Adds 7+5=12, then multiplies by 2.

**Expected output:** `12 24`

## Manual Usage

### Assemble single file to binary:
```bash
python3 asm.py input.asm output.bin
```

### Assemble to object file:
```bash
python3 asm_obj.py input.asm output.o
```

### Link object files:
```bash
python3 linker.py output.bin file1.o file2.o file3.o
```

### Run binary:
```bash
python3 vm.py program.bin
```

### Debug mode:
```bash
python3 vm.py program.bin -d
```

## Object File Format

Object files use a simple format:
- Magic number: "RVO1"
- Header: text size, data size, symbol count, relocation count
- Text section
- Data section (unused currently)
- Symbol table
- Relocation table

## Architecture

```
Source Files (.asm)
        |
        v
    Assembler (asm_obj.py)
        |
        v
   Object Files (.o)
        |
        v
     Linker (linker.py)
        |
        v
  Executable (.bin)
        |
        v
   Virtual Machine (vm.py)
```

## Writing Programs

### Directives
- `.global label` - Export symbol
- `.extern label` - Import external symbol

### Example with external calls:
```asm
.global _start
.extern my_function

_start:
    li a0, 10
    jal ra, my_function
    # ... rest of code
```

## License

Public domain / MIT - use freely!
EOF

echo "Sample files created in samples/"
echo ""
echo "Files created:"
ls -la samples/
echo ""
echo "To build and run all samples:"
echo "  make all"
echo ""
echo "To build individual programs:"
echo "  make hello"
echo "  make factorial"
echo "  etc."
echo ""
echo "Setup complete!"
