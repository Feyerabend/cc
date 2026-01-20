
# symbols for assignment, member access, array indexing, and operators
ASSIGN = '='
PERIOD = '.'
LBRACKET = '['
RBRACKET = ']'

# simple tokens
IDENT = "IDENT"
NUMBER = "NUMBER"
LPAREN = '('
RPAREN = ')'
PLUS = "+"
MINUS = "-"
TIMES = "*"
SLASH = "/"
PERCENT = "%"
ANDSYM = "&"
OR = "|"
XORSYM = "^"
UMINUS = "UMINUS"


sym = None  # current symbol
buf = ""  # current buffer (identifier or number)
token_list = []  # tokenized list
token_index = 0

# node types
MEMBER_ACCESS = "MEMBER_ACCESS"
ARRAY_ACCESS = "ARRAY_ACCESS"
ASSIGNMENT = "ASSIGNMENT"
INUMBER = "INUMBER"
OP = "OP"

# current position in token list
def nextsym():
    global sym, buf, token_index
    if token_index < len(token_list):
        sym, buf = token_list[token_index]
        token_index += 1
    else:
        sym, buf = None, None  # end of input

# recognise a symbol
def recognize(expected):
    return sym == expected

# accept a symbol
def accept(expected):
    if recognize(expected):
        nextsym()
        return True
    return False

# expect a symbol (raise error if not matched)
def expect(expected):
    if not accept(expected):
        print(f"Error: Expected {expected} but found {sym}")
        return False
    return True

# tokenization
def tokenize(input_string):
    global token_list, token_index
    token_list = []
    token_index = 0
    i = 0
    n = len(input_string)
    
    while i < n:

        if input_string[i].isspace():
            i += 1
            continue

        elif input_string[i] in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
            start = i
            while i < n and input_string[i].isalnum():
                i += 1
            token_list.append(('IDENT', input_string[start:i]))

        elif input_string[i] in '0123456789':
            start = i
            while i < n and input_string[i].isdigit():
                i += 1
            token_list.append(('NUMBER', input_string[start:i]))

        elif input_string[i] == '=':
            token_list.append(('=', '='))
            i += 1

        elif input_string[i] == '.':
            token_list.append(('PERIOD', '.'))
            i += 1

        elif input_string[i] == '[':
            token_list.append(('LBRACKET', '['))
            i += 1

        elif input_string[i] == ']':
            token_list.append(('RBRACKET', ']'))
            i += 1

        elif input_string[i] == '+':
            token_list.append(('PLUS', '+'))
            i += 1

        elif input_string[i] == '-':
            token_list.append(('MINUS', '-'))
            i += 1

        elif input_string[i] == '*':
            token_list.append(('TIMES', '*'))
            i += 1

        elif input_string[i] == '/':
            token_list.append(('SLASH', '/'))
            i += 1

        elif input_string[i] == '%':
            token_list.append(('PERCENT', '%'))
            i += 1

        elif input_string[i] == '&':
            token_list.append(('ANDSYM', '&'))
            i += 1

        elif input_string[i] == '|':
            token_list.append(('OR', '|'))
            i += 1

        elif input_string[i] == '^':
            token_list.append(('XORSYM', '^'))
            i += 1

        elif input_string[i] == '(':
            token_list.append(('LPAREN', '('))
            i += 1

        elif input_string[i] == ')':
            token_list.append(('RPAREN', ')'))
            i += 1

        else:
            print(f"Unknown character: {input_string[i]}")
            i += 1

    token_list.append((None, None))  # end of input marker


# AST Node
class ASTNode:
    def __init__(self, type):
        self.type = type
        self.node1 = None
        self.node2 = None
        self.value = None
        self.name = None
        self.member = None
        self.index = None

def nnode(type):
    return ASTNode(type)

def print_ast(node, depth=0):
    if node is None:
        return
    indent = '  ' * depth
    print(f"{indent}{node.type}")
    if node.value is not None:
        print(f"{indent}  Value: {node.value}")
    if node.name is not None:
        print(f"{indent}  Name: {node.name}")
    if node.member is not None:
        print(f"{indent}  Member: {node.member}")
    if node.index is not None:
        print(f"{indent}  Index: {node.index}")
    if node.node1:
        print_ast(node.node1, depth + 1)
    if node.node2:
        print_ast(node.node2, depth + 1)

# factor (identifiers, numbers, parentheses, member access, array indexing)
def parse_factor():
    if recognize('IDENT'):
        node = nnode('IDENT')
        node.name = buf
        nextsym()

        # member access: object.property or array[index]
        while True:
            if recognize('PERIOD'):
                # member access (object.property)
                nextsym()
                if recognize('IDENT'):
                    member_node = nnode('MEMBER_ACCESS')
                    member_node.node1 = node
                    member_node.member = buf
                    node = member_node
                    nextsym()
            elif recognize('LBRACKET'):
                # array indexing (array[index])
                nextsym()
                index_expr = parse_expression()
                expect('RBRACKET')
                array_node = nnode('ARRAY_ACCESS')
                array_node.node1 = node
                array_node.index = index_expr
                node = array_node
            else:
                break  # no more member access or array indexing

    elif recognize('NUMBER'):
        node = nnode('NUMBER')
        node.value = int(buf)
        nextsym()

    elif accept('LPAREN'):
        node = parse_expression()
        expect('RPAREN')
    
    else:
        print(f"Syntax error: Unexpected symbol {buf}")
        node = None
    return node

# expression (assignments and operators)
def parse_expression():
    if recognize('MINUS'):
        node = nnode('UMINUS')
        nextsym()
        node.node1 = parse_term()
    else:
        node = parse_term()
    
    # assignment: var = expression
    if recognize(ASSIGN):
        assign_node = nnode('ASSIGNMENT')
        assign_node.var = node  # left side of assignment (variable)
        nextsym()
        assign_node.node1 = parse_expression()  # right side of assignment (expression)
        node = assign_node

    # operators like +, -, OR, XOR
    while sym in ('PLUS', 'MINUS', 'OR', 'XORSYM'):
        operator = node
        if sym == 'PLUS':
            op_type = 'ADD'
        elif sym == 'MINUS':
            op_type = 'SUB'
        elif sym == 'OR':
            op_type = 'OR'
        elif sym == 'XORSYM':
            op_type = 'XOR'
        node = nnode(op_type)
        nextsym()
        node.node1 = operator
        node.node2 = parse_term()
    return node

# term (multiplication, division, modulus, logical AND)
def parse_term():
    """Parse terms: multiplication, division, modulus, and logical AND."""
    node = parse_factor()
    while sym in ('TIMES', 'SLASH', 'PERCENT', 'ANDSYM'):
        operator = node
        if sym == 'TIMES':
            op_type = 'MULTIPLY'
        elif sym == 'SLASH':
            op_type = 'DIVIDE'
        elif sym == 'PERCENT':
            op_type = 'MOD'
        elif sym == 'ANDSYM':
            op_type = 'AND'
        node = nnode(op_type)
        nextsym()
        node.node1 = operator
        node.node2 = parse_factor()
    return node

def parse(input_string):
    tokenize(input_string)
    nextsym()
    return parse_expression()

# Test array indexing and assignment
test_input1 = "array[3] = object.property + 5"
ast1 = parse(test_input1)
print("Parsed AST 1:")
print_ast(ast1)

# Test simple assignment
test_input2 = "x = 3"
ast2 = parse(test_input2)
print("\nParsed AST 2:")
print_ast(ast2)

# Test member access
test_input3 = "object.property"
ast3 = parse(test_input3)
print("\nParsed AST 3:")
print_ast(ast3)
