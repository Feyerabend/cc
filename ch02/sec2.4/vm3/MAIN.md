
## Main

This is the main program that loads and executes a bytecode file for the virtual machine (VM).
It takes a machine code file as input, reads and parses the file to load the bytecode into the
VM, and then executes it.


### Components

1.	Globals:
	- `MAXPROGLEN`: Defines the maximum length of the bytecode program that can be loaded.
	- `program`: An integer array that holds the parsed bytecode instructions.

2.	File I/O:
	- `allocateprogram()`: Allocates memory for the program array based on MAXPROGLEN.
	- `fsize(FILE* file)`: Determines the size of the input file.
	- `read(char *path)`: Reads the entire content of the file from the provided path and returns it as a string buffer.

3.	Execution:
	- `exec(int* code, int start)`: Creates a new VM instance, initializes it with the bytecode
      (code) and the starting point (start), runs the VM, and frees the VM after execution.

4.	Main:
	The main function handles the overall flow:
	- It first reads the bytecode file specified as a command-line argument (`argv[1]`).
    - The bytecode is expected to be a series of integers separated by commas, with the
      first integer being the starting program counter (start), and the rest being the actual bytecode instructions.
	- The bytecode is parsed, loaded into the program array, and then executed by calling `exec()`.
	- The execution time is measured using `clock()` and printed after the VM finishes execution.


### Parsing

The input file contains machine code in the form of comma-separated numbers. For example, the file might look like:

```shell
0,2,5,3,9,1,0
```

Where:
    - The first number (0) is the starting address (start), which tells the VM where to begin execution.
	- The following numbers (2, 5, 3, 9, 1, 0) represent the bytecode instructions.

The code uses `strtok` to tokenize the input string and convert each token into an integer using `atoi`.
These integers are then loaded into the program array, which will be passed to the VM for execution.

### Structure

1.	Loading program:
	- The program file is read and stored in the source string.
	- The start value is parsed first (the header), then the rest of the program (the body) is parsed
      and loaded into the program array.

2.	Printing:
	- After loading the program into memory, the bytecode is printed to show the code that will be executed.

3.	Timing:
	- The execution is timed using `clock()`. The duration is calculated in seconds and printed after the
      VM finishes running the bytecode.


#### Example

If the input file contains:

```shell
0,SET,5,SET,10,ADD,PRINT,HALT
```

The program will:
1.	Load the bytecode starting at address 0.
2.	Execute the bytecode:
	- Set 5 on the stack.
	- Set 10 on the stack.
	- Add the two numbers.
	- Print the result (15).
	- Halt the VM.

The output would show the VM state after each instruction and print the result of the PRINT instruction.

### Conclusion

This program integrates with the defined VM to provide a complete pipeline for loading, executing, and timing
the execution of bytecode files. The program also includes basic error checking, such as file reading, but
could be extended further for robustness (e.g. handling invalid bytecode formats or execution errors).
