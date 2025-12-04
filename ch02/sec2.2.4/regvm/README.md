
## REGVM overview

## regvm.c

This C code implements a simple virtual machine (VM) that operates on four
registers (`A`, `B`, `C`, `D`), and includes a basic instruction set that
can manipulate these registers. The VM supports fetching instructions from
memory, decoding them, executing them, and updating flags (`Z` for zero and
`N` for negative values).


### Structure

The virtual machine is defined as a `REGVM` struct, containing:
- *Program Counter (`pc`)*: Tracks the next instruction to execute.
- *Registers*: An array representing the four registers.
- *Flags*: An array holding the zero (`Z`) and negative (`N`) flags.
- *Memory*: A program memory capable of storing up to `MAX_PROGRAM_SIZE` instructions.


### Key functions

1. *`init_vm`*: Initializes the VM by resetting the program counter, registers, flags, and memory.
2. *`load_program`*: Loads a program into the VM’s memory.
3. *`fetch`*: Retrieves the next instruction from memory and increments the program counter.
4. *`decode_and_execute`*: Decodes and executes instructions like
   `MOV`, `ADD`, `SUB`, `MUL`, `CMP`, `JMP`, and `PRINT`. It also handles flag updates for arithmetic operations.
5. *`update_flags`*: Updates the zero and negative flags based on the result of an arithmetic operation.
6. *`run`*: Fetches, decodes, and executes instructions in a loop until the program finishes.

### Example: Factorial of 5

The program calculates the factorial of 5 using the following instructions:
- *MOV A 1*: Initializes `A` to 1.
- *MOV B 5*: Initializes `B` to 5.
- *CMP B 0*: Compares `B` to 0.
- *JZ 7*: Jumps to instruction 7 if `B` is 0 (which is the end).
- *MUL A B*: Multiplies `A` by `B`.
- *SUB B 1*: Decreases `B` by 1.
- *JMP 3*: Jumps back to the comparison step (loop).
- *PRINT A*: Outputs the result stored in `A` (the factorial).

### Complete C code

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_PROGRAM_SIZE 100
#define MAX_REGISTERS 4

typedef struct {
    int pc;
    int registers[MAX_REGISTERS]; // A, B, C, D
    int flags[2]; // Z, N
    char *memory[MAX_PROGRAM_SIZE];
} REGVM;

// fwd decl
void init_vm(REGVM *vm);
void load_program(REGVM *vm, char *program[], int size);
void fetch(REGVM *vm, char *instruction);
int decode_and_execute(REGVM *vm, char *instruction);
void update_flags(REGVM *vm, int value);
void run(REGVM *vm);
int get_value(REGVM *vm, char *arg);

void init_vm(REGVM *vm) {
    vm->pc = 0;
    memset(vm->registers, 0, sizeof(vm->registers));
    memset(vm->flags, 0, sizeof(vm->flags));
    memset(vm->memory, 0, sizeof(vm->memory));
}

void load_program(REGVM *vm, char *program[], int size) {
    for (int i = 0; i < size; i++) {
        vm->memory[i] = program[i];
    }
}

void fetch(REGVM *vm, char *instruction) {
    if (vm->pc < MAX_PROGRAM_SIZE && vm->memory[vm->pc] != NULL) {
        *instruction = vm->memory[vm->pc];
        vm->pc++;
    } else {
        *instruction = NULL;
    }
}

int get_value(REGVM *vm, char *arg) {
    if (arg[0] >= 'A' && arg[0] <= 'D') {
        return vm->registers[arg[0] - 'A'];
    } else {
        return atoi(arg);
    }
}

int decode_and_execute(REGVM *vm, char *instruction) {
    if (!instruction)
        return 0;

    char opcode[4];
    char arg1[2];
    char arg2[10];
    sscanf(instruction, "%s %s %s", opcode, arg1, arg2);

    int val1, val2;

    if (strcmp(opcode, "MOV") == 0) {
        val1 = (arg1[0] - 'A');
        vm->registers[val1] = get_value(vm, arg2);

    } else if (strcmp(opcode, "ADD") == 0) {
        val1 = (arg1[0] - 'A');
        vm->registers[val1] += get_value(vm, arg2);
        update_flags(vm, vm->registers[val1]);

    } else if (strcmp(opcode, "SUB") == 0) {
        val1 = (arg1[0] - 'A');
        vm->registers[val1] -= get_value(vm, arg2);
        update_flags(vm, vm->registers[val1]);

    } else if (strcmp(opcode, "MUL") == 0) {
        val1 = (arg1[0] - 'A');
        vm->registers[val1] *= get_value(vm, arg2);
        update_flags(vm, vm->registers[val1]);

    } else if (strcmp(opcode, "CMP") == 0) {
        val1 = get_value(vm, arg1);
        val2 = get_value(vm, arg2);
        vm->flags[0] = (val1 == val2) ? 1 : 0;

    } else if (strcmp(opcode, "JMP") == 0) {
        vm->pc = atoi(arg1);

    } else if (strcmp(opcode, "JZ") == 0) {
        if (vm->flags[0]) {
            vm->pc = atoi(arg1);
        }

    } else if (strcmp(opcode, "PRINT") == 0) {
        val1 = (arg1[0] - 'A');
        printf("Register %c: %d\n", arg1[0], vm->registers[val1]);

    } else {
        fprintf(stderr, "Unknown opcode: %s\n", opcode);
        return 0;
    }

    return 1;
}

void update_flags(REGVM *vm, int value) {
    vm->flags[0] = (value == 0) ? 1 : 0;  // Zero
    vm->flags[1] = (value < 0) ? 1 : 0;   // Negative
}

void run(REGVM *vm) {
    char *instruction;
    while (1) {
        fetch(vm, &instruction);
        if (!instruction || !decode_and_execute(vm, instruction)) {
            break;
        }
    }
}

int main() {
    REGVM vm;
    init_vm(&vm);

    char *factorial[] = {
        "MOV A 1",
        "MOV B 5",
        "CMP B 0",
        "JZ 7",
        "MUL A B",
        "SUB B 1",
        "JMP 3",
        "PRINT A"
    };

    load_program(&vm, factorial, sizeof(factorial) / sizeof(factorial[0]));
    run(&vm);

    return 0;
}
```


---
## regvm.py

This Python code implements a similar virtual machine as the C version. It
is designed to handle basic instructions (`MOV`, `ADD`, `SUB`, `MUL`, etc.)
and modify registers accordingly. The program runs a simple loop to compute
the factorial of 5.


### Structure

1. *`__init__`:* Initializes the virtual machine with four registers (`A`, `B`, `C`, `D`),
   a program counter (`pc`), two flags (`Z`, `N`), and an empty memory list.
2. *`load_program`:* Loads the list of program instructions into the VM's memory.
3. *`fetch`:* Retrieves the next instruction based on the program counter and increments the counter.
4. *`decode_and_execute`:* Decodes and executes the instruction based on the opcode.
   Supports `MOV`, `ADD`, `SUB`, `MUL`, `CMP`, `JMP`, `JZ`, and `PRINT` operations.
5. *`update_flags`:* Updates the zero (`Z`) and negative (`N`) flags based on the value of a register.
6. *`run`:* Runs the VM, fetching and executing instructions until the end of the program.


### Example: Factorial of 5 (yeah again)

The example program in `factorial` computes the factorial of 5:
- *MOV A 1:* Initializes `A` to 1.
- *MOV B 5:* Initializes `B` to 5.
- *CMP B 0:* Compares `B` with 0. If `B` is 0, it jumps to instruction 7 (end).
- *MUL A B:* Multiplies `A` by `B`.
- *SUB B 1:* Decreases `B` by 1.
- *JMP 3:* Jumps back to the comparison step (loop).
- *PRINT A*: Outputs the result stored in register `A`, which will be the factorial of 5.

### Complete Python code

```python
class REGVM:
    def __init__(self):
        self.pc = 0
        self.registers = {
            'A': 0,
            'B': 0,
            'C': 0,
            'D': 0
        }
        self.flags = {
            'Z': 0, # Zero
            'N': 0  # Negative
        }
        self.memory = []

    def load_program(self, program):
        self.memory = program

    def fetch(self):
        if self.pc < len(self.memory):
            instruction = self.memory[self.pc]
            self.pc += 1
            return instruction
        else:
            return None

    def decode_and_execute(self, instruction):
        if not instruction:
            return False

        parts = instruction.split()
        opcode = parts[0]
        args = parts[1:]

        if opcode == 'MOV':
            fst = args[0]
            snd = args[1]
            self.registers[fst] = int(snd)

        elif opcode == 'ADD':
            fst = args[0]
            snd = args[1]
            if snd.isalpha():
                self.registers[fst] += self.registers[snd]
            else:
                self.registers[fst] += int(snd)
            self.update_flags(self.registers[fst])

        elif opcode == 'SUB':
            fst = args[0]
            snd = args[1]
            if snd.isalpha():
                self.registers[fst] -= self.registers[snd]
            else:
                self.registers[fst] -= int(snd)
            self.update_flags(self.registers[fst])

        elif opcode == 'MUL':
            fst = args[0]
            snd = args[1]
            if snd.isalpha():
                self.registers[fst] *= self.registers[snd]
            else:
                self.registers[fst] *= int(snd)
            self.update_flags(self.registers[fst])

        elif opcode == 'CMP':
            fst = args[0]
            snd = args[1]
            if self.registers[fst] == int(snd):
                self.flags['Z'] = 1
            else:
                self.flags['Z'] = 0

        elif opcode == 'JMP':
            fst = args[0]
            self.pc = int(fst)

        elif opcode == 'JZ':
            fst = args[0]
            if self.flags['Z']:
                self.pc = int(fst)

        elif opcode == 'PRINT':
            fst = args[0]
            print(f"Register {fst}: {self.registers[fst]}")

        else:
            raise ValueError(f"Unknown opcode: {opcode}")
        
        return True
    
    def update_flags(self, value):
        self.flags['Z'] = 1 if value == 0 else 0
        self.flags['N'] = 1 if value < 0 else 0
    
    def run(self):
        while True:
            instruction = self.fetch()
            if not instruction or not self.decode_and_execute(instruction):
                break

# factorial
factorial = [
    "MOV A 1",   # init A with 1
    "MOV B 5",   # init B with 5
    "CMP B 0",   # compare B with 0
    "JZ 7",      # if B is 0, jump to end
    "MUL A B",   # multiply A by B and store in A
    "SUB B 1",   # subtract 1 from B
    "JMP 3",     # jump to loop
    "PRINT A",   # Print the result in register A
]

vm = REGVM()
vm.load_program(factorial)
vm.run()
```

### Details in the Python version:
1. *Object-Oriented Design*: The virtual machine is implemented as a class (`REGVM`),
   encapsulating the program counter, registers, flags, and memory.
2. *Instruction execution*: The method `decode_and_execute` decodes the opcode and its
   arguments, executing instructions like `MOV`, `ADD`, `SUB`, `MUL`, `CMP`, `JMP`, `JZ`,
   and `PRINT`. Arithmetic operations update the flags as needed.
3. *Program execution*: The `run` method loops over the program, fetching and executing
   instructions until the program finishes.
4. *Factorial*: The program computes the factorial of 5 in a loop, multiplying the current
   value of `A` by `B` and decrementing `B` until it reaches 0. The result is printed at the end.

### Output:
The Python virtual machine calculates `5!` (factorial of 5), and the result will be printed as:

```shell
Register A: 120
```

This output shows the content of register `A`, which holds the value `120`, the result of `5! = 5 * 4 * 3 * 2 * 1 = 120`.

This comparison demonstrates how a basic virtual machine can be implemented in both C and Python,
with similar logic but differing in terms of language features and syntax.
