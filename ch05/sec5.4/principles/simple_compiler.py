"""
Simple Arithmetic Compiler
Demonstrates all 7 compiler phases for arithmetic expressions
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any


# 1. LEXICAL ANALYSIS (Tokenisation)

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


# 3. SEMANTIC ANALYSIS

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table: Dict[str, str] = {}
    
    def analyze(self, ast: List[ASTNode]):
        for node in ast:
            self.check_node(node)
    
    def check_node(self, node: ASTNode):
        if isinstance(node, AssignmentNode):
            # Register variable in symbol table
            self.symbol_table[node.variable] = "int"
            self.check_node(node.expression)
        elif isinstance(node, BinaryOpNode):
            self.check_node(node.left)
            self.check_node(node.right)
        elif isinstance(node, VariableNode):
            # Check if variable is defined
            if node.name not in self.symbol_table:
                raise Exception(f"Undefined variable: {node.name}")
        elif isinstance(node, NumberNode):
            pass  # Numbers are always valid


# 4. INTERMEDIATE CODE GENERATION

@dataclass
class IRInstruction:
    op: str
    arg1: Any = None
    arg2: Any = None
    result: str = None

class IRGenerator:
    def __init__(self):
        self.instructions: List[IRInstruction] = []
        self.temp_counter = 0
    
    def new_temp(self) -> str:
        temp = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp
    
    def generate(self, ast: List[ASTNode]) -> List[IRInstruction]:
        for node in ast:
            self.gen_node(node)
        return self.instructions
    
    def gen_node(self, node: ASTNode) -> str:
        if isinstance(node, NumberNode):
            temp = self.new_temp()
            self.instructions.append(IRInstruction("LOAD_CONST", node.value, None, temp))
            return temp
        elif isinstance(node, VariableNode):
            temp = self.new_temp()
            self.instructions.append(IRInstruction("LOAD_VAR", node.name, None, temp))
            return temp
        elif isinstance(node, BinaryOpNode):
            left = self.gen_node(node.left)
            right = self.gen_node(node.right)
            temp = self.new_temp()
            op_map = {'+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV'}
            self.instructions.append(IRInstruction(op_map[node.op], left, right, temp))
            return temp
        elif isinstance(node, AssignmentNode):
            expr_result = self.gen_node(node.expression)
            self.instructions.append(IRInstruction("STORE", expr_result, None, node.variable))
            return expr_result


# 5. OPTIMISATION

class Optimizer:
    def optimize(self, ir: List[IRInstruction]) -> List[IRInstruction]:
        # Constant folding: evaluate operations on constants at compile time
        optimized = []
        temp_values = {}
        
        for instr in ir:
            if instr.op == "LOAD_CONST":
                temp_values[instr.result] = instr.arg1
                optimized.append(instr)
            elif instr.op in ['ADD', 'SUB', 'MUL', 'DIV']:
                # Check if both operands are constants
                if instr.arg1 in temp_values and instr.arg2 in temp_values:
                    val1 = temp_values[instr.arg1]
                    val2 = temp_values[instr.arg2]
                    if instr.op == 'ADD':
                        result = val1 + val2
                    elif instr.op == 'SUB':
                        result = val1 - val2
                    elif instr.op == 'MUL':
                        result = val1 * val2
                    elif instr.op == 'DIV':
                        result = val1 // val2
                    
                    # Replace with constant load
                    temp_values[instr.result] = result
                    optimized.append(IRInstruction("LOAD_CONST", result, None, instr.result))
                else:
                    optimized.append(instr)
            else:
                optimized.append(instr)
        
        return optimized


# 6. CODE GENERATION

class CodeGenerator:
    def generate(self, ir: List[IRInstruction]) -> str:
        """Generate executable Python code"""
        lines = []
        lines.append("# Generated code")
        
        for instr in ir:
            if instr.op == "LOAD_CONST":
                lines.append(f"{instr.result} = {instr.arg1}")
            elif instr.op == "LOAD_VAR":
                lines.append(f"{instr.result} = {instr.arg1}")
            elif instr.op == "ADD":
                lines.append(f"{instr.result} = {instr.arg1} + {instr.arg2}")
            elif instr.op == "SUB":
                lines.append(f"{instr.result} = {instr.arg1} - {instr.arg2}")
            elif instr.op == "MUL":
                lines.append(f"{instr.result} = {instr.arg1} * {instr.arg2}")
            elif instr.op == "DIV":
                lines.append(f"{instr.result} = {instr.arg1} // {instr.arg2}")
            elif instr.op == "STORE":
                lines.append(f"{instr.result} = {instr.arg1}")
        
        return "\n".join(lines)


# 7. LINKING (Simplified - just execute the code; see section 5.9)

class Linker:
    def link_and_execute(self, code: str, context: Dict = None) -> Dict:
        """Execute the generated code and return the variables"""
        if context is None:
            context = {}
        exec(code, context)
        return context


# MAIN COMPILER

class Compiler:
    def compile_and_run(self, source_code: str):
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
        print(f"  Symbol table: {analyzer.symbol_table}")
        print("  ✓ No semantic errors")
        print()
        
        # 4. Intermediate Code Generation
        print("4. INTERMEDIATE CODE GENERATION:")
        ir_gen = IRGenerator()
        ir = ir_gen.generate(ast)
        for instr in ir:
            print(f"  {instr}")
        print()
        
        # 5. Optimisation
        print("5. OPTIMISATION:")
        optimizer = Optimizer()
        optimized_ir = optimizer.optimize(ir)
        for instr in optimized_ir:
            print(f"  {instr}")
        print()
        
        # 6. Code Generation
        print("6. CODE GENERATION:")
        code_gen = CodeGenerator()
        generated_code = code_gen.generate(optimized_ir)
        print(generated_code)
        print()
        
        # 7. Linking and Execution
        print("7. LINKING & EXECUTION:")
        linker = Linker()
        result = linker.link_and_execute(generated_code)
        print("  Variables after execution:")
        for var, value in result.items():
            if not var.startswith('__') and not var.startswith('t'):
                print(f"    {var} = {value}")
        print()



# DEMO

if __name__ == "__main__":
    compiler = Compiler()
    
    # Example 1: Simple arithmetic
    compiler.compile_and_run("x = 5 + 3 * 2;")
    
    # Example 2: More complex with optimisation opportunity
    compiler.compile_and_run("result = 10 + 20 * 2 - 5;")
    
    # Example 3: With parentheses
    compiler.compile_and_run("y = (10 + 5) * 3;")
