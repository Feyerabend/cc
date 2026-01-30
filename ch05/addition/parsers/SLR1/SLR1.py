
productions = [
    ('', []),        # placeholder
    ('E', ['E', '+', 'T']),
    ('E', ['T']),
    ('T', ['T', '*', 'F']),
    ('T', ['F']),
    ('F', ['(', 'E', ')']),
    ('F', ['num'])
]

action = {
    0: {'num': ('s', 5), '(': ('s', 4)},
    1: {'+': ('s', 6), '$': ('acc',)},
    2: {'+': ('r', 2), '*': ('s', 7), ')': ('r', 2), '$': ('r', 2)},
    3: {'+': ('r', 4), '*': ('r', 4), ')': ('r', 4), '$': ('r', 4)},
    4: {'num': ('s', 5), '(': ('s', 4)},
    5: {'+': ('r', 6), '*': ('r', 6), ')': ('r', 6), '$': ('r', 6)},
    6: {'num': ('s', 5), '(': ('s', 4)},
    7: {'num': ('s', 5), '(': ('s', 4)},
    8: {'+': ('s', 6), ')': ('s', 11)},
    9: {'+': ('r', 1), '*': ('s', 7), ')': ('r', 1), '$': ('r', 1)},
    10: {'+': ('r', 3), '*': ('r', 3), ')': ('r', 3), '$': ('r', 3)},
    11: {'+': ('r', 5), '*': ('r', 5), ')': ('r', 5), '$': ('r', 5)}
}

goto = {
    0: {'E': 1, 'T': 2, 'F': 3},
    4: {'E': 8, 'T': 2, 'F': 3},
    6: {'T': 9, 'F': 3},
    7: {'F': 10}
}


def tokenize(expr):
    tokens = []
    i = 0
    while i < len(expr):
        if expr[i].isdigit():
            num = ''
            while i < len(expr) and expr[i].isdigit():
                num += expr[i]
                i += 1
            tokens.append('num')
        elif expr[i] in '+*()':
            tokens.append(expr[i])
            i += 1
        elif expr[i].isspace():
            i += 1
        else:
            raise ValueError(f"Invalid character {expr[i]}")
    tokens.append('$')
    return tokens


def parse(tokens):
    stack = [0]
    i = 0
    while True:
        state = stack[-1]
        token = tokens[i]
        if token not in action[state]:
            raise SyntaxError(f"Unexpected token {token} at position {i}")
        act = action[state][token]

        if act[0] == 's':  # shift
            stack.append(token)
            stack.append(act[1])
            i += 1
        elif act[0] == 'r':  # reduce
            prod_num = act[1]
            lhs, rhs = productions[prod_num]
            for _ in range(len(rhs) * 2):
                stack.pop()
            state = stack[-1]
            stack.append(lhs)
            stack.append(goto[state][lhs])
        elif act[0] == 'acc':
            print("Parsing successful!")
            return
        else:
            raise SyntaxError("Invalid action")

expr = "3 + 4 * (2 + 5)"
tokens = tokenize(expr)
parse(tokens)
