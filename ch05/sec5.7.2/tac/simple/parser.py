
class ASTNode:
    """Node of an Abstract Syntax Tree."""
    def __init__(self, value, left=None, right=None):
        self.value = value    # Operator or operand
        self.left = left      # Left child (if any)
        self.right = right    # Right child (if any)

class Parser:
    """
    PEG-inspired recursive descent parser
    for simple arithmetic expressions.
    Grammar (in PEG notation approximation):
       Expression <- Term (('+' / '-') Term)*
             Term <- Factor (('*' / '/') Factor)*
           Factor <- Number / '(' Expression ')'
           Number <- [0-9]+
    """
    def __init__(self, expression):
        self.expression = expression.replace(" ", "")  # Classic remove spaces
        self.pos = 0
        self.length = len(self.expression)

    def parse(self):
        """Parse the entire expression."""
        node = self.parse_expression()
        if self.pos != self.length:
            raise ValueError("Extra characters after expression")
        return node

    def parse_expression(self):
        """Expression <- Term (('+' / '-') Term)*"""
        node = self.parse_term()
        while self.pos < self.length and self.expression[self.pos] in ('+', '-'):
            op = self.expression[self.pos]
            self.pos += 1
            right = self.parse_term()
            node = ASTNode(op, node, right)
        return node

    def parse_term(self):
        """Term <- Factor (('*' / '/') Factor)*"""
        node = self.parse_factor()
        while self.pos < self.length and self.expression[self.pos] in ('*', '/'):
            op = self.expression[self.pos]
            self.pos += 1
            right = self.parse_factor()
            node = ASTNode(op, node, right)
        return node

    def parse_factor(self):
        """Factor <- Number / '(' Expression ')'"""
        if self.pos >= self.length:
            raise ValueError("Unexpected end of input")
        char = self.expression[self.pos]
        if char.isdigit():
            return self.parse_number()
        elif char == '(':
            self.pos += 1
            node = self.parse_expression()
            if self.pos < self.length and self.expression[self.pos] == ')':
                self.pos += 1
                return node
            else:
                raise ValueError("Mismatched parentheses")
        else:
            raise ValueError(f"Unexpected character: '{char}'")

    def parse_number(self):
        """Number <- [0-9]+"""
        start = self.pos
        while self.pos < self.length and self.expression[self.pos].isdigit():
            self.pos += 1
        if start == self.pos:
            raise ValueError("Expected number")
        return ASTNode(int(self.expression[start:self.pos]))

def parse_expression(expression):
    """Convenience function to parse an expression string into AST."""
    parser = Parser(expression)
    return parser.parse()
