
class ASTNode:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

    def __repr__(self):
        if not self.left and not self.right:
            return str(self.value)
        return f"({self.value} {self.left} {self.right})"

# generating an abstract syntax tree (AST)
def parse_expression_to_ast(tokens):
    def parse_expression(tokens):
        node = parse_term(tokens)
        while tokens and tokens[0] in ['+', '-']:
            op = tokens.pop(0)
            node = ASTNode(op, left=node, right=parse_term(tokens))
        return node

    def parse_term(tokens):
        node = parse_factor(tokens)
        while tokens and tokens[0] in ['*', '/']:
            op = tokens.pop(0)
            node = ASTNode(op, left=node, right=parse_factor(tokens))
        return node

    def parse_factor(tokens):
        token = tokens.pop(0)
        if token.isdigit():
            return ASTNode(int(token))
        elif token == '(':
            node = parse_expression(tokens)
            tokens.pop(0)  # remove closing parenthesis
            return node
        return None

    return parse_expression(tokens)

# example
tokens = "3 + 2 * ( 4 - 1 )".split()
ast = parse_expression_to_ast(tokens)
print("AST:", ast)
