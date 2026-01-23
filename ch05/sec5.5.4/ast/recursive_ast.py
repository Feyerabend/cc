from dataclasses import dataclass
from typing import List, Optional
import re

@dataclass
class ASTNode:
    pass

@dataclass
class Number(ASTNode):
    value: int

@dataclass
class Variable(ASTNode):
    name: str

@dataclass
class BinOp(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode

@dataclass
class Assignment(ASTNode):
    var: str
    expr: ASTNode

@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    then_branch: List[ASTNode]
    else_branch: Optional[List[ASTNode]] = None

@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode
    body: List[ASTNode]

@dataclass
class Program(ASTNode):
    statements: List[ASTNode]


class RecursiveDescentParser:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.length = len(text)
    
    def skip_whitespace(self):
        while self.pos < self.length and self.text[self.pos].isspace():
            self.pos += 1
    
    def peek(self, s: str) -> bool:
        self.skip_whitespace()
        return self.text[self.pos:self.pos + len(s)] == s
    
    def consume(self, s: str) -> bool:
        if self.peek(s):
            self.pos += len(s)
            self.skip_whitespace()
            return True
        return False
    
    def expect(self, s: str):
        if not self.consume(s):
            raise SyntaxError(f"Expected '{s}' at position {self.pos}")
    
    def parse_number(self) -> Optional[Number]:
        self.skip_whitespace()
        match = re.match(r'\d+', self.text[self.pos:])
        if match:
            value = int(match.group(0))
            self.pos += len(match.group(0))
            self.skip_whitespace()
            return Number(value)
        return None
    
    def parse_identifier(self) -> Optional[str]:
        self.skip_whitespace()
        match = re.match(r'[a-zA-Z_][a-zA-Z0-9_]*', self.text[self.pos:])
        if match:
            name = match.group(0)
            self.pos += len(match.group(0))
            self.skip_whitespace()
            return name
        return None
    
    def parse_primary(self) -> ASTNode:
        # Try number
        num = self.parse_number()
        if num:
            return num
        
        # Try parenthesized expression
        if self.consume('('):
            expr = self.parse_expression()
            self.expect(')')
            return expr
        
        # Try variable
        ident = self.parse_identifier()
        if ident:
            return Variable(ident)
        
        raise SyntaxError(f"Expected primary expression at position {self.pos}")
    
    def parse_term(self) -> ASTNode:
        left = self.parse_primary()
        
        while self.peek('*') or self.peek('/'):
            if self.consume('*'):
                op = '*'
            else:
                self.consume('/')
                op = '/'
            right = self.parse_primary()
            left = BinOp(op, left, right)
        
        return left
    
    def parse_arithmetic(self) -> ASTNode:
        left = self.parse_term()
        
        while self.peek('+') or (self.peek('-') and not self.peek('->')):
            if self.consume('+'):
                op = '+'
            else:
                self.consume('-')
                op = '-'
            right = self.parse_term()
            left = BinOp(op, left, right)
        
        return left
    
    def parse_expression(self) -> ASTNode:
        left = self.parse_arithmetic()
        
        # Comparison operators
        cmp_ops = ['==', '!=', '<=', '>=', '<', '>']
        for op in cmp_ops:
            if self.peek(op):
                self.consume(op)
                right = self.parse_arithmetic()
                return BinOp(op, left, right)
        
        return left
    
    def parse_assignment(self) -> Optional[Assignment]:
        saved_pos = self.pos
        ident = self.parse_identifier()
        
        if ident and self.consume('='):
            expr = self.parse_expression()
            self.expect(';')
            return Assignment(ident, expr)
        
        # Not an assignment, restore position
        self.pos = saved_pos
        return None
    
    def parse_if_statement(self) -> Optional[IfStmt]:
        if not self.consume('if'):
            return None
        
        self.expect('(')
        condition = self.parse_expression()
        self.expect(')')
        self.expect('{')
        then_branch = []
        while not self.peek('}'):
            stmt = self.parse_statement()
            if stmt:
                then_branch.append(stmt)
        self.expect('}')
        
        else_branch = None
        if self.consume('else'):
            self.expect('{')
            else_branch = []
            while not self.peek('}'):
                stmt = self.parse_statement()
                if stmt:
                    else_branch.append(stmt)
            self.expect('}')
        
        return IfStmt(condition, then_branch, else_branch)
    
    def parse_while_statement(self) -> Optional[WhileStmt]:
        if not self.consume('while'):
            return None
        
        self.expect('(')
        condition = self.parse_expression()
        self.expect(')')
        self.expect('{')
        body = []
        while not self.peek('}'):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
        self.expect('}')
        
        return WhileStmt(condition, body)
    
    def parse_statement(self) -> Optional[ASTNode]:
        # Try if statement
        if_stmt = self.parse_if_statement()
        if if_stmt:
            return if_stmt
        
        # Try while statement
        while_stmt = self.parse_while_statement()
        if while_stmt:
            return while_stmt
        
        # Try assignment
        assignment = self.parse_assignment()
        if assignment:
            return assignment
        
        return None
    
    def parse_program(self) -> Program:
        self.skip_whitespace()
        statements = []
        
        while self.pos < self.length:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            else:
                break
        
        return Program(statements)


if __name__ == "__main__":
    code = """
        x = 10;
        y = 20;
        if (x < y) {
            z = x + y;
            unused = 42;
        } else {
            z = x - y;
        }
        result = z * 2;
        dead = 99;
    """
    
    parser = RecursiveDescentParser(code)
    ast = parser.parse_program()
    
    print("Parsed successfully!")
    print("\nAST:")
    import json
    
    def ast_to_dict(node):
        if isinstance(node, list):
            return [ast_to_dict(n) for n in node]
        elif isinstance(node, ASTNode):
            d = {'type': node.__class__.__name__}
            for k, v in node.__dict__.items():
                d[k] = ast_to_dict(v)
            return d
        else:
            return node
    
    print(json.dumps(ast_to_dict(ast), indent=2))
