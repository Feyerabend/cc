
## VM3

This code implements a simple stack-based virtual machine (VM) in C. The VM executes
bytecode instructions, which manipulate a stack and allow basic arithmetic, logic,
control flow, and memory operations.


#### VM

```c
typedef struct {
    int* code;    // array of bytecode instructions
    int* stack;   // stack used for operations
    int pc;       // program counter (points to the next instruction)
    int sp;       // stack pointer (points to the top of the stack)
    int fp;       // frame pointer (used to track function call frames)
} VM;
```

The VM keeps track of its program counter (pc), stack pointer (sp), frame pointer (fp),
the instruction code, and a stack of a fixed size (STACK_SIZE).

Instruction Set: The VM supports a set of opcodes, which are constants that represent
operations (e.g., ADD, SUB, CALL, etc.). Each opcode may or may not take arguments
depending on its arity (number of required operands).

#### Functions

1. VM management:
  * `newVM(int* code, int pc)`: Initializes a new VM instance with bytecode and an initial program counter (pc).
  * `freeVM(VM* vm)`: Frees the VM's allocated resources (mainly the stack).
  * `push(VM* vm, int v)`: Pushes a value onto the stack.
  * `pop(VM* vm)`: Pops the top value from the stack.
  * `nextcode(VM* vm)`: Fetches the next instruction or argument from the bytecode and advances the program counter.

2. Debugging and/or logging:
  * `print_stack(VM* vm)`: Prints the current stack contents.
  * `print_vm_state(VM* vm)`: Prints the current state of the VM (including the program counter, stack pointer, and frame pointer).

3. Main loop:
  * `run(VM* vm)`: This is the heart of the virtual machine, where the bytecode is executed in a loop.
    The function fetches the next opcode, decodes it, and performs the associated operation. After each
    instruction, the state of the VM is printed (if debugging). If a HALT opcode is encountered, the
    VM stops execution.


#### Instructions

Arithmetic:
  * ADD: Pops two values from the stack, adds them, and pushes the result back.
  * SUB: Pops two values, subtracts the second from the first, and pushes the result.
  * MUL, MOD: Performs multiplication and modulo operations similarly.

Control flow:
  * JP: Unconditional jump to the specified address.
  * JPZ: Jumps to the address if the top of the stack is zero.
  * JPNZ: Jumps to the address if the top of the stack is non-zero.

Function calls:
  * CALL: Jumps to a function address, saving the return address and frame pointer.
  * RET: Returns from the current function, restoring the stack and program state.

Memory:
  * LD, ST: Load and store values in the local stack frame.
  * LOAD, STORE: Load and store values in global memory (using stack as global memory).

Logic:
  * AND, OR: Logical AND/OR on the top two stack values.
  * LSH, RSH: Left and right shift operations.
  * EQ, EQZ: Equality and zero-check.

Stack:
  * DUP: Duplicates the top value on the stack.
  * DROP: Discards the top value on the stack.

I/O:
  * PRINT: Prints the top value on the stack followed by a newline.
  * PRNT: Prints the top value on the stack without a newline.


#### Example

During execution, the VM fetches the next opcode using nextcode(vm) and uses a switch statement to
execute the corresponding operation. After executing each instruction, the current state of the VM
(stack and register values) is printed for debugging purposes.

For example, an assembly program with:

```assembly
SET 5
SET 10
ADD
PRINT
HALT
```

would push the values 5 and 10 onto the stack, add them, print the result (15), and halt the execution.

### Key points

* Stack-based: All operations are performed on values pushed onto and popped from the stack.
* Simple function calls: The VM supports basic function calls and returns with CALL and RET, using a stack-based frame pointer for local variables.
* Memory access: The LD, ST, LOAD, and STORE instructions allow interaction with local and global memory.

This implementation offers a minimal foundation for a stack-based virtual machine,
useful for executing bytecode or an assembly-like language.
