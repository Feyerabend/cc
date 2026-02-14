import math
import random
from typing import Any
from basic_expressions import (
    Expression, NumberExpression, StringExpression, VariableExpression,
    BinaryExpression, FunctionExpression, ArrayExpression
)
from basic_shared import InterpreterState

class Evaluator:
    def __init__(self, state: InterpreterState):
        self.state = state

    def evaluate(self, expr: Expression) -> Any:
        if isinstance(expr, NumberExpression):
            return expr.value
        elif isinstance(expr, StringExpression):
            return expr.value
        elif isinstance(expr, VariableExpression):
            return self.state.variables.get(expr.name, 0)
        elif isinstance(expr, BinaryExpression):
            return self.evaluate_binary(expr)
        elif isinstance(expr, FunctionExpression):
            return self.evaluate_function(expr)
        elif isinstance(expr, ArrayExpression):
            indices = [int(self.evaluate(idx)) for idx in expr.indices]
            if expr.name not in self.state.arrays:
                raise ValueError(f"Array '{expr.name}' not declared")
            # Adjust for 1-based indexing
            adjusted_indices = [idx - 1 for idx in indices]
            index_tuple = tuple(adjusted_indices)
            dims = self.state.array_dims.get(expr.name, ())
            if len(indices) != len(dims):
                raise ValueError(f"Array '{expr.name}' expects {len(dims)} indices, got {len(indices)}")
            for i, idx in enumerate(indices):
                if not (1 <= idx <= dims[i] - 1):
                    raise ValueError(f"Index {idx} out of bounds for array '{expr.name}' dimension {i}")
            print(f"DEBUG: Accessing array {expr.name} at indices {indices} -> adjusted {adjusted_indices}") # ----<
            return self.state.arrays[expr.name].get(index_tuple, 0)
        raise ValueError(f"Unknown expression type: {type(expr)}")

    def evaluate_binary(self, expr: BinaryExpression) -> Any:
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)
        
        if expr.operator in ["+", "-", "*", "/"]:
            if not (isinstance(left, (int, float)) and isinstance(right, (int, float))):
                raise ValueError(f"Arithmetic operator '{expr.operator}' requires numeric operands")
            if expr.operator == "+":
                return left + right
            elif expr.operator == "-":
                return left - right
            elif expr.operator == "*":
                return left * right
            elif expr.operator == "/":
                return left / right if right != 0 else 0
        
        if expr.operator in ["=", "<>", "<", ">", "<=", ">="]:
            # Make sure we compare compatible types
            if isinstance(left, str) and isinstance(right, str):
                # String comparison
                if expr.operator == "=":
                    return 1 if left == right else 0
                elif expr.operator == "<>":
                    return 1 if left != right else 0
                elif expr.operator == "<":
                    return 1 if left < right else 0
                elif expr.operator == ">":
                    return 1 if left > right else 0
                elif expr.operator == "<=":
                    return 1 if left <= right else 0
                elif expr.operator == ">=":
                    return 1 if left >= right else 0
            elif isinstance(left, (int, float)) and isinstance(right, (int, float)):
                # Numeric comparison
                if expr.operator == "=":
                    return 1 if left == right else 0
                elif expr.operator == "<>":
                    return 1 if left != right else 0
                elif expr.operator == "<":
                    return 1 if left < right else 0
                elif expr.operator == ">":
                    return 1 if left > right else 0
                elif expr.operator == "<=":
                    return 1 if left <= right else 0
                elif expr.operator == ">=":
                    return 1 if left >= right else 0
            else:
                # Different types cannot be compared in most cases
                raise ValueError(f"Cannot compare {type(left).__name__} with {type(right).__name__}")
        
        raise ValueError(f"Unknown operator: {expr.operator}")

    def evaluate_function(self, expr: FunctionExpression) -> Any:
        args = [self.evaluate(arg) for arg in expr.args]
        name = expr.name.lower()
        
        math_functions = {
            "sin": lambda x: math.sin(x[0]) if len(x) == 1 else math.sin(0),
            "cos": lambda x: math.cos(x[0]) if len(x) == 1 else math.cos(0),
            "tan": lambda x: math.tan(x[0]) if len(x) == 1 else math.tan(0),
            "atn": lambda x: math.atan(x[0]) if len(x) == 1 else math.atan(0),
            "abs": lambda x: abs(x[0]) if len(x) == 1 else 0,
            "sqr": lambda x: math.sqrt(x[0]) if len(x) == 1 and x[0] >= 0 else 0,
            "log": lambda x: math.log(x[0]) if len(x) == 1 and x[0] > 0 else 0,
            "exp": lambda x: math.exp(x[0]) if len(x) == 1 else 0,
            "int": lambda x: int(x[0]) if len(x) == 1 else 0,
        }
        
        string_functions = {
            "left$": lambda x: x[0][:int(x[1])] if len(x) == 2 and isinstance(x[0], str) else "",
            "right$": lambda x: x[0][-int(x[1]):] if len(x) == 2 and isinstance(x[0], str) else "",
            "mid$": lambda x: x[0][int(x[1])-1:int(x[1])-1+int(x[2])] if len(x) >= 3 and isinstance(x[0], str) else "",
            "len": lambda x: len(x[0]) if len(x) == 1 and isinstance(x[0], str) else 0,
            "str$": lambda x: str(x[0]) if len(x) == 1 else "",
            "val": lambda x: float(x[0]) if len(x) == 1 and isinstance(x[0], str) else 0,
            "chr$": lambda x: chr(int(x[0])) if len(x) == 1 and isinstance(x[0], (int, float)) else "",
            "asc": lambda x: ord(x[0][0]) if len(x) == 1 and isinstance(x[0], str) and x[0] else 0,
        }

        if name == "rnd":
            if len(args) == 0:
                return random.random()
            elif len(args) == 1 and isinstance(args[0], (int, float)):
                random.seed(args[0])
                return random.random()
            return 0
        
        if name in math_functions:
            result = math_functions[name](args)
            print(f"DEBUG: Evaluated function {name} with args {args} to {result}")
            return result
        if name in string_functions:
            result = string_functions[name](args)
            print(f"DEBUG: Evaluated function {name} with args {args} to {result}")
            return result
        
        raise ValueError(f"Unknown function: {name}")
