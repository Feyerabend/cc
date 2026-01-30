from collections import defaultdict

# Grammar
productions = [
    ("S'", ["E"]),        # Augmented start
    ("E", ["E", "+", "T"]),
    ("E", ["T"]),
    ("T", ["T", "*", "F"]),
    ("T", ["F"]),
    ("F", ["(", "E", ")"]),
    ("F", ["num"])
]

terminals = ["num", "+", "*", "(", ")", "$"]
nonterminals = ["S'", "E", "T", "F"]

# FIRST sets
def compute_first():
    first = defaultdict(set)
    for t in terminals:
        first[t].add(t)
    changed = True
    while changed:
        changed = False
        for lhs, rhs in productions:
            first_before = first[lhs].copy()
            if rhs == ['']:
                first[lhs].add('')
            else:
                for symbol in rhs:
                    first[lhs].update(first[symbol] - set(['']))
                    if '' not in first[symbol]:
                        break
                else:
                    first[lhs].add('')
            if first_before != first[lhs]:
                changed = True
    return first

FIRST = compute_first()

# LR(1) Item
class Item:
    def __init__(self, lhs, rhs, dot=0, lookahead='$'):
        self.lhs = lhs
        self.rhs = rhs
        self.dot = dot
        self.lookahead = lookahead

    def __eq__(self, other):
        return (self.lhs, self.rhs, self.dot, self.lookahead) == (other.lhs, other.rhs, other.dot, other.lookahead)

    def __hash__(self):
        return hash((self.lhs, tuple(self.rhs), self.dot, self.lookahead))

    def __repr__(self):
        r = self.rhs[:]
        r.insert(self.dot, '•')
        return f"{self.lhs} -> {' '.join(r)}, {self.lookahead}"

# Closure function
def closure(items):
    closure_set = set(items)
    changed = True
    while changed:
        changed = False
        new_items = set()
        for item in closure_set:
            if item.dot < len(item.rhs):
                B = item.rhs[item.dot]
                if B in nonterminals:
                    beta = item.rhs[item.dot + 1:] + [item.lookahead]
                    first_beta = set()
                    for s in beta:
                        first_beta.update(FIRST[s] - set(['']))
                        if '' not in FIRST[s]:
                            break
                    else:
                        first_beta.add(item.lookahead)
                    for lhs2, rhs2 in productions:
                        if lhs2 == B:
                            for la in first_beta:
                                new_item = Item(lhs2, rhs2, 0, la)
                                if new_item not in closure_set:
                                    new_items.add(new_item)
        if new_items:
            closure_set.update(new_items)
            changed = True
    return closure_set

# GOTO function
def GOTO(items, X):
    goto_set = set()
    for item in items:
        if item.dot < len(item.rhs) and item.rhs[item.dot] == X:
            goto_set.add(Item(item.lhs, item.rhs, item.dot + 1, item.lookahead))
    return closure(goto_set)

# Build canonical LR(1) collection
def canonical_collection():
    C = []
    start = closure({Item("S'", ["E"], 0, '$')})
    C.append(start)
    changed = True
    while changed:
        changed = False
        new_states = []
        for I in C:
            for X in terminals + nonterminals:
                goto_set = GOTO(I, X)
                if goto_set and goto_set not in C and goto_set not in new_states:
                    new_states.append(goto_set)
                    changed = True
        C.extend(new_states)
    return C

collection = canonical_collection()
state_indices = {frozenset(s): i for i, s in enumerate(collection)}

# Build ACTION and GOTO tables
ACTION = defaultdict(dict)
GOTO_table = defaultdict(dict)

for i, I in enumerate(collection):
    for item in I:
        if item.dot < len(item.rhs):
            symbol = item.rhs[item.dot]
            goto_set = GOTO(I, symbol)
            if goto_set:
                j = state_indices[frozenset(goto_set)]
                if symbol in terminals:
                    ACTION[i][symbol] = ('s', j)
                else:
                    GOTO_table[i][symbol] = j
        else:
            if item.lhs == "S'":
                ACTION[i]['$'] = ('acc',)
            else:
                for idx, (lhs, rhs) in enumerate(productions):
                    if lhs == item.lhs and rhs == item.rhs:
                        ACTION[i][item.lookahead] = ('r', idx)
                        break

# Tokenizer
def tokenize(expr):
    tokens = []
    values = []
    i = 0
    while i < len(expr):
        if expr[i].isdigit():
            num = ''
            while i < len(expr) and expr[i].isdigit():
                num += expr[i]
                i += 1
            tokens.append('num')
            values.append(int(num))
        elif expr[i] in '+*()':
            tokens.append(expr[i])
            values.append(expr[i])
            i += 1
        elif expr[i].isspace():
            i += 1
        else:
            raise ValueError(f"Invalid character {expr[i]}")
    tokens.append('$')
    values.append('$')
    return tokens, values

# Shift-reduce parser with evaluation
def parse(expr):
    tokens, values = tokenize(expr)
    stack = [0]
    val_stack = []
    i = 0
    while True:
        state = stack[-1]
        token = tokens[i]
        if token not in ACTION[state]:
            raise SyntaxError(f"Unexpected token {token} at position {i}")
        act = ACTION[state][token]

        if act[0] == 's':  # shift
            stack.append(act[1])
            if token == 'num':
                val_stack.append(values[i])
            else:
                val_stack.append(values[i])
            i += 1
        elif act[0] == 'r':  # reduce
            prod_num = act[1]
            lhs, rhs = productions[prod_num]
            rhs_len = len(rhs)
            args = []
            if rhs != ['']:
                for _ in range(rhs_len):
                    stack.pop()
                    args.insert(0, val_stack.pop())
            state = stack[-1]
            stack.append(GOTO_table[state][lhs])
            # Evaluate on-the-fly
            if lhs == 'E':
                if rhs == ['E', '+', 'T']:
                    val_stack.append(args[0] + args[2])
                elif rhs == ['T']:
                    val_stack.append(args[0])
            elif lhs == 'T':
                if rhs == ['T', '*', 'F']:
                    val_stack.append(args[0] * args[2])
                elif rhs == ['F']:
                    val_stack.append(args[0])
            elif lhs == 'F':
                if rhs == ['(', 'E', ')']:
                    val_stack.append(args[1])
                elif rhs == ['num']:
                    val_stack.append(args[0])
        elif act[0] == 'acc':
            return val_stack[0]

# Example usage
expr = "3 + 4 * (2 + 5)"
result = parse(expr)
print(f"{expr} = {result}")
