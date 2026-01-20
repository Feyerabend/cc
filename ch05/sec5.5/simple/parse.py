
# constants for symbol types
IDENT = 1
NUMBER = 2
FLOAT = 3
TIMES = 4
SLASH = 5
PERCENT = 6
ANDSYM = 7
PLUS = 8
MINUS = 9
ORSYM = 10
XORSYM = 11
LPAREN = 12
RPAREN = 13
PERIOD = 14
UMINUS = 15
ADD = 16
SUB = 17
MULTIPLY = 18
DIVIDE = 19
MOD = 20
AND = 21
OR = 22
XOR = 23

# tokens list for parsing
tokens = []
current_token_index = 0
sym = None
buf = ""

# Node and Value classes
class Node:
    def __init__(self, node_type):
        self.type = node_type
        self.node1 = None  # left child
        self.node2 = None  # right child
        self.value = None  # value (for constants)
        self.name = None   # name for identifiers

class Value:
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end

# tokenizer to convert input string to tokens
def tokenize(input_str):
    global tokens
    i = 0
    while i < len(input_str):
        char = input_str[i]

        if char.isalpha():  # identifiers (variable names)
            start = i
            while i < len(input_str) and input_str[i].isalnum():
                i += 1
            tokens.append((IDENT, input_str[start:i]))

        elif char.isdigit() or char == '.':  # numbers (including floats)
            start = i
            has_dot = False
            while i < len(input_str) and (input_str[i].isdigit() or (input_str[i] == '.' and not has_dot)):
                if input_str[i] == '.':
                    has_dot = True
                i += 1
            if has_dot:
                tokens.append((FLOAT, input_str[start:i]))  # float token
            else:
                tokens.append((NUMBER, input_str[start:i]))  # integer token

        elif char == '+':
            tokens.append((PLUS, '+'))
            i += 1
        elif char == '-':
            tokens.append((MINUS, '-'))
            i += 1
        elif char == '*':
            tokens.append((TIMES, '*'))
            i += 1
        elif char == '/':
            tokens.append((SLASH, '/'))
            i += 1
        elif char == '%':
            tokens.append((PERCENT, '%'))
            i += 1

        elif char == '(':
            tokens.append((LPAREN, '('))
            i += 1
        elif char == ')':
            tokens.append((RPAREN, ')'))
            i += 1

        elif char == '.':
            tokens.append((PERIOD, '.'))
            i += 1

        elif char == ' ' or char == '\t' or char == '\n':  # Skip whitespace
            i += 1
        else:
            raise SyntaxError(f"Unknown character {char}")

    tokens.append((None, ""))  # end-of-input marker
    nextsym()

# get next symbol from token list
def nextsym():
    global sym, buf, current_token_index
    if current_token_index < len(tokens):
        sym, buf = tokens[current_token_index]
        current_token_index += 1
    else:
        sym = None

# accept current symbol if matches, and move to next token
def accept(symbol):
    if recognize(symbol):
        nextsym()
        return True
    return False

# recognize current symbol
def recognize(symbol):
    return sym == symbol

# expect a symbol, raise error if it doesn't match
def expect(symbol):
    if not accept(symbol):
        raise SyntaxError(f"Expected symbol {symbol}, but found {sym}")

# create a new node with specific operation type
def nnode(op_type):
    return Node(op_type)

# parse factors (numbers, identifiers, parentheses)
def factor():
    n = None
    if recognize(IDENT):
        n = nnode(IDENT)
        n.name = buf
        nextsym()
    elif recognize(NUMBER):
        n = nnode(NUMBER)
        n.value = int(buf)
        nextsym()
    elif recognize(FLOAT):
        n = nnode(FLOAT)
        n.value = float(buf)
        nextsym()
    elif accept(LPAREN):
        n = expression()
        expect(RPAREN)
    elif recognize(MINUS):  # unary minus handling
        nextsym()
        n = factor()
        unary_minus = nnode(UMINUS)
        unary_minus.node1 = n
        return unary_minus
    else:
        print(f"Syntax error: Unexpected symbol {buf}")
    return n

# term function to handle multiplication, division, etc.
def term():
    n = factor()
    while sym in (TIMES, SLASH, PERCENT, ANDSYM):
        m = n
        if sym == TIMES:
            h = MULTIPLY
        elif sym == SLASH:
            h = DIVIDE
        elif sym == PERCENT:
            h = MOD
        elif sym == ANDSYM:
            h = AND
        n = nnode(h)
        nextsym()
        n.node1 = m
        n.node2 = factor()
    return n

# expressions to handle addition, subtraction, etc.
def expression():
    if recognize(MINUS):  # unary minus handling at expression level
        n = nnode(UMINUS)
        nextsym()
        n.node1 = term()
    else:
        n = term()
    while sym in (PLUS, MINUS, ORSYM, XORSYM):
        m = n
        if sym == PLUS:
            h = ADD
        elif sym == MINUS:
            h = SUB
        elif sym == ORSYM:
            h = OR
        elif sym == XORSYM:
            h = XOR
        n = nnode(h)
        nextsym()
        n.node1 = m
        n.node2 = term()
    return n

# display the AST
def print_tree(node, depth=0):
    if node is None:
        return
    if node.type == IDENT:
        print(" " * depth + f"IDENT({node.name})")
    elif node.type == NUMBER:
        print(" " * depth + f"NUMBER({node.value})")
    elif node.type == FLOAT:
        print(" " * depth + f"FLOAT({node.value})")
    elif node.type in (ADD, SUB, MULTIPLY, DIVIDE, MOD, AND, OR, XOR):
        print(" " * depth + f"OP({node.type})")
        print_tree(node.node1, depth + 2)  # left child
        print_tree(node.node2, depth + 2)  # right child
    elif node.type == UMINUS:
        print(" " * depth + "UMINUS")
        print_tree(node.node1, depth + 2)

def run_parser(input_str):
    tokenize(input_str)  # tokenize input string
    result = expression()  # start parsing from expression level
    print("Parsed AST:")
    print_tree(result)  # print Abstract Syntax Tree (AST)

# Test Case 1: Expression with floating-point numbers and unary minus
sample_input = "(a + 3.5) * (c - 1.2) + 3 * -4.5"
run_parser(sample_input)

# Test Case 2: Simple floating-point number
sample_input2 = "5.25"
run_parser(sample_input2)

# Test Case 3: Expression with a floating-point result and unary minus
sample_input3 = "(5.5 + 2.5) * -3"
run_parser(sample_input3)
