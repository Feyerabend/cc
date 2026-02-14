import re

from dataclasses import dataclass
from typing import List

@dataclass
class Token:
    type: str
    value: str
    position: int

class Tokenizer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.length = len(text)
        self.tokens: List[Token] = []
        self.errors: List[str] = []
        self.keywords = {"to", "step", "next", "for", "if", "then", "else", "goto", "gosub", "return", "end"}

    def tokenize(self) -> List[Token]:
        while self.pos < self.length:
            self.skip_whitespace()
            if self.pos >= self.length:
                break

            char = self.text[self.pos]
            
            if char.isdigit() or char == '.':
                self.tokenize_number()
            elif char.isalpha() or char == '_':
                self.tokenize_identifier()
            elif char in '"\'':
                self.tokenize_string()
            elif char in '+-*/=<>':
                self.tokenize_operator()
            elif char == '(':
                self.tokens.append(Token("LPAREN", "(", self.pos))
                self.pos += 1
            elif char == ')':
                self.tokens.append(Token("RPAREN", ")", self.pos))
                self.pos += 1
            elif char in ',;:':
                self.tokens.append(Token(char, char, self.pos))
                self.pos += 1
            else:
                self.errors.append(f"Unexpected character at position {self.pos}: {char}")
                self.pos += 1
            
        return self.tokens

    def skip_whitespace(self):
        while self.pos < self.length and self.text[self.pos].isspace():
            self.pos += 1

    def tokenize_number(self):
        start = self.pos
        decimal_point = False

        while self.pos < self.length:
            if self.text[self.pos] == '.' and not decimal_point:
                decimal_point = True
            elif not self.text[self.pos].isdigit():
                break
            self.pos += 1

        number_str = self.text[start:self.pos]
        try:
            float(number_str)
            self.tokens.append(Token("NUMBER", number_str, start))
        except ValueError:
            self.errors.append(f"Invalid number format at position {start}: {number_str}")

    def tokenize_identifier(self):
        start = self.pos
        while self.pos < self.length and (self.text[self.pos].isalnum() or self.text[self.pos] in "_$"):
            self.pos += 1
        identifier = self.text[start:self.pos]
        if identifier.lower() in self.keywords:
            self.tokens.append(Token("KEYWORD", identifier, start))
        else:
            self.tokens.append(Token("IDENTIFIER", identifier, start))

        self.skip_whitespace()
        if self.pos < self.length and self.text[self.pos] == '(':
            self.tokens.append(Token("LPAREN", "(", self.pos))
            self.pos += 1

    def tokenize_string(self):
        start = self.pos
        quote_char = self.text[self.pos]
        self.pos += 1

        while self.pos < self.length and self.text[self.pos] != quote_char:
            self.pos += 1

        if self.pos >= self.length:
            self.errors.append(f"Unterminated string literal at position {start}")
            return

        self.pos += 1
        string_value = self.text[start:self.pos]
        self.tokens.append(Token("STRING", string_value, start))

    def tokenize_operator(self):
        start = self.pos
        if self.pos + 1 < self.length:
            two_char_op = self.text[self.pos:self.pos+2]
            if two_char_op in ["<=", ">=", "<>"]:
                self.tokens.append(Token("OPERATOR", two_char_op, start))
                self.pos += 2
                return

        self.tokens.append(Token("OPERATOR", self.text[self.pos], start))
        self.pos += 1
