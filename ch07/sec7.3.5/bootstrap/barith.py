#!/usr/bin/env python3

# Bootstrap Language - Self-Hosting Interpreter
# The outer Python layer is minimal infrastructure.

import re
from typing import Any, Dict, List

class Lexer:
    def __init__(self, code: str):
        self.code = code
        
    def tokenize(self) -> List[tuple]:
        tokens = []
        patterns = [
            ('NUMBER', r'\d+'),
            ('STRING', r'"[^"]*"'),
            ('IF', r'\bif\b'),
            ('WHILE', r'\bwhile\b'),
            ('LET', r'\blet\b'),
            ('FN', r'\bfn\b'),
            ('RETURN', r'\breturn\b'),
            ('AND', r'\band\b'),
            ('OR', r'\bor\b'),
            ('EQ', r'=='),
            ('NE', r'!='),
            ('LE', r'<='),
            ('GE', r'>='),
            ('LT', r'<'),
            ('GT', r'>'),
            ('ASSIGN', r'='),
            ('PLUS', r'\+'),
            ('MINUS', r'-'),
            ('MULT', r'\*'),
            ('DIV', r'/'),
            ('LPAREN', r'\('),
            ('RPAREN', r'\)'),
            ('LBRACE', r'\{'),
            ('RBRACE', r'\}'),
            ('LBRACK', r'\['),
            ('RBRACK', r'\]'),
            ('COMMA', r','),
            ('DOT', r'\.'),
            ('ID', r'[a-zA-Z_][a-zA-Z0-9_]*'),
            ('NEWLINE', r'\n'),
            ('SKIP', r'[ \t]+'),
            ('COMMENT', r'#[^\n]*'),
        ]
        pattern = '|'.join(f'(?P<{name}>{pat})' for name, pat in patterns)
        for match in re.finditer(pattern, self.code):
            kind = match.lastgroup
            value = match.group()
            if kind not in ('SKIP', 'NEWLINE', 'COMMENT'):
                tokens.append((kind, value))
        return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        
    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    def consume(self, expected=None):
        if self.pos >= len(self.tokens):
            return None
        token = self.tokens[self.pos]
        if expected and token[0] != expected:
            raise SyntaxError(f"Expected {expected}, got {token[0]} ({token[1]!r})")
        self.pos += 1
        return token
    
    def parse(self):
        statements = []
        while self.peek():
            statements.append(self.parse_statement())
        return statements
    
    def parse_statement(self):
        token = self.peek()
        if token[0] == 'LET':   return self.parse_let()
        elif token[0] == 'FN':  return self.parse_fn()
        elif token[0] == 'IF':  return self.parse_if()
        elif token[0] == 'WHILE': return self.parse_while()
        elif token[0] == 'RETURN': return self.parse_return()
        else: return ('EXPR', self.parse_expr())
    
    def parse_let(self):
        self.consume('LET')
        name = self.consume('ID')[1]
        self.consume('ASSIGN')
        return ('LET', name, self.parse_expr())
    
    def parse_fn(self):
        self.consume('FN')
        name = self.consume('ID')[1]
        self.consume('LPAREN')
        params = []
        while self.peek()[0] != 'RPAREN':
            params.append(self.consume('ID')[1])
            if self.peek()[0] == 'COMMA':
                self.consume('COMMA')
        self.consume('RPAREN')
        self.consume('LBRACE')
        body = []
        while self.peek()[0] != 'RBRACE':
            body.append(self.parse_statement())
        self.consume('RBRACE')
        return ('FN', name, params, body)
    
    def parse_if(self):
        self.consume('IF')
        cond = self.parse_expr()
        self.consume('LBRACE')
        body = []
        while self.peek()[0] != 'RBRACE':
            body.append(self.parse_statement())
        self.consume('RBRACE')
        else_body = []
        return ('IF', cond, body, else_body)
    
    def parse_while(self):
        self.consume('WHILE')
        cond = self.parse_expr()
        self.consume('LBRACE')
        body = []
        while self.peek()[0] != 'RBRACE':
            body.append(self.parse_statement())
        self.consume('RBRACE')
        return ('WHILE', cond, body)
    
    def parse_return(self):
        self.consume('RETURN')
        return ('RETURN', self.parse_expr())
    
    def parse_expr(self):   return self.parse_or()
    
    def parse_or(self):
        left = self.parse_and()
        while self.peek() and self.peek()[0] == 'OR':
            self.consume()
            left = ('OR', left, self.parse_and())
        return left
    
    def parse_and(self):
        left = self.parse_comparison()
        while self.peek() and self.peek()[0] == 'AND':
            self.consume()
            left = ('AND', left, self.parse_comparison())
        return left
    
    def parse_comparison(self):
        left = self.parse_additive()
        if self.peek() and self.peek()[0] in ('EQ','NE','LT','GT','LE','GE'):
            op = self.consume()[0]
            return (op, left, self.parse_additive())
        return left
    
    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.peek() and self.peek()[0] in ('PLUS','MINUS'):
            op = self.consume()[0]
            left = (op, left, self.parse_multiplicative())
        return left
    
    def parse_multiplicative(self):
        left = self.parse_postfix()
        while self.peek() and self.peek()[0] in ('MULT','DIV'):
            op = self.consume()[0]
            left = (op, left, self.parse_postfix())
        return left
    
    def parse_postfix(self):
        expr = self.parse_primary()
        while self.peek() and self.peek()[0] == 'LBRACK':
            self.consume('LBRACK')
            index = self.parse_expr()
            self.consume('RBRACK')
            expr = ('INDEX', expr, index)
        return expr
    
    def parse_primary(self):
        token = self.peek()
        if token[0] == 'MINUS':
            self.consume()
            operand = self.parse_primary()
            return ('MINUS', ('NUMBER', 0), operand)
        elif token[0] == 'NUMBER':
            self.consume()
            return ('NUMBER', int(token[1]))
        elif token[0] == 'STRING':
            self.consume()
            return ('STRING', token[1][1:-1])
        elif token[0] == 'LBRACK':
            return self.parse_list()
        elif token[0] == 'ID':
            name = self.consume()[1]
            if self.peek() and self.peek()[0] == 'LPAREN':
                return self.parse_call(name)
            return ('ID', name)
        elif token[0] == 'LPAREN':
            self.consume('LPAREN')
            expr = self.parse_expr()
            self.consume('RPAREN')
            return expr
        raise SyntaxError(f"Unexpected token: {token}")
    
    def parse_list(self):
        self.consume('LBRACK')
        elements = []
        while self.peek()[0] != 'RBRACK':
            elements.append(self.parse_expr())
            if self.peek()[0] == 'COMMA':
                self.consume('COMMA')
        self.consume('RBRACK')
        return ('LIST', elements)
    
    def parse_call(self, name):
        self.consume('LPAREN')
        args = []
        while self.peek()[0] != 'RPAREN':
            args.append(self.parse_expr())
            if self.peek()[0] == 'COMMA':
                self.consume('COMMA')
        self.consume('RPAREN')
        return ('CALL', name, args)


class Interpreter:
    def __init__(self):
        self.globals = {
            'print':    lambda *args: print(*[str(a) for a in args]),
            'len':      lambda x: len(x),
            'append':   lambda lst, item: lst + [item],
            'get':      lambda lst, i: lst[i] if lst is not None and 0 <= i < len(lst) else None,
            'set':      lambda lst, i, val: lst[:i] + [val] + lst[i+1:],
            'substr':   lambda s, start, end: s[start:end],
            'char_at':  lambda s, i: s[i] if 0 <= i < len(s) else "",
            'str_eq':   lambda a, b: 1 if a == b else 0,
            'str_cat':  lambda a, b: str(a) + str(b),
            'is_digit': lambda c: 1 if (c and c.isdigit()) else 0,
            'is_alpha': lambda c: 1 if (c and c.isalpha()) else 0,
            'is_space': lambda c: 1 if (c and c in ' \t\n') else 0,
            'int_val':  lambda s: int(s) if str(s).lstrip('-').isdigit() else 0,
            'to_str':   lambda n: str(n),
            'error':    lambda msg: (_ for _ in ()).throw(RuntimeError(msg)),
        }
        
    def run(self, ast):
        for stmt in ast:
            result = self.eval_stmt(stmt, self.globals)
            if result and result[0] == 'RETURN':
                return result[1]
    
    def eval_stmt(self, stmt, env):
        kind = stmt[0]
        if kind == 'LET':
            env[stmt[1]] = self.eval_expr(stmt[2], env)
        elif kind == 'FN':
            _, name, params, body = stmt
            env[name] = ('FUNCTION', params, body, env)
        elif kind == 'IF':
            _, cond, body, else_body = stmt
            if self.eval_expr(cond, env):
                for s in body:
                    r = self.eval_stmt(s, env)
                    if r and r[0] == 'RETURN': return r
            else:
                for s in else_body:
                    r = self.eval_stmt(s, env)
                    if r and r[0] == 'RETURN': return r
        elif kind == 'WHILE':
            _, cond, body = stmt
            while self.eval_expr(cond, env):
                for s in body:
                    r = self.eval_stmt(s, env)
                    if r and r[0] == 'RETURN': return r
        elif kind == 'RETURN':
            return ('RETURN', self.eval_expr(stmt[1], env))
        elif kind == 'EXPR':
            self.eval_expr(stmt[1], env)
    
    def eval_expr(self, expr, env):
        kind = expr[0]
        if kind == 'NUMBER': return expr[1]
        elif kind == 'STRING': return expr[1]
        elif kind == 'LIST':  return [self.eval_expr(e, env) for e in expr[1]]
        elif kind == 'ID':
            if expr[1] not in env:
                raise NameError(f"Undefined: {expr[1]}")
            return env[expr[1]]
        elif kind == 'INDEX':
            lst = self.eval_expr(expr[1], env)
            idx = self.eval_expr(expr[2], env)
            return lst[idx]
        elif kind == 'CALL':
            _, name, args = expr
            fn = env[name]
            vals = [self.eval_expr(a, env) for a in args]
            if callable(fn):
                return fn(*vals)
            _, params, body, fn_env = fn
            local = {**fn_env, **dict(zip(params, vals))}
            for s in body:
                r = self.eval_stmt(s, local)
                if r and r[0] == 'RETURN': return r[1]
            return None
        elif kind == 'PLUS':  return self.eval_expr(expr[1], env) + self.eval_expr(expr[2], env)
        elif kind == 'MINUS': return self.eval_expr(expr[1], env) - self.eval_expr(expr[2], env)
        elif kind == 'MULT':  return self.eval_expr(expr[1], env) * self.eval_expr(expr[2], env)
        elif kind == 'DIV':   return self.eval_expr(expr[1], env) // self.eval_expr(expr[2], env)
        elif kind == 'EQ':    return 1 if self.eval_expr(expr[1], env) == self.eval_expr(expr[2], env) else 0
        elif kind == 'NE':    return 1 if self.eval_expr(expr[1], env) != self.eval_expr(expr[2], env) else 0
        elif kind == 'LT':    return 1 if self.eval_expr(expr[1], env) <  self.eval_expr(expr[2], env) else 0
        elif kind == 'GT':    return 1 if self.eval_expr(expr[1], env) >  self.eval_expr(expr[2], env) else 0
        elif kind == 'LE':    return 1 if self.eval_expr(expr[1], env) <= self.eval_expr(expr[2], env) else 0
        elif kind == 'GE':    return 1 if self.eval_expr(expr[1], env) >= self.eval_expr(expr[2], env) else 0
        elif kind == 'AND':   return self.eval_expr(expr[1], env) and self.eval_expr(expr[2], env)
        elif kind == 'OR':    return self.eval_expr(expr[1], env) or  self.eval_expr(expr[2], env)
        raise RuntimeError(f"Unknown expr: {expr}")

def run_code(code: str):
    tokens = Lexer(code).tokenize()
    ast    = Parser(tokens).parse()
    Interpreter().run(ast)


# -----------------------------------------------------------------------------
# THE SELF-HOSTED LAYER
# A recursive-descent parser written in the language itself.
# It handles:
#   . Multi-digit numbers
#   . + - * /  with correct precedence  (mul/div binds tighter)
#   . Parenthesised sub-expressions nested arbitrarily deep
#   . Unary minus
#
# The inner parser passes a mutable "state" list [pos] around
# so each function can advance the cursor and return both a value
# AND the updated position.
# -----------------------------------------------------------------------------

self_hosted_code = r'''
# -----------------------------------------------------------------------------
# Self-hosted recursive-descent arithmetic parser
#
# Design: every parse function returns a triple  [value, new_pos, ok]
# so callers can thread position through the recursion without mutation.
# The language has no break/else, so loops use tail-recursive helpers.
# -----------------------------------------------------------------------------

# Tokenizer

fn skip_spaces(code, i) {
    let n = len(code)
    if i < n {
        if is_space(char_at(code, i)) {
            return skip_spaces(code, i + 1)
        }
    }
    return i
}

fn scan_number(code, i) {
    let n = len(code)
    if i < n {
        if is_digit(char_at(code, i)) {
            return scan_number(code, i + 1)
        }
    }
    return i
}

fn tokenize_loop(code, i, tokens) {
    let n = len(code)
    let i = skip_spaces(code, i)
    if i >= n {
        return tokens
    }

    let c = char_at(code, i)

    if is_digit(c) {
        let end = scan_number(code, i)
        let num_str = substr(code, i, end)
        return tokenize_loop(code, end, append(tokens, ["NUM", int_val(num_str)]))
    }
    if str_eq(c, "+") {
        return tokenize_loop(code, i + 1, append(tokens, ["PLUS", 0]))
    }
    if str_eq(c, "-") {
        return tokenize_loop(code, i + 1, append(tokens, ["MINUS", 0]))
    }
    if str_eq(c, "*") {
        return tokenize_loop(code, i + 1, append(tokens, ["MULT", 0]))
    }
    if str_eq(c, "/") {
        return tokenize_loop(code, i + 1, append(tokens, ["DIV", 0]))
    }
    if str_eq(c, "(") {
        return tokenize_loop(code, i + 1, append(tokens, ["LPAREN", 0]))
    }
    if str_eq(c, ")") {
        return tokenize_loop(code, i + 1, append(tokens, ["RPAREN", 0]))
    }
    # Unknown char - skip
    return tokenize_loop(code, i + 1, tokens)
}

fn tokenize(code) {
    return tokenize_loop(code, 0, [])
}

# Token helpers

fn tok_type(tokens, pos) {
    let tok = get(tokens, pos)
    if tok == 0 {
        return "EOF"
    }
    return get(tok, 0)
}

fn tok_val(tokens, pos) {
    let tok = get(tokens, pos)
    if tok == 0 {
        return 0
    }
    return get(tok, 1)
}

# -- parse_primary: NUMBER | LPAREN expr RPAREN | MINUS primary --
# Returns [value, new_pos]

fn parse_primary(tokens, pos) {
    let tt = tok_type(tokens, pos)

    if str_eq(tt, "NUM") {
        return [tok_val(tokens, pos), pos + 1]
    }
    if str_eq(tt, "LPAREN") {
        let inner = parse_expr(tokens, pos + 1)
        let val   = get(inner, 0)
        let npos  = get(inner, 1)
        # consume RPAREN
        return [val, npos + 1]
    }
    if str_eq(tt, "MINUS") {
        let inner = parse_primary(tokens, pos + 1)
        let val   = get(inner, 0)
        let npos  = get(inner, 1)
        return [0 - val, npos]
    }
    return [0, pos + 1]
}

# -- parse_term_loop: left-associative * / chain --

fn parse_term_loop(tokens, pos, left) {
    let tt = tok_type(tokens, pos)

    if str_eq(tt, "MULT") {
        let rhs  = parse_primary(tokens, pos + 1)
        let rval = get(rhs, 0)
        let rpos = get(rhs, 1)
        return parse_term_loop(tokens, rpos, left * rval)
    }
    if str_eq(tt, "DIV") {
        let rhs  = parse_primary(tokens, pos + 1)
        let rval = get(rhs, 0)
        let rpos = get(rhs, 1)
        return parse_term_loop(tokens, rpos, left / rval)
    }
    return [left, pos]
}

fn parse_term(tokens, pos) {
    let lhs  = parse_primary(tokens, pos)
    let lval = get(lhs, 0)
    let lpos = get(lhs, 1)
    return parse_term_loop(tokens, lpos, lval)
}

# -- parse_expr_loop: left-associative + - chain --

fn parse_expr_loop(tokens, pos, left) {
    let tt = tok_type(tokens, pos)

    if str_eq(tt, "PLUS") {
        let rhs  = parse_term(tokens, pos + 1)
        let rval = get(rhs, 0)
        let rpos = get(rhs, 1)
        return parse_expr_loop(tokens, rpos, left + rval)
    }
    if str_eq(tt, "MINUS") {
        let rhs  = parse_term(tokens, pos + 1)
        let rval = get(rhs, 0)
        let rpos = get(rhs, 1)
        return parse_expr_loop(tokens, rpos, left - rval)
    }
    return [left, pos]
}

fn parse_expr(tokens, pos) {
    let lhs  = parse_term(tokens, pos)
    let lval = get(lhs, 0)
    let lpos = get(lhs, 1)
    return parse_expr_loop(tokens, lpos, lval)
}

# -- Top-level --

fn evaluate(code) {
    let tokens = tokenize(code)
    let result = parse_expr(tokens, 0)
    return get(result, 0)
}

# -- Test harness --

fn run_test(expr, expected) {
    let got = evaluate(expr)
    if got == expected {
        print(str_cat(str_cat(str_cat("  PASS  ", expr), "  =>  "), to_str(got)))
    }
    if got != expected {
        print(str_cat(str_cat(str_cat(str_cat(str_cat(
            "  FAIL  ", expr), "  got "), to_str(got)),
            "  expected "), to_str(expected)))
    }
}

print("*** Self-hosted recursive-descent arithmetic parser ***")
print("")
print("")
print("Single numbers:")
run_test("42", 42)
run_test("100", 100)
run_test("0", 0)
print("")
print("Basic arithmetic:")
run_test("3 + 4", 7)
run_test("10 - 3", 7)
run_test("6 * 7", 42)
run_test("20 / 4", 5)
print("")
print("Operator precedence (* / before + -):")
run_test("2 + 3 * 4", 14)
run_test("10 - 2 * 3", 4)
run_test("2 * 3 + 4 * 5", 26)
run_test("100 / 10 + 3 * 7", 31)
print("")
print("Parentheses override precedence:")
run_test("(2 + 3) * 4", 20)
run_test("2 * (3 + 4)", 14)
run_test("(10 - 2) * (3 + 1)", 32)
print("")
print("Deeply nested:")
run_test("((2 + 3) * (4 - 1)) + 7", 22)
run_test("(((10)))", 10)
run_test("2 * (3 * (4 * (5 * 1)))", 120)
run_test("((1 + 2) * (3 + 4)) * ((5 - 3) * (6 / 2))", 126)
print("")
print("Unary minus:")
run_test("-5 + 10", 5)
run_test("-(3 + 4)", -7)
run_test("-2 * -3", 6)
run_test("10 + -4", 6)
print("")
print("Chained operations (left-associativity):")
run_test("1 + 2 + 3 + 4 + 5", 15)
run_test("100 / 2 / 5", 10)
run_test("2 * 3 * 4 * 5", 120)
run_test("20 - 5 - 3 - 2", 10)
'''


if __name__ == '__main__':
    print("\nBootstrap: language interpreting a real parser of itself")
    print("-" * 56)
    print()
    run_code(self_hosted_code)
    print()
    print("Done. The inner parser is genuine recursive descent.\n")
