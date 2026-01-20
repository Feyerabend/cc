import re

# token types with improved regular expressions
TOKEN_TYPES = [
    ("KEYWORD_CONST", r'\bconst\b'),
    ("KEYWORD_VAR", r'\bvar\b'),
    ("KEYWORD_PROCEDURE", r'\bprocedure\b'),
    ("KEYWORD_CALL", r'\bcall\b'),
    ("KEYWORD_ODD", r'\bodd\b'),
    ("KEYWORD_IF", r'\bif\b'),
    ("KEYWORD_THEN", r'\bthen\b'),
    ("KEYWORD_WHILE", r'\bwhile\b'),
    ("KEYWORD_DO", r'\bdo\b'),
    ("KEYWORD_BEGIN", r'\bbegin\b'),
    ("KEYWORD_END", r'\bend\b'),
    ("OPERATOR_ASSIGN", r':='),
    ("OPERATOR_EQUAL", r'='),
    ("OPERATOR_NOT_EQUAL", r'#'),
    ("OPERATOR_LT", r'<'),
    ("OPERATOR_LE", r'<='),
    ("OPERATOR_GT", r'>'),
    ("OPERATOR_GE", r'>='),
    ("OPERATOR_PLUS", r'\+'),
    ("OPERATOR_MINUS", r'-'),
    ("OPERATOR_STAR", r'\*'),
    ("OPERATOR_SLASH", r'/'),
    ("DELIM_COMMA", r','),
    ("DELIM_SEMICOLON", r';'),
    ("DELIM_PERIOD", r'\.'),
    ("DELIM_LPAREN", r'\('),
    ("DELIM_RPAREN", r'\)'),
    ("NUMBER", r'\b\d+\b'),
    ("IDENT", r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
    ("WHITESPACE", r'\s+'),
    ("MISMATCH", r'.'),  # any unexpected character
]

# compile the regular expressions into a master pattern
master_pattern = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_TYPES))

def tokenize(code):
    tokens = []
    line_number = 1
    column_number = 1
    warnings = []
    errors = []

    for mo in master_pattern.finditer(code):
        kind = mo.lastgroup
        value = mo.group()
        
        # track line and column positions
        start_pos = mo.start()
        line_start = code.rfind("\n", 0, start_pos) + 1
        line_end = code.find("\n", start_pos)
        line_end = line_end if line_end != -1 else len(code)
        current_line = code[line_start:line_end]

        # update line number and column number
        line_number = code.count("\n", 0, start_pos) + 1
        column_number = start_pos - line_start + 1

        # debug print statements to see what the tokenizer is processing
        print(f"Processing: '{value}' (Line: {line_number}, Column: {column_number})")
        
        if kind == 'WHITESPACE':
            continue  # skip whitespaces
        elif kind == 'MISMATCH':
            errors.append((line_number, column_number, f"Unexpected character: '{value}' at line {line_number}, column {column_number}"))
            # debug print to check error location
            print(f"Error: Unexpected character at Line {line_number}, Column {column_number}: '{value}'")
        elif kind in {'NUMBER', 'IDENT'} and value.isupper():
            warnings.append((line_number, column_number, f"Warning: Identifier '{value}' is uppercase at line {line_number}, column {column_number}"))
        else:
            tokens.append((kind, value))

    # raise errors if there are any
    if errors:
        for error in errors:
            print(f"ERROR: {error[2]}")
        raise RuntimeError("Tokenization failed due to errors.")
    
    # print warnings
    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning[2]}")
    
    return tokens


# Test invalid cases
source_code_with_invalid_operator = """
const n = 13;
var i, h;
procedure sub;
const k = 7;
var j;
begin
    j !! n;
end.
"""

source_code_with_missing_semicolon = """
const n = 13
var i, h;
procedure sub;
const k = 7;
var j;
begin
    j := n;
end.
"""

source_code_with_unescaped_character = """
const n = 13;
var i, h;
procedure sub;
const k = 7;
var j;
begin
    j := n \;
end.
"""

# Try tokenizing the erroneous code
try:
    print("Tokenizing code with invalid operator:")
    tokens = tokenize(source_code_with_invalid_operator)
    for token in tokens:
        print(token)
except RuntimeError as e:
    print(str(e))

try:
    print("\nTokenizing code with missing semicolon:")
    tokens = tokenize(source_code_with_missing_semicolon)
    for token in tokens:
        print(token)
except RuntimeError as e:
    print(str(e))

try:
    print("\nTokenizing code with unescaped character:")
    tokens = tokenize(source_code_with_unescaped_character)
    for token in tokens:
        print(token)
except RuntimeError as e:
    print(str(e))


