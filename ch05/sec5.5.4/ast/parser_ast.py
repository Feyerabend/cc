from dataclasses import dataclass
from typing import Any, Callable, Optional, List, Tuple

@dataclass
class ASTNode:
    pass

@dataclass
class Number(ASTNode):
    value: int

@dataclass
class Variable(ASTNode):
    name: str

@dataclass
class BinOp(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode

@dataclass
class Assignment(ASTNode):
    var: str
    expr: ASTNode

@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    then_branch: List[ASTNode]
    else_branch: Optional[List[ASTNode]] = None

@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode
    body: List[ASTNode]

@dataclass
class Program(ASTNode):
    statements: List[ASTNode]



class ParseResult:
    def __init__(self, success: bool, value: Any = None, rest: str = ""):
        self.success = success
        self.value = value
        self.rest = rest

class Parser:
    def __init__(self, parse_fn: Callable[[str], ParseResult]):
        self.parse_fn = parse_fn
    
    def __call__(self, text: str) -> ParseResult:
        return self.parse_fn(text)
    
    def __or__(self, other):
        def parse(text):
            r = self(text)
            return r if r.success else other(text)
        return Parser(parse)
    
    def __rshift__(self, fn):
        def parse(text):
            r = self(text)
            return ParseResult(r.success, fn(r.value) if r.success else None, r.rest)
        return Parser(parse)
    
    def then(self, other):
        def parse(text):
            r1 = self(text)
            if not r1.success:
                return r1
            r2 = other(r1.rest)
            if not r2.success:
                return r2
            return ParseResult(True, (r1.value, r2.value), r2.rest)
        return Parser(parse)
    
    def many(self):
        def parse(text):
            values = []
            rest = text
            while True:
                r = self(rest)
                if not r.success:
                    break
                values.append(r.value)
                rest = r.rest
            return ParseResult(True, values, rest)
        return Parser(parse)
    
    def optional(self):
        def parse(text):
            r = self(text)
            return ParseResult(True, r.value if r.success else None, r.rest if r.success else text)
        return Parser(parse)



def regex(pattern: str) -> Parser:
    import re
    def parse(text):
        m = re.match(pattern, text)
        if m:
            return ParseResult(True, m.group(0), text[m.end():])
        return ParseResult(False)
    return Parser(parse)

def string(s: str) -> Parser:
    def parse(text):
        if text.startswith(s):
            return ParseResult(True, s, text[len(s):])
        return ParseResult(False)
    return Parser(parse)

def whitespace():
    return regex(r'\s*')

def token(s: str) -> Parser:
    return string(s).then(whitespace()) >> (lambda x: x[0])




def build_parser():
    # Forward declarations for recursive grammar
    expr_parser = [None]
    stmt_parser = [None]
    
    # Numbers
    number = regex(r'\d+').then(whitespace()) >> (lambda x: Number(int(x[0])))
    
    # Variables
    ident = regex(r'[a-zA-Z_][a-zA-Z0-9_]*').then(whitespace()) >> (lambda x: x[0])
    variable = ident >> Variable
    
    # Primary expressions
    primary = number | variable | (
        token('(').then(lambda t: expr_parser[0](t)).then(token(')'))
        >> (lambda x: x[0][1])
    )
    
    # Binary operators with precedence
    def binop(op_parser, operand):
        def parse(text):
            r1 = operand(text)
            if not r1.success:
                return r1
            left = r1.value
            rest = r1.rest
            while True:
                r_op = op_parser(rest)
                if not r_op.success:
                    break
                r2 = operand(r_op.rest)
                if not r2.success:
                    break
                left = BinOp(r_op.value, left, r2.value)
                rest = r2.rest
            return ParseResult(True, left, rest)
        return Parser(parse)
    
    mul_op = token('*') | token('/')
    add_op = token('+') | token('-')
    cmp_op = token('==') | token('!=') | token('<=') | token('>=') | token('<') | token('>')
    
    term = binop(mul_op, primary)
    arith = binop(add_op, term)
    expr = binop(cmp_op, arith)
    
    expr_parser[0] = expr
    
    # Statements
    assignment = ident.then(token('=')).then(expr).then(token(';')) >> (
        lambda x: Assignment(x[0][0][0], x[0][1])
    )
    
    def if_stmt(text):
        r1 = token('if')(text)
        if not r1.success: return r1
        r2 = token('(')(r1.rest)
        if not r2.success: return r2
        r3 = expr(r2.rest)
        if not r3.success: return r3
        r4 = token(')')(r3.rest)
        if not r4.success: return r4
        r5 = token('{')(r4.rest)
        if not r5.success: return r5
        r6 = stmt_parser[0].many()(r5.rest)
        if not r6.success: return r6
        r7 = token('}')(r6.rest)
        if not r7.success: return r7
        
        # Optional else
        r_else = token('else')(r7.rest)
        if r_else.success:
            r8 = token('{')(r_else.rest)
            if not r8.success: return r8
            r9 = stmt_parser[0].many()(r8.rest)
            if not r9.success: return r9
            r10 = token('}')(r9.rest)
            if not r10.success: return r10
            return ParseResult(True, IfStmt(r3.value, r6.value, r9.value), r10.rest)
        
        return ParseResult(True, IfStmt(r3.value, r6.value), r7.rest)
    
    def while_stmt(text):
        r1 = token('while')(text)
        if not r1.success: return r1
        r2 = token('(')(r1.rest)
        if not r2.success: return r2
        r3 = expr(r2.rest)
        if not r3.success: return r3
        r4 = token(')')(r3.rest)
        if not r4.success: return r4
        r5 = token('{')(r4.rest)
        if not r5.success: return r5
        r6 = stmt_parser[0].many()(r5.rest)
        if not r6.success: return r6
        r7 = token('}')(r6.rest)
        if not r7.success: return r7
        return ParseResult(True, WhileStmt(r3.value, r6.value), r7.rest)
    
    stmt = assignment | Parser(if_stmt) | Parser(while_stmt)
    stmt_parser[0] = stmt
    
    # Program is a list of statements
    program = whitespace().then(stmt.many()) >> (lambda x: Program(x[1]))
    
    return program



if __name__ == "__main__":
    parser = build_parser()
    
    code = """
        x = 10;
        y = 20;
        if (x < y) {
            z = x + y;
            unused = 42;
        } else {
            z = x - y;
        }
        result = z * 2;
        dead = 99;
    """
    
    result = parser(code)
    if result.success:
        print("Parsed successfully!")
        print("\nAST:")
        import json
        
        def ast_to_dict(node):
            if isinstance(node, list):
                return [ast_to_dict(n) for n in node]
            elif isinstance(node, ASTNode):
                d = {'type': node.__class__.__name__}
                for k, v in node.__dict__.items():
                    d[k] = ast_to_dict(v)
                return d
            else:
                return node
        
        print(json.dumps(ast_to_dict(result.value), indent=2))
    else:
        print("Parse failed")
