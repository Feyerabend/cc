
class PrecendenceParser:
    def __init__(self):
        # precedence table
        # lower number = lower precedence
        self.operators = {
            '+': 1,
            '-': 1,
            '*': 2,
            '/': 2
        }

    def is_operator(self, token):
        return token in self.operators

    def precedence(self, operator):
        return self.operators.get(operator, -1)  # -1 for non-operators

    def parse(self, tokens):
        stack = []
        operators = []

        def reduce():
            operator = operators.pop()
            right = stack.pop()
            left = stack.pop()
            return (operator, left, right)

        for token in tokens:
            if token.isdigit():
                stack.append(int(token)) # integers only
            elif self.is_operator(token):
                while (operators and self.precedence(operators[-1]) >= self.precedence(token)):
                    stack.append(reduce()) # reductions while precendece cond met
                operators.append(token)  # push current op
            elif token == '(':
                operators.append(token)  # push opening parenthesis
            elif token == ')':
                # reduce until matching '('
                while operators and operators[-1] != '(':
                    stack.append(reduce())
                operators.pop()  # pop '('

        # remaining reductions
        while operators:
            stack.append(reduce())

        # final item on the stack is the parse tree!
        return stack[0]

    def evaluate(self, tree):
        if isinstance(tree, int):  # leaf node (operand)
            return tree
        operator, left, right = tree
        left_val = self.evaluate(left)
        right_val = self.evaluate(right)
        if operator == '+':
            return left_val + right_val
        elif operator == '-':
            return left_val - right_val
        elif operator == '*':
            return left_val * right_val
        elif operator == '/':
            return left_val / right_val

    def to_postfix(self, tree):
        if isinstance(tree, int):
            return str(tree)
        operator, left, right = tree
        return f"{self.to_postfix(left)} {self.to_postfix(right)} {operator}"

    def to_prefix(self, tree):
        if isinstance(tree, int):
            return str(tree)
        operator, left, right = tree
        return f"{operator} {self.to_prefix(left)} {self.to_prefix(right)}"


# example
parser = PrecendenceParser()

infix = "3 + 5 * ( 2 - 8 ) / 4"
tokens = infix.split()  # simple tokenize input

parse_tree = parser.parse(tokens)

result = parser.evaluate(parse_tree)
postfix = parser.to_postfix(parse_tree)
prefix = parser.to_prefix(parse_tree)

print("Infix:   ", infix)
print("Parse Tree:", parse_tree)
print("Postfix: ", postfix)
print("Prefix:  ", prefix)
print("Result:  ", result)
