from typing import List, Optional
from basic_tokenizer import Token
from basic_expressions import (
    Expression, NumberExpression, StringExpression, VariableExpression,
    BinaryExpression, ArrayExpression, FunctionExpression
)
from basic_shared import ParserError

RESERVED_FUNCTIONS = {
    "sin", "cos", "tan", "atn", "abs", "sqr", "log", "exp", "int", "rnd",
    "left$", "right$", "mid$", "len", "str$", "val", "chr$", "asc"
}

def is_reserved_function(name: str) -> bool:
    return name.lower() in RESERVED_FUNCTIONS

class ParseBasic:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.length = len(tokens)

    def parse(self) -> Expression:
        if self.pos >= self.length:
            return NumberExpression(0)
        expr = self.parse_expression()
        return expr

    def parse_number(self) -> NumberExpression:
        if self.pos < self.length and self.tokens[self.pos].type == "NUMBER":
            token = self.tokens[self.pos]
            self.pos += 1
            return NumberExpression(float(token.value))
        return NumberExpression(0)

    def parse_expression(self) -> Expression:
        try:
            expr = self.parse_comparison()
            print(f"DEBUG: Parsed expression: {expr}")
            return expr
        except Exception as e:
            print(f"DEBUG: Error parsing expression: {e}")
            return NumberExpression(0)  # Return default on error

    def parse_comparison(self) -> Expression:
        left = self.parse_term()
        while self.pos < self.length and self.tokens[self.pos].type == "OPERATOR" and self.tokens[self.pos].value in ["=", "<>", "<", ">", "<=", ">="]:
            op = self.tokens[self.pos].value
            self.pos += 1
            right = self.parse_term()
            left = BinaryExpression(left, op, right)
        return left

    def parse_term(self) -> Expression:
        left = self.parse_factor()
        while self.pos < self.length and self.tokens[self.pos].type == "OPERATOR" and self.tokens[self.pos].value in ["+", "-"]:
            op = self.tokens[self.pos].value
            self.pos += 1
            right = self.parse_factor()
            left = BinaryExpression(left, op, right)
        return left

    def parse_factor(self) -> Expression:
        left = self.parse_primary()
        while self.pos < self.length and self.tokens[self.pos].type == "OPERATOR" and self.tokens[self.pos].value in ["*", "/"]:
            op = self.tokens[self.pos].value
            self.pos += 1
            right = self.parse_primary()
            left = BinaryExpression(left, op, right)
        return left

    def parse_primary(self) -> Expression:
        if self.pos >= self.length:
            return NumberExpression(0)

        token = self.tokens[self.pos]
        handlers = {
            "NUMBER": self._parse_number,
            "STRING": self._parse_string,
            "IDENTIFIER": self._parse_identifier,
            "LPAREN": self._parse_parenthesized
        }

        handler = handlers.get(token.type)
        if handler:
            return handler(token)
        
        raise ParserError(f"Unexpected token at position {token.position}: {token.value}")

    def _parse_number(self, token: Token) -> NumberExpression:
        self.pos += 1
        return NumberExpression(float(token.value))

    def _parse_string(self, token: Token) -> StringExpression:
        self.pos += 1
        return StringExpression(token.value[1:-1])

    def _parse_identifier(self, token: Token) -> Expression:
        self.pos += 1
        name = token.value

        if self.pos < self.length and self.tokens[self.pos].type == "LPAREN":
            if is_reserved_function(name):
                return self._parse_function(name, token.position)
            return self._parse_array(name, token.position)

        if is_reserved_function(name):
            return FunctionExpression(name, [])
        return VariableExpression(name)

    def _parse_parenthesized(self, token: Token) -> Expression:
        self.pos += 1  #  LPAREN
        expr = self.parse_expression()
        if self.pos >= self.length or self.tokens[self.pos].type != "RPAREN":
            raise ParserError(f"Expected RPAREN at position {token.position}")
        self.pos += 1  #  RPAREN
        return expr

    def _parse_function(self, name: str, position: int) -> FunctionExpression:
        self.pos += 1  #  LPAREN
        args = self._parse_arguments(position)
        if self.pos >= self.length or self.tokens[self.pos].type != "RPAREN":
            raise ParserError(f"Expected RPAREN at position {position}")
        self.pos += 1  #  RPAREN
        return FunctionExpression(name, args)

    def _parse_array(self, name: str, position: int) -> ArrayExpression:
        try:
            self.pos += 1  # LPAREN
            indices = self._parse_arguments(position)
            if self.pos >= self.length or self.tokens[self.pos].type != "RPAREN":
                raise ParserError(f"Expected RPAREN at position {position}")
            self.pos += 1  # RPAREN
            return ArrayExpression(name, indices)
        except Exception as e:
            print(f"DEBUG: Error parsing array '{name}': {e}")
            return ArrayExpression(name, [NumberExpression(0)])

    def _parse_arguments(self, position: int) -> List[Expression]:
        args = []
        if self.pos >= self.length or self.tokens[self.pos].type == "RPAREN":
            return args

        while self.pos < self.length and self.tokens[self.pos].type != "RPAREN":
            arg = self.parse_expression()
            args.append(arg)
            if self.pos >= self.length:
                raise ParserError(f"Expected ',' or RPAREN at position {position}, reached end of input")
            current_token = self.tokens[self.pos]
            if current_token.type == "COMMA":
                self.pos += 1
                if self.pos >= self.length:
                    raise ParserError(f"Unexpected end after comma at position {current_token.position}")
                if self.tokens[self.pos].type == "RPAREN":
                    raise ParserError(f"Unexpected RPAREN after comma at position {self.tokens[self.pos].position}")
            elif current_token.type != "RPAREN":
                raise ParserError(f"Expected ',' or RPAREN at position {current_token.position}, found {current_token.value}")

        return args

def create_parser(tokens: List[Token]) -> ParseBasic:
    return ParseBasic(tokens)
