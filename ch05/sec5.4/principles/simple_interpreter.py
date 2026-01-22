"""
Simple Arithmetic Interpreter
Demonstrates interpreter phases for arithmetic expressions
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any


# 1. LEXICAL ANALYSIS (Tokenisation)
# Note: This is identical to the compiler version

class TokenType(Enum):
    NUMBER = "NUMBER"
    IDENTIFIER = "IDENTIFIER"
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    ASSIGN = "ASSIGN"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    SEMICOLON = "SEMICOLON"
    EOF = "EOF"

@dataclass
class Token:
    type: TokenType
    value: Any
    position: int

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
    
    def tokenize(self) -> List[Token]:
        tokens = []
        while self.pos < len(self.text):
            if self.text[self.pos].isspace():
                self.pos += 1
                continue
            
            if self.text[self.pos].isdigit():
                tokens.append(self.read_number())
            elif self.text[self.pos].isalpha():
                tokens.append(self.read_identifier())
            elif self.text[self.pos] == '+':
                tokens.append(Token(TokenType.PLUS, '+', self.pos))
                self.pos += 1
            elif self.text[self.pos] == '-':
                tokens.append(Token(TokenType.MINUS, '-', self.pos))
                self.pos += 1
            elif self.text[self.pos] == '*':
                tokens.append(Token(TokenType.MULTIPLY, '*', self.pos))
                self.pos += 1
            elif self.text[self.pos] == '/':
                tokens.append(Token(TokenType.DIVIDE, '/', self.pos))
                self.pos += 1
            elif self.text[self.pos] == '=':
                tokens.append(Token(TokenType.ASSIGN, '=', self.pos))
                self.pos += 1
            elif self.text[self.pos] == '(':
                tokens.append(Token(TokenType.LPAREN, '(', self.pos))
                self.pos += 1
            elif self.text[self.pos] == ')':
                tokens.append(Token(TokenType.RPAREN, ')', self.pos))
                self.pos += 1
            elif self.text[self.pos] == ';':
                tokens.append(Token(TokenType.SEMICOLON, ';', self.pos))
                self.pos += 1
            else:
                raise Exception(f"Unknown character: {self.text[self.pos]}")
        
        tokens.append(Token(TokenType.EOF, None, self.pos))
        return tokens
    
    def read_number(self) -> Token:
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1
        return Token(TokenType.NUMBER, int(self.text[start:self.pos]), start)
    
    def read_identifier(self) -> Token:
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos].isalnum():
            self.pos += 1
        return Token(TokenType.IDENTIFIER, self.text[start:self.pos], start)


# 2. SYNTAX ANALYSIS (Parsing - builds AST)
# Note: This is also identical to the compiler version

@dataclass
class ASTNode:
    pass

@dataclass
class NumberNode(ASTNode):
    value: int

@dataclass
class VariableNode(ASTNode):
    name: str

@dataclass
class BinaryOpNode(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode

@dataclass
class AssignmentNode(ASTNode):
    variable: str
    expression: ASTNode

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def parse(self) -> List[ASTNode]:
        statements = []
        while self.current().type != TokenType.EOF:
            statements.append(self.parse_statement())
        return statements
    
    def current(self) -> Token:
        return self.tokens[self.pos]
    
    def consume(self, expected_type: TokenType) -> Token:
        token = self.current()
        if token.type != expected_type:
            raise Exception(f"Expected {expected_type}, got {token.type}")
        self.pos += 1
        return token
    
    def parse_statement(self) -> ASTNode:
        # Check for assignment: identifier = expression;
        if self.current().type == TokenType.IDENTIFIER:
            name = self.current().value
            self.pos += 1
            self.consume(TokenType.ASSIGN)
            expr = self.parse_expression()
            self.consume(TokenType.SEMICOLON)
            return AssignmentNode(name, expr)
        raise Exception("Expected assignment statement")
    
    def parse_expression(self) -> ASTNode:
        return self.parse_additive()
    
    def parse_additive(self) -> ASTNode:
        left = self.parse_multiplicative()
        while self.current().type in [TokenType.PLUS, TokenType.MINUS]:
            op = self.current().value
            self.pos += 1
            right = self.parse_multiplicative()
            left = BinaryOpNode(left, op, right)
        return left
    
    def parse_multiplicative(self) -> ASTNode:
        left = self.parse_primary()
        while self.current().type in [TokenType.MULTIPLY, TokenType.DIVIDE]:
            op = self.current().value
            self.pos += 1
            right = self.parse_primary()
            left = BinaryOpNode(left, op, right)
        return left
    
    def parse_primary(self) -> ASTNode:
        token = self.current()
        if token.type == TokenType.NUMBER:
            self.pos += 1
            return NumberNode(token.value)
        elif token.type == TokenType.IDENTIFIER:
            self.pos += 1
            return VariableNode(token.value)
        elif token.type == TokenType.LPAREN:
            self.pos += 1
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN)
            return expr
        raise Exception(f"Unexpected token: {token.type}")


# 3. SEMANTIC ANALYSIS (Simplified for interpreter)
# Note: Many interpreters do minimal upfront semantic checking,
# instead checking during execution

class SemanticAnalyzer:
    def __init__(self):
        self.variables_assigned: set = set()
    
    def analyze(self, ast: List[ASTNode]):
        """Lightweight semantic checking"""
        for node in ast:
            self.check_node(node)
    
    def check_node(self, node: ASTNode):
        if isinstance(node, AssignmentNode):
            # Track that this variable will be assigned
            self.variables_assigned.add(node.variable)
            self.check_node(node.expression)
        elif isinstance(node, BinaryOpNode):
            self.check_node(node.left)
            self.check_node(node.right)
        elif isinstance(node, VariableNode):
            # In a real interpreter, we might skip this check
            # and let it fail at runtime if undefined
            if node.name not in self.variables_assigned:
                raise Exception(f"Variable '{node.name}' used before assignment")
        elif isinstance(node, NumberNode):
            pass


# 4. DIRECT EXECUTION (This is where interpreters differ)
# Instead of generating intermediate code, we execute the AST directly

class Interpreter:
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.execution_trace: List[str] = []
    
    def interpret(self, ast: List[ASTNode]) -> Dict[str, Any]:
        """Execute the AST directly and return final variable state"""
        for statement in ast:
            self.execute_statement(statement)
        return self.variables
    
    def execute_statement(self, node: ASTNode):
        """Execute a statement node"""
        if isinstance(node, AssignmentNode):
            value = self.evaluate_expression(node.expression)
            self.variables[node.variable] = value
            self.execution_trace.append(f"Assigned {node.variable} = {value}")
    
    def evaluate_expression(self, node: ASTNode) -> Any:
        """Evaluate an expression node and return its value"""
        if isinstance(node, NumberNode):
            self.execution_trace.append(f"  Evaluate number: {node.value}")
            return node.value
        
        elif isinstance(node, VariableNode):
            if node.name not in self.variables:
                raise Exception(f"Undefined variable: {node.name}")
            value = self.variables[node.name]
            self.execution_trace.append(f"  Load variable {node.name}: {value}")
            return value
        
        elif isinstance(node, BinaryOpNode):
            # Recursively evaluate left and right sides
            left_val = self.evaluate_expression(node.left)
            right_val = self.evaluate_expression(node.right)
            
            # Perform the operation
            if node.op == '+':
                result = left_val + right_val
                self.execution_trace.append(f"  Compute {left_val} + {right_val} = {result}")
            elif node.op == '-':
                result = left_val - right_val
                self.execution_trace.append(f"  Compute {left_val} - {right_val} = {result}")
            elif node.op == '*':
                result = left_val * right_val
                self.execution_trace.append(f"  Compute {left_val} * {right_val} = {result}")
            elif node.op == '/':
                result = left_val // right_val
                self.execution_trace.append(f"  Compute {left_val} / {right_val} = {result}")
            else:
                raise Exception(f"Unknown operator: {node.op}")
            
            return result
        
        raise Exception(f"Unknown expression node: {type(node)}")


# MAIN INTERPRETER

class SimpleInterpreter:
    def interpret_and_run(self, source_code: str):
        print("=" * 60)
        print("SOURCE CODE:")
        print(source_code)
        print()
        
        # 1. Lexical Analysis
        print("1. LEXICAL ANALYSIS (Tokens):")
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        for token in tokens:
            print(f"  {token}")
        print()
        
        # 2. Syntax Analysis
        print("2. SYNTAX ANALYSIS (AST):")
        parser = Parser(tokens)
        ast = parser.parse()
        for node in ast:
            print(f"  {node}")
        print()
        
        # 3. Semantic Analysis
        print("3. SEMANTIC ANALYSIS:")
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        print(f"  Variables to be assigned: {analyzer.variables_assigned}")
        print("  ✓ No semantic errors")
        print()
        
        # 4. Direct Execution (THE KEY DIFFERENCE!)
        print("4. DIRECT EXECUTION:")
        print("  Walking the AST and executing immediately..")
        interpreter = Interpreter()
        result = interpreter.interpret(ast)
        
        print()
        print("  Execution trace:")
        for trace in interpreter.execution_trace:
            print(f"    {trace}")
        
        print()
        print("  Final variable values:")
        for var, value in result.items():
            print(f"    {var} = {value}")
        print()
        
        return result


# EXAMPLES

if __name__ == "__main__":
    interpreter = SimpleInterpreter()
    
    print("INTERPRETER DEMO")
    print("Note: The interpreter executes code DIRECTLY from the AST")
    print("No intermediate code, no optimisation, no code generation!")
    print()
    
    # Example 1: Simple arithmetic
    interpreter.interpret_and_run("x = 5 + 3 * 2;")
    
    # Example 2: More complex expression
    interpreter.interpret_and_run("result = 10 + 20 * 2 - 5;")
    
    # Example 3: With parentheses
    interpreter.interpret_and_run("y = (10 + 5) * 3;")
