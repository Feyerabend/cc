import re

class LL1Parser:
    def __init__(self, input):
        self.tokens = self.tokenize(input)
        self.tokens.append('$')  # end-of-input marker
        self.pos = 0
        self.stack = ['$', 'E']  # parsing stack starts with $ and the start symbol

        # parsing table
        self.table = {
            'E': {
                'num': ['T', 'E\''],
                '(': ['T', 'E\'']
            },
            'E\'': {
                '+': ['+', 'T', 'E\''],
                '-': ['-', 'T', 'E\''],
                ')': [],
                '$': []
            },
            'T': {
                'num': ['F', 'T\''],
                '(': ['F', 'T\'']
            },
            'T\'': {
                '+': [],
                '-': [],
                '*': ['*', 'F', 'T\''],
                '/': ['/', 'F', 'T\''],
                '%': ['%', 'F', 'T\''],
                ')': [],
                '$': []
            },
            'F': {
                'num': ['num'],
                '(': ['(', 'E', ')']
            }
        }

    def tokenize(self, input):
        token_pattern = r'\d+\.\d+|\d+|[+\-*/%^()]'
        tokens = re.findall(token_pattern, input)
        print(f"Tokens: {tokens}")
        return tokens

    def lookahead(self): # one item look ahead
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def parse(self):
        while self.stack:
            top = self.stack.pop()
            token = self.lookahead()

            if top in self.table:  # non-terminal
                if token in self.table[top]:
                    production = self.table[top][token]
                    print(f"Applying production {top} → {' '.join(production)}")
                    self.stack.extend(reversed(production))  # push production onto stack
                else:
                    raise Exception(f"Error: Unexpected token {token} for {top}")

            elif top == token:  # terminal matches input
                print(f"Consuming: {token}")
                self.pos += 1

            elif top == 'num' and self.is_number(token):  # match number
                print(f"Consuming number: {token}")
                self.pos += 1

            else:
                raise Exception(f"Error: Unexpected token {token}. Expected {top}")

        if self.lookahead() == '$': # end parsing
            print("Input parsed successfully!")
        else:
            raise Exception(f"Error: Unexpected input at end. Found {self.lookahead()}")

    def is_number(self, token):
        """Check if the token is a valid number (integer or floating-point)."""
        return re.match(r'^\d+(\.\d+)?$', token)



input_string = "3 + 2 * 4"
parser = LL1Parser(input_string)
parser.parse()

input_string2 = "3.14 * ( 2 + 5.6 )"
parser2 = LL1Parser(input_string2)
parser2.parse()

input_string3 = "5 + 3.5 ^ 2"
parser3 = LL1Parser(input_string3)
parser3.parse()

input_string4 = "2 * (3 + 2.5)"
parser4 = LL1Parser(input_string4)
parser4.parse()

input_string5 = "1.5 + 2.5 * 3"
parser5 = LL1Parser(input_string5)
parser5.parse()