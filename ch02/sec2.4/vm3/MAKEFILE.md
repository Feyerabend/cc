
## Makefile

The Makefile compiles a C project, executes a Python script for assembling bytecode, and runs the resulting C program.

### Components

1.	Compiler configuration:
	- `CC = gcc`: Defines the C compiler as gcc.
	- `CFLAGS = -Wall`: Enables all warnings during the compilation to catch potential issues.
	- `LDFLAGS`: Left empty for now but can include linker flags if needed.
	- `OBJFILES = main.o vm3.o`: The object files that will be generated and linked to create the final executable.
	- `TARGET = main`: The name of the final executable binary.

2.	Python for assembly:
	- `PYTHON_SCRIPT = asm.py`: Specifies the Python script that assembles the input assembly file into bytecode.
	- `FILE ?= input`: Defines the default input file base name. This can be overridden by passing a different value for FILE when invoking make.
	- `INPUT_FILE = $(FILE).a`: The input assembly file name.
	- `OUTPUT_FILE = $(FILE).b`: The bytecode output file produced by the Python script.


#### Rules

1.	`all`:
    - This is the default target and is responsible for running both the Python script (python_run) and then
      compiling and executing the C program; `$(TARGET)` and `run_c_program`.

2.	`$(TARGET)`:
	- Compiles the C source files (`main.c` and `vm3.c`, which correspond to `main.o` and `vm3.o`) into the target executable (`main`).

3.	`python_run`:
	- Invokes the Python assembler (`asm.py`) with the input file (`input.a` by default) and outputs the bytecode to the output file (`input.b`).
	- The -v flag in the Python command enables verbose mode, meaning detailed information will be printed during the assembly process.

4.	`run_c_program`:
	- Executes the compiled C program (`./main`) with the bytecode output file (`input.b`) as an argument. This runs the VM using the assembled bytecode.

5.	`clean`:
	- Removes all generated object files `(*.o)`, the target executable (main), and any temporary files `(*~)`.


#### Workflow

The makeup of this folder is much to illustrate the workflow around compiling, linking, assembling files.

1.	Assembling bytecode:
	- The Python script assembles the input assembly file (`input.a`), producing a bytecode/binary file (`input.b`).

2.	Compiling and linking:
	- The C files (`main.c` and `vm3.c`) are compiled into object files (`main.o` and `vm3.o`), which are then linked
      to produce the executable (`main`).

3.	Running the VM:
	- The assembled bytecode is passed to the C program for execution. The output of the VM (e.g. printed values
      from bytecode) will be displayed.


#### Customisation and sample

You can specify a different input file by running:

```make
make FILE=someprogram
```

This would assemble `someprogram.a` and execute the resulting bytecode (`someprogram.b`).

If you have an assembly file `input.a`, you can run:

```make
make
```

This will:

1.	Assemble `input.a` into `input.b`.
2.	Compile and link the C files.
3.	Run the VM with `input.b`.

If you want to clean up after running the program:

```make
make clean
```

This will remove the compiled files and the executable.
