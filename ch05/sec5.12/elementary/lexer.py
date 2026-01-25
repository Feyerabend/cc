import re

TOKEN_SPEC = [
    ("COMMENT", r"#.*"),
    ("STRING", r'"(?:[^"\\]|\\.)*"'),
    ("NUMBER", r"\d+(\.\d+)?"),
    ("IDENTIFIER", r"[a-zA-Z_]\w*"),
    ("EQ", r"=="),
    ("NE", r"!="),
    ("LE", r"<="),
    ("GE", r">="),
    ("LT", r"<"),
    ("GT", r">"),
    ("ASSIGN", r"="),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("TIMES", r"\*"),
    ("DIVIDE", r"/"),
    ("MOD", r"%"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("LBRACE", r"\{"),
    ("RBRACE", r"\}"),
    ("COMMA", r","),
    ("SEMICOLON", r";"),
    ("NEWLINE", r"\n"),
    ("SKIP", r"[ \t]+"),
    ("MISMATCH", r"."),
]

KEYWORDS = {
    "let", "if", "else", "while", "print", "input", "fn", "return"
}

class Token:
    def __init__(self, kind, value, line, column):
        self.kind = kind
        self.value = value
        self.line = line
        self.column = column
    
    def __repr__(self):
        return f"Token({self.kind}, {self.value!r}, {self.line}:{self.column})"

def tokenize(code):
    token_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC)
    token_re = re.compile(token_regex)
    tokens = []
    line_num = 1
    line_start = 0
    
    for match in token_re.finditer(code):
        kind = match.lastgroup
        value = match.group()
        column = match.start() - line_start + 1
        
        if kind == "COMMENT" or kind == "SKIP":
            continue
        elif kind == "NEWLINE":
            line_num += 1
            line_start = match.end()
            continue
        elif kind == "MISMATCH":
            raise SyntaxError(f"Unexpected character '{value}' at {line_num}:{column}")
        elif kind == "IDENTIFIER" and value in KEYWORDS:
            kind = value.upper()
        elif kind == "STRING":
            value = value[1:-1]  # strip quotes
        elif kind == "NUMBER":
            value = float(value) if '.' in value else int(value)
        
        tokens.append(Token(kind, value, line_num, column))
    
    return tokens

if __name__ == "__main__":
    sample = '''
let x = 42;
let name = "Alice";
print("Hello, " + name);

if x > 10 {
    print("x is large");
}

let i = 0;
while i < 5 {
    print(i);
    i = i + 1;
}
'''
    tokens = tokenize(sample)
    for token in tokens:
        print(token)
