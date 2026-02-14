"""
Expression abstract syntax tree (AST) nodes.
Defines the structure of parsed expressions.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Any


class Expression(ABC):
    """Base class for all expression types."""
    
    @abstractmethod
    def __repr__(self) -> str:
        """Return string representation of the expression."""
        pass


@dataclass
class NumberExpression(Expression):
    """Numeric literal expression."""
    value: float

    def __repr__(self) -> str:
        return f"Number({self.value})"


@dataclass
class StringExpression(Expression):
    """String literal expression."""
    value: str

    def __repr__(self) -> str:
        return f'String("{self.value}")'


@dataclass
class VariableExpression(Expression):
    """Variable reference expression."""
    name: str

    def __repr__(self) -> str:
        return f"Var({self.name})"


@dataclass
class BinaryExpression(Expression):
    """Binary operation expression (e.g., a + b, x < y)."""
    left: Expression
    operator: str
    right: Expression

    def __repr__(self) -> str:
        return f"Binary({self.left} {self.operator} {self.right})"


@dataclass
class ArrayExpression(Expression):
    """Array access expression (e.g., A(1,2))."""
    name: str
    indices: List[Expression]

    def __repr__(self) -> str:
        indices_str = ", ".join(repr(idx) for idx in self.indices)
        return f"Array({self.name}[{indices_str}])"


@dataclass
class FunctionExpression(Expression):
    """Function call expression (e.g., SIN(X), LEFT$("hello", 2))."""
    name: str
    args: List[Expression]

    def __repr__(self) -> str:
        args_str = ", ".join(repr(arg) for arg in self.args)
        return f"Function({self.name}({args_str}))"
