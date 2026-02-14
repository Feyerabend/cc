"""
Expression evaluation for BASIC.
Evaluates AST nodes to produce runtime values.
"""
import math
import random
from typing import Any, Tuple
from ..expressions.ast import (
    Expression, NumberExpression, StringExpression, VariableExpression,
    BinaryExpression, ArrayExpression, FunctionExpression
)
from ..core.state import InterpreterState
from ..core.exceptions import EvaluationError, ArrayError


class ExpressionEvaluator:
    """Evaluates expression AST nodes against interpreter state."""

    def __init__(self, state: InterpreterState, debug: bool = False):
        self.state = state
        self.debug = debug

    def evaluate(self, expr: Expression) -> Any:
        """Evaluate an expression and return its value."""
        if isinstance(expr, NumberExpression):
            return expr.value

        elif isinstance(expr, StringExpression):
            return expr.value

        elif isinstance(expr, VariableExpression):
            return self.state.get_variable(expr.name, 0)

        elif isinstance(expr, BinaryExpression):
            return self._evaluate_binary(expr)

        elif isinstance(expr, ArrayExpression):
            return self._evaluate_array(expr)

        elif isinstance(expr, FunctionExpression):
            return self._evaluate_function(expr)

        raise EvaluationError(f"Unknown expression type: {type(expr).__name__}")

    def _evaluate_binary(self, expr: BinaryExpression) -> Any:
        """Evaluate binary operations."""
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)
        op = expr.operator

        # Arithmetic operators
        if op in ["+", "-", "*", "/"]:
            return self._evaluate_arithmetic(op, left, right)

        # Comparison operators
        if op in ["=", "<>", "<", ">", "<=", ">="]:
            return self._evaluate_comparison(op, left, right)

        raise EvaluationError(f"Unknown operator: {op}")

    def _evaluate_arithmetic(self, op: str, left: Any, right: Any) -> float:
        """Evaluate arithmetic operations."""
        if not (isinstance(left, (int, float)) and isinstance(right, (int, float))):
            raise EvaluationError(
                f"Arithmetic operator '{op}' requires numeric operands, "
                f"got {type(left).__name__} and {type(right).__name__}"
            )

        operations = {
            "+": lambda l, r: l + r,
            "-": lambda l, r: l - r,
            "*": lambda l, r: l * r,
            "/": lambda l, r: l / r if r != 0 else 0
        }

        return operations[op](left, right)

    def _evaluate_comparison(self, op: str, left: Any, right: Any) -> int:
        """Evaluate comparison operations. Returns 1 for true, 0 for false."""
        # Type compatibility check
        if type(left) != type(right):
            if not (isinstance(left, (int, float)) and isinstance(right, (int, float))):
                raise EvaluationError(
                    f"Cannot compare {type(left).__name__} with {type(right).__name__}"
                )

        operations = {
            "=": lambda l, r: l == r,
            "<>": lambda l, r: l != r,
            "<": lambda l, r: l < r,
            ">": lambda l, r: l > r,
            "<=": lambda l, r: l <= r,
            ">=": lambda l, r: l >= r
        }

        result = operations[op](left, right)
        return 1 if result else 0

    def _evaluate_array(self, expr: ArrayExpression) -> Any:
        """Evaluate array access."""
        # Evaluate indices
        indices = [int(self.evaluate(idx)) for idx in expr.indices]

        # Check if array exists
        if expr.name not in self.state.arrays:
            raise ArrayError(f"Array '{expr.name}' not declared")

        # Get array dimensions
        dims = self.state.array_dims.get(expr.name, ())

        # Validate index count
        if len(indices) != len(dims):
            raise ArrayError(
                f"Array '{expr.name}' expects {len(dims)} indices, got {len(indices)}"
            )

        # Validate index bounds (1-based indexing in BASIC)
        for i, idx in enumerate(indices):
            if not (1 <= idx <= dims[i]):
                raise ArrayError(
                    f"Index {idx} out of bounds for array '{expr.name}' dimension {i} "
                    f"(valid range: 1 to {dims[i]})"
                )

        # Convert to 0-based indexing for internal storage
        adjusted_indices = tuple(idx - 1 for idx in indices)

        if self.debug:
            print(f"DEBUG: Array access {expr.name}{indices} -> {adjusted_indices}")

        return self.state.get_array_value(expr.name, adjusted_indices, 0)

    def _evaluate_function(self, expr: FunctionExpression) -> Any:
        """Evaluate built-in function calls."""
        args = [self.evaluate(arg) for arg in expr.args]
        name = expr.name.lower()

        # Check for user-defined functions first (FNxxx)
        if expr.name.upper().startswith("FN"):
            return self._evaluate_user_function(expr.name.upper(), args)

        # Special case: RND function
        if name == "rnd":
            if len(args) == 0:
                result = random.random()
            elif len(args) == 1 and isinstance(args[0], (int, float)):
                random.seed(int(args[0]))
                result = random.random()
            else:
                result = 0
            if self.debug:
                print(f"DEBUG: RND({args}) = {result}")
            return result

        # Math functions
        result = self._try_math_function(name, args)
        if result is not None:
            if self.debug:
                print(f"DEBUG: {name.upper()}({args}) = {result}")
            return result

        # String functions
        result = self._try_string_function(name, args)
        if result is not None:
            if self.debug:
                print(f"DEBUG: {name.upper()}({args}) = {result}")
            return result

        raise EvaluationError(f"Unknown function: {name}")
    
    def _evaluate_user_function(self, func_name: str, args: list) -> Any:
        """Evaluate user-defined function (DEF FN)."""
        if not hasattr(self.state, 'user_functions'):
            raise EvaluationError(f"User function {func_name} not defined")
        
        if func_name not in self.state.user_functions:
            raise EvaluationError(f"User function {func_name} not defined")
        
        func_def = self.state.user_functions[func_name]
        params = func_def['params']
        expression_str = func_def['expression']
        
        # Check argument count
        if len(args) != len(params):
            raise EvaluationError(
                f"Function {func_name} expects {len(params)} arguments, got {len(args)}"
            )
        
        # Save current variable values for parameters
        saved_values = {}
        for param in params:
            if param in self.state.variables:
                saved_values[param] = self.state.variables[param]
        
        try:
            # Bind arguments to parameters
            for param, arg_value in zip(params, args):
                self.state.set_variable(param, arg_value)
            
            # Evaluate the function expression
            from ..parsing.tokenizer import Tokenizer
            from ..parsing.parser import ExpressionParser
            
            tokenizer = Tokenizer(expression_str)
            tokens = tokenizer.tokenize()
            parser = ExpressionParser(tokens)
            expr = parser.parse()
            result = self.evaluate(expr)
            
            if self.debug:
                print(f"DEBUG: {func_name}({args}) = {result}")
            
            return result
        
        finally:
            # Restore original variable values
            for param in params:
                if param in saved_values:
                    self.state.set_variable(param, saved_values[param])
                else:
                    # Remove if it didn't exist before
                    if param in self.state.variables:
                        del self.state.variables[param]

    def _try_math_function(self, name: str, args: list) -> Any:
        """Try to evaluate as a math function."""
        math_functions = {
            "sin": (1, lambda x: math.sin(x[0])),
            "cos": (1, lambda x: math.cos(x[0])),
            "tan": (1, lambda x: math.tan(x[0])),
            "atn": (1, lambda x: math.atan(x[0])),
            "abs": (1, lambda x: abs(x[0])),
            "sqr": (1, lambda x: math.sqrt(x[0]) if x[0] >= 0 else 0),
            "log": (1, lambda x: math.log(x[0]) if x[0] > 0 else 0),
            "exp": (1, lambda x: math.exp(x[0])),
            "int": (1, lambda x: int(x[0]))
        }

        if name in math_functions:
            expected_args, func = math_functions[name]
            if len(args) == expected_args:
                try:
                    return func(args)
                except (ValueError, TypeError, OverflowError):
                    return 0
            return 0

        return None

    def _try_string_function(self, name: str, args: list) -> Any:
        """Try to evaluate as a string function."""
        string_functions = {
            "left$": self._func_left,
            "right$": self._func_right,
            "mid$": self._func_mid,
            "len": self._func_len,
            "str$": self._func_str,
            "val": self._func_val,
            "chr$": self._func_chr,
            "asc": self._func_asc
        }

        if name in string_functions:
            return string_functions[name](args)

        return None

    # String function implementations

    def _func_left(self, args: list) -> str:
        """LEFT$(str, n) - leftmost n characters."""
        if len(args) == 2 and isinstance(args[0], str):
            return args[0][:int(args[1])]
        return ""

    def _func_right(self, args: list) -> str:
        """RIGHT$(str, n) - rightmost n characters."""
        if len(args) == 2 and isinstance(args[0], str):
            return args[0][-int(args[1]):]
        return ""

    def _func_mid(self, args: list) -> str:
        """MID$(str, start, len) - substring starting at position start."""
        if len(args) >= 3 and isinstance(args[0], str):
            start = int(args[1]) - 1  # 1-based to 0-based
            length = int(args[2])
            return args[0][start:start + length]
        return ""

    def _func_len(self, args: list) -> int:
        """LEN(str) - length of string."""
        if len(args) == 1 and isinstance(args[0], str):
            return len(args[0])
        return 0

    def _func_str(self, args: list) -> str:
        """STR$(num) - convert number to string."""
        if len(args) == 1:
            return str(args[0])
        return ""

    def _func_val(self, args: list) -> float:
        """VAL(str) - convert string to number."""
        if len(args) == 1 and isinstance(args[0], str):
            try:
                return float(args[0])
            except ValueError:
                return 0
        return 0

    def _func_chr(self, args: list) -> str:
        """CHR$(code) - character from ASCII code."""
        if len(args) == 1 and isinstance(args[0], (int, float)):
            try:
                return chr(int(args[0]))
            except ValueError:
                return ""
        return ""

    def _func_asc(self, args: list) -> int:
        """ASC(str) - ASCII code of first character."""
        if len(args) == 1 and isinstance(args[0], str) and args[0]:
            return ord(args[0][0])
        return 0
