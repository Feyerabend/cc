
## RISC-V RV32IM Virtual Machine (ANSI C)

A complete RISC-V RV32IM (Base Integer + Multiply/Divide)
virtual machine implementation in ANSI C (C89/C90).

- *Full RV32IM support*: All base integer and M extension instructions
- *ANSI C compatible*: Works with older C compilers (C89/C90)
- *Interrupt support*: Extensible framework for custom interrupt handlers
- *Debug features*: Instruction tracing, register dumps, memory inspection
- *System calls*: Basic RISC-V Linux ABI syscalls (print, exit)

### Building

```bash
make
```

This will produce the `riscv_vm` executable.

### Usage

```bash
./riscv_vm [options] <binary_file>
```

#### Options

- `-d` - Enable debug mode (shows execution statistics)
- `-t` - Trace instruction execution (prints each instruction)
- `-r` - Print final register state
- `-m start:len` - Dump memory region (addresses in hex)
- `-h` - Show help message

#### Examples

```bash
## Run program with debug output
./riscv_vm -d program.bin

## Run with instruction tracing
./riscv_vm -t program.bin

## Run with register dump at end
./riscv_vm -r program.bin

## Run with memory dump from 0x1000, length 0x100
./riscv_vm -m 1000:100 program.bin

## Full debug: trace + registers + memory
./riscv_vm -d -t -r -m 0:200 program.bin
```

### Interrupt Handling

The VM provides hooks for implementing custom interrupt handling.
This is useful for:
- Timer interrupts
- I/O device interrupts
- External hardware simulation
- Debugging breakpoints

#### Setting Up Interrupts

1. Implement a check function that returns an interrupt number or -1:

```c
int my_interrupt_check(void *user_data) {
    /* Check your conditions */
    if (timer_expired()) {
        return 0;  /* Timer interrupt */
    }
    if (io_ready()) {
        return 1;  /* I/O interrupt */
    }
    return -1;  /* No interrupt */
}
```

2. Implement a handler function:

```c
void my_interrupt_handler(void *user_data, int interrupt_num) {
    riscv_vm_t *vm = (riscv_vm_t *)user_data;
    
    switch (interrupt_num) {
        case 0:  /* Timer */
            /* Save context, jump to timer ISR, etc. */
            break;
        case 1:  /* I/O */
            /* Handle I/O interrupt */
            break;
    }
}
```

3. Register handlers before execution:

```c
vm_set_interrupt_handler(vm, 
                         my_interrupt_check,
                         my_interrupt_handler,
                         vm);  /* Can pass any data as user_data */
```

The check function is called after each instruction. If it returns a non-negative number, the handler is invoked.


### Supported Instructions

#### Base Integer (RV32I)

*Arithmetic*: ADD, SUB, ADDI  
*Logical*: AND, OR, XOR, ANDI, ORI, XORI  
*Shifts*: SLL, SRL, SRA, SLLI, SRLI, SRAI  
*Comparison*: SLT, SLTU, SLTI, SLTIU  
*Loads*: LB, LH, LW, LBU, LHU  
*Stores*: SB, SH, SW  
*Branches*: BEQ, BNE, BLT, BGE, BLTU, BGEU  
*Jumps*: JAL, JALR  
*Upper Imm*: LUI, AUIPC  
*System*: ECALL, EBREAK  

#### M Extension (Multiply/Divide)

*Multiply*: MUL, MULH, MULHSU, MULHU  
*Divide*: DIV, DIVU  
*Remainder*: REM, REMU  

### System Calls

The VM implements basic RISC-V Linux ABI syscalls via ECALL:

| Number | Name | Description |
|--------|------|-------------|
| 1 | print_int | Print integer in a0 |
| 4 | print_str | Print null-terminated string at address in a0 |
| 10 | exit | Terminate execution |
| 11 | print_char | Print character in a0 |


### Architecture Details

#### Memory
- Default: 64KB (configurable)
- Little-endian byte order
- Aligned access enforced for multi-byte operations

#### Registers
- 32 general-purpose registers (x0-x31)
- x0 hardwired to zero
- ABI names: zero, ra, sp, gp, tp, t0-t6, s0-s11, a0-a7

#### Program Counter
- 32-bit PC
- Starts at address 0x00000000
- Increments by 4 for normal instructions
- Branch/jump targets must be word-aligned


### Example: Creating a Custom Extension

You can extend the VM to support custom instructions or peripherals:

```c
/* In your code */
void my_peripheral_init(riscv_vm_t *vm) {
    /* Set up interrupt handler */
    vm_set_interrupt_handler(vm, 
                             check_peripheral,
                             handle_peripheral,
                             my_peripheral_data);
}

/* Interrupt check - called after each instruction */
int check_peripheral(void *data) {
    my_peripheral_t *periph = (my_peripheral_t *)data;
    if (periph->data_ready) {
        return PERIPHERAL_IRQ_NUM;
    }
    return -1;
}

/* Interrupt handler */
void handle_peripheral(void *data, int irq) {
    riscv_vm_t *vm = (riscv_vm_t *)data;
    /* Could modify PC to jump to ISR */
    /* Could modify registers */
    /* Could write to memory */
}
```

### Performance Notes

- Compiled with `-O2` for good performance
- Consider `-O3` for maximum speed
- Profile-guided optimization (PGO) can help for specific workloads
- Interrupt checks add minimal overhead when handler is NULL


### Contributing

To add features:
1. Add new opcodes to the `opcode_t` enum in `riscv_vm.h`
2. Update the `decode()` function in `riscv_vm.c`
3. Add execution logic in the `execute()` function
4. Update `opcode_to_string()` for debug output

### Debugging Tips

1. Use `-t` to trace execution and find where it diverges
2. Use `-r` to see final register state
3. Use `-m` to inspect memory regions
4. Add breakpoints by checking PC in the interrupt handler
5. Use EBREAK instructions to halt at specific points

### Known Limitations

- No privilege levels (machine/supervisor/user modes)
- No CSR (Control and Status Registers) support
- No atomic operations (A extension)
- No floating-point (F/D extensions)
- No compressed instructions (C extension)
- Fixed memory size (no MMU/virtual memory)

These could be added as extensions following the interrupt handler pattern.
