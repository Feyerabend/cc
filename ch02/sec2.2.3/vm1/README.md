## VM1

### Explanation of the C program with a simple stack-based Virtual Machine

The code implements a basic stack-based virtual machine (VM) in C, which supports a
few arithmetic operations (`ADD`, `SUB`, `MUL`), a `SET` operation to push values onto
the stack, and a `PRINT` operation to output the result. The program reads instructions
(opcodes) from an array (`code`), executes them, and prints the result.

#### Components of the VM

1. *`VM` structure*:
   - `int* code`: Pointer to the array holding the instructions (program) to be executed.
   - `int* stack`: Stack for holding intermediate values (used for calculations).
   - `int pc`: Program counter that tracks the current instruction being executed.
   - `int sp`: Stack pointer that tracks the top of the stack.

2. *`newVM` Function*:
   - This function creates a new `VM` instance, allocating memory for the virtual machine structure and its stack.
   - It initializes the program counter (`pc`) and stack pointer (`sp`). The stack pointer is initialized to `-1` to indicate that the stack is empty.

   ```c
   VM* newVM(int* code, int pc) {
       VM* vm = (VM*) malloc(sizeof(VM));
       if (vm == NULL) return NULL;
       vm->stack = (int*) malloc(sizeof(int) * STACK_SIZE);
       if (vm->stack == NULL) return NULL;

       vm->code = code;
       vm->pc = pc;
       vm->sp = -1;

       return vm;
   }
   ```

3. *`freeVM` function*:
   - Frees the memory allocated for the virtual machine and its stack.
   
   ```c
   void freeVM(VM* vm) {
       if (vm != NULL) {
           free(vm->stack);
           free(vm);
       }
   }
   ```

4. *`pop` function*:
   - Pops (removes) the top value from the stack by decrementing the stack pointer and returning the value at the top.

   ```c
   int pop(VM* vm) {
       int sp = (vm->sp)--;
       return vm->stack[sp];
   }
   ```

5. *`push` function*:
   - Pushes a value onto the stack by incrementing the stack pointer and storing the value at the new top of the stack.
   
   ```c
   void push(VM* vm, int v) {
       int sp = ++(vm->sp);
       vm->stack[sp] = v;
   }
   ```

6. *`nextcode` function*:
   - Fetches the next instruction (or operand) from the `code` array and increments the program counter.

   ```c
   int nextcode(VM* vm) {
       int pc = (vm->pc)++;
       return vm->code[pc];
   }
   ```


#### VM execution

The `run` function is the main loop of the virtual machine. It continuously fetches, decodes, and executes instructions until a `HALT` opcode is encountered. 

```c
void run(VM* vm) {
    int v, a, b;

    do {
        int opcode = nextcode(vm);
        switch (opcode) {

            case HALT:
                return;

            case SET:
                v = nextcode(vm);
                push(vm, v);
                break;

            case ADD:
                b = pop(vm);
                a = pop(vm);
                push(vm, a + b);
                break;

            case SUB:
                b = pop(vm);
                a = pop(vm);
                push(vm, a - b);
                break;

            case MUL:
                b = pop(vm);
                a = pop(vm);
                push(vm, a * b);
                break;

            case PRINT:
                v = pop(vm);
                printf("%d\n", v);
                break;

            default:
                break;
        }
    } while (TRUE);
}
```

*Instructions*:
- *`HALT`*: Stops the execution of the program.
- *`SET`*: Pushes a value onto the stack.
- *`ADD`*, *`SUB`*, *`MUL`*: Pops two values from the stack, performs the corresponding arithmetic operation, and pushes the result back onto the stack.
- *`PRINT`*: Pops the top value from the stack and prints it.


#### Sample

The `program[]` array contains a simple set of instructions to demonstrate how the virtual machine works. This program pushes two values (`33` and `44`) onto the stack, adds them together, prints the result, and halts.

```c
int program[] = {
    SET, 33,
    SET, 44,
    ADD,
    PRINT,
    HALT
};
```

The steps of execution:
1. *SET 33*: Push `33` onto the stack.
2. *SET 44*: Push `44` onto the stack.
3. *ADD*: Pop `44` and `33` from the stack, add them (`33 + 44 = 77`), and push the result `77` onto the stack.
4. *PRINT*: Pop `77` from the stack and print it.
5. *HALT*: Stop execution.

#### Output

```bash
77
```



#### Main

The `main` function creates a new virtual machine, runs the program, and prints the execution time.

```c
int main() {
    VM* vm = newVM(program, 0);
    if (vm != NULL) {
        clock_t t;
        t = clock();

        run(vm);

        t = clock() - t;
        double duration = ((double) t) / CLOCKS_PER_SEC;
        printf("%f seconds\n", duration);
        freeVM(vm);
    }
    return 0;
}
```


### Summary

This C code represents a simple stack-based virtual machine that can execute a small set of instructions.
It processes arithmetic operations on a stack and can print results. The provided sample program demonstrates
how the VM works by calculating and printing the sum of two numbers.
