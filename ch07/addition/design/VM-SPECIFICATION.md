
## Educational Virtual Machine Specification

This has been at the core throughout this book,
and now fits togheter as:
*A Simple Stack-Based VM for Teaching Compilation*


### 1. Overview

#### 1.1 Design Philosophy

This virtual machine is designed to be:

- *Simple*: Easy to understand and implement
- *Educational*: Exposes fundamental concepts clearly
- *Stack-based*: Natural fit for expression evaluation
- *Typed*: Instructions specify operand types
- *Portable*: Can run on any platform

#### 1.2 Architecture

The VM consists of:

- *Operand Stack*: Primary location for computation
- *Call Stack*: Stores activation records (frames)
- *Heap*: Dynamic memory allocation
- *Global Memory*: Static variables
- *Program Memory*: Bytecode instructions

#### 1.3 Memory Model

```
top
   -----------------------------------------
   Program Memory      Bytecode instructions

    Global Memory      Static variables

       Heap            Dynamic allocations
        v              (grows downward)

        ^
    Call Stack         Activation records
                       (grows upward)
 
   Operand Stack       Computation values
   -----------------------------------------
bottom
```

### 2. Data Types

#### 2.1 Primitive Types

The VM supports these primitive types:

|Type|    Size|    Range|                    Representation|
|----|--------|---------|----------------------------------|
|Int8|    1 byte|  -128 to 127|              Two's complement|
|Int16|   2 bytes| -32768 to 32767|          Two's complement|
|Int32|   4 bytes| -2147483648 to ..|        Two's complement|
|Bool|    1 byte|  0 (false) or 1 (true)|    Single byte|


#### 2.2 Composite Types

- Array:   `[size: 4 bytes][elements..]`
- Record:  `[field1][field2]...[fieldN]`
- Closure: `[fn_ptr: 4 bytes][captures...]`


#### 2.3 Pointers

Heap pointers are 32-bit addresses (4 bytes).

### 3. Execution Model

#### 3.1 Program Structure

A program consists of:

Program:
  - Constant pool
  - Global variable declarations
  - Function definitions
  - Entry point (main function)

#### 3.2 Activation Records

Each function call creates an activation record:

```
Activation Record:

  Return Address     4 bytes
  Previous Frame     4 bytes (frame pointer)

    Local 0          Variable size
    Local 1
      .. 
    Local N
```

#### 3.3 Operand Stack

Stack grows upward in memory:


Stack Operations:
- Push: Increment SP, store value
- Pop:  Load value, decrement SP
- Peek: Load value at SP-offset


Stack holds typed values:
Stack Entry: `[type: 1 byte][value: 1-4 bytes]`


### 4. Instruction Set

#### 4.1 Instruction Format

```
Instruction Format:
  Opcode    Operands (0-4 bytes)
  1 byte    Depends on instruction
```

#### 4.2 Stack Manipulation

##### PUSH_I8 value
- *Operation*: Push 8-bit integer onto stack
- *Encoding*: `0x01 [value: 1 byte]`
- *Stack*: `[] -->[Int8]`

##### PUSH_I16 value
- *Operation*: Push 16-bit integer onto stack
- *Encoding*: `0x02 [value: 2 bytes]`
- *Stack*: `[] -->[Int16]`

##### PUSH_I32 value
- *Operation*: Push 32-bit integer onto stack
- *Encoding*: `0x03 [value: 4 bytes]`
- *Stack*: `[] -->[Int32]`

##### PUSH_BOOL value
- *Operation*: Push boolean onto stack
- *Encoding*: `0x04 [value: 1 byte]`
- *Stack*: `[] -->[Bool]`

##### POP
- *Operation*: Discard top stack value
- *Encoding*: `0x05`
- *Stack*: `[any] -->[]`

##### DUP
- *Operation*: Duplicate top stack value
- *Encoding*: `0x06`
- *Stack*: `[value] -->[value, value]`

##### SWAP
- *Operation*: Swap top two stack values
- *Encoding*: `0x07`
- *Stack*: `[a, b] -->[b, a]`

#### 4.3 Arithmetic Operations

##### ADD_I8
- *Operation*: Add two 8-bit integers
- *Encoding*: `0x10`
- *Stack*: `[Int8, Int8] -->[Int8]`
- *Semantics*: `pop b, pop a, push(a + b)`

##### ADD_I16
- *Operation*: Add two 16-bit integers
- *Encoding*: `0x11`
- *Stack*: `[Int16, Int16] -->[Int16]`

##### ADD_I32
- *Operation*: Add two 32-bit integers
- *Encoding*: `0x12`
- *Stack*: `[Int32, Int32] -->[Int32]`

##### SUB_I8 / SUB_I16 / SUB_I32
- *Operation*: Subtract integers
- *Encoding*: `0x13` / `0x14` / `0x15`
- *Stack*: `[Int, Int] -->[Int]`
- *Semantics*: `pop b, pop a, push(a - b)`

##### MUL_I8 / MUL_I16 / MUL_I32
- *Operation*: Multiply integers
- *Encoding*: `0x16` / `0x17` / `0x18`
- *Stack*: `[Int, Int] -->[Int]`

##### DIV_I8 / DIV_I16 / DIV_I32
- *Operation*: Divide integers
- *Encoding*: `0x19` / `0x1A` / `0x1B`
- *Stack*: `[Int, Int] -->[Int]`
- *Semantics*: `pop b, pop a, push(a / b)`
- *Error*: Division by zero causes runtime error

##### MOD_I8 / MOD_I16 / MOD_I32
- *Operation*: Modulo operation
- *Encoding*: `0x1C` / `0x1D` / `0x1E`
- *Stack*: `[Int, Int] -->[Int]`

##### NEG_I8 / NEG_I16 / NEG_I32
- *Operation*: Negate integer
- *Encoding*: `0x1F` / `0x20` / `0x21`
- *Stack*: `[Int] -->[Int]`
- *Semantics*: `pop a, push(-a)`

#### 4.4 Comparison Operations

##### LT_I8 / LT_I16 / LT_I32
- *Operation*: Less than comparison
- *Encoding*: `0x30` / `0x31` / `0x32`
- *Stack*: `[Int, Int] -->[Bool]`
- *Semantics*: `pop b, pop a, push(a < b)`

##### LE_I8 / LE_I16 / LE_I32
- *Operation*: Less than or equal
- *Encoding*: `0x33` / `0x34` / `0x35`
- *Stack*: `[Int, Int] -->[Bool]`

##### GT_I8 / GT_I16 / GT_I32
- *Operation*: Greater than
- *Encoding*: `0x36` / `0x37` / `0x38`
- *Stack*: `[Int, Int] -->[Bool]`

##### GE_I8 / GE_I16 / GE_I32
- *Operation*: Greater than or equal
- *Encoding*: `0x39` / `0x3A` / `0x3B`
- *Stack*: `[Int, Int] -->[Bool]`

##### EQ_I8 / EQ_I16 / EQ_I32
- *Operation*: Equality comparison
- *Encoding*: `0x3C` / `0x3D` / `0x3E`
- *Stack*: `[Int, Int] -->[Bool]`

##### NE_I8 / NE_I16 / NE_I32
- *Operation*: Inequality comparison
- *Encoding*: `0x3F` / `0x40` / `0x41`
- *Stack*: `[Int, Int] -->[Bool]`

#### 4.5 Logical Operations

##### AND
- *Operation*: Logical AND
- *Encoding*: `0x50`
- *Stack*: `[Bool, Bool] -->[Bool]`

##### OR
- *Operation*: Logical OR
- *Encoding*: `0x51`
- *Stack*: `[Bool, Bool] -->[Bool]`

##### NOT
- *Operation*: Logical NOT
- *Encoding*: `0x52`
- *Stack*: `[Bool] -->[Bool]`

#### 4.6 Control Flow

##### JUMP offset
- *Operation*: Unconditional jump
- *Encoding*: `0x60 [offset: 4 bytes signed]`
- *Stack*: `[] -->[]`
- *Semantics*: `PC = PC + offset`

##### JUMP_IF_TRUE offset
- *Operation*: Jump if top of stack is true
- *Encoding*: `0x61 [offset: 4 bytes signed]`
- *Stack*: `[Bool] -->[]`
- *Semantics*: `pop value; if value then PC = PC + offset`

##### JUMP_IF_FALSE offset
- *Operation*: Jump if top of stack is false
- *Encoding*: `0x62 [offset: 4 bytes signed]`
- *Stack*: `[Bool] -->[]`
- *Semantics*: `pop value; if not value then PC = PC + offset`

#### 4.7 Function Calls

##### CALL function_index arity
- *Operation*: Call function
- *Encoding*: `0x70 [index: 2 bytes] [arity: 1 byte]`
- *Stack*: `[arg1, arg2, .., argN] -->[result]`
- *Semantics*:
  1. Pop arity arguments from stack
  2. Create new activation record
  3. Copy arguments to new frame's locals
  4. Push return address
  5. Jump to function

##### RETURN
- *Operation*: Return from function
- *Encoding*: `0x71`
- *Stack*: `[return_value] -->[return_value]` (in caller's frame)
- *Semantics*:
  1. Pop return value
  2. Restore previous activation record
  3. Push return value
  4. Resume at return address

##### CALL_NATIVE native_id arity
- *Operation*: Call native function
- *Encoding*: `0x72 [id: 2 bytes] [arity: 1 byte]`
- *Stack*: `[arg1, .., argN] -->[result]`
- *Semantics*: Call built-in function (print, etc.)

#### 4.8 Local Variables

##### LOAD_LOCAL index
- *Operation*: Load local variable onto stack
- *Encoding*: `0x80 [index: 2 bytes]`
- *Stack*: `[] -->[value]`
- *Semantics*: `push(locals[index])`

##### STORE_LOCAL index
- *Operation*: Store top of stack to local variable
- *Encoding*: `0x81 [index: 2 bytes]`
- *Stack*: `[value] -->[]`
- *Semantics*: `locals[index] = pop()`

#### 4.9 Global Variables

##### LOAD_GLOBAL index
- *Operation*: Load global variable onto stack
- *Encoding*: `0x90 [index: 2 bytes]`
- *Stack*: `[] -->[value]`

##### STORE_GLOBAL index
- *Operation*: Store top of stack to global variable
- *Encoding*: `0x91 [index: 2 bytes]`
- *Stack*: `[value] -->[]`

#### 4.10 Memory Operations

##### ALLOC size
- *Operation*: Allocate heap memory
- *Encoding*: `0xA0 [size: 4 bytes]`
- *Stack*: `[] -->[pointer]`
- *Semantics*: Allocate size bytes, push pointer

##### LOAD_MEM
- *Operation*: Load value from memory address
- *Encoding*: `0xA1`
- *Stack*: `[pointer] -->[value]`

##### STORE_MEM
- *Operation*: Store value to memory address
- *Encoding*: `0xA2`
- *Stack*: `[pointer, value] -->[]`

##### LOAD_FIELD offset
- *Operation*: Load field from struct/record
- *Encoding*: `0xA3 [offset: 2 bytes]`
- *Stack*: `[pointer] -->[value]`
- *Semantics*: `push(mem[pop() + offset])`

##### STORE_FIELD offset
- *Operation*: Store to struct/record field
- *Encoding*: `0xA4 [offset: 2 bytes]`
- *Stack*: `[pointer, value] -->[]`

#### 4.11 Array Operations

##### NEW_ARRAY type length
- *Operation*: Create new array
- *Encoding*: `0xB0 [type: 1 byte] [length: 4 bytes]`
- *Stack*: `[] -->[array_ptr]`

##### LOAD_ARRAY_ELEM
- *Operation*: Load array element
- *Encoding*: `0xB1`
- *Stack*: `[array_ptr, index] -->[value]`

##### STORE_ARRAY_ELEM
- *Operation*: Store to array element
- *Encoding*: `0xB2`
- *Stack*: `[array_ptr, index, value] -->[]`

##### ARRAY_LENGTH
- *Operation*: Get array length
- *Encoding*: `0xB3`
- *Stack*: `[array_ptr] -->[length]`

#### 4.12 Type Conversion

##### I8_TO_I16
- *Operation*: Convert Int8 to Int16
- *Encoding*: `0xC0`
- *Stack*: `[Int8] -->[Int16]`

##### I8_TO_I32
- *Operation*: Convert Int8 to Int32
- *Encoding*: `0xC1`
- *Stack*: `[Int8] -->[Int32]`

##### I16_TO_I32
- *Operation*: Convert Int16 to Int32
- *Encoding*: `0xC2`
- *Stack*: `[Int16] -->[Int32]`

##### I32_TO_I16
- *Operation*: Convert Int32 to Int16 (truncate)
- *Encoding*: `0xC3`
- *Stack*: `[Int32] -->[Int16]`

##### I32_TO_I8
- *Operation*: Convert Int32 to Int8 (truncate)
- *Encoding*: `0xC4`
- *Stack*: `[Int32] -->[Int8]`

#### 4.13 Closure Support

##### MAKE_CLOSURE fn_index capture_count
- *Operation*: Create closure
- *Encoding*: `0xD0 [fn: 2 bytes] [count: 1 byte]`
- *Stack*: `[capture1, .., captureN] -->[closure_ptr]`

##### LOAD_CLOSURE index
- *Operation*: Load captured variable
- *Encoding*: `0xD1 [index: 1 byte]`
- *Stack*: `[] -->[value]`

##### CALL_CLOSURE arity
- *Operation*: Call closure
- *Encoding*: `0xD2 [arity: 1 byte]`
- *Stack*: `[closure_ptr, arg1, ..., argN] -->[result]`

#### 4.14 Debugging

##### DEBUG_PRINT
- *Operation*: Print top of stack (for debugging)
- *Encoding*: `0xF0`
- *Stack*: `[value] -->[]`

##### BREAKPOINT
- *Operation*: Trigger debugger
- *Encoding*: `0xF1`
- *Stack*: `[] -->[]`

##### HALT
- *Operation*: Stop execution
- *Encoding*: `0xFF`
- *Stack*: `[] -->[]`

### 5. Bytecode File Format

#### 5.1 File Structure

```
BytecodeFile:
--------------------
    Magic Number        4 bytes: 0x45 0x56 0x4D 0x00 ("EVM\0")

    Version             2 bytes: major, minor

    Constant Pool       Variable size

    Global Variables    Variable size

    Functions           Variable size

    Entry Point         2 bytes: function index

    Debug Info          Optional, variable size
--------------------
```

#### 5.2 Constant Pool

```
ConstantPool:
  count: 2 bytes
  entries: [Constant × count]

Constant:
  tag: 1 byte
    0x01 = Integer (4 bytes)
    0x02 = String (2 bytes length + data)
    0x03 = Float (4 bytes)
```

#### 5.3 Function Definition

```
Function:
  name_length: 2 bytes
  name: [byte × name_length]
  arity: 1 byte
  local_count: 2 bytes
  max_stack: 2 bytes
  code_length: 4 bytes
  code: [byte × code_length]
```

### 6. Runtime Behavior

#### 6.1 Startup

1. Load bytecode file
2. Verify magic number and version
3. Initialize constant pool
4. Allocate globals
5. Initialize heap
6. Call entry point function

#### 6.2 Execution Cycle

```
while running:
  opcode = fetch_byte()
  match opcode:
    case PUSH_I32:
      value = fetch_i32()
      stack.push(value)
    case ADD_I32:
      b = stack.pop()
      a = stack.pop()
      stack.push(a + b)
    ...
```

#### 6.3 Memory Management

*Stack Overflow*: Error if stack exceeds limit
*Heap Allocation*: Bump allocator or garbage collection
*Frame Management*: Automatic on call/return

#### 6.4 Error Handling

Runtime errors cause immediate halt:

- Division by zero
- Stack overflow/underflow
- Null pointer dereference
- Array index out of bounds
- Type mismatch

### 7. Standard Library

#### 7.1 Native Functions

##### print_i32(value: Int32) -> ()
- *ID*: 0
- *Operation*: Print 32-bit integer

##### print_bool(value: Bool) -> ()
- *ID*: 1
- *Operation*: Print boolean

##### print_string(ptr: Pointer) -> ()
- *ID*: 2
- *Operation*: Print null-terminated string

##### read_i32() -> Int32
- *ID*: 3
- *Operation*: Read integer from input

### 8. Implementation Guidelines

#### 8.1 Minimal Implementation

A basic VM needs:

```python
class VM:
    def __init__(self):
        self.program = []      # Bytecode
        self.pc = 0            # Program counter
        self.stack = []        # Operand stack
        self.frames = []       # Call stack
        self.globals = {}      # Global variables
        self.heap = {}         # Heap memory
    
    def execute(self):
        while self.pc < len(self.program):
            opcode = self.fetch_byte()
            self.execute_instruction(opcode)
```

#### 8.2 Optimization Opportunities

- *Instruction combining*: Fuse common patterns
- *Stack caching*: Keep top values in registers
- *Direct threading*: Use computed goto
- *JIT compilation*: Compile hot code to native

#### 8.3 Extensions

Possible additions:

- *Float operations*: Add Float32/Float64 types
- *String operations*: Built-in string type
- *Exception handling*: Try/catch mechanism
- *Concurrency*: Thread operations
- *FFI*: Call native code

### 9. Example Programs

#### 9.1 Hello World

```assembly
; Print "Hello"
PUSH_I32 0        ; String constant index
CALL_NATIVE 2 1   ; print_string
HALT
```

#### 9.2 Factorial

```assembly
function factorial:
  ; Input: n in local 0
  ; Output: n! on stack
  
  LOAD_LOCAL 0      ; n
  PUSH_I32 1
  LE_I32            ; n <= 1?
  JUMP_IF_FALSE recursive
  
  PUSH_I32 1        ; Base case: return 1
  RETURN
  
recursive:
  LOAD_LOCAL 0      ; n
  LOAD_LOCAL 0
  PUSH_I32 1
  SUB_I32           ; n - 1
  CALL factorial 1  ; factorial(n-1)
  MUL_I32           ; n * factorial(n-1)
  RETURN
```

#### 9.3 Sum Array

```assembly
function sum_array:
  ; Input: array_ptr in local 0
  ; Output: sum on stack
  
  PUSH_I32 0
  STORE_LOCAL 1     ; sum = 0
  PUSH_I32 0
  STORE_LOCAL 2     ; i = 0
  
loop:
  LOAD_LOCAL 2      ; i
  LOAD_LOCAL 0      ; array
  ARRAY_LENGTH
  LT_I32            ; i < length?
  JUMP_IF_FALSE done
  
  LOAD_LOCAL 1      ; sum
  LOAD_LOCAL 0      ; array
  LOAD_LOCAL 2      ; i
  LOAD_ARRAY_ELEM   ; array[i]
  ADD_I32           ; sum + array[i]
  STORE_LOCAL 1     ; sum = sum + array[i]
  
  LOAD_LOCAL 2      ; i
  PUSH_I32 1
  ADD_I32           ; i + 1
  STORE_LOCAL 2     ; i = i + 1
  
  JUMP loop
  
done:
  LOAD_LOCAL 1      ; return sum
  RETURN
```

### 10. Comparison with Other VMs

#### 10.1 JVM (Java Virtual Machine)

*Similarities*:
- Stack-based architecture
- Bytecode format
- Type system

*Differences*:
- JVM more complex (verifier, class loading)
- JVM has object model
- This VM is simpler, more educational

#### 10.2 WebAssembly

*Similarities*:
- Stack machine
- Typed instructions
- Low-level

*Differences*:
- Wasm targets web browsers
- Wasm has linear memory model
- This VM has call stack + heap

#### 10.3 Python VM

*Similarities*:
- Stack-based
- Bytecode interpreter

*Differences*:
- Python VM is dynamic
- No type in instructions
- This VM is statically typed

### 11. Performance Characteristics

#### 11.1 Time Complexity

- *Instruction dispatch*: O(1)
- *Stack operations*: O(1)
- *Function call*: O(1) setup + O(locals)
- *Heap allocation*: O(1) bump, O(n) with GC

#### 11.2 Space Complexity

- *Per function*: O(locals + max_stack)
- *Per call*: O(1) frame overhead
- *Heap*: Depends on allocation pattern

### 12. Security Considerations

#### 12.1 Validation

Before execution, verify:

- Valid magic number
- Supported version
- Valid opcodes
- Jump targets within bounds
- Function indices valid
- Type consistency

#### 12.2 Resource Limits

Set limits on:

- Maximum stack depth
- Maximum heap size
- Maximum call depth
- Execution time (optional)

### 13. Tools and Ecosystem

#### 13.1 Assembler

Convert assembly to bytecode:

```
evm-asm program.s -o program.evm
```

#### 13.2 Disassembler

Convert bytecode to assembly:

```
evm-disasm program.evm
```

#### 13.3 Debugger

Interactive debugging:

```
evm-debug program.evm
> break factorial
> run
> step
> print locals
```

#### 13.4 Profiler

Performance analysis:

```
evm-prof program.evm
```

### 14. Future Extensions

#### 14.1 Planned Features

- Exception handling
- Floating-point operations
- Multi-threading support
- Just-in-time compilation
- Better garbage collection

#### 14.2 Research Directions

- Formal verification of VM
- Security analysis tools
- Optimization techniques
- Hardware implementation


### Appendix A: Opcode Summary Table

| Opcode | Mnemonic | Args | Stack Effect |
|--------|----------|------|--------------|
| 0x01 | PUSH_I8 | value(1) | [] -->[Int8] |
| 0x02 | PUSH_I16 | value(2) | [] -->[Int16] |
| 0x03 | PUSH_I32 | value(4) | [] -->[Int32] |
| 0x04 | PUSH_BOOL | value(1) | [] -->[Bool] |
| 0x05 | POP | - | [any] -->[] |
| 0x06 | DUP | - | [a] -->[a,a] |
| 0x07 | SWAP | - | [a,b] -->[b,a] |
| 0x10 | ADD_I8 | - | [a,b] -->[a+b] |
| 0x11 | ADD_I16 | - | [a,b] -->[a+b] |
| 0x12 | ADD_I32 | - | [a,b] -->[a+b] |
| 0x13 | SUB_I8 | - | [a,b] -->[a-b] |
| 0x14 | SUB_I16 | - | [a,b] -->[a-b] |
| 0x15 | SUB_I32 | - | [a,b] -->[a-b] |
| 0x16 | MUL_I8 | - | [a,b] -->[a*b] |
| 0x17 | MUL_I16 | - | [a,b] -->[a*b] |
| 0x18 | MUL_I32 | - | [a,b] -->[a*b] |
| 0x30 | LT_I32 | - | [a,b] -->[a<b] |
| 0x60 | JUMP | offset(4) | [] -->[] |
| 0x61 | JUMP_IF_TRUE | offset(4) | [Bool] -->[] |
| 0x62 | JUMP_IF_FALSE | offset(4) | [Bool] -->[] |
| 0x70 | CALL | index(2), arity(1) | [args] -->[ret] |
| 0x71 | RETURN | - | [val] -->[val] |
| 0x80 | LOAD_LOCAL | index(2) | [] -->[val] |
| 0x81 | STORE_LOCAL | index(2) | [val] -->[] |
| 0xFF | HALT | - | [] -->[] |


### Appendix B: Sample

#### B.1 Python Implementation Sketch

```python
class VM:
    def __init__(self, bytecode):
        self.code = bytecode
        self.pc = 0
        self.stack = []
        self.frames = []
        self.globals = [0] * 256
    
    def run(self):
        while self.pc < len(self.code):
            op = self.fetch_byte()
            self.dispatch(op)
    
    def dispatch(self, opcode):
        if opcode == 0x03:  ## PUSH_I32
            value = self.fetch_i32()
            self.stack.append(value)
        elif opcode == 0x12:  ## ADD_I32
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a + b)
        ## ... more opcodes
```

#### B.2 C Implementation Sketch

```c
typedef struct {
    uint8_t* code;
    size_t pc;
    int32_t* stack;
    size_t sp;
    Frame* frames;
    size_t fp;
} VM;

void vm_run(VM* vm) {
    while (vm->pc < vm->code_length) {
        uint8_t op = vm->code[vm->pc++];
        vm_dispatch(vm, op);
    }
}
```

### Reference

- Lindholm, T., et al. (2014). *The Java Virtual Machine Specification*
- Nystrom, R. (2021). *Crafting Interpreters*
- Aho, A. V., et al. (2006). *Compilers: Principles, Techniques, and Tools*
- WebAssembly Community Group (2019). *WebAssembly Specification*
