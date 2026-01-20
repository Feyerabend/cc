
## 6502 Tail-Recursive Fibonacci

This project demonstrates tail recursion on the MOS 6502 processor by implementing
the Fibonacci sequence using a tail-recursive algorithm. Because of the complexity
of the x86 architecture, we have instead chosen the simpler (though older) MOS 6502.
Its small and regular instruction set makes the underlying control flow easier to
reason about, which makes it especially well suited for educational purposes.

Working with the 6502 allows the focus to remain on the algorithmic structure of tail
recursion rather than on architectural details. The processor’s limited register set
and straightforward calling conventions make the transformation from recursive
definitions to iterative or tail-recursive forms both visible and instructive.
In this way, the project serves not only as an implementation of Fibonacci, but
also as a concrete demonstration of how high-level recursion concepts can be mapped
onto low-level machine code.


### Files

- *fib_tail.asm* - 6502 assembly source (tail-recursive Fibonacci)
- *main.c* - Emulator runner that executes the assembled code
- *fake6502.c/h* - MOS 6502 CPU emulator
- *asm.py* - 6502 assembler
- *bin2header.py* - Binary to C header converter (optional)
- *Makefile* - Build automation


### Algorithm

The tail-recursive Fibonacci function follows this pattern:

```
fib(n, a, b):
    if n = 0: return a
    if n = 1: return b
    else: fib(n-1, b, a+b)
```

Starting with `fib(10, 0, 1)` calculates F(10) = 55.


#### 6502 Register Usage

- *A* = n (counter)
- *X* = a (accumulator value)
- *Y* = b (previous value)
- *$00* = temporary storage (zero page)


#### Tail Call Optimisation

Instead of using `JSR` and `RTS` for recursion (which builds up the stack),
the function uses `JMP` to loop back, implementing true tail-call optimisation.
This means:
- No stack growth during recursion
- Constant memory usage
- Effectively converts recursion into iteration at the machine level


### Building and Running

#### Quick Start
```bash
make run
```

#### Step by Step

1. *Assemble the 6502 code:*
   ```bash
   python3 asm.py fib_tail.asm fib.bin
   ```

2. *Compile the emulator:*
   ```bash
   gcc -o run6502 main.c fake6502.c -I.
   ```

3. *Run the emulation:*
   ```bash
   ./run6502 fib.bin
   ```

#### Expected Output

```
6502 Tail-Recursive Fibonacci Emulator
=======================================

Loaded 32768 bytes at $8000

Starting execution...
Initial state: PC=$8000 A=$00 X=$00 Y=$00 SP=$FD

Halted at PC=$800C (infinite loop detected)
Executed 158 instructions

Results:
--------
F(10) = 55 (stored at $0200)

Final CPU state:
  PC = $800C
  A  = $37 (55)
  X  = $22 (34)
  Y  = $37 (55)
  SP = $FD
  P  = $21 (nv-dizC)

Verification:
F(10) should be 55
✓ PASS: Result is correct!
```

### Debugging

#### Verbose Assembly
```bash
make debug
```

This shows the assembly process with addresses and labels.

#### Hex Dump
```bash
make dump
```

Shows the raw binary output.

#### Enable Execution Trace

Edit `main.c` and uncomment this line in the main loop:
```c
// printf("[$%04X] A=%02X X=%02X Y=%02X SP=%02X\n", 
//        current_pc, A, X, Y, SP);
```

Then rebuild and run to see every instruction executed.


### Comparison with x86

The x86 version (x86tail.asm from the book) uses a
similar approach but with different registers:
- *EAX* = n
- *EBX* = a
- *ECX* = b

Both implementations demonstrate that tail recursion is a general
technique applicable across different architectures.

### How It Works

1. *Initialisation*: Set n=10, a=0, b=1
2. *Loop*: While n > 1:
   - Calculate new_b = a + b
   - Set new_a = old b
   - Decrement n
   - Jump back (tail call)
3. *Base cases*: Return a if n=0, b if n=1
4. *Result*: Stored at memory location $0200

The beauty of tail recursion is that it's just a fancy loop--the
CPU never builds up a call stack.

### Memory Map

- *$0000-$00FF*: Zero page (fast access)
- *$0100-$01FF*: Stack
- *$0200*: Result storage
- *$8000-$FFFF*: ROM/Program space
- *$FFFA-$FFFF*: Interrupt vectors

### Educational Value

This example teaches:
1. Tail recursion optimization
2. Register management on limited hardware
3. 6502 assembly programming
4. CPU emulation concepts
5. Cross-platform algorithm implementation

### Clean Up

```bash
make clean
```

Removes all build artefacts.
