from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

class Expression(ABC):
    @abstractmethod
    def __str__(self) -> str:
        pass

class NumberExpression(Expression):
    def __init__(self, value: float):
        self.value = value
    
    def __str__(self) -> str:
        return str(self.value)

class StringExpression(Expression):
    def __init__(self, value: str):
        self.value = value
    
    def __str__(self) -> str:
        return f'"{self.value}"'

class VariableExpression(Expression):
    def __init__(self, name: str):
        self.name = name
    
    def __str__(self) -> str:
        return self.name

class BinaryExpression(Expression):
    def __init__(self, left: Expression, operator: str, right: Expression):
        self.left = left
        self.operator = operator
        self.right = right
    
    def __str__(self) -> str:
        return f"({self.left} {self.operator} {self.right})"

@dataclass
class ArrayExpression(Expression):
    name: str
    indices: List[Expression]

    def __str__(self) -> str:
        indices_str = ", ".join(str(index) for index in self.indices)
        return f"{self.name}({indices_str})"

class FunctionExpression(Expression):
    def __init__(self, name: str, args: List[Expression]):
        self.name = name
        self.args = args
    
    def __str__(self) -> str:
        args_str = ", ".join(str(arg) for arg in self.args)
        return f"{self.name}({args_str})"
