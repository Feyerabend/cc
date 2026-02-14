"""
Lexical analysis (tokenization) for BASIC code.
Converts source text into a stream of tokens.
"""
from dataclasses import dataclass
from typing import List, Set
from ..core.exceptions import TokenizationError


@dataclass
class Token:
    """Represents a single token from the source code."""
    type: str
    value: str
    position: int

    def __repr__(self) -> str:
        return f"Token({self.type}, '{self.value}', pos={self.position})"


class Tokenizer:
    """Converts BASIC source code into tokens."""
    
    # Reserved keywords that have special meaning
    KEYWORDS: Set[str] = {
        "to", "step", "next", "for", "if", "then", "else",
        "goto", "gosub", "return", "end", "while", "wend"
    }
    
    # Two-character operators
    TWO_CHAR_OPERATORS: Set[str] = {"<=", ">=", "<>"}

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.length = len(text)
        self.tokens: List[Token] = []
        self.errors: List[str] = []

    def tokenize(self) -> List[Token]:
        """Tokenize the entire input text."""
        while self.pos < self.length:
            self._skip_whitespace()
            if self.pos >= self.length:
                break

            char = self.text[self.pos]
            
            # Dispatch to appropriate tokenizer method
            if char.isdigit() or char == '.':
                self._tokenize_number()
            elif char.isalpha() or char == '_':
                self._tokenize_identifier()
            elif char in '"\'':
                self._tokenize_string()
            elif char in '+-*/=<>':
                self._tokenize_operator()
            elif char == '(':
                self._add_token("LPAREN", "(")
            elif char == ')':
                self._add_token("RPAREN", ")")
            elif char == ',':
                self._add_token("COMMA", ",")
            elif char in ';:':
                self._add_token(char, char)
            else:
                self.errors.append(f"Unexpected character at position {self.pos}: {char}")
                self.pos += 1
        
        if self.errors:
            raise TokenizationError("; ".join(self.errors))
        
        return self.tokens

    def _skip_whitespace(self) -> None:
        """Skip over whitespace characters."""
        while self.pos < self.length and self.text[self.pos].isspace():
            self.pos += 1

    def _add_token(self, token_type: str, value: str) -> None:
        """Add a token and advance position."""
        self.tokens.append(Token(token_type, value, self.pos))
        self.pos += len(value)

    def _tokenize_number(self) -> None:
        """Tokenize a numeric literal."""
        start = self.pos
        has_decimal = False

        while self.pos < self.length:
            char = self.text[self.pos]
            if char == '.' and not has_decimal:
                has_decimal = True
                self.pos += 1
            elif char.isdigit():
                self.pos += 1
            else:
                break

        number_str = self.text[start:self.pos]
        try:
            float(number_str)  # Validate it's a valid number
            self.tokens.append(Token("NUMBER", number_str, start))
        except ValueError:
            self.errors.append(f"Invalid number format at position {start}: {number_str}")

    def _tokenize_identifier(self) -> None:
        """Tokenize an identifier or keyword."""
        start = self.pos
        
        # Read alphanumeric characters, underscores, and dollar signs
        while self.pos < self.length and (
            self.text[self.pos].isalnum() or self.text[self.pos] in "_$"
        ):
            self.pos += 1
        
        identifier = self.text[start:self.pos]
        
        # Determine if it's a keyword or identifier
        token_type = "KEYWORD" if identifier.lower() in self.KEYWORDS else "IDENTIFIER"
        self.tokens.append(Token(token_type, identifier, start))

    def _tokenize_string(self) -> None:
        """Tokenize a string literal."""
        start = self.pos
        quote_char = self.text[self.pos]
        self.pos += 1

        # Read until closing quote
        while self.pos < self.length and self.text[self.pos] != quote_char:
            self.pos += 1

        if self.pos >= self.length:
            self.errors.append(f"Unterminated string literal at position {start}")
            return

        self.pos += 1  # Skip closing quote
        string_value = self.text[start:self.pos]
        self.tokens.append(Token("STRING", string_value, start))

    def _tokenize_operator(self) -> None:
        """Tokenize an operator (including multi-character operators)."""
        start = self.pos
        
        # Check for two-character operators
        if self.pos + 1 < self.length:
            two_char = self.text[self.pos:self.pos + 2]
            if two_char in self.TWO_CHAR_OPERATORS:
                self.tokens.append(Token("OPERATOR", two_char, start))
                self.pos += 2
                return
        
        # Single-character operator
        self.tokens.append(Token("OPERATOR", self.text[self.pos], start))
        self.pos += 1
