import re
from typing import List, Tuple

TOKENS = [
    ('CLASS', r'\bclass\b'),
    ('INHERITS', r'\binherits\b'),
    ('DEF', r'\bdef\b'),
    ('PRINT', r'\bprint\b'),
    ('STRING', r'"[^"]*"'),
    ('ID', r'[A-Za-z_][A-Za-z0-9_]*'),
    ('LBRACE', r'\{'),
    ('RBRACE', r'\}'),
    ('LPAREN', r'\('),
    ('RPAREN', r'\)'),
    ('SEMI', r';'),
    ('SKIP', r'\s+'),
]

def lex(src: str) -> List[Tuple[str, str]]:
    """Tokenize source code. Returns list of (token_type, value) tuples."""
    tokens = []
    pos = 0
    while pos < len(src):
        for tok_type, pattern in TOKENS:
            regex = re.compile(pattern)
            match = regex.match(src, pos)
            if match:
                if tok_type != 'SKIP':
                    tokens.append((tok_type, match.group(0)))
                pos = match.end()
                break
        else:
            raise SyntaxError(f"Unexpected char: {src[pos]}")
    return tokens
