
class ParseTreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []

    def __repr__(self):
        if not self.children:
            return str(self.value)
        return f"({self.value} {' '.join(map(str, self.children))})"

# generating a full parse tree
def parse_expression_to_tree(tokens):
    def parse_expression(tokens):
        node = ParseTreeNode("Expr")
        term_node = parse_term(tokens)
        node.children.append(term_node)
        while tokens and tokens[0] in ['+', '-']:
            op = tokens.pop(0)
            op_node = ParseTreeNode(op)
            node.children.append(op_node)
            node.children.append(parse_term(tokens))
        return node

    def parse_term(tokens):
        node = ParseTreeNode("Term")
        factor_node = parse_factor(tokens)
        node.children.append(factor_node)
        while tokens and tokens[0] in ['*', '/']:
            op = tokens.pop(0)
            op_node = ParseTreeNode(op)
            node.children.append(op_node)
            node.children.append(parse_factor(tokens))
        return node

    def parse_factor(tokens):
        token = tokens.pop(0)
        if token.isdigit():
            return ParseTreeNode(f"Num({token})")
        elif token == '(':
            expr_node = parse_expression(tokens)
            tokens.pop(0)  # remove closing parenthesis
            return expr_node
        return None

    return parse_expression(tokens)

# example
tokens = "3 + 2 * ( 4 - 1 )".split()
parse_tree = parse_expression_to_tree(tokens)
print("Parse Tree:", parse_tree)
