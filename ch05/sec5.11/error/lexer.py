import re
from error_reporter import ErrorReporter, ErrorSeverity, ErrorCategory, get_suggestion

TOKEN_SPEC = [
    ("COMMENT", r"#.*"),
    ("STRING", r'"(?:[^"\\]|\\.)*"'),
    ("UNTERMINATED_STRING", r'"(?:[^"\\]|\\.)*$'),
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

def tokenize(code, error_reporter=None):
    """Tokenize source code with error reporting"""
    if error_reporter is None:
        error_reporter = ErrorReporter(code)
    
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
        elif kind == "UNTERMINATED_STRING":
            error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.LEXICAL,
                "Unterminated string literal",
                line=line_num,
                column=column,
                suggestion=get_suggestion("unterminated_string")
            )
            # Try to recover by treating it as a string anyway
            value = value[1:]  # strip opening quote
            kind = "STRING"
        elif kind == "MISMATCH":
            error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.LEXICAL,
                f"Unexpected character '{value}'",
                line=line_num,
                column=column,
                suggestion=get_suggestion("invalid_character")
            )
            continue
        elif kind == "IDENTIFIER":
            # Check for common typos in keywords
            lower_value = value.lower()
            if lower_value in KEYWORDS and value != lower_value:
                error_reporter.report(
                    ErrorSeverity.WARNING,
                    ErrorCategory.LEXICAL,
                    f"Keyword '{lower_value}' should be lowercase",
                    line=line_num,
                    column=column,
                    suggestion=f"Use '{lower_value}' instead of '{value}'"
                )
                value = lower_value
            
            if value in KEYWORDS:
                kind = value.upper()
        elif kind == "STRING":
            value = value[1:-1]  # strip quotes
            # Unescape common escape sequences
            value = value.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
        elif kind == "NUMBER":
            # Validate number format
            if value.count('.') > 1:
                error_reporter.report(
                    ErrorSeverity.ERROR,
                    ErrorCategory.LEXICAL,
                    f"Invalid number format: '{value}' (multiple decimal points)",
                    line=line_num,
                    column=column,
                    suggestion=get_suggestion("invalid_number")
                )
                # Try to use the first part
                value = value.split('.')[0] + '.' + value.split('.')[1]
            
            try:
                value = float(value) if '.' in value else int(value)
            except ValueError:
                error_reporter.report(
                    ErrorSeverity.ERROR,
                    ErrorCategory.LEXICAL,
                    f"Invalid number format: '{value}'",
                    line=line_num,
                    column=column,
                    suggestion=get_suggestion("invalid_number")
                )
                value = 0  # Default value for error recovery
        
        tokens.append(Token(kind, value, line_num, column))
    
    return tokens

if __name__ == "__main__":
    sample = '''
let x = 42;
Let name = "Alice;  # unterminated string and wrong case
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
    reporter = ErrorReporter(sample)
    tokens = tokenize(sample, reporter)
    
    print("Tokens:")
    for token in tokens:
        print(f"  {token}")
    
    print("\n" + "="*70)
    reporter.print_report()
