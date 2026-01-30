
# symbols for ..
ASSIGN = '='    # assignment
PERIOD = '.'    # member access
LBRACKET = '['  # array indexing
RBRACKET = ']'  # .. and operators

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

sym = None       # current symbol
buf = ""         # current buffer (identifier or number)
token_list = []  # tokenised list
token_index = 0

# node types
MEMBER_ACCESS = "MEMBER_ACCESS"
ARRAY_ACCESS = "ARRAY_ACCESS"
ASSIGNMENT = "ASSIGNMENT"
NUMBER_NODE = "NUMBER"
IDENT_NODE = "IDENT"
OP_ADD = 'ADD'
OP_SUB = 'SUB'
OP_OR = 'OR'
OP_XOR = 'XOR'
OP_MULTIPLY = 'MULTIPLY'
OP_DIVIDE = 'DIVIDE'
OP_MOD = 'MOD'
OP_AND = 'AND'
OP_UMINUS = "UMINUS"

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
        raise SyntaxError(f"Expected {expected} but found {sym}")
    return True

# tokenisation
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

        elif input_string[i].isalpha():
            start = i
            while i < n and input_string[i].isalnum():
                i += 1
            token_list.append((IDENT, input_string[start:i]))

        elif input_string[i].isdigit():
            start = i
            while i < n and input_string[i].isdigit():
                i += 1
            token_list.append((NUMBER, input_string[start:i]))

        elif input_string[i] == '=':
            token_list.append((ASSIGN, '='))
            i += 1

        elif input_string[i] == '.':
            token_list.append((PERIOD, '.'))
            i += 1

        elif input_string[i] == '[':
            token_list.append((LBRACKET, '['))
            i += 1

        elif input_string[i] == ']':
            token_list.append((RBRACKET, ']'))
            i += 1

        elif input_string[i] == '+':
            token_list.append((PLUS, '+'))
            i += 1

        elif input_string[i] == '-':
            token_list.append((MINUS, '-'))
            i += 1

        elif input_string[i] == '*':
            token_list.append((TIMES, '*'))
            i += 1

        elif input_string[i] == '/':
            token_list.append((SLASH, '/'))
            i += 1

        elif input_string[i] == '%':
            token_list.append((PERCENT, '%'))
            i += 1

        elif input_string[i] == '&':
            token_list.append((ANDSYM, '&'))
            i += 1

        elif input_string[i] == '|':
            token_list.append((OR, '|'))
            i += 1

        elif input_string[i] == '^':
            token_list.append((XORSYM, '^'))
            i += 1

        elif input_string[i] == '(':
            token_list.append((LPAREN, '('))
            i += 1

        elif input_string[i] == ')':
            token_list.append((RPAREN, ')'))
            i += 1

        else:
            raise ValueError(f"Unknown character: {input_string[i]}")
            i += 1

    token_list.append((None, None))  # end of input marker



# AST Node
class ASTNode:
    def __init__(self, node_type):
        self.type = node_type
        self.node1 = None
        self.node2 = None
        self.value = None
        self.name = None
        self.member = None
        self.index = None
        self.var = None  # For assignment left side

def nnode(node_type):
    return ASTNode(node_type)

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
        print(f"{indent}  Index:")
        print_ast(node.index, depth + 2)
    if node.var is not None:
        print(f"{indent}  Var:")
        print_ast(node.var, depth + 2)
    if node.node1:
        print(f"{indent}  Node1:")
        print_ast(node.node1, depth + 2)
    if node.node2:
        print(f"{indent}  Node2:")
        print_ast(node.node2, depth + 2)


# Referred productions can be found at the end of this file.

# Parse P (Primary) - Corresponds to productions 20, 21, 22
# Synthesizes P.ast from terminals or sub-expression
def parse_P():
    if recognize(IDENT):
        node = nnode(IDENT_NODE)
        node.name = buf  # .lexval equivalent
        nextsym()
        return node
    elif recognize(NUMBER):
        node = nnode(NUMBER_NODE)
        node.value = int(buf)  # .numval equivalent
        nextsym()
        return node
    elif accept(LPAREN):
        node = parse_E()  # P.ast = E.ast
        expect(RPAREN)
        return node
    else:
        raise SyntaxError(f"Unexpected symbol {sym}")


# Parse F (Factor with postfix ops) - Corresponds to productions 17, 18, 19
# Synthesizes F.ast by building MEMBER_ACCESS or ARRAY_ACCESS nodes
# This handles left-associative postfix operations,
# which are not in basic CFGs but extended in attribute grammars for semantics
def parse_F():
    node = parse_P()  # F.ast = P.ast
    while True:
        if accept(PERIOD):
            if not recognize(IDENT):
                raise SyntaxError("Expected IDENT after PERIOD")
            member_node = nnode(MEMBER_ACCESS)
            member_node.node1 = node  # F.ast.node1 = F1.ast
            member_node.member = buf  # F.ast.member = IDENT.lexval
            nextsym()
            node = member_node
        elif accept(LBRACKET):
            index_expr = parse_E()
            expect(RBRACKET)
            array_node = nnode(ARRAY_ACCESS)
            array_node.node1 = node        # F.ast.node1 = F1.ast
            array_node.index = index_expr  # F.ast.index = E.ast
            node = array_node
        else:
            break
    return node


# Parse T (Term with multiplicative ops) - Corresponds to productions 11, 12, 13-16
# Synthesizes T.ast with left-associative binary ops
# Attribute grammar allows computing op types as MultOp.type
def parse_T():
    node = parse_F()  # T.ast = F.ast
    while sym in (TIMES, SLASH, PERCENT, ANDSYM):
        op_type = {
            TIMES: OP_MULTIPLY,
            SLASH: OP_DIVIDE,
            PERCENT: OP_MOD,
            ANDSYM: OP_AND
        }[sym]  # MultOp.type
        nextsym()
        op_node = nnode(op_type)
        op_node.node1 = node       # T.ast.node1 = T1.ast
        op_node.node2 = parse_F()  # T.ast.node2 = F.ast
        node = op_node
    return node


# Parse S (Signed term) - Corresponds to productions 9, 10
# Synthesizes S.ast for unary minus, unique semantic handling not just syntactic
def parse_S():
    if accept(MINUS):
        node = nnode(OP_UMINUS)
        node.node1 = parse_T()  # S.ast.node1 = T.ast
        return node
    else:
        return parse_T()  # S.ast = T.ast


# Parse A (Additive expression) - Corresponds to productions 3, 4, 5-8
# Synthesizes A.ast with left-associative binary ops
# Similar to T, but for additive level; attribute rules map to op types
def parse_A():
    node = parse_S()  # A.ast = S.ast
    while sym in (PLUS, MINUS, OR, XORSYM):
        op_type = {
            PLUS: OP_ADD,
            MINUS: OP_SUB,
            OR: OP_OR,
            XORSYM: OP_XOR
        }[sym]  # AddOp.type
        nextsym()
        op_node = nnode(op_type)
        op_node.node1 = node       # A.ast.node1 = A1.ast
        op_node.node2 = parse_S()  # A.ast.node2 = S.ast (allows unary after op)
        node = op_node
    return node


# Parse E (Expression with assignment) - Corresponds to productions 1, 2
# Synthesizes E.ast, with right-associative assignment
# This is where attribute grammars shine for semantics: building assignment nodes distinctly from expressions
def parse_E():
    node = parse_A()  # E.ast = A.ast
    if accept(ASSIGN):
        assign_node = nnode(ASSIGNMENT)
        assign_node.var = node         # E.ast.var = A.ast
        assign_node.node1 = parse_E()  # E.ast.node1 = E1.ast (right-recursive)
        node = assign_node
    return node

def parse(input_string):
    tokenize(input_string)
    nextsym()
    ast = parse_E()
    if sym is not None:
        raise SyntaxError("Extra input after expression")
    return ast


'''
Production Rules

Expression (E) - Handled by parse_E()
1. E → A  
   E.ast = A.ast  
2. E → A = E1  
   E.ast = nnode('ASSIGNMENT')  
   E.ast.var = A.ast  
   E.ast.node1 = E1.ast

Additive Expression (A) - Handled by parse_A()
3. A → S  
   A.ast = S.ast  
4. A → A1 AddOp T  
   A.ast = nnode(AddOp.type)  
   A.ast.node1 = A1.ast  
   A.ast.node2 = T.ast  
5. AddOp → +  
   AddOp.type = 'ADD'  
6. AddOp → -  
   AddOp.type = 'SUB'  
7. AddOp → |  
   AddOp.type = 'OR'  
8. AddOp → ^  
   AddOp.type = 'XOR'

Signed Term (S) - Handled by parse_S()
9. S → T  
   S.ast = T.ast  
10. S → - T  
    S.ast = nnode('UMINUS')  
    S.ast.node1 = T.ast

Term (T) - Handled by parse_T()
11. T → F  
    T.ast = F.ast  
12. T → T1 MultOp F  
    T.ast = nnode(MultOp.type)  
    T.ast.node1 = T1.ast  
    T.ast.node2 = F.ast  
13. MultOp → *  
    MultOp.type = 'MULTIPLY'  
14. MultOp → /  
    MultOp.type = 'DIVIDE'  
15. MultOp → %  
    MultOp.type = 'MOD'  
16. MultOp → &  
    MultOp.type = 'AND'

Factor (F) - Handled by parse_F()
17. F → P  
    F.ast = P.ast  
18. F → F1 . IDENT  
    F.ast = nnode('MEMBER_ACCESS')  
    F.ast.node1 = F1.ast  
    F.ast.member = IDENT.lexval  
19. F → F1 [ E ]  
    F.ast = nnode('ARRAY_ACCESS')  
    F.ast.node1 = F1.ast  
    F.ast.index = E.ast

Primary (P) - Handled by parse_P()
20. P → IDENT  
    P.ast = nnode('IDENT')  
    P.ast.name = IDENT.lexval  
21. P → NUMBER  
    P.ast = nnode('NUMBER')  
    P.ast.value = NUMBER.numval  
22. P → ( E )  
    P.ast = E.ast
'''