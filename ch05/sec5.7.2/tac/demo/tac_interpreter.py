#!/usr/bin/env python3
"""
TAC Interpreter - Factorial Example
====================================

This program demonstrates a complete Three-Address Code program
by implementing a factorial calculator.

The TAC is executed by a simple interpreter, showing how TAC
serves as an intermediate representation that can be directly
executed or compiled to machine code.
"""

from typing import Dict, List, Any, Optional


class TACInterpreter:
    """Interpreter for Three-Address Code programs."""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize the interpreter.
        
        Args:
            verbose: If True, print execution trace
        """
        self.verbose = verbose
        self.variables: Dict[str, Any] = {}
        self.labels: Dict[str, int] = {}
        self.program: List[Dict] = []
        self.pc = 0  # Program counter
        
    def load_program(self, program: List[Dict]):
        """
        Load a TAC program into the interpreter.
        
        Args:
            program: List of TAC instruction dictionaries
        """
        self.program = program
        self.pc = 0
        self.variables = {}
        
        # First pass: find all labels
        for i, instr in enumerate(program):
            if instr.get('type') == 'label':
                self.labels[instr['identifier']] = i
        
        if self.verbose:
            print("Labels found:", self.labels)
    
    def evaluate_term(self, term: Dict) -> Any:
        """
        Evaluate a term (can be a variable, constant, or expression).
        
        Args:
            term: Dictionary representing a term
            
        Returns:
            The evaluated value
        """
        if term['type'] == 'term':
            value = term['value']
            # Check if it's a variable or constant
            if isinstance(value, str):
                if value.isdigit():
                    return int(value)
                elif value in self.variables:
                    return self.variables[value]
                else:
                    raise NameError(f"Undefined variable: {value}")
            else:
                return value
        elif term['type'] == 'binary_op':
            left = self.evaluate_term(term['left'])
            right = self.evaluate_term(term['right'])
            op = term['operator']
            
            if op == '+':
                return left + right
            elif op == '-':
                return left - right
            elif op == '*':
                return left * right
            elif op == '/':
                return left // right  # Integer division
            elif op == '<=':
                return left <= right
            elif op == '<':
                return left < right
            elif op == '>=':
                return left >= right
            elif op == '>':
                return left > right
            elif op == '==':
                return left == right
            elif op == '!=':
                return left != right
            else:
                raise ValueError(f"Unknown operator: {op}")
        else:
            raise ValueError(f"Unknown term type: {term['type']}")
    
    def execute_instruction(self, instr: Dict) -> bool:
        """
        Execute a single TAC instruction.
        
        Args:
            instr: Instruction dictionary
            
        Returns:
            True to continue execution, False to halt
        """
        instr_type = instr.get('type')
        
        if self.verbose:
            print(f"[PC={self.pc}] Executing: {instr_type}", end="")
        
        if instr_type == 'label':
            # Labels are just markers, no execution
            if self.verbose:
                print(f" {instr['identifier']}")
            pass
        
        elif instr_type == 'assignment':
            # Variable assignment
            dest = instr['dest']
            value = self.evaluate_term(instr['rhs'])
            self.variables[dest] = value
            
            if self.verbose:
                print(f" {dest} = {value}")
        
        elif instr_type == 'if':
            # Conditional jump
            condition = self.evaluate_term(instr['condition'])
            target_label = instr['label']
            
            if self.verbose:
                print(f" condition={condition}, goto {target_label if condition else 'next'}")
            
            if condition:
                if target_label in self.labels:
                    self.pc = self.labels[target_label]
                    return True  # Don't increment PC
                else:
                    raise ValueError(f"Undefined label: {target_label}")
        
        elif instr_type == 'goto':
            # Unconditional jump
            target_label = instr['label']
            
            if self.verbose:
                print(f" {target_label}")
            
            if target_label in self.labels:
                self.pc = self.labels[target_label]
                return True  # Don't increment PC
            else:
                raise ValueError(f"Undefined label: {target_label}")
        
        elif instr_type == 'print':
            # Print a variable
            var_name = instr['value']
            if var_name in self.variables:
                value = self.variables[var_name]
                print(f"\n>>> OUTPUT: {var_name} = {value}")
            else:
                raise NameError(f"Undefined variable: {var_name}")
        
        elif instr_type == 'halt':
            # Stop execution
            if self.verbose:
                print()
            return False
        
        else:
            raise ValueError(f"Unknown instruction type: {instr_type}")
        
        # Increment program counter
        self.pc += 1
        return True
    
    def run(self):
        """Execute the loaded program."""
        if self.verbose:
            print("\n" + "="*60)
            print("EXECUTING TAC PROGRAM")
            print("="*60 + "\n")
        
        while self.pc < len(self.program):
            if not self.execute_instruction(self.program[self.pc]):
                break
        
        if self.verbose:
            print("\n" + "="*60)
            print("EXECUTION COMPLETE")
            print("="*60)
            print("\nFinal variable values:")
            for var, val in sorted(self.variables.items()):
                print(f"  {var} = {val}")


# Example TAC program: Factorial
factorial_program = [
    {"type": "label", "identifier": "start"},
    {"type": "assignment", "dest": "n", "rhs": {"type": "term", "value": "5"}},  # 5! = 120
    {"type": "assignment", "dest": "result", "rhs": {"type": "term", "value": "1"}},
    {"type": "label", "identifier": "loop"},
    {"type": "if", "condition": {
        "type": "binary_op",
        "left": {"type": "term", "value": "n"},
        "operator": "<=",
        "right": {"type": "term", "value": "0"}
    }, "label": "end"},
    {"type": "assignment", "dest": "result", "rhs": {
        "type": "binary_op",
        "left": {"type": "term", "value": "result"},
        "operator": "*",
        "right": {"type": "term", "value": "n"}
    }},
    {"type": "assignment", "dest": "n", "rhs": {
        "type": "binary_op",
        "left": {"type": "term", "value": "n"},
        "operator": "-",
        "right": {"type": "term", "value": "1"}
    }},
    {"type": "goto", "label": "loop"},
    {"type": "label", "identifier": "end"},
    {"type": "print", "value": "result"},
    {"type": "halt"},
]

# Example: Sum of first N numbers
sum_program = [
    {"type": "label", "identifier": "start"},
    {"type": "assignment", "dest": "n", "rhs": {"type": "term", "value": "10"}},
    {"type": "assignment", "dest": "i", "rhs": {"type": "term", "value": "1"}},
    {"type": "assignment", "dest": "sum", "rhs": {"type": "term", "value": "0"}},
    {"type": "label", "identifier": "loop"},
    {"type": "if", "condition": {
        "type": "binary_op",
        "left": {"type": "term", "value": "i"},
        "operator": ">",
        "right": {"type": "term", "value": "n"}
    }, "label": "end"},
    {"type": "assignment", "dest": "sum", "rhs": {
        "type": "binary_op",
        "left": {"type": "term", "value": "sum"},
        "operator": "+",
        "right": {"type": "term", "value": "i"}
    }},
    {"type": "assignment", "dest": "i", "rhs": {
        "type": "binary_op",
        "left": {"type": "term", "value": "i"},
        "operator": "+",
        "right": {"type": "term", "value": "1"}
    }},
    {"type": "goto", "label": "loop"},
    {"type": "label", "identifier": "end"},
    {"type": "print", "value": "sum"},
    {"type": "halt"},
]


def print_tac_program(program: List[Dict], title: str):
    """Print a TAC program in human-readable format."""
    print("\n" + "="*60)
    print(title)
    print("="*60)
    
    for instr in program:
        instr_type = instr.get('type')
        
        if instr_type == 'label':
            print(f"label {instr['identifier']}:")
        elif instr_type == 'assignment':
            print(f"  {instr['dest']} = {format_term(instr['rhs'])}")
        elif instr_type == 'if':
            print(f"  if {format_term(instr['condition'])} goto {instr['label']}")
        elif instr_type == 'goto':
            print(f"  goto {instr['label']}")
        elif instr_type == 'print':
            print(f"  print {instr['value']}")
        elif instr_type == 'halt':
            print(f"  halt")
    
    print("="*60)


def format_term(term: Dict) -> str:
    """Format a term for display."""
    if term['type'] == 'term':
        return str(term['value'])
    elif term['type'] == 'binary_op':
        left = format_term(term['left'])
        right = format_term(term['right'])
        op = term['operator']
        return f"{left} {op} {right}"
    return str(term)


def main():
    """Main function to demonstrate TAC execution."""
    
    print("="*60)
    print("TAC INTERPRETER - EXAMPLE PROGRAMS")
    print("="*60)
    
    # Factorial example
    print_tac_program(factorial_program, "FACTORIAL PROGRAM (5!)")
    print("\nPress Enter to execute...")
    input()
    
    interpreter = TACInterpreter(verbose=True)
    interpreter.load_program(factorial_program)
    interpreter.run()
    
    print("\n\n")
    
    # Sum example
    print_tac_program(sum_program, "SUM PROGRAM (1 + 2 + ... + 10)")
    print("\nPress Enter to execute...")
    input()
    
    interpreter = TACInterpreter(verbose=True)
    interpreter.load_program(sum_program)
    interpreter.run()
    
    print("\n\nDemonstration complete!")


if __name__ == "__main__":
    main()
