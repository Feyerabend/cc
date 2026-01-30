
# symbols for assignment and .. operators
ASSIGN = '='

# simple tokens
IDENT = "IDENT"
INT = "INT"
FLOAT = "FLOAT"
LPAREN = '('
RPAREN = ')'
PLUS = "+"
MINUS = "-"
TIMES = "*"
SLASH = "/"

sym = None  # current symbol
buf = ""  # current buffer (identifier or number)
token_list = []  # tokenised list
token_index = 0

# node types
ASSIGNMENT = "ASSIGNMENT"
NUMBER = "NUMBER"
IDENT = "IDENT"
ADD = 'ADD'
SUB = 'SUB'
MULTIPLY = 'MULTIPLY'
DIVIDE = 'DIVIDE'
UMINUS = "UMINUS"

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

        elif input_string[i].isalpha():
            start = i
            while i < n and input_string[i].isalnum():
                i += 1
            token_list.append((IDENT, input_string[start:i]))

        elif input_string[i].isdigit() or input_string[i] == '.':
            start = i
            dot_count = 0
            while i < n and (input_string[i].isdigit() or input_string[i] == '.'):
                if input_string[i] == '.':
                    dot_count += 1
                if dot_count > 1:
                    raise ValueError("Invalid number format")
                i += 1
            buf_str = input_string[start:i]
            if buf_str == '.' or buf_str[-1] == '.':
                raise ValueError("Invalid number format")
            if '.' in buf_str:
                token_list.append((FLOAT, buf_str))
            else:
                token_list.append((INT, buf_str))

        elif input_string[i] == '=':
            token_list.append((ASSIGN, '='))
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
        self.var = None  # For assignment left side
        self.data_type = None  # Synthesised type

def nnode(node_type):
    return ASTNode(node_type)

def print_ast(node, depth=0):
    if node is None:
        return
    indent = '  ' * depth
    print(f"{indent}{node.type}")
    if node.data_type is not None:
        print(f"{indent}  Data Type: {node.data_type}")
    if node.value is not None:
        print(f"{indent}  Value: {node.value}")
    if node.name is not None:
        print(f"{indent}  Name: {node.name}")
    if node.var is not None:
        print(f"{indent}  Var:")
        print_ast(node.var, depth + 2)
    if node.node1:
        print(f"{indent}  Node1:")
        print_ast(node.node1, depth + 2)
    if node.node2:
        print(f"{indent}  Node2:")
        print_ast(node.node2, depth + 2)

def is_compatible(left_type, right_type):
    if left_type == right_type:
        return True
    if left_type == "float" and right_type == "int":
        return True
    return False


# Parse P (Primary) - Corresponds to productions 17-19 (simplified, now without postfix)
# Synthesizes P.ast and P.syn_type; uses P.inh_env
def parse_P(env):
    if recognize(IDENT):
        name = buf
        nextsym()
        try:
            data_type = env[name]
        except KeyError:
            raise NameError(f"Undefined variable: {name}")
        node = nnode(IDENT)
        node.name = name
        node.data_type = data_type
        return node, data_type
    elif sym in (INT, FLOAT):
        if sym == INT:
            value = int(buf)
            data_type = "int"
        else:
            value = float(buf)
            data_type = "float"
        nextsym()
        node = nnode(NUMBER)
        node.value = value
        node.data_type = data_type
        return node, data_type
    elif accept(LPAREN):
        node, data_type = parse_E(env)
        expect(RPAREN)
        return node, data_type
    else:
        raise SyntaxError(f"Unexpected symbol {sym}")


# Parse T (Term with multiplicative ops) - Corresponds to productions 9-12
# Synthesizes T.ast and T.syn_type; uses T.inh_env, passes to children
def parse_T(env):
    node, data_type = parse_P(env)
    while sym in (TIMES, SLASH):
        op_type = MULTIPLY if sym == TIMES else DIVIDE
        nextsym()
        node2, data_type2 = parse_P(env)
        op_node = nnode(op_type)
        op_node.node1 = node
        op_node.node2 = node2
        res_type = "float" if op_type == DIVIDE or data_type == "float" or data_type2 == "float" else "int"
        op_node.data_type = res_type
        node = op_node
        data_type = res_type
    return node, data_type


# Parse S (Signed term) - Corresponds to productions 7,8
# Synthesizes S.ast and S.syn_type; uses S.inh_env, passes to children
def parse_S(env):
    if accept(MINUS):
        node1, data_type1 = parse_T(env)
        node = nnode(UMINUS)
        node.node1 = node1
        node.data_type = data_type1
        return node, data_type1
    else:
        return parse_T(env)


# Parse A (Additive expression) - Corresponds to productions 3-6
# Synthesizes A.ast and A.syn_type; uses A.inh_env, passes to children
def parse_A(env):
    node, data_type = parse_S(env)
    while sym in (PLUS, MINUS):
        op_type = ADD if sym == PLUS else SUB
        nextsym()
        node2, data_type2 = parse_S(env)
        op_node = nnode(op_type)
        op_node.node1 = node
        op_node.node2 = node2
        res_type = "float" if data_type == "float" or data_type2 == "float" else "int"
        op_node.data_type = res_type
        node = op_node
        data_type = res_type
    return node, data_type


# Parse E (Expression with assignment) - Corresponds to productions 1,2
# Synthesizes E.ast and E.syn_type; uses E.inh_env, passes to children
def parse_E(env):
    node, data_type = parse_A(env)
    if accept(ASSIGN):
        if node.type != IDENT:
            raise SyntaxError("Left side of assignment must be an identifier")
        left_type = data_type
        right_node, right_type = parse_E(env)
        if not is_compatible(left_type, right_type):
            raise TypeError(f"Type mismatch: cannot assign {right_type} to {left_type}")
        assign_node = nnode(ASSIGNMENT)
        assign_node.var = node
        assign_node.node1 = right_node
        assign_node.data_type = right_type
        node = assign_node
        data_type = right_type
    return node, data_type

def parse(input_string, env=None):
    if env is None:
        env = {}
    tokenize(input_string)
    nextsym()
    ast, _ = parse_E(env)
    if sym is not None:
        raise SyntaxError("Extra input after expression")
    return ast

'''
1. E → A
   A.inh_env = E.inh_env
   E.ast = A.ast
   E.syn_type = A.syn_type

2. E → A = E1
   A.inh_env = E.inh_env
   E1.inh_env = E.inh_env
      Check: A.ast.type must be 'IDENT' (lvalue restriction)
      Check: compatible(A.syn_type, E1.syn_type) or error
   E.ast = nnode('ASSIGNMENT')
   E.ast.var = A.ast
   E.ast.node1 = E1.ast
   E.ast.data_type = E1.syn_type
   E.syn_type = E1.syn_type

3. A → S
   S.inh_env = A.inh_env
   A.ast = S.ast
   A.syn_type = S.syn_type

4. A → A1 AddOp S
   A1.inh_env = A.inh_env
   S.inh_env = A.inh_env
   A.ast = nnode(AddOp.type)
   A.ast.node1 = A1.ast
   A.ast.node2 = S.ast
   A.syn_type = "float" if "float" in (A1.syn_type, S.syn_type) else "int"
   A.ast.data_type = A.syn_type

5. AddOp → +
   AddOp.type = 'ADD'

6. AddOp → -
   AddOp.type = 'SUB'

7. S → T
   T.inh_env = S.inh_env
   S.ast = T.ast
   S.syn_type = T.syn_type

8. S → - T
   T.inh_env = S.inh_env
   S.ast = nnode('UMINUS')
   S.ast.node1 = T.ast
   S.syn_type = T.syn_type
   S.ast.data_type = S.syn_type

9. T → P
   P.inh_env = T.inh_env
   T.ast = P.ast
   T.syn_type = P.syn_type

10. T → T1 MultOp P
    T1.inh_env = T.inh_env
    P.inh_env = T.inh_env
    T.ast = nnode(MultOp.type)
    T.ast.node1 = T1.ast
    T.ast.node2 = P.ast
    T.syn_type = "float" if MultOp.type == 'DIVIDE' or "float" in (T1.syn_type, P.syn_type) else "int"
    T.ast.data_type = T.syn_type

11. MultOp → *
    MultOp.type = 'MULTIPLY'

12. MultOp → /
    MultOp.type = 'DIVIDE'

13. P → IDENT
    P.syn_type = P.inh_env[IDENT.lexval] (error if undefined)
    P.ast = nnode('IDENT')
    P.ast.name = IDENT.lexval
    P.ast.data_type = P.syn_type

14. P → INT
    P.syn_type = "int"
    P.ast = nnode('NUMBER')
    P.ast.value = int(INT.lexval)
    P.ast.data_type = "int"

15. P → FLOAT
    P.syn_type = "float"
    P.ast = nnode('NUMBER')
    P.ast.value = float(FLOAT.lexval)
    P.ast.data_type = "float"

16. P → ( E )
    E.inh_env = P.inh_env
    P.ast = E.ast
    P.syn_type = E.syn_type
'''