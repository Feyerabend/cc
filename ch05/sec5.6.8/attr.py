import re
from dataclasses import dataclass


# Lexer

TOKEN_SPEC = [
    ("INT",   r"\d+"),
    ("ID",    r"[a-zA-Z_][a-zA-Z0-9_]*"),
    ("PLUS",  r"\+"),
    ("MUL",   r"\*"),
    ("COLON", r":"),
    ("EQ",    r"="),
    ("SEMI",  r";"),
    ("SKIP",  r"[ \t\n]+"),
    ("MISMATCH", r"."),
]

KEYWORDS = {"let", "i32"}

token_re = re.compile("|".join(
    f"(?P<{name}>{regex})" for name, regex in TOKEN_SPEC
))

@dataclass
class Token:
    type: str
    value: str

def lex(code):
    tokens = []
    for m in token_re.finditer(code):
        kind = m.lastgroup
        value = m.group()
        if kind == "ID" and value in KEYWORDS:
            kind = value.upper()
        if kind == "SKIP":
            continue
        if kind == "MISMATCH":
            raise SyntaxError(f"Unexpected: {value}")
        tokens.append(Token(kind, value))
    return tokens


# Parser + Attributes

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.env = {}  # symbol table: name -> type

    def peek(self):
        return self.tokens[self.pos]

    def eat(self, kind):
        tok = self.peek()
        if tok.type != kind:
            raise SyntaxError(f"Expected {kind}, got {tok.type}")
        self.pos += 1
        return tok

    # Program -> Stmt*
    def program(self):
        while self.pos < len(self.tokens):
            self.stmt()

    # Stmt -> let ID : i32 = Expr ;
    def stmt(self):
        self.eat("LET")
        name = self.eat("ID").value
        self.eat("COLON")
        self.eat("I32")
        self.eat("EQ")

        expr = self.expr()

        self.eat("SEMI")

        # Attribute action:
        # Define variable in environment
        if expr["type"] != "i32":
            raise TypeError("Only i32 supported")
        self.env[name] = "i32"

        print(f"declare {name}: i32 = {expr['value']}")

    # Expr -> Term ( + Term )*
    def expr(self):
        left = self.term()
        while self.pos < len(self.tokens) and self.peek().type == "PLUS":
            self.eat("PLUS")
            right = self.term()

            # Attribute rules:
            left = {
                "type": "i32",
                "value": left["value"] + right["value"]
            }
        return left

    # Term -> Factor ( * Factor )*
    def term(self):
        left = self.factor()
        while self.pos < len(self.tokens) and self.peek().type == "MUL":
            self.eat("MUL")
            right = self.factor()

            left = {
                "type": "i32",
                "value": left["value"] * right["value"]
            }
        return left

    # Factor -> INT | ID
    def factor(self):
        tok = self.peek()
        if tok.type == "INT":
            self.eat("INT")
            return {"type": "i32", "value": int(tok.value)}

        elif tok.type == "ID":
            name = self.eat("ID").value
            if name not in self.env:
                raise NameError(f"Undefined variable {name}")
            # Value unknown at compile-time, mock with 0
            return {"type": self.env[name], "value": 0}

        else:
            raise SyntaxError(f"Unexpected token {tok.type}")


# Test

code = """
let x: i32 = 10 + 5;
let y: i32 = x * 2;
let z: i32 = 3 * 4 + 1;
"""

tokens = lex(code)
parser = Parser(tokens)
parser.program()

print("\nSymbol table:")
for k, v in parser.env.items():
    print(f"{k}: {v}")

