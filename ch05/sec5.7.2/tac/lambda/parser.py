# parser.py
# Parser for lambda calculus expressions using recursive descent.

class ASTNode:
    """Base class for AST nodes in lambda calculus."""
    pass

class Var(ASTNode):
    """Variable node."""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Var('{self.name}')"

class Lam(ASTNode):
    """Lambda abstraction node."""
    def __init__(self, param, body):
        self.param = param
        self.body = body

    def __repr__(self):
        return f"Lam('{self.param}', {self.body})"

class App(ASTNode):
    """Application node."""
    def __init__(self, func, arg):
        self.func = func
        self.arg = arg

    def __repr__(self):
        return f"App({self.func}, {self.arg})"

class Parser:
    """
    Recursive descent parser for lambda calculus.
    Grammar:
    expr   <- lam / app_expr
    lam    <- ('λ' | '\\') var '.' expr
    app_expr <- atom (atom)*          # Left-associative application
    atom   <- var / '(' expr ')'
    var    <- [a-z]+
    """
    def __init__(self, expression):
        self.expression = expression  # Keep spaces for now
        self.pos = 0
        self.length = len(self.expression)
        self._skip_whitespace()

    def _skip_whitespace(self):
        """Skip whitespace characters."""
        while self.pos < self.length and self.expression[self.pos].isspace():
            self.pos += 1

    def peek(self):
        """Peek at current character without consuming."""
        if self.pos < self.length:
            return self.expression[self.pos]
        return None

    def consume(self, char=None):
        """Consume current character, optionally checking it matches."""
        if self.pos >= self.length:
            raise ValueError("Unexpected end of input")
        current = self.expression[self.pos]
        if char and current != char:
            raise ValueError(f"Expected '{char}', got '{current}'")
        self.pos += 1
        self._skip_whitespace()
        return current

    def parse(self):
        """Parse the entire expression."""
        node = self.parse_expr()
        if self.pos != self.length:
            raise ValueError(f"Extra characters after expression: {self.expression[self.pos:]}")
        return node

    def parse_expr(self):
        """Parse expression: lambda or application sequence."""
        char = self.peek()
        if char in ('λ', '\\'):
            return self.parse_lam()
        else:
            return self.parse_app_expr()

    def parse_app_expr(self):
        """Parse application expression: left-associative sequence of atoms."""
        node = self.parse_atom()
        while self.pos < self.length and self.peek() not in (')', None):
            # Check if we're about to hit a closing paren
            if self.peek() == ')':
                break
            arg = self.parse_atom()
            node = App(node, arg)
        return node

    def parse_atom(self):
        """Parse atomic expression: variable or parenthesized expression."""
        char = self.peek()
        if char is None:
            raise ValueError("Unexpected end of input")
        
        if char == '(':
            self.consume('(')
            node = self.parse_expr()
            self.consume(')')
            return node
        elif char.isalpha():
            return self.parse_var()
        else:
            raise ValueError(f"Unexpected character: '{char}'")

    def parse_lam(self):
        """Parse lambda: ('λ' | '\\') var '.' expr"""
        char = self.peek()
        if char == '\\':
            self.consume('\\')
        elif char == 'λ':
            self.consume('λ')
        else:
            raise ValueError(f"Expected lambda, got '{char}'")
        
        param = self.parse_var().name
        self.consume('.')
        body = self.parse_expr()
        return Lam(param, body)

    def parse_var(self):
        """Parse variable: [a-z]+"""
        start = self.pos
        while self.pos < self.length and self.expression[self.pos].isalpha():
            self.pos += 1
        if start == self.pos:
            raise ValueError("Expected variable name")
        var = Var(self.expression[start:self.pos])
        self._skip_whitespace()
        return var

def parse_lambda(expression):
    """Convenience function to parse lambda expression to AST."""
    parser = Parser(expression)
    return parser.parse()

def print_ast(node, level=0):
    """Print AST with indentation."""
    indent = "  " * level
    if isinstance(node, Var):
        print(f"{indent}Var: {node.name}")
    elif isinstance(node, Lam):
        print(f"{indent}Lam: param={node.param}")
        print_ast(node.body, level + 1)
    elif isinstance(node, App):
        print(f"{indent}App:")
        print_ast(node.func, level + 1)
        print_ast(node.arg, level + 1)
