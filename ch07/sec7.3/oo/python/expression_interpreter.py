"""
Translation and modernisation of the 1999 Java expression interpreter.

Grammar (prefix / S-expression notation):
    expr  ::= NUMBER | IDENT | (~ expr) | (OP expr expr)
    OP    ::= + | - | * | / | %

Example:
    (+ (/ p q) (* 2 (- p (% p q))))
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Iterator



# Context  (variable store)

class Context:
    """Holds variable bindings (name → int)."""

    def __init__(self) -> None:
        self._bindings: dict[str, int] = {}

    def assign(self, var: "VariableExp", value: int) -> None:
        self._bindings[str(var)] = value

    def lookup(self, name: str) -> int:
        try:
            return self._bindings[name]
        except KeyError:
            raise NameError(f"Undefined variable: '{name}'") from None

    def __repr__(self) -> str:  # pragma: no cover
        items = ", ".join(f"{k}={v}" for k, v in self._bindings.items())
        return f"Context({items})"


# AST  (abstract syntax tree)

class NumberExp(ABC):
    """Abstract base for all expression nodes."""

    @abstractmethod
    def evaluate(self, ctx: Context) -> int: ...

    @abstractmethod
    def replace(self, name: str, expr: "NumberExp") -> "NumberExp": ...

    @abstractmethod
    def copy(self) -> "NumberExp": ...

    @abstractmethod
    def __str__(self) -> str: ...

    # Operator overloads so you can compose expressions naturally in Python
    def __add__(self, other: "NumberExp") -> "PlusExp": return PlusExp(self, other)
    def __sub__(self, other: "NumberExp") -> "MinusExp": return MinusExp(self, other)
    def __mul__(self, other: "NumberExp") -> "MultiplyExp": return MultiplyExp(self, other)
    def __truediv__(self, other: "NumberExp") -> "DivideExp": return DivideExp(self, other)
    def __mod__(self, other: "NumberExp") -> "ModuloExp": return ModuloExp(self, other)
    def __neg__(self) -> "UnaryMinusExp": return UnaryMinusExp(self)


class IntegerExp(NumberExp):
    def __init__(self, value: int) -> None:
        self._value = value

    def evaluate(self, ctx: Context) -> int:
        return self._value

    def replace(self, name: str, expr: NumberExp) -> NumberExp:
        return IntegerExp(self._value)

    def copy(self) -> NumberExp:
        return IntegerExp(self._value)

    def __str__(self) -> str:
        return str(self._value)


class VariableExp(NumberExp):
    def __init__(self, name: str) -> None:
        self._name = name

    def evaluate(self, ctx: Context) -> int:
        return ctx.lookup(self._name)

    def replace(self, name: str, expr: NumberExp) -> NumberExp:
        return expr.copy() if name == self._name else VariableExp(self._name)

    def copy(self) -> NumberExp:
        return VariableExp(self._name)

    def __str__(self) -> str:
        return self._name


class UnaryMinusExp(NumberExp):
    def __init__(self, operand: NumberExp) -> None:
        self._op = operand

    def evaluate(self, ctx: Context) -> int:
        return -self._op.evaluate(ctx)

    def replace(self, name: str, expr: NumberExp) -> NumberExp:
        return UnaryMinusExp(self._op.replace(name, expr))

    def copy(self) -> NumberExp:
        return UnaryMinusExp(self._op.copy())

    def __str__(self) -> str:
        return f"(~ {self._op})"


class _BinaryExp(NumberExp):
    """Internal mixin for binary operators — avoids copy-paste across subclasses."""

    symbol: str  # override in subclass

    def __init__(self, left: NumberExp, right: NumberExp) -> None:
        self._left = left
        self._right = right

    def replace(self, name: str, expr: NumberExp) -> NumberExp:
        return type(self)(self._left.replace(name, expr), self._right.replace(name, expr))

    def copy(self) -> NumberExp:
        return type(self)(self._left.copy(), self._right.copy())

    def __str__(self) -> str:
        return f"({self.symbol} {self._left} {self._right})"


class PlusExp(_BinaryExp):
    symbol = "+"
    def evaluate(self, ctx: Context) -> int:
        return self._left.evaluate(ctx) + self._right.evaluate(ctx)


class MinusExp(_BinaryExp):
    symbol = "-"
    def evaluate(self, ctx: Context) -> int:
        return self._left.evaluate(ctx) - self._right.evaluate(ctx)


class MultiplyExp(_BinaryExp):
    symbol = "*"
    def evaluate(self, ctx: Context) -> int:
        return self._left.evaluate(ctx) * self._right.evaluate(ctx)


class EvaluationError(ArithmeticError):
    """Raised for runtime evaluation errors (e.g. division by zero)."""


class DivideExp(_BinaryExp):
    symbol = "/"
    def evaluate(self, ctx: Context) -> int:
        divisor = self._right.evaluate(ctx)
        if divisor == 0:
            raise EvaluationError("Division by zero.")
        return self._left.evaluate(ctx) // divisor  # integer division matches Java


class ModuloExp(_BinaryExp):
    symbol = "%"
    def evaluate(self, ctx: Context) -> int:
        divisor = self._right.evaluate(ctx)
        if divisor == 0:
            raise EvaluationError("Modulo by zero.")
        return self._left.evaluate(ctx) % divisor



# Lexer

class TokenKind(Enum):
    IDENT    = auto()
    NUMBER   = auto()
    UMINUS   = auto()
    PLUS     = auto()
    MINUS    = auto()
    MULTIPLY = auto()
    DIVIDE   = auto()
    MODULO   = auto()
    LPAREN   = auto()
    RPAREN   = auto()
    EOF      = auto()
    UNKNOWN  = auto()


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    value: int | str | None = field(default=None)

    def __str__(self) -> str:  # pragma: no cover
        if self.value is not None:
            return f"{self.kind.name}({self.value!r})"
        return self.kind.name


_SINGLE_CHAR: dict[str, TokenKind] = {
    "~": TokenKind.UMINUS,
    "+": TokenKind.PLUS,
    "-": TokenKind.MINUS,
    "*": TokenKind.MULTIPLY,
    "/": TokenKind.DIVIDE,
    "%": TokenKind.MODULO,
    "(": TokenKind.LPAREN,
    ")": TokenKind.RPAREN,
}

_TOKEN_RE = re.compile(
    r"(?P<IDENT>[A-Za-z][A-Za-z0-9]*)"
    r"|(?P<NUMBER>\d+)"
    r"|(?P<OP>[~+\-*/%()])"
    r"|(?P<WS>\s+)"
    r"|(?P<UNKNOWN>.)"
)


class LexError(SyntaxError):
    pass


def tokenise(source: str) -> Iterator[Token]:
    """Yield Token objects from *source*, skipping whitespace."""
    for m in _TOKEN_RE.finditer(source):
        if m.lastgroup == "WS":
            continue
        elif m.lastgroup == "IDENT":
            yield Token(TokenKind.IDENT, m.group())
        elif m.lastgroup == "NUMBER":
            yield Token(TokenKind.NUMBER, int(m.group()))
        elif m.lastgroup == "OP":
            yield Token(_SINGLE_CHAR[m.group()])
        else:
            raise LexError(f"Unexpected character: {m.group()!r}")
    yield Token(TokenKind.EOF)



# Parser

class ParseError(SyntaxError):
    pass


class Parser:
    """
    Recursive-descent parser for prefix / S-expression arithmetic.

    Grammar:
        expr  ::= IDENT
                | NUMBER
                | '(' '~' expr ')'
                | '(' OP expr expr ')'
        OP    ::= '+' | '-' | '*' | '/' | '%'
    """

    def __init__(self, source: str) -> None:
        self._tokens = list(tokenise(source))
        self._pos = 0

    # helpers

    @property
    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        tok = self._current
        if tok.kind is not TokenKind.EOF:
            self._pos += 1
        return tok

    def _expect(self, kind: TokenKind) -> Token:
        tok = self._advance()
        if tok.kind is not kind:
            raise ParseError(f"Expected {kind.name}, got {tok}")
        return tok

    # recursive descent

    def parse(self) -> NumberExp:
        expr = self._parse_expr()
        if self._current.kind is not TokenKind.EOF:
            raise ParseError(f"Unexpected token after expression: {self._current}")
        return expr

    def _parse_expr(self) -> NumberExp:
        tok = self._current

        if tok.kind is TokenKind.IDENT:
            self._advance()
            return VariableExp(tok.value)  # type: ignore[arg-type]

        if tok.kind is TokenKind.NUMBER:
            self._advance()
            return IntegerExp(tok.value)  # type: ignore[arg-type]

        if tok.kind is TokenKind.LPAREN:
            self._advance()  # consume '('
            inner = self._parse_inner()
            self._expect(TokenKind.RPAREN)
            return inner

        raise ParseError(f"Unexpected token: {tok}")

    def _parse_inner(self) -> NumberExp:
        """Parse the operator + operands inside a parenthesised expression."""
        tok = self._advance()  # consume operator token

        _BINARY: dict[TokenKind, type[_BinaryExp]] = {
            TokenKind.PLUS:     PlusExp,
            TokenKind.MINUS:    MinusExp,
            TokenKind.MULTIPLY: MultiplyExp,
            TokenKind.DIVIDE:   DivideExp,
            TokenKind.MODULO:   ModuloExp,
        }

        if tok.kind is TokenKind.UMINUS:
            operand = self._parse_expr()
            return UnaryMinusExp(operand)

        if tok.kind in _BINARY:
            left  = self._parse_expr()
            right = self._parse_expr()
            return _BINARY[tok.kind](left, right)

        raise ParseError(f"Expected operator inside parentheses, got {tok}")



# Convenience helper

def evaluate(source: str, **variables: int) -> int:
    """
    Parse *source* and evaluate it with the given variable bindings.

    >>> evaluate("(+ (/ p q) (* 2 (- p (% p q))))", p=12, q=4)
    27
    """
    ctx = Context()
    for name, val in variables.items():
        ctx.assign(VariableExp(name), val)
    expr = Parser(source).parse()
    return expr.evaluate(ctx)



if __name__ == "__main__":

    print()
    print("Example a: simple addition")
    print()
    src = "(+ 5 3)"
    expr = Parser(src).parse()
    print(f"{expr} -> {expr.evaluate(Context())}")
    print()

    print()
    print("Example b: variables  p=12, q=4")
    print()
    ctx = Context()
    p, q = VariableExp("p"), VariableExp("q")
    ctx.assign(p, 12)
    ctx.assign(q, 4)
    src = "(+ (/ p q) (* 2 (- p (% p q))))"
    expr = Parser(src).parse()
    print(f"p <- {ctx.lookup('p')}")
    print(f"q <- {ctx.lookup('q')}")
    print(f"{expr} -> {expr.evaluate(ctx)}")
    # 12/4 + 2*(12 - 12%4) = 3 + 24 = 27
    print()

    print()
    print("Example c: unary minus  a=7, b=3")
    print()
    result = evaluate("(+ (* a b) (~ b))", a=7, b=3)
    print(f"(+ (* a b) (~ b)) -> {result}")
    # 7*3 + (-3) = 18
    print()

    print()
    print("Example d: division by zero  z=0")
    print()
    ctx2 = Context()
    z = VariableExp("z")
    ctx2.assign(z, 0)
    expr2 = Parser("(/ 10 z)").parse()
    print(f"z <- {ctx2.lookup('z')}")
    try:
        print(f"{expr2} -> {expr2.evaluate(ctx2)}")
    except EvaluationError as exc:
        print(f"EvaluationError: {exc}")
    print()

    print()
    print("Example e: Python operator overloads (no parsing needed)")
    print()
    # Build the same tree as example 2 programmatically
    p2, q2 = VariableExp("p"), VariableExp("q")
    tree = (p2 / q2) + IntegerExp(2) * (p2 - (p2 % q2))
    ctx3 = Context()
    ctx3.assign(p2, 12)
    ctx3.assign(q2, 4)
    print(f"{tree} -> {tree.evaluate(ctx3)}")
    print()

