#!/usr/bin/env python3
# coding: utf-8

"""
Virtual machine that executes numeric code assembled by the met.py assembler.
"""

import sys
import getopt
from collections import deque
from typing import List, Any, Deque, Union, Optional


class Opcodes:
    """Constants for opcodes - shared with the assembler."""
    # Internal states
    EXIT = -1
    DONE = -2
    
    # Instructions - must be in sync with met.py
    NOP = 0
    CALL = 1
    FALSE = 2
    FFLAG = 3
    TFLAG = 4
    MATCH = 5
    PRINT = 6
    RETURN = 7
    STOP = 8
    THEN = 9
    TRUE = 10


class Stack:
    """A simple stack implementation."""
    
    def __init__(self):
        """Initialize an empty stack."""
        self.stack: List[Any] = []
    
    def push(self, value: Any) -> None:
        """Push a value onto the stack.
        
        Args:
            value: Value to push
        """
        self.stack.append(value)
    
    def pop(self) -> Any:
        """Pop a value from the stack.
        
        Returns:
            The value from the top of the stack, or EXIT if the stack is empty
        """
        if len(self.stack) > 0:
            return self.stack.pop()
        return Opcodes.EXIT
    
    def is_empty(self) -> bool:
        """Check if the stack is empty.
        
        Returns:
            True if the stack is empty, False otherwise
        """
        return len(self.stack) == 0
    
    def peek(self) -> Any:
        """Look at the top value without popping it.
        
        Returns:
            The value from the top of the stack, or EXIT if the stack is empty
        """
        if len(self.stack) > 0:
            return self.stack[-1]
        return Opcodes.EXIT


class VirtualMachine:
    """A virtual machine that executes numeric code."""
    
    def __init__(self):
        """Initialize the virtual machine."""
        self.code: List[Any] = []
        self.stack = Stack()      # Call stack
        self.tape = Stack()       # Input/output pointer stack
        self.pc = 0               # Program counter
        self.flag = False         # Global flag
        self.input: Deque[str] = deque()
        self.inp = 0              # Input pointer
        self.output: List[str] = []
        self.outp = 0             # Output pointer
        self.verbose = False
    
    def set_code(self, contents: List[Any]) -> None:
        """Set the code to be executed.
        
        Args:
            contents: The code to execute
        """
        self.code = contents
    
    def set_input(self, input_data: Union[List[str], Deque[str]]) -> None:
        """Set the input data.
        
        Args:
            input_data: The input data
        """
        self.input = deque(input_data) if isinstance(input_data, list) else input_data
        self.output = []
        self.inp = 0
        self.outp = 0
    
    def get_output(self) -> str:
        """Get the output data.
        
        Returns:
            The output data as a space-separated string
        """
        return ' '.join(self.output)
    
    def next_code(self) -> Any:
        """Get the next code value and advance the program counter.
        
        Returns:
            The next code value, or EXIT if at the end of the code
        """
        if self.pc < len(self.code):
            c = self.code[self.pc]
            self.pc += 1
            return c
        return Opcodes.EXIT
    
    def execute(self, op: int) -> Optional[int]:
        """Execute an operation.
        
        Args:
            op: The operation code to execute
        
        Returns:
            DONE if the program should stop, None otherwise
        """
        if op == Opcodes.CALL:
            # Call address and put current pc on stack
            address = self.next_code()
            self.tape.push(self.inp)
            self.tape.push(self.outp)
            self.stack.push(self.pc)
            self.pc = address
        
        elif op == Opcodes.FALSE:
            # If flag is false, jump to address
            address = self.next_code()
            if not self.flag:
                self.pc = address
        
        elif op == Opcodes.FFLAG:
            # Set global flag to false
            self.flag = False
        
        elif op == Opcodes.TFLAG:
            # Set global flag to true
            self.flag = True
        
        elif op == Opcodes.MATCH:
            # Check what's on input tape and match with item
            item = self.next_code()
            c = self.input[self.inp]
            if c == '$':
                return Opcodes.DONE
            if c == item:
                self.flag = True
                self.inp += 1
            else:
                self.flag = False
        
        elif op == Opcodes.PRINT:
            # Print to output tape
            item = self.next_code()
            self.output.insert(self.outp, item)
            self.outp += 1
        
        elif op == Opcodes.RETURN:
            # Return from call
            address = self.stack.pop()
            self.pc = address
            
            # Pop the output pointer
            self.outp = self.tape.pop()
            
            # Determine input pointer based on flag
            pointer = self.tape.pop()
            if not self.flag:
                self.inp = pointer
        
        elif op == Opcodes.STOP:
            # Explicit stop
            return Opcodes.DONE
        
        elif op == Opcodes.THEN:
            # Match next item in input if flag is true
            item = self.next_code()
            c = self.input[self.inp]
            if c == '$':
                return Opcodes.DONE
            if c == item:
                if self.flag:
                    self.inp += 1
                else:
                    self.flag = False
            else:
                self.flag = False
        
        elif op == Opcodes.TRUE:
            # If flag is true, jump to address
            address = self.next_code()
            if self.flag:
                self.pc = address
        
        return None
    
    def print_debug(self) -> None:
        """Print debug information."""
        print("OUTPUT=", self.get_output())
        print("FLAG=", self.flag)
    
    def run(self, contents: List[Any], verbose: bool = False) -> str:
        """Run the virtual machine.
        
        Args:
            contents: The code to execute
            verbose: Whether to print debug information
        
        Returns:
            The output of the program
        """
        self.verbose = verbose
        self.set_code(contents)
        
        while True:
            opcode = self.next_code()
            if opcode == Opcodes.EXIT:  # No more codes
                break
            
            end_flag = self.execute(opcode)
            if end_flag == Opcodes.DONE:  # Explicit stop
                if verbose:
                    self.print_debug()
                return self.get_output()
        
        return self.get_output()


class Runner:
    """Runs a program on the virtual machine."""
    
    def __init__(self):
        """Initialize the runner."""
        self.vm = VirtualMachine()
        self.contents = []
    
    def load(self, file: str) -> List[Any]:
        """Load a file of comma-separated values.
        
        Args:
            file: The file to load
        
        Returns:
            The contents of the file as a list
        """
        content = []
        with open(file, 'r') as f:
            for line in f.readlines():
                chars = line.strip().split(',')
                for i in chars:
                    if i.strip():  # Skip empty entries
                        if i.isdigit():
                            content.append(int(i))
                        else:
                            content.append(i)
        return content
    
    def run_program(self, program_file: str, input_file: str, output_file: str, verbose: bool = False) -> None:
        """Run a program on the virtual machine.
        
        Args:
            program_file: The file containing the program
            input_file: The file containing the input data
            output_file: The file to write the output to
            verbose: Whether to print debug information
        """
        if verbose:
            print("Input file:", input_file)
        
        # Load input file and add end marker
        input_data = self.load(input_file) + ['$']
        self.vm.set_input(input_data)
        
        if verbose:
            print("INPUT=", self.vm.input)
        
        # Load program file
        print("Program file:", program_file)
        self.contents = self.load(program_file)
        
        # Run program
        out = self.vm.run(self.contents, verbose)
        
        # Save output
        with open(output_file, 'w') as f:
            f.write(out)


def main():
    """Main function to handle command line arguments."""
    input_file = ''
    output_file = ''
    test_file = ''
    verbose = False
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "vht:i:o:", ["tfile=", "ifile=", "ofile="])
    except getopt.GetoptError:
        print('calfe.py -t <testfile> -i <inputfile> -o <outputfile>')
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-v':
            verbose = True
        elif opt == '-h':
            print('usage: calfe.py -t <testfile> -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-t", "--tfile"):
            test_file = arg
        elif opt in ("-i", "--ifile"):
            input_file = arg
        elif opt in ("-o", "--ofile"):
            output_file = arg
    
    if not input_file or not output_file or not test_file:
        print('Error: Input, output, and test files must be specified')
        print('usage: calfe.py -t <testfile> -i <inputfile> -o <outputfile>')
        sys.exit(2)
    
    if verbose:
        print("Running...")
    
    runner = Runner()
    runner.run_program(input_file, test_file, output_file, verbose)
    
    if verbose:
        print("Done.")


if __name__ == "__main__":
    main()
