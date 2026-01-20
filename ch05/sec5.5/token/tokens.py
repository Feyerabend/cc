import re

# reserved
KEYWORDS = {
    'const': 'CONST',
    'var': 'VAR',
    'procedure': 'PROCEDURE',
    'call': 'CALL',
    'begin': 'BEGIN',
    'end': 'END',
    'if': 'IF',
    'then': 'THEN',
    'while': 'WHILE',
    'odd': 'ODD',
}

TOKEN_SPECIFICATIONS = [
    ('NUMBER', r'\d+'),          # Integer
    ('IDENT', r'[a-zA-Z_][a-zA-Z0-9_]*'),  # Identifier
    ('ASSIGN', r':='),           # Assignment
    ('PERIOD', r'\.'),           # Period (.)
    ('COMMA', r','),             # Comma
    ('SEMICOLON', r';'),         # Semicolon
    ('LPAREN', r'\('),           # Left Parenthesis
    ('RPAREN', r'\)'),           # Right Parenthesis
    ('PLUS', r'\+'),             # Plus
    ('MINUS', r'-'),             # Minus
    ('STAR', r'\*'),             # Multiplication
    ('SLASH', r'/'),             # Division
    ('EQUAL', r'='),             # Equal
    ('NEQUAL', r'#'),            # Not Equal
    ('LT', r'<'),                # Less Than
    ('LE', r'<='),               # Less Than or Equal
    ('GT', r'>'),                # Greater Than
    ('GE', r'>='),               # Greater Than or Equal
    ('QUESTION', r'\?'),         # Question mark
    ('BANG', r'!'),              # Exclamation mark
    ('WHITESPACE', r'\s+'),      # Whitespace (ignored)
    ('NEWLINE', r'\n'),          # Newline (ignored)
]

def tokenize(code):
    tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in TOKEN_SPECIFICATIONS)
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        
        if kind == 'WHITESPACE' or kind == 'NEWLINE':
            continue
        elif kind == 'IDENT' and value in KEYWORDS:
            kind = KEYWORDS[value]  # Replace identifier with keyword type
        yield kind, value


# Example usage:
code = "x := 5 ."
tokens = list(tokenize(code))
# Output tokens in the desired format
formatted_tokens = [(kind, value) for kind, value in tokens]
print(formatted_tokens)
