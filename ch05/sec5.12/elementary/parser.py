from ast_nodes import *

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    def peek(self, offset=1):
        p = self.pos + offset
        return self.tokens[p] if p < len(self.tokens) else None
    
    def consume(self, expected_kind=None):
        token = self.current()
        if token is None:
            raise SyntaxError(f"Unexpected end of input")
        if expected_kind and token.kind != expected_kind:
            raise SyntaxError(f"Expected {expected_kind}, got {token.kind} at {token.line}:{token.column}")
        self.pos += 1
        return token
    
    def parse(self):
        statements = []
        while self.current():
            statements.append(self.parse_statement())
        return Program(statements)
    
    def parse_statement(self):
        token = self.current()
        
        if token.kind == "LET":
            return self.parse_let()
        elif token.kind == "PRINT":
            return self.parse_print()
        elif token.kind == "INPUT":
            return self.parse_input()
        elif token.kind == "IF":
            return self.parse_if()
        elif token.kind == "WHILE":
            return self.parse_while()
        elif token.kind == "IDENTIFIER":
            return self.parse_assignment()
        else:
            raise SyntaxError(f"Unexpected token {token.kind} at {token.line}:{token.column}")
    
    def parse_let(self):
        self.consume("LET")
        identifier = self.consume("IDENTIFIER").value
        self.consume("ASSIGN")
        expression = self.parse_expression()
        self.consume("SEMICOLON")
        return LetStatement(identifier, expression)
    
    def parse_assignment(self):
        identifier = self.consume("IDENTIFIER").value
        self.consume("ASSIGN")
        expression = self.parse_expression()
        self.consume("SEMICOLON")
        return AssignStatement(identifier, expression)
    
    def parse_print(self):
        self.consume("PRINT")
        self.consume("LPAREN")
        expression = self.parse_expression()
        self.consume("RPAREN")
        self.consume("SEMICOLON")
        return PrintStatement(expression)
    
    def parse_input(self):
        self.consume("INPUT")
        self.consume("LPAREN")
        identifier = self.consume("IDENTIFIER").value
        self.consume("RPAREN")
        self.consume("SEMICOLON")
        return InputStatement(identifier)
    
    def parse_if(self):
        self.consume("IF")
        condition = self.parse_expression()
        then_block = self.parse_block()
        else_block = None
        if self.current() and self.current().kind == "ELSE":
            self.consume("ELSE")
            else_block = self.parse_block()
        return IfStatement(condition, then_block, else_block)
    
    def parse_while(self):
        self.consume("WHILE")
        condition = self.parse_expression()
        body = self.parse_block()
        return WhileStatement(condition, body)
    
    def parse_block(self):
        self.consume("LBRACE")
        statements = []
        while self.current() and self.current().kind != "RBRACE":
            statements.append(self.parse_statement())
        self.consume("RBRACE")
        return Block(statements)
    
    def parse_expression(self):
        return self.parse_comparison()
    
    def parse_comparison(self):
        node = self.parse_additive()
        while self.current() and self.current().kind in ("EQ", "NE", "LT", "GT", "LE", "GE"):
            op = self.consume().kind
            right = self.parse_additive()
            node = BinaryOp(op, node, right)
        return node
    
    def parse_additive(self):
        node = self.parse_multiplicative()
        while self.current() and self.current().kind in ("PLUS", "MINUS"):
            op = self.consume().kind
            right = self.parse_multiplicative()
            node = BinaryOp(op, node, right)
        return node
    
    def parse_multiplicative(self):
        node = self.parse_unary()
        while self.current() and self.current().kind in ("TIMES", "DIVIDE", "MOD"):
            op = self.consume().kind
            right = self.parse_unary()
            node = BinaryOp(op, node, right)
        return node
    
    def parse_unary(self):
        if self.current() and self.current().kind in ("MINUS", "PLUS"):
            op = self.consume().kind
            operand = self.parse_unary()
            return UnaryOp(op, operand)
        return self.parse_primary()
    
    def parse_primary(self):
        token = self.current()
        
        if token.kind == "NUMBER":
            self.consume()
            return NumberLiteral(token.value)
        elif token.kind == "STRING":
            self.consume()
            return StringLiteral(token.value)
        elif token.kind == "IDENTIFIER":
            self.consume()
            return Identifier(token.value)
        elif token.kind == "LPAREN":
            self.consume("LPAREN")
            node = self.parse_expression()
            self.consume("RPAREN")
            return node
        else:
            raise SyntaxError(f"Unexpected token {token.kind} at {token.line}:{token.column}")

if __name__ == "__main__":
    from lexer import tokenize
    
    code = '''
let x = 42;
let name = "Alice";
print("Hello, " + name);
'''
    tokens = tokenize(code)
    parser = Parser(tokens)
    ast = parser.parse()
    print(ast)
