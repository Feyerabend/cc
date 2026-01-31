#!/usr/bin/env python3
"""
Three-Address Code (TAC) Generator
===================================

This program converts arithmetic expressions into Three-Address Code (TAC),
an intermediate representation used in compilers.

Author: Educational Implementation
Purpose: Demonstrate TAC generation from infix expressions
"""

import re
from typing import List, Tuple


class TACGenerator:
    """Generates Three-Address Code from arithmetic expressions."""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize the TAC generator.
        
        Args:
            verbose: If True, print detailed debugging information
        """
        self.verbose = verbose
        self.temp_count = 0
        self.tac_instructions = []
        
    def generate_temp_var(self) -> str:
        """
        Generate a unique temporary variable name.
        
        Returns:
            A string like 't0', 't1', 't2', etc.
        """
        temp_var = f"t{self.temp_count}"
        self.temp_count += 1
        return temp_var
    
    def tokenize(self, expr: str) -> List[str]:
        """
        Tokenize the input expression.
        
        Args:
            expr: Input arithmetic expression
            
        Returns:
            List of tokens (operands, operators, parentheses)
            
        Example:
            tokenize("a + (b * c)") -> ['a', '+', '(', 'b', '*', 'c', ')']
        """
        # Regular expression pattern to match:
        # - Numbers: \d+
        # - Variables: [a-zA-Z]+
        # - Operators and parentheses: [()+\-*/]
        token_pattern = r'\d+|[a-zA-Z_]\w*|[()+\-*/]'
        tokens = re.findall(token_pattern, expr)
        
        if self.verbose:
            print(f"Tokenized '{expr}' -> {tokens}")
        
        return tokens
    
    def precedence(self, op: str) -> int:
        """
        Return the precedence level of an operator.
        
        Args:
            op: Operator character (+, -, *, /)
            
        Returns:
            Integer precedence level (higher = higher precedence)
        """
        precedence_map = {
            '+': 1,
            '-': 1,
            '*': 2,
            '/': 2
        }
        return precedence_map.get(op, 0)
    
    def is_operator(self, token: str) -> bool:
        """Check if a token is an operator."""
        return token in ['+', '-', '*', '/']
    
    def is_operand(self, token: str) -> bool:
        """Check if a token is an operand (number or variable)."""
        return token.isdigit() or token.isalpha() or token.startswith('t')
    
    def parse_to_tac(self, tokens: List[str]) -> List[str]:
        """
        Convert tokens to Three-Address Code using a stack-based algorithm.
        
        This implements a modified shunting-yard algorithm that generates
        TAC instructions as it processes the input.
        
        Args:
            tokens: List of tokens from tokenize()
            
        Returns:
            List of TAC instruction strings
        """
        self.tac_instructions = []
        self.temp_count = 0
        stack = []  # Stack holds operands and operators
        
        if self.verbose:
            print("\n" + "="*60)
            print("PARSING TOKENS TO TAC")
            print("="*60)
        
        for i, token in enumerate(tokens):
            if self.verbose:
                print(f"\n[Step {i+1}] Processing token: '{token}'")
            
            if self.is_operand(token):
                # Operand: push to stack
                stack.append(token)
                if self.verbose:
                    print(f"  Action: Pushed operand to stack")
                    print(f"  Stack: {stack}")
            
            elif token == '(':
                # Left parenthesis: push to stack
                stack.append('(')
                if self.verbose:
                    print(f"  Action: Pushed '(' to stack")
                    print(f"  Stack: {stack}")
            
            elif token == ')':
                # Right parenthesis: process until matching '('
                if self.verbose:
                    print(f"  Action: Processing expression in parentheses")
                    print(f"  Stack before: {stack}")
                
                operands = []
                while stack and stack[-1] != '(':
                    operands.append(stack.pop())
                
                if not stack or stack[-1] != '(':
                    raise SyntaxError(f"Mismatched parentheses at position {i}")
                
                stack.pop()  # Remove '('
                
                # Process the operands we collected
                operands.reverse()  # Restore correct order
                while len(operands) >= 3:
                    arg1 = operands.pop(0)
                    operator = operands.pop(0)
                    arg2 = operands.pop(0)
                    result = self.generate_temp_var()
                    
                    instruction = f"{result} = {arg1} {operator} {arg2}"
                    self.tac_instructions.append(instruction)
                    operands.insert(0, result)
                    
                    if self.verbose:
                        print(f"  Generated: {instruction}")
                
                # Push remaining result back to stack
                if operands:
                    stack.extend(operands)
                
                if self.verbose:
                    print(f"  Stack after: {stack}")
            
            elif self.is_operator(token):
                # Operator: handle precedence
                if self.verbose:
                    print(f"  Action: Processing operator '{token}'")
                    print(f"  Stack before: {stack}")
                
                # Pop operators with higher or equal precedence
                while (len(stack) >= 3 and 
                       self.is_operator(stack[-2]) and
                       self.precedence(stack[-2]) >= self.precedence(token)):
                    
                    arg2 = stack.pop()
                    operator = stack.pop()
                    arg1 = stack.pop()
                    result = self.generate_temp_var()
                    
                    instruction = f"{result} = {arg1} {operator} {arg2}"
                    self.tac_instructions.append(instruction)
                    stack.append(result)
                    
                    if self.verbose:
                        print(f"  Generated: {instruction}")
                        print(f"  Stack now: {stack}")
                
                stack.append(token)
                if self.verbose:
                    print(f"  Pushed operator to stack")
                    print(f"  Stack after: {stack}")
            
            else:
                raise SyntaxError(f"Unknown token: '{token}' at position {i}")
        
        # Process remaining items on stack
        if self.verbose:
            print(f"\n[Final] Processing remaining stack: {stack}")
        
        while len(stack) > 1:
            if len(stack) < 3:
                raise SyntaxError(f"Invalid expression. Remaining stack: {stack}")
            
            arg2 = stack.pop()
            operator = stack.pop()
            arg1 = stack.pop()
            result = self.generate_temp_var()
            
            instruction = f"{result} = {arg1} {operator} {arg2}"
            self.tac_instructions.append(instruction)
            stack.append(result)
            
            if self.verbose:
                print(f"  Generated: {instruction}")
        
        return self.tac_instructions
    
    def generate(self, expr: str) -> List[str]:
        """
        Main entry point: convert expression to TAC.
        
        Args:
            expr: Arithmetic expression string
            
        Returns:
            List of TAC instruction strings
        """
        tokens = self.tokenize(expr)
        tac = self.parse_to_tac(tokens)
        return tac
    
    def print_tac(self):
        """Print the generated TAC instructions in a formatted way."""
        print("\n" + "="*60)
        print("GENERATED THREE-ADDRESS CODE")
        print("="*60)
        for i, instruction in enumerate(self.tac_instructions):
            print(f"{i+1}. {instruction}")
        print("="*60)


def demonstrate_examples():
    """Demonstrate TAC generation with multiple examples."""
    
    examples = [
        "a + (b * c) / 5 - 8",
        "x + y * z",
        "(a + b) * (c - d)",
        "a * b + c * d",
        "((a + b) * c) - d",
    ]
    
    for expr in examples:
        print("\n\n" + "#"*60)
        print(f"# EXAMPLE: {expr}")
        print("#"*60)
        
        generator = TACGenerator(verbose=True)
        generator.generate(expr)
        generator.print_tac()
        
        print("\nPress Enter to continue to next example...")
        input()


def main():
    """Main function with interactive mode."""
    
    print("="*60)
    print("THREE-ADDRESS CODE GENERATOR")
    print("="*60)
    print()
    print("This program converts arithmetic expressions to TAC.")
    print()
    
    # Demo mode
    print("Choose mode:")
    print("1. Run demonstrations")
    print("2. Interactive mode")
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == '1':
        demonstrate_examples()
    else:
        # Interactive mode
        print("\nEnter arithmetic expressions (or 'quit' to exit)")
        print("Examples: a + b * c, (x + y) * z, a + (b * c) / 5 - 8")
        print()
        
        while True:
            expr = input("Expression: ").strip()
            
            if expr.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not expr:
                continue
            
            try:
                generator = TACGenerator(verbose=True)
                generator.generate(expr)
                generator.print_tac()
            except Exception as e:
                print(f"\nError: {e}")
            
            print()


if __name__ == "__main__":
    main()
