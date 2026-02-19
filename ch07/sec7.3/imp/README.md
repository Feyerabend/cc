
## A Mini C Compiler Project for the 6502

A minimal but working C compiler that targets the MOS 6502 processor.
This project demonstrates compiler construction principles and provides
a foundation for building a self-hosting compiler (if you want to build
a real compiler, here is where to start).


### Current Status

*Working Features:*
- Compiles C to 6502 machine code
- Functions with parameters and return values
- Local variables
- Arithmetic operators: `+`, `-`, `*`
- Comparison operators: `==`, `!=`, `<`, `>`
- Control flow: `if`, `else`, `while`, `return`
- Stack-based expression evaluation
- Runtime initialisation and proper program entry
- Successfully runs on fake6502 emulator

*Example:* Compiling this C code:
```c
int add(int a, int b) {
    return a + b;
}

int main() {
    int x;
    x = 10;
    int y;
    y = 20;
    int z;
    z = add(x, y);
    return z;
}
```

Produces working 6502 machine code that returns 30 (0x1E) in the accumulator!


### Project Structure

```
minicc.c       - The C compiler (lexer, parser, code generator)
fake6502.c/h   - MOS 6502 CPU emulator
run6502.c      - Test harness for running compiled code
disasm.c       - 6502 disassembler for debugging
simple.c       - Example program  
test2.c        - More complex examples
Makefile       - Build system
```


### Supported Very Small C Subset

#### Data Types
- `int` - 8-bit integer (matches 6502 accumulator)
- `char` - 8-bit character (parsed but treated as int)
- `void` - For function returns

#### Operators
- Arithmetic: `+`, `-`, `*` (division `/` partially implemented)
- Comparison: `==`, `!=`, `<`, `>` (returns 0 or 1)
- Assignment: `=`

#### Control Flow
```c
if (condition) { ... }
if (condition) { ... } else { ... }
while (condition) { ... }
return expression;
```

#### Functions
```c
int function_name(int param1, int param2) {
    // local variables
    int local;
    local = param1 + param2;
    return local;
}
```

#### Limitations
- No pointers (yet)
- No arrays (yet)
- No structs
- No global variables (yet)
- No string literals (yet)
- No preprocessor
- 8-bit integers only



### Architecture

#### Memory Layout
```
$0000-$00FF: Zero page (variables, temp registers)
  $10-$7F:   Local variables and function parameters
  $F0-$F2:   Temporary registers for expressions
$0100-$01FF: Hardware stack
$0600-$FFFF: Program code
```

#### Calling Convention
1. Arguments are evaluated and pushed on the stack
2. Callee pops arguments into zero page ($10, $11, ...)
3. Return value left in accumulator (A register)
4. Stack-based expression evaluation throughout

#### Code Generation Strategy
- Stack-based expression evaluation
- All intermediate values pushed/popped from stack
- Simple register allocation (zero page for locals)
- Direct JSR/RTS for function calls


### Example Output

```
$ make test
Compiling simple.c...
Compiled 2 functions, 74 bytes

Disassembly:
0600: A2 FF    LDX #$FF        ; Init stack
0602: 9A       TXS
0603: 20 20 06 JSR $0620       ; Call main()
0606: 4C 07 06 JMP $0607       ; Infinite loop (exit/halt)
...

Running on 6502 emulator:
Initial: PC=0600 A=00 X=00 Y=00 SP=FD
Final:   PC=0609 A=1E X=FF Y=00 SP=FF
Total cycles: 162

Result: A=1E (30 in decimal)    Correct!
```



### Learning Resources

Resources:
- [6502.org](http://www.6502.org/) - The definitive 6502 resource
- [6502 Instruction Reference](http://www.6502.org/tutorials/6502opcodes.html)
- [Easy 6502](https://skilldrick.github.io/easy6502/) - Interactive tutorial

6502?
- Simple, elegant instruction set (56 instructions)
- Historical importance (Apple II, C64, NES, Atari)
- Easy to understand and emulate
- Perfect size for learning


### Future Work / Project Ideas

__Phase 1: Core Language Features__
- [ ] *Division and modulo* - Implement `/` and `%` operators
- [ ] *Logical operators* - Add `&&`, `||`, `!` 
- [ ] *Compound assignments* - Support `+=`, `-=`, `*=`
- [ ] *For loops* - Transform to while loops internally
- [ ] *Switch statements* - Generate jump tables
- [ ] *Break and continue* - Track loop context in codegen

__Phase 2: Memory and Data Structures__
- [ ] *Pointers* - Add `*` and `&` operators
  - Use zero page indirect addressing modes
  - Implement pointer arithmetic
- [ ] *Arrays* - Fixed-size arrays `int arr[10]`
  - Array indexing with bounds checking
  - Array initialization
- [ ] *Global variables* - Data segment at $0200-$05FF
- [ ] *String literals* - Store strings in data segment
  - Basic string functions (strcpy, strcmp)

__Phase 3: Advanced Features__
- [ ] *Structs* - Compound data types
  - Member access operator `.`
  - Struct assignment and copying
- [ ] *Function pointers* - Indirect function calls
- [ ] *Recursion optimization* - Tail call optimization
- [ ] *Inline functions* - Inline small functions for speed

__Phase 4: Code Quality & Optimization__
- [ ] *Error messages* - Line numbers and better diagnostics
- [ ] *Warnings* - Unused variables, type mismatches
- [ ] *Constant folding* - Evaluate constants at compile time
- [ ] *Dead code elimination* - Remove unreachable code
- [ ] *Peephole optimization* - Combine adjacent instructions
- [ ] *Register allocation* - Better use of X and Y registers

__Phase 5: Self-Hosting__
- [ ] *Dynamic memory* - Simple heap allocator
- [ ] *File I/O* - Read source from files
- [ ] *Multi-pass compilation* - Separate parsing and codegen
- [ ] *Bootstrap the compiler!*
  - Stage 0: Compile minicc.c with GCC
  - Stage 1: Use stage 0 to compile minicc.c
  - Stage 2: Use stage 1 to compile minicc.c
  - Verify: stage 1 and stage 2 produce identical output

__Phase 6: Tooling & Ecosystem__
- [ ] *Standard library* - printf, malloc, string functions
- [ ] *Linker* - Combine multiple object files
- [ ] *Assembler integration* - Inline assembly blocks
- [ ] *Debugger* - Breakpoints and single-stepping
- [ ] *Profiler* - Cycle counting and optimization hints

__Phase 7: Target Platforms__
- [ ] *NES* - Nintendo Entertainment System support
- [ ] *C64* - Commodore 64 platform
- [ ] *Apple II* - Classic Apple computer
- [ ] *Atari 2600* - Extremely constrained environment
- [ ] *Multiple backends* - Add x86, ARM, RISC-V targets


### Suggested Learning Paths

__Path A: Language Features (You know this)__
- *Goal:* Understand parsing and language design  
- *Start with:* For loops, logical operators, arrays  
- *Learn:* Parser construction, AST manipulation

__Path B: Code Generation (Probably also within your knowledge)__
- *Goal:* Master assembly and optimization  
- *Start with:* Peephole optimization, register allocation  
- *Learn:* CPU architecture, optimization techniques

__Path C: Self-Hosting (More advanced)__
- *Goal:* Make the compiler compile itself  
- *Start with:* Pointers -> dynamic memory -> file I/O  
- *Learn:* Complete compiler pipeline

__Path D: Platform Specific (Hardware Focus)__
- *Goal:* Target real 6502 systems  
- *Start with:* NES "Hello World" program  
- *Learn:* Hardware constraints, memory-mapped I/O


### Known Issues

1. *Stack overflow* - No checking, will wrap around
2. *Type checking* - Minimal, assumes everything is int
3. *Comments* - Only single-line `//`, not `/* */`
4. *No preprocessor* - No `#define`, `#include`
5. *Error recovery* - Exits on first error
6. *Code size* - Generates verbose, unoptimized code


### Testing Your Changes

```bash
## Create test program
echo 'int main() { return 5 * 6; }' > test.c

## Compile
./minicc test.c

## Disassemble (optional)
./disasm out.bin

## Run and verify
./run6502 out.bin
## Check that A register = 1E (30 in hex)
```


### Milestones

- *Milestone 1*: Compile basic arithmetic (DONE)
- *Milestone 2*: Functions and calls (DONE)
- *Milestone 3*: Control flow (DONE)
- *Milestone 4*: Arrays and pointers
- *Milestone 5*: File I/O and multi-file compilation
- *Milestone 6*: Self-hosting!

*"If you wish to write a C compiler from scratch, you must first write a C compiler."* - The Bootstrap Paradox
