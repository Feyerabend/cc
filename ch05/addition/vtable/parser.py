from typing import Dict, List, Tuple

class Parser:
    """Parse tokens into Abstract Syntax Tree (AST)."""
    
    def __init__(self, tokens: List[Tuple[str, str]]):
        self.tokens = tokens
        self.pos = 0

    def peek(self, tok_type: str) -> bool:
        return self.pos < len(self.tokens) and self.tokens[self.pos][0] == tok_type

    def consume(self, expected_type: str) -> Tuple[str, str]:
        if self.peek(expected_type):
            token = self.tokens[self.pos]
            self.pos += 1
            return token
        current = self.tokens[self.pos] if self.pos < len(self.tokens) else "EOF"
        raise SyntaxError(f"Expected {expected_type}, got {current[0]}")

    def parse_class(self) -> Dict:
        """Parse a class definition into AST."""
        self.consume('CLASS')
        name = self.consume('ID')[1]
        parent = 'Object'
        
        if self.peek('INHERITS'):
            self.consume('INHERITS')
            parent = self.consume('ID')[1]
        
        self.consume('LBRACE')
        methods = []
        
        while not self.peek('RBRACE'):
            if self.peek('DEF'):
                self.consume('DEF')
                methods.append(self._parse_method())
        
        self.consume('RBRACE')
        
        return {
            'name': name,
            'parent': parent,
            'methods': methods
        }

    def _parse_method(self) -> Dict:
        """Parse a method definition."""
        name = self.consume('ID')[1]
        self.consume('LPAREN')
        self.consume('RPAREN')
        self.consume('LBRACE')
        
        body = []
        while not self.peek('RBRACE'):
            if self.peek('PRINT'):
                self.consume('PRINT')
                body.append(self._parse_print())
        
        self.consume('RBRACE')
        return {'name': name, 'body': body}

    def _parse_print(self) -> Dict:
        """Parse a print statement."""
        self.consume('LPAREN')
        expr = self.consume('STRING')[1]
        self.consume('RPAREN')
        self.consume('SEMI')
        return {'type': 'print', 'value': expr[1:-1]}  # strip quotes

