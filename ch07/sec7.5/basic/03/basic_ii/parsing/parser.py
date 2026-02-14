"""
Syntax analysis (parsing) for BASIC expressions.
Converts tokens into an abstract syntax tree (AST).
"""
from typing import List
from ..parsing.tokenizer import Token
from ..expressions.ast import (
    Expression, NumberExpression, StringExpression, VariableExpression,
    BinaryExpression, ArrayExpression, FunctionExpression
)
from ..core.exceptions import ParserError


class ExpressionParser:
    """Parses tokens into expression AST nodes using recursive descent."""
    
    # Built-in BASIC functions
    BUILTIN_FUNCTIONS = {
        # Math functions
        "sin", "cos", "tan", "atn", "abs", "sqr", "log", "exp", "int", "rnd",
        # String functions
        "left$", "right$", "mid$", "len", "str$", "val", "chr$", "asc"
    }

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.length = len(tokens)

    def parse(self) -> Expression:
        """Parse the token stream into an expression."""
        if self.pos >= self.length:
            return NumberExpression(0.0)
        return self._parse_expression()

    def parse_number(self) -> NumberExpression:
        """Parse a number token into a NumberExpression."""
        if self.pos < self.length and self.tokens[self.pos].type == "NUMBER":
            token = self.tokens[self.pos]
            self.pos += 1
            return NumberExpression(float(token.value))
        return NumberExpression(0.0)

    # Expression parsing with operator precedence
    # Precedence (lowest to highest): comparison, addition/subtraction, multiplication/division, primary

    def _parse_expression(self) -> Expression:
        """Parse a complete expression (entry point)."""
        return self._parse_comparison()

    def _parse_comparison(self) -> Expression:
        """Parse comparison operators: =, <>, <, >, <=, >="""
        left = self._parse_additive()
        
        while self._match_operator(["=", "<>", "<", ">", "<=", ">="]):
            op = self._previous().value
            right = self._parse_additive()
            left = BinaryExpression(left, op, right)
        
        return left

    def _parse_additive(self) -> Expression:
        """Parse addition and subtraction: +, -"""
        left = self._parse_multiplicative()
        
        while self._match_operator(["+", "-"]):
            op = self._previous().value
            right = self._parse_multiplicative()
            left = BinaryExpression(left, op, right)
        
        return left

    def _parse_multiplicative(self) -> Expression:
        """Parse multiplication and division: *, /"""
        left = self._parse_primary()
        
        while self._match_operator(["*", "/"]):
            op = self._previous().value
            right = self._parse_primary()
            left = BinaryExpression(left, op, right)
        
        return left

    def _parse_primary(self) -> Expression:
        """Parse primary expressions: numbers, strings, variables, functions, arrays, parentheses."""
        if self.pos >= self.length:
            return NumberExpression(0.0)

        token = self._current()
        
        # Handle unary minus (e.g., -X, -5)
        if token.type == "OPERATOR" and token.value == "-":
            self.pos += 1
            # Parse the operand
            operand = self._parse_primary()
            # Return as 0 - operand
            return BinaryExpression(NumberExpression(0), "-", operand)
        
        # Handle unary plus (just skip it)
        if token.type == "OPERATOR" and token.value == "+":
            self.pos += 1
            return self._parse_primary()

        # Number literal
        if token.type == "NUMBER":
            self.pos += 1
            return NumberExpression(float(token.value))

        # String literal
        if token.type == "STRING":
            self.pos += 1
            # Remove quotes
            return StringExpression(token.value[1:-1])

        # Identifier (variable, function, or array)
        if token.type == "IDENTIFIER":
            return self._parse_identifier()

        # Parenthesized expression
        if token.type == "LPAREN":
            return self._parse_parenthesized()

        raise ParserError(f"Unexpected token at position {token.position}: {token.value}")

    def _parse_identifier(self) -> Expression:
        """Parse an identifier: could be variable, function call, or array access."""
        name_token = self._current()
        name = name_token.value
        self.pos += 1

        # Check if followed by parentheses
        if self.pos < self.length and self._current().type == "LPAREN":
            # Function call or array access
            if self._is_builtin_function(name):
                return self._parse_function_call(name)
            elif self._is_user_function(name):
                # User-defined function (FNxxx)
                return self._parse_function_call(name)
            else:
                # Array access
                return self._parse_array_access(name)

        # Check if it's a zero-argument function
        if self._is_builtin_function(name):
            return FunctionExpression(name, [])

        # Simple variable
        return VariableExpression(name)

    def _parse_function_call(self, name: str) -> FunctionExpression:
        """Parse a function call: FUNC(arg1, arg2, ...)"""
        self._expect("LPAREN")
        args = self._parse_argument_list()
        self._expect("RPAREN")
        return FunctionExpression(name, args)

    def _parse_array_access(self, name: str) -> ArrayExpression:
        """Parse array access: ARRAY(idx1, idx2, ...)"""
        self._expect("LPAREN")
        indices = self._parse_argument_list()
        self._expect("RPAREN")
        return ArrayExpression(name, indices)

    def _parse_parenthesized(self) -> Expression:
        """Parse a parenthesized expression: (expr)"""
        self._expect("LPAREN")
        expr = self._parse_expression()
        self._expect("RPAREN")
        return expr

    def _parse_argument_list(self) -> List[Expression]:
        """Parse a comma-separated list of expressions."""
        args = []

        # Empty argument list
        if self.pos < self.length and self._current().type == "RPAREN":
            return args

        # Parse arguments
        while True:
            args.append(self._parse_expression())

            if self.pos >= self.length:
                break

            if self._current().type == "COMMA":
                self.pos += 1
                # Check for trailing comma
                if self.pos < self.length and self._current().type == "RPAREN":
                    raise ParserError(f"Unexpected RPAREN after comma")
            elif self._current().type == "RPAREN":
                break
            else:
                raise ParserError(
                    f"Expected ',' or ')' at position {self._current().position}"
                )

        return args

    # Helper methods

    def _current(self) -> Token:
        """Get current token."""
        if self.pos >= self.length:
            raise ParserError("Unexpected end of input")
        return self.tokens[self.pos]

    def _previous(self) -> Token:
        """Get previous token."""
        return self.tokens[self.pos - 1]

    def _match_operator(self, operators: List[str]) -> bool:
        """Check if current token is an operator in the given list."""
        if self.pos >= self.length:
            return False
        token = self.tokens[self.pos]
        if token.type == "OPERATOR" and token.value in operators:
            self.pos += 1
            return True
        return False

    def _expect(self, token_type: str) -> Token:
        """Expect a specific token type and consume it."""
        if self.pos >= self.length:
            raise ParserError(f"Expected {token_type}, got end of input")
        token = self.tokens[self.pos]
        if token.type != token_type:
            raise ParserError(
                f"Expected {token_type} at position {token.position}, got {token.type}"
            )
        self.pos += 1
        return token

    def _is_builtin_function(self, name: str) -> bool:
        """Check if name is a built-in function."""
        return name.lower() in self.BUILTIN_FUNCTIONS
    
    def _is_user_function(self, name: str) -> bool:
        """Check if name is a user-defined function (starts with FN)."""
        return name.upper().startswith("FN") and len(name) >= 3
