import re

class PackratParser:
    def __init__(self, input_string):
        self.input = input_string
        self.position = 0
        self.memo = {}  # memoization table: (rule, position) -> result

    def parse(self):
        result = self.expr()
        self.skip_whitespace()  # no trailing input
        if self.position != len(self.input):
            raise SyntaxError(f"Unexpected input at position {self.position}")
        return result

    # decorator: memoization
    def memoize(func):
        def wrapper(self, *args):
            key = (func.__name__, self.position)
            if key in self.memo:
                return self.memo[key]
            result = func(self, *args)
            self.memo[key] = result
            return result
        return wrapper

    def skip_whitespace(self):
        while self.position < len(self.input) and self.input[self.position].isspace():
            self.position += 1

    def consume(self, pattern):
        self.skip_whitespace()
        match = re.match(pattern, self.input[self.position:])
        if match:
            value = match.group(0)
            self.position += len(value)
            return value
        return None

    @memoize
    def expr(self):
        """Expr <- Term (('+' | '-') Term)*"""
        node = self.term()
        while True:
            if self.consume(r'\+'):
                node = ('+', node, self.term())
            elif self.consume(r'-'):
                node = ('-', node, self.term())
            else:
                break
        return node

    @memoize
    def term(self):
        """Term <- Factor (('*' | '/') Factor)*"""
        node = self.factor()
        while True:
            if self.consume(r'\*'):
                node = ('*', node, self.factor())
            elif self.consume(r'/'):
                node = ('/', node, self.factor())
            else:
                break
        return node

    @memoize
    def factor(self):
        """Factor <- Number | '(' Expr ')'"""
        number = self.consume(r'\d+')
        if number:
            return int(number)
        if self.consume(r'\('):
            node = self.expr()
            if not self.consume(r'\)'):
                raise SyntaxError("Expected ')'")
            return node
        raise SyntaxError("Expected a number or '(' expression ')'")


if __name__ == "__main__":
    expression = "3 + 4 * (2 - 1)"
    parser = PackratParser(expression)
    try:
        ast = parser.parse()
        print("Parsed AST:", ast)
    except SyntaxError as e:
        print("Syntax error:", e)
