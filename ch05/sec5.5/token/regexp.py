import re

class RegexpTokenizer:
    def __init__(self):
        self.token_patterns = [
            ("IDENTIFIER", r"[a-zA-Z_][a-zA-Z0-9_]*"),
            ("NUMBER", r"\d+"),
            ("OPERATOR", r"[+\-*/=]"),
            ("WHITESPACE", r"\s+"), # ignore
        ]
        # combine patterns into single regex
        self.regex = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in self.token_patterns))

    def tokenize(self, input_string):
        tokens = []
        for match in self.regex.finditer(input_string):
            # which token matched
            token_type = match.lastgroup
            token_value = match.group(token_type)
            if token_type != "WHITESPACE": # skip
                tokens.append((token_type, token_value))
        return tokens


tokenizer = RegexpTokenizer()
print(tokenizer.tokenize("x = 42 + y * 5"))
