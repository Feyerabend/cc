#!/usr/bin/env python3
"""
A simple K-like array programming language interpreter.

This interpreter implements a subset of K language features including:
- Monadic and dyadic operations
- Array operations with rank polymorphism
- Vector programming primitives
- Lambda functions
- Dictionaries and data structures
"""

import sys
import functools
import itertools
from dataclasses import dataclass
from typing import Callable, Dict, List, Union, Optional, Any
from enum import Enum


# Type definitions
Atom = Union[int, float, str, bool]
Vector = List
Value = Union[Atom, Vector]
MonadicFunction = Callable[[Value], Value]
DyadicFunction = Callable[[Value, Value], Value]
Dictionary = Dict[Value, Value]


class ErrorType(Enum):
    """Error types for better error categorization."""
    SYNTAX = "syntax error"
    TYPE = "type error"
    RANK = "rank error"
    DOMAIN = "domain error"
    INDEX = "index error"
    LENGTH = "length error"
    UNDEFINED = "undefined variable"


class KError(Exception):
    """Custom exception for K interpreter errors."""
    def __init__(self, error_type: ErrorType, message: str):
        self.error_type = error_type
        self.message = message
        super().__init__(f"{error_type.value}: {message}")


def raise_error(message: str, error_type: ErrorType = ErrorType.DOMAIN) -> None:
    """Raise a K interpreter error."""
    raise KError(error_type, message)


@dataclass
class Operation:
    """Represents a K operation with optional monadic and dyadic forms."""
    symbol: str
    monadic: Optional[MonadicFunction] = None
    dyadic: Optional[DyadicFunction] = None
    description: str = ""
    
    def __post_init__(self):
        if self.monadic is None and self.dyadic is None:
            raise ValueError(f"Operation {self.symbol} must have at least one implementation")


class OperationRegistry:
    """Registry for K operations supporting both monadic and dyadic forms."""
    
    def __init__(self):
        self.operations: Dict[str, Operation] = {}
    
    def register(self, operation: Operation) -> None:
        """Register a new operation."""
        if operation.symbol in self.operations:
            raise ValueError(f"Operation {operation.symbol} is already registered")
        self.operations[operation.symbol] = operation
    
    def get_monadic(self, symbol: str) -> MonadicFunction:
        """Get the monadic form of an operation."""
        if symbol not in self.operations:
            raise_error(f"unknown operation: {symbol}", ErrorType.SYNTAX)
        
        monadic = self.operations[symbol].monadic
        if monadic is None:
            raise_error(f"operation {symbol} does not have a monadic form", ErrorType.SYNTAX)
        
        return monadic
    
    def get_dyadic(self, symbol: str) -> DyadicFunction:
        """Get the dyadic form of an operation."""
        if symbol not in self.operations:
            raise_error(f"unknown operation: {symbol}", ErrorType.SYNTAX)
        
        dyadic = self.operations[symbol].dyadic
        if dyadic is None:
            raise_error(f"operation {symbol} does not have a dyadic form", ErrorType.SYNTAX)
        
        return dyadic
    
    def get_operation(self, symbol: str) -> Operation:
        """Get an operation by symbol."""
        if symbol not in self.operations:
            raise_error(f"unknown operation: {symbol}", ErrorType.SYNTAX)
        return self.operations[symbol]
    
    def has_monadic(self, symbol: str) -> bool:
        """Check if an operation has a monadic form."""
        return symbol in self.operations and self.operations[symbol].monadic is not None
    
    def has_dyadic(self, symbol: str) -> bool:
        """Check if an operation has a dyadic form."""
        return symbol in self.operations and self.operations[symbol].dyadic is not None
    
    def list_operations(self) -> List[str]:
        """List all registered operations with their descriptions."""
        result = []
        for symbol, op in sorted(self.operations.items()):
            forms = []
            if op.monadic:
                forms.append("monadic")
            if op.dyadic:
                forms.append("dyadic")
            result.append(f"{symbol:>3} ({', '.join(forms):>15}) - {op.description}")
        return result


# Global state
operation_registry = OperationRegistry()
global_variables: Dict[str, Value] = {}


# ============================================================================
# Type checking and utilities
# ============================================================================

def is_atomic(value: Any) -> bool:
    """Check if a value is atomic (scalar)."""
    return isinstance(value, (int, float, str, bool))


def get_type(value: Any) -> str:
    """Get the type character for a value."""
    type_map = {
        bool: 'b',
        int: 'i',
        float: 'f',
        str: 's',
        list: 'l',
        dict: 'd'
    }
    return type_map.get(type(value), '?')


def ensure_list(value: Value) -> List:
    """Ensure a value is a list."""
    return [value] if is_atomic(value) else value


# ============================================================================
# Monadic operations
# ============================================================================

def negate(value: Value) -> Value:
    """Negate a number or flip a boolean (-x)."""
    if is_atomic(value):
        if isinstance(value, bool):
            return not value
        elif isinstance(value, (int, float)):
            return -value
        else:
            raise_error("cannot negate string", ErrorType.TYPE)
    else:
        return list(map(negate, value))


def generate_sequence(value: Value) -> List[int]:
    """Generate sequence from 0 to n-1 (!x)."""
    if is_atomic(value):
        if isinstance(value, (int, float)):
            n = int(value)
            if n < 0:
                raise_error("iota requires non-negative argument", ErrorType.DOMAIN)
            return list(range(n))
        else:
            raise_error("iota requires numeric argument", ErrorType.TYPE)
    else:
        raise_error("iota requires atomic value", ErrorType.RANK)


def get_length(value: Value) -> int:
    """Get the length of a list or string (#x)."""
    if is_atomic(value):
        if isinstance(value, str):
            return len(value)
        else:
            raise_error("cannot get length of non-string atomic value", ErrorType.RANK)
    else:
        return len(value)


def reverse_list(value: Value) -> Value:
    """Reverse a list or string (|x)."""
    if is_atomic(value):
        if isinstance(value, str):
            return value[::-1]
        else:
            raise_error("cannot reverse non-sequence atomic value", ErrorType.RANK)
    else:
        return list(reversed(value))


def first_element(value: Value) -> Value:
    """Get the first element of a list or string (@x)."""
    if is_atomic(value):
        if isinstance(value, str):
            return value[0] if value else ""
        else:
            raise_error("cannot get first element of an atom", ErrorType.RANK)
    else:
        if not value:
            raise_error("cannot get first element of empty list", ErrorType.INDEX)
        return value[0]


def get_type_info(value: Value) -> Union[str, List[str]]:
    """Get type information ($x)."""
    if is_atomic(value):
        return get_type(value)
    else:
        return [get_type(x) for x in value]


def where(value: Value) -> List[int]:
    """Return indices where counts are non-zero (^x)."""
    if is_atomic(value):
        raise_error("where requires a list", ErrorType.RANK)
    
    result = []
    for i, count in enumerate(value):
        if not isinstance(count, (int, bool)):
            raise_error("where requires integer counts", ErrorType.TYPE)
        result.extend([i] * int(count))
    return result


def group(value: Value) -> Dictionary:
    """Group indices by value (monadic group is actually dyadic ^)."""
    if is_atomic(value):
        raise_error("group requires a list", ErrorType.RANK)
    
    groups = {}
    for i, v in enumerate(value):
        key_str = str(v)
        if key_str not in groups:
            groups[key_str] = []
        groups[key_str].append(i)
    
    # Convert string keys back to appropriate types
    result = {}
    for k, v in groups.items():
        try:
            if k.lower() in ('true', 'false'):
                result[k.lower() == 'true'] = v
            elif '.' in k and k.replace('.', '').replace('-', '', 1).isdigit():
                result[float(k)] = v
            elif k.lstrip('-').isdigit():
                result[int(k)] = v
            else:
                result[k] = v
        except (ValueError, AttributeError):
            result[k] = v
    
    return result


def unique(value: Value) -> Value:
    """Get unique elements preserving order (?x)."""
    if is_atomic(value):
        return value
    
    seen = set()
    result = []
    for item in value:
        # Use string representation for hashing
        item_key = str(item) if not isinstance(item, (list, dict)) else id(item)
        if item_key not in seen:
            seen.add(item_key)
            result.append(item)
    return result


def sort(value: Value) -> List:
    """Sort elements in ascending order (`x)."""
    if is_atomic(value):
        raise_error("sort requires a list", ErrorType.RANK)
    
    if not value:
        return []
    
    try:
        return sorted(value)
    except TypeError:
        # Fall back to string comparison for mixed types
        return sorted(value, key=str)


def sum_values(value: Value) -> Union[int, float]:
    """Sum all values in a list (+x)."""
    if is_atomic(value):
        return value
    
    if not value:
        return 0
    
    try:
        return sum(value)
    except TypeError:
        raise_error("cannot sum non-numeric elements", ErrorType.TYPE)


def minimum(value: Value) -> Value:
    """Get minimum value (&x)."""
    if is_atomic(value):
        return value
    
    if not value:
        raise_error("empty list has no minimum", ErrorType.DOMAIN)
    
    try:
        return min(value)
    except TypeError:
        raise_error("cannot compare mixed types for minimum", ErrorType.TYPE)


def maximum(value: Value) -> Value:
    """Get maximum value (*x)."""
    if is_atomic(value):
        return value
    
    if not value:
        raise_error("empty list has no maximum", ErrorType.DOMAIN)
    
    try:
        return max(value)
    except TypeError:
        raise_error("cannot compare mixed types for maximum", ErrorType.TYPE)


def average(value: Value) -> float:
    """Calculate average of values (%x)."""
    if is_atomic(value):
        return float(value)
    
    if not value:
        raise_error("cannot average empty list", ErrorType.DOMAIN)
    
    try:
        return sum(value) / len(value)
    except TypeError:
        raise_error("average requires numeric elements", ErrorType.TYPE)


def raze(value: Value) -> List:
    """Flatten a list of lists (;x)."""
    if is_atomic(value):
        return [value]
    
    result = []
    for item in value:
        if is_atomic(item):
            result.append(item)
        else:
            result.extend(item)
    return result


def flip_matrix(value: Value) -> List[List]:
    """Transpose a matrix (.x)."""
    if is_atomic(value):
        raise_error("flip requires a matrix", ErrorType.RANK)
    
    if not value:
        return []
    
    if not all(isinstance(row, list) for row in value):
        raise_error("all elements must be lists for flip", ErrorType.RANK)
    
    if value:
        row_lengths = [len(row) for row in value]
        if len(set(row_lengths)) > 1:
            raise_error("all rows must have same length for flip", ErrorType.RANK)
    
    return [list(col) for col in zip(*value)]


def coalesce(value: Value) -> Value:
    """Return first non-null value (:x)."""
    if is_atomic(value):
        return value
    
    for item in value:
        if item is not None:
            return item
    
    return None


# ============================================================================
# Dyadic operations
# ============================================================================

def apply_dyadic(x: Value, y: Value, operation: Callable) -> Value:
    """
    Apply a dyadic operation with automatic rank extension.
    Handles scalar-vector, vector-scalar, and vector-vector operations.
    """
    if is_atomic(x):
        if is_atomic(y):
            return operation(x, y)
        else:
            return [operation(x, element) for element in y]
    elif is_atomic(y):
        return [operation(element, y) for element in x]
    else:
        if len(x) != len(y):
            raise_error("lists must have equal length for dyadic operations", ErrorType.LENGTH)
        return [operation(a, b) for a, b in zip(x, y)]


def add(x: Value, y: Value) -> Value:
    """Add two values (x+y)."""
    def add_atoms(a, b):
        # Check booleans first, BEFORE checking int/float
        # (since bool is a subclass of int in Python)
        if isinstance(a, bool) and isinstance(b, bool):
            return a or b
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return a + b
        elif isinstance(a, str) and isinstance(b, str):
            return a + b
        else:
            raise_error(f"cannot add {type(a).__name__} and {type(b).__name__}", ErrorType.TYPE)
    
    return apply_dyadic(x, y, add_atoms)


def subtract(x: Value, y: Value) -> Value:
    """Subtract two values (x-y)."""
    def subtract_atoms(a, b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return a - b
        elif isinstance(a, bool) and isinstance(b, bool):
            return a and not b
        else:
            raise_error(f"cannot subtract {type(b).__name__} from {type(a).__name__}", ErrorType.TYPE)
    
    return apply_dyadic(x, y, subtract_atoms)


def multiply(x: Value, y: Value) -> Value:
    """Multiply two values (x*y)."""
    def multiply_atoms(a, b):
        # Check booleans first, BEFORE checking int/float
        if isinstance(a, bool) and isinstance(b, bool):
            return a and b
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return a * b
        elif isinstance(a, str) and isinstance(b, int):
            return a * b
        elif isinstance(a, int) and isinstance(b, str):
            return b * a
        else:
            raise_error(f"cannot multiply {type(a).__name__} and {type(b).__name__}", ErrorType.TYPE)
    
    return apply_dyadic(x, y, multiply_atoms)


def divide(x: Value, y: Value) -> Value:
    """Divide and return as percentage (x%y)."""
    def divide_atoms(a, b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if b == 0:
                raise_error("division by zero", ErrorType.DOMAIN)
            return (a / b) * 100  # Return as percentage
        else:
            raise_error(f"cannot divide {type(a).__name__} by {type(b).__name__}", ErrorType.TYPE)
    
    return apply_dyadic(x, y, divide_atoms)


def modulo(x: Value, y: Value) -> Value:
    """Modulo operation (x!y)."""
    if not is_atomic(x):
        raise_error("modulo requires atomic first argument", ErrorType.RANK)
    
    if not isinstance(x, (int, float)):
        raise_error("modulo requires numeric first argument", ErrorType.TYPE)
    
    def mod_atom(y_val, x_val):
        if isinstance(y_val, (int, float)):
            return y_val % x_val
        else:
            raise_error(f"cannot apply modulo to {type(y_val).__name__}", ErrorType.TYPE)
    
    if is_atomic(y):
        return mod_atom(y, x)
    else:
        return [mod_atom(element, x) for element in y]


def logical_and(x: Value, y: Value) -> Value:
    """Logical/bitwise AND (x&y)."""
    def and_atoms(a, b):
        # Check booleans first
        if isinstance(a, bool) and isinstance(b, bool):
            return a and b
        elif isinstance(a, int) and isinstance(b, int):
            return a & b
        else:
            raise_error(f"cannot apply & to {type(a).__name__} and {type(b).__name__}", ErrorType.TYPE)
    
    return apply_dyadic(x, y, and_atoms)


def logical_or(x: Value, y: Value) -> Value:
    """Logical/bitwise OR (x|y)."""
    def or_atoms(a, b):
        # Check booleans first
        if isinstance(a, bool) and isinstance(b, bool):
            return a or b
        elif isinstance(a, int) and isinstance(b, int):
            return a | b
        else:
            raise_error(f"cannot apply | to {type(a).__name__} and {type(b).__name__}", ErrorType.TYPE)
    
    return apply_dyadic(x, y, or_atoms)


def equals(x: Value, y: Value) -> Value:
    """Equality check (x=y)."""
    return apply_dyadic(x, y, lambda a, b: a == b)


def not_equal(x: Value, y: Value) -> Value:
    """Inequality check (x~y)."""
    return apply_dyadic(x, y, lambda a, b: a != b)


def take(x: Value, y: Value) -> Value:
    """Take n elements from a list (x#y)."""
    if not is_atomic(x):
        raise_error("take requires atomic first argument", ErrorType.RANK)
    
    if not isinstance(x, int):
        raise_error("take requires integer first argument", ErrorType.TYPE)
    
    if is_atomic(y):
        return [y] * x
    else:
        if x >= 0:
            # Take from front with wrapping
            return [y[i % len(y)] for i in range(x)]
        else:
            # Take from back with wrapping
            x = abs(x)
            return [y[-(i % len(y) + 1)] for i in range(x)][::-1]


def drop(x: Value, y: Value) -> Value:
    """Drop n elements from a list (x_y)."""
    if not is_atomic(x):
        raise_error("drop requires atomic first argument", ErrorType.RANK)
    
    if not isinstance(x, int):
        raise_error("drop requires integer first argument", ErrorType.TYPE)
    
    if is_atomic(y):
        if isinstance(y, str):
            return y[x:] if x >= 0 else y[:x]
        else:
            raise_error("cannot drop from atomic value", ErrorType.RANK)
    else:
        return y[x:] if x >= 0 else y[:x]


def find(x: Value, y: Value) -> List[int]:
    """Find indices of x in y (x?y)."""
    if is_atomic(y):
        if isinstance(y, str):
            if is_atomic(x) and isinstance(x, str):
                indices = []
                start = 0
                while True:
                    pos = y.find(x, start)
                    if pos == -1:
                        break
                    indices.append(pos)
                    start = pos + 1
                return indices
            else:
                raise_error("finding in string requires string pattern", ErrorType.TYPE)
        else:
            raise_error("find requires sequence as second argument", ErrorType.RANK)
    else:
        return [i for i, val in enumerate(y) if val == x]


def concatenate(x: Value, y: Value) -> Value:
    """Concatenate two values (x,y)."""
    if is_atomic(x) and is_atomic(y):
        if isinstance(x, str) and isinstance(y, str):
            return x + y
        else:
            return [x, y]
    elif is_atomic(x):
        return [x] + (y if isinstance(y, list) else [y])
    elif is_atomic(y):
        return (x if isinstance(x, list) else [x]) + [y]
    else:
        return x + y


def index_access(x: Value, y: Value) -> Value:
    """Index into a list or string (x@y)."""
    if is_atomic(x):
        if isinstance(x, str):
            if is_atomic(y):
                if isinstance(y, int):
                    if y >= len(x) or y < -len(x):
                        raise_error("string index out of range", ErrorType.INDEX)
                    return x[y]
                else:
                    raise_error("string indexing requires integer index", ErrorType.TYPE)
            else:
                # Index with list - preserve order
                result = []
                for i in y:
                    if not isinstance(i, int):
                        raise_error("string indexing requires integer indices", ErrorType.TYPE)
                    if i >= len(x) or i < -len(x):
                        raise_error("string index out of range", ErrorType.INDEX)
                    result.append(x[i])
                return ''.join(result)
        else:
            raise_error("cannot index atomic non-string value", ErrorType.RANK)
    else:
        if is_atomic(y):
            if isinstance(y, int):
                if y >= len(x) or y < -len(x):
                    raise_error("list index out of range", ErrorType.INDEX)
                return x[y]
            else:
                raise_error("list indexing requires integer index", ErrorType.TYPE)
        else:
            return [x[i] for i in y]


def dict_lookup(x: Value, y: Value) -> Value:
    """Dictionary lookup (x$y)."""
    if not isinstance(x, dict):
        raise_error("first argument must be a dictionary", ErrorType.TYPE)
    
    if is_atomic(y):
        return x.get(y, None)
    else:
        return [x.get(k, None) for k in y]


# ============================================================================
# Higher-order operations
# ============================================================================

class LambdaFunction:
    """Represents a lambda function."""
    
    def __init__(self, body: str):
        self.body = body
        self.params = ['x', 'y', 'z']
    
    def __call__(self, *args):
        """Execute the lambda with given arguments."""
        old_vars = global_variables.copy()
        
        try:
            # Bind arguments to parameter names
            for i, arg in enumerate(args):
                if i < len(self.params):
                    global_variables[self.params[i]] = arg
            
            # Evaluate the body
            result = evaluate_expression(self.body)
            return result
        finally:
            # Restore old variable state
            for param in self.params:
                if param in global_variables:
                    if param not in old_vars:
                        del global_variables[param]
                    else:
                        global_variables[param] = old_vars[param]
    
    def __repr__(self):
        return f"{{'{self.body}'}}"


def fold(operation: Callable, sequence: List) -> Value:
    """Fold (reduce) an operation over a sequence."""
    if not sequence:
        raise_error("cannot fold empty sequence", ErrorType.DOMAIN)
    return functools.reduce(lambda acc, element: operation(acc, element), sequence)


def scan(operation: Callable, sequence: List) -> List:
    """Scan (cumulative fold) an operation over a sequence."""
    if not sequence:
        return []
    return list(itertools.accumulate(sequence, lambda acc, element: operation(acc, element)))


def each(operation: Callable, sequence: Value) -> List:
    """Apply operation to each element."""
    if is_atomic(sequence):
        raise_error("each requires a sequence", ErrorType.RANK)
    return [operation(element) for element in sequence]


# ============================================================================
# Parser and evaluator
# ============================================================================

def parse_value(token: str) -> Value:
    """Parse a token into a value."""
    # String literal
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1]
    
    # Boolean
    if token.lower() == "true":
        return True
    elif token.lower() == "false":
        return False
    
    # Float
    if '.' in token:
        try:
            return float(token)
        except ValueError:
            pass
    
    # Integer
    try:
        return int(token)
    except ValueError:
        pass
    
    # Otherwise it's an identifier
    return token


def evaluate_expression(expression: Any) -> Value:
    """
    Evaluate an expression.
    
    Expressions can be:
    - Atomic values (int, float, bool, str)
    - List expressions [op, arg] or [left, op, right]
    - String expressions including literals (1;2;3), [a:1;b:2], {x+y}
    """
    # Handle empty expression
    if not expression:
        return None
    
    # Handle pre-parsed list expressions
    if isinstance(expression, list):
        if not expression:
            return []
        
        # Monadic operation: [op, arg]
        if len(expression) == 2:
            op, arg = expression
            if isinstance(op, str) and operation_registry.has_monadic(op):
                # Evaluate argument
                if isinstance(arg, str) and arg in global_variables:
                    evaluated_arg = global_variables[arg]
                else:
                    evaluated_arg = evaluate_expression(arg)
                return operation_registry.get_monadic(op)(evaluated_arg)
        
        # Dyadic operation: [left, op, right]
        if len(expression) == 3:
            left, op, right = expression
            if isinstance(op, str) and operation_registry.has_dyadic(op):
                # Evaluate left
                if isinstance(left, str) and left in global_variables:
                    evaluated_left = global_variables[left]
                else:
                    evaluated_left = evaluate_expression(left)
                
                # Evaluate right
                if isinstance(right, (int, float)):
                    evaluated_right = right
                elif isinstance(right, str) and right in global_variables:
                    evaluated_right = global_variables[right]
                else:
                    evaluated_right = evaluate_expression(right)
                
                return operation_registry.get_dyadic(op)(evaluated_left, evaluated_right)
        
        # Handle lists of atomic values or nested structures
        # Evaluate any string elements that are quoted strings
        evaluated = []
        for item in expression:
            if isinstance(item, str) and item.startswith('"') and item.endswith('"'):
                evaluated.append(item[1:-1])  # Remove quotes
            elif isinstance(item, list):
                evaluated.append(evaluate_expression(item))
            else:
                evaluated.append(item)
        return evaluated
    
    # Handle atomic values
    if isinstance(expression, (int, float, bool)):
        return expression
    
    # Handle string expressions
    if isinstance(expression, str):
        # List literal: (1;2;3)
        if expression.startswith('(') and expression.endswith(')'):
            if len(expression) == 2:  # Empty list ()
                return []
            
            items = []
            current = ''
            paren_count = 0
            
            for i, char in enumerate(expression[1:-1], 1):
                if char == '(':
                    paren_count += 1
                    current += char
                elif char == ')':
                    paren_count -= 1
                    current += char
                elif char == ';' and paren_count == 0:
                    if current.strip():
                        items.append(evaluate_expression(current.strip()))
                    current = ''
                else:
                    current += char
            
            if current.strip():
                items.append(evaluate_expression(current.strip()))
            
            return items
        
        # Dictionary literal: [a:1;b:2]
        if expression.startswith('[') and expression.endswith(']'):
            if len(expression) == 2:  # Empty dict []
                return {}
            
            result = {}
            current = ''
            bracket_count = 0
            
            for char in expression[1:-1]:
                if char == '[':
                    bracket_count += 1
                    current += char
                elif char == ']':
                    bracket_count -= 1
                    current += char
                elif char == ';' and bracket_count == 0:
                    if current.strip():
                        parts = current.split(':', 1)
                        if len(parts) != 2:
                            raise_error("invalid dictionary entry", ErrorType.SYNTAX)
                        key = evaluate_expression(parts[0].strip())
                        val = evaluate_expression(parts[1].strip())
                        result[key] = val
                    current = ''
                else:
                    current += char
            
            if current.strip():
                parts = current.split(':', 1)
                if len(parts) != 2:
                    raise_error("invalid dictionary entry", ErrorType.SYNTAX)
                key = evaluate_expression(parts[0].strip())
                val = evaluate_expression(parts[1].strip())
                result[key] = val
            
            return result
        
        # Lambda expression: {x+y}
        if expression.startswith('{') and expression.endswith('}'):
            body = expression[1:-1]
            return LambdaFunction(body)
        
        # Atomic value or variable
        value = parse_value(expression)
        if isinstance(value, str):
            # Check if it's a quoted string
            if not (expression.startswith('"') and expression.endswith('"')):
                # It's a variable reference
                if value in global_variables:
                    return global_variables[value]
                else:
                    raise_error(f"undefined variable: {value}", ErrorType.UNDEFINED)
        return value
    
    raise_error("cannot evaluate expression", ErrorType.SYNTAX)


# ============================================================================
# Operation registration
# ============================================================================

def register_standard_operations():
    """Register all standard K operations."""
    
    operation_registry.register(Operation(
        symbol="+",
        monadic=sum_values,
        dyadic=add,
        description="Sum of list (monadic) or addition (dyadic)"
    ))
    
    operation_registry.register(Operation(
        symbol="-",
        monadic=negate,
        dyadic=subtract,
        description="Negation (monadic) or subtraction (dyadic)"
    ))
    
    operation_registry.register(Operation(
        symbol="!",
        monadic=generate_sequence,
        dyadic=modulo,
        description="Generate sequence (monadic) or modulo (dyadic)"
    ))
    
    operation_registry.register(Operation(
        symbol="#",
        monadic=get_length,
        dyadic=take,
        description="Length of list (monadic) or take elements (dyadic)"
    ))
    
    operation_registry.register(Operation(
        symbol="_",
        monadic=None,
        dyadic=drop,
        description="Drop elements from a list or string"
    ))
    
    operation_registry.register(Operation(
        symbol="?",
        monadic=unique,
        dyadic=find,
        description="Unique elements (monadic) or find occurrences (dyadic)"
    ))
    
    operation_registry.register(Operation(
        symbol="^",
        monadic=where,
        dyadic=group,
        description="Where indices (monadic) or group by value (dyadic)"
    ))
    
    operation_registry.register(Operation(
        symbol=",",
        monadic=ensure_list,
        dyadic=concatenate,
        description="Ensure list (monadic) or concatenate (dyadic)"
    ))
    
    operation_registry.register(Operation(
        symbol="@",
        monadic=first_element,
        dyadic=index_access,
        description="First element (monadic) or index access (dyadic)"
    ))
    
    operation_registry.register(Operation(
        symbol="$",
        monadic=get_type_info,
        dyadic=dict_lookup,
        description="Type info (monadic) or dictionary lookup (dyadic)"
    ))
    
    operation_registry.register(Operation(
        symbol="`",
        monadic=sort,
        dyadic=None,
        description="Sort elements in ascending order"
    ))
    
    operation_registry.register(Operation(
        symbol="=",
        monadic=None,
        dyadic=equals,
        description="Equality check"
    ))
    
    operation_registry.register(Operation(
        symbol="~",
        monadic=None,
        dyadic=not_equal,
        description="Inequality check"
    ))
    
    operation_registry.register(Operation(
        symbol="&",
        monadic=minimum,
        dyadic=logical_and,
        description="Minimum (monadic) or logical/bitwise AND (dyadic)"
    ))
    
    operation_registry.register(Operation(
        symbol="|",
        monadic=reverse_list,
        dyadic=logical_or,
        description="Reverse (monadic) or logical/bitwise OR (dyadic)"
    ))
    
    operation_registry.register(Operation(
        symbol="*",
        monadic=maximum,
        dyadic=multiply,
        description="Maximum (monadic) or multiplication (dyadic)"
    ))
    
    operation_registry.register(Operation(
        symbol="%",
        monadic=average,
        dyadic=divide,
        description="Average (monadic) or percentage division (dyadic)"
    ))
    
    operation_registry.register(Operation(
        symbol=";",
        monadic=raze,
        dyadic=None,
        description="Flatten a list of lists"
    ))
    
    operation_registry.register(Operation(
        symbol=".",
        monadic=flip_matrix,
        dyadic=None,
        description="Transpose a matrix"
    ))
    
    operation_registry.register(Operation(
        symbol=":",
        monadic=coalesce,
        dyadic=None,
        description="First non-null value from a list"
    ))


# ============================================================================
# REPL and main
# ============================================================================

def repl():
    """Run the K interpreter REPL."""
    print("K Interpreter")
    print("Type 'exit' to quit, 'help' for operations list, 'vars' to see variables")
    print()
    
    while True:
        try:
            line = input("  ")
            line = line.strip()
            
            if not line:
                continue
            
            if line == "exit":
                break
            
            if line == "help":
                print("\nAvailable operations:")
                for op_info in operation_registry.list_operations():
                    print(f"  {op_info}")
                print()
                continue
            
            if line == "vars":
                if global_variables:
                    print("\nVariables:")
                    for name, value in sorted(global_variables.items()):
                        print(f"  {name} = {value}")
                else:
                    print("\nNo variables defined")
                print()
                continue
            
            # Handle assignment
            if ':' in line and not line.startswith('['):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    expr = parts[1].strip()
                    result = evaluate_expression(expr)
                    global_variables[var_name] = result
                    print(result)
                    continue
            
            # Evaluate expression
            result = evaluate_expression(line)
            print(result)
            
        except KError as e:
            print(f"  {e}")
        except KeyboardInterrupt:
            print("\n")
            break
        except EOFError:
            break
        except Exception as e:
            print(f"  error: {e}")


def main():
    """Main entry point."""
    register_standard_operations()
    
    if len(sys.argv) > 1:
        # Run file
        filename = sys.argv[1]
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            result = evaluate_expression(line)
                            print(result)
                        except KError as e:
                            print(f"error: {e}")
                            sys.exit(1)
        except FileNotFoundError:
            print(f"error: file not found: {filename}")
            sys.exit(1)
    else:
        # Run REPL
        repl()


if __name__ == "__main__":
    main()
