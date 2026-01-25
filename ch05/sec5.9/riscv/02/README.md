## RISC-V Toolchain

A complete RISC-V RV32I assembler, linker, and virtual machine written in Python.

- *asm.py* - Simple assembler (single file to binary)
- *asm_obj.py* - Object file assembler (produces relocatable .o files)
- *linker.py* - Linker (combines multiple .o files into executable)
- *vm.py* - Virtual machine (executes RISC-V binary code)


### Quick Start

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


### Features

__Supported Instructions__
- RV32I base instruction set
- M extension (multiply/divide)
- Pseudo-instructions (nop, mv, li, j, ret)

__Syscalls__
- syscall 1: Print integer (a0)
- syscall 4: Print string (a0 = address)
- syscall 10: Exit
- syscall 11: Print character (a0)


### Sample Program Linking 2 Programs

*multifile* (main + math):
Demonstrates linking multiple object files.
Adds 7+5=12, then multiplies by 2: *Output:* `12 24`


### Usage

Assemble single file to binary:
```bash
python3 asm.py input.asm output.bin
```

Assemble to object file:
```bash
python3 asm_obj.py input.asm output.o
```

Link object files:
```bash
python3 linker.py output.bin file1.o file2.o file3.o
```

Run binary:
```bash
python3 vm.py program.bin
```

### Debug
```bash
python3 vm.py program.bin -d
```


### Writing Programs

Directives:
- `.global label` - Export symbol
- `.extern label` - Import external symbol

Example with external calls:
```asm
.global _start
.extern my_function

_start:
    li a0, 10
    jal ra, my_function
    # ... rest of code
```


![RISCV](./../../../assets/image/riscv.png)
