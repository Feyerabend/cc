
## Assembler

This is introduced to get an idea of how assembler could work. Naturally it is much simplified.
This Python assembler reads an input assembly file, converts it into bytecode based on
instructions defined in a header file (`vm3.h`), and outputs the resulting bytecode to
a file.

1. `no_comments(content)`: This function strips comments (lines starting with #) from
   the input code, making it easier to focus on the actual instructions.

2. `prepare(content)`: This function prepares the input content for parsing by:
    * Removing comments.
	* Stripping excess whitespace from each line.
	* Converting each line into a list of tokens (split by whitespace).
    It also filters out empty lines.

3. `to_decimal(number, line_num)`: Converts a given string to an integer. If conversion
   fails, an error message is printed, and the program exits.

4. `parse(line_num, line, ops)`: This function parses each line of assembly instructions.
   It checks if the opcode is valid and ensures the correct number of arguments (based on
   the arity defined in the enum_dict).

5. `assemble(inputfile, outputfile, enum_dict, verbose)`: This is the main function that
   assembles the code. It performs *two passes* over the input file:
	* First pass: Identifies labels and calculates their offsets. Labels are noted by names
      ending with `:` (e.g. `START:`).
	* Second pass: Replaces labels with actual memory addresses.
   It then converts tokens into decimal values (or memory addresses) and inserts the start
   address (based on the :START label) at the beginning of the bytecode output.

6. `extract(file_path)`: This function extracts the opcodes and their arity (argument count)
   from a header file (`vm3.h`). It looks for an enum structure where opcodes are listed and
   maps each opcode to a unique integer (opcode number) and its arity.

7. `main(argv)`: This is the entry point of the script. It processes command-line arguments
   to get the input and output file paths and handles a verbose option to print extra information
   during execution.

### Example

* The assembler reads a source file written in an assembly-like language.

* It extracts opcodes from the vm3.h header file (which defines the instructions and their arity).

* The source code is processed to replace labels with numeric memory addresses.

* Finally, the processed code is converted into bytecode and written to the specified output file.

### Key points

* *Labels*: Mark specific points in the code to jump to. They are processed and replaced with
  actual memory addresses.

* *Opcodes*: Defined in the header file, each has a corresponding integer and may require
  arguments.

* *Arity*: The number of arguments required by an opcode.

This assembler effectively translates human-readable assembly instructions into a binary
format (bytecode) understandable by a virtual machine.
