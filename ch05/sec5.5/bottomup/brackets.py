import re

TOKEN_TYPES = [
    ('LBRACKET', r'\['),   # left bracket
    ('RBRACKET', r'\]'),   # right bracket
    ('VALUE', r'"[^"]*"'), # quoted value
    ('WHITESPACE', r'\s+'),
]

def tokenize(input_string):
    tokens = []
    position = 0
    while position < len(input_string):
        match = None
        for token_type, regex in TOKEN_TYPES:
            pattern = re.compile(regex)
            match = pattern.match(input_string, position)
            if match:
                value = match.group(0)
                if token_type != 'WHITESPACE':  # skip
                    tokens.append((token_type, value))
                position = match.end()
                break
        if not match:
            raise ValueError(f'Invalid character at position {position}')
    return tokens

# Bottom-Up Parser
class ShiftReduceParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.stack = []
        self.index = 0
        self.parse_tree = []

    def shift(self):
        token = self.tokens[self.index]
        self.stack.append(token)
        self.index += 1
        print(f"Shift: {token} -> Stack: {self.stack}")

    def reduce(self):
        print(f"Stack before reduce: {self.stack}")
        # Rule 1: E -> [ E ]
        if len(self.stack) >= 3 and self.stack[-3][0] == 'LBRACKET' and self.stack[-2][0] == 'E' and self.stack[-1][0] == 'RBRACKET':
            rhs = [self.stack.pop(), self.stack.pop(), self.stack.pop()]  # pop RBRACKET, E, LBRACKET
            lhs = ('E', rhs)
            self.stack.append(lhs)
            self.parse_tree.append(lhs)
            print(f"Reduced to E --> [ E ]: {lhs}")
            return True

        # Rule 2: E -> E E
        elif len(self.stack) >= 2 and self.stack[-2][0] == 'E' and self.stack[-1][0] == 'E':
            rhs = [self.stack.pop(), self.stack.pop()]  # pop E and E
            lhs = ('E', rhs)
            self.stack.append(lhs)
            self.parse_tree.append(lhs)
            print(f"Reduced to E --> E E: {lhs}")
            return True

        # Rule 3: E -> "value"
        elif len(self.stack) >= 1 and self.stack[-1][0] == 'VALUE':
            rhs = [self.stack.pop()]  # pop VALUE
            lhs = ('E', rhs)
            self.stack.append(lhs)
            self.parse_tree.append(lhs)
            print(f"Reduced to E --> VALUE: {lhs}")
            return True

        return False

    def parse(self):
        while self.index < len(self.tokens) or len(self.stack) > 1:
            if self.index < len(self.tokens):
                self.shift()

            reduced = False
            while self.reduce():
                reduced = True

            if not reduced and self.index >= len(self.tokens):
                break

        if len(self.stack) == 1 and isinstance(self.stack[0], tuple) and self.stack[0][0] == 'E':
            return self.parse_tree
        else:
            raise ValueError("Parsing failed: Invalid input or incomplete grammar")

# example
input_string = '[ "value" [ "value" "value" ] ]'
tokens = tokenize(input_string)

print("Tokens:")
for token in tokens:
    print(token)

parser = ShiftReduceParser(tokens)
parse_tree = parser.parse()

print("\nParse Tree:")
for node in parse_tree:
    print(node)
