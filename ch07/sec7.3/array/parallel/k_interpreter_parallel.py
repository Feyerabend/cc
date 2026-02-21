#!/usr/bin/env python3
"""
K Interpreter with Parallel Execution Support

This version adds parallel execution capabilities for operations on large vectors.
Parallelization is applied automatically when arrays exceed a threshold size.
"""

import sys
import functools
import itertools
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable, Dict, List, Union, Optional, Any
from enum import Enum


# Configuration for parallel execution
PARALLEL_THRESHOLD = 1000  # Only parallelize for arrays with 1000+ elements
NUM_WORKERS = mp.cpu_count()  # Use all available CPU cores
USE_THREADS = False  # False for CPU-bound (processes), True for I/O-bound (threads)


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


# ============================================================================
# Parallel execution utilities
# ============================================================================

def chunk_list(lst: List, n_chunks: int) -> List[List]:
    """Split a list into roughly equal chunks."""
    chunk_size = len(lst) // n_chunks
    remainder = len(lst) % n_chunks
    
    chunks = []
    start = 0
    for i in range(n_chunks):
        # Distribute remainder across first chunks
        size = chunk_size + (1 if i < remainder else 0)
        chunks.append(lst[start:start + size])
        start += size
    
    return chunks


def parallel_map(func: Callable, data: List, threshold: int = PARALLEL_THRESHOLD) -> List:
    """
    Apply a function to list elements in parallel if list is large enough.
    
    Args:
        func: Function to apply to each element
        data: List of elements to process
        threshold: Minimum size to use parallelization
    
    Returns:
        List of results in the same order as input
    """
    if len(data) < threshold:
        # Serial execution for small arrays
        return [func(x) for x in data]
    
    # Parallel execution for large arrays
    n_workers = min(NUM_WORKERS, len(data))
    
    try:
        if USE_THREADS:
            with ThreadPoolExecutor(max_workers=n_workers) as executor:
                return list(executor.map(func, data))
        else:
            with ProcessPoolExecutor(max_workers=n_workers) as executor:
                return list(executor.map(func, data))
    except Exception as e:
        # Fallback to serial if parallel fails (e.g., unpicklable objects)
        return [func(x) for x in data]


def parallel_starmap(func: Callable, pairs: List[tuple], threshold: int = PARALLEL_THRESHOLD) -> List:
    """
    Apply a binary function to pairs of elements in parallel.
    
    Args:
        func: Binary function to apply
        pairs: List of (a, b) tuples
        threshold: Minimum size to use parallelization
    
    Returns:
        List of results
    """
    if len(pairs) < threshold:
        return [func(a, b) for a, b in pairs]
    
    n_workers = min(NUM_WORKERS, len(pairs))
    
    try:
        if USE_THREADS:
            with ThreadPoolExecutor(max_workers=n_workers) as executor:
                return list(executor.starmap(func, pairs))
        else:
            with ProcessPoolExecutor(max_workers=n_workers) as executor:
                return list(executor.starmap(func, pairs))
    except Exception as e:
        return [func(a, b) for a, b in pairs]


def parallel_reduce(func: Callable, data: List, threshold: int = PARALLEL_THRESHOLD) -> Value:
    """
    Parallel reduction using divide-and-conquer.
    
    For associative operations like +, *, min, max, this can be parallelized
    by reducing chunks in parallel and then reducing the results.
    """
    if len(data) < threshold:
        return functools.reduce(func, data)
    
    n_workers = min(NUM_WORKERS, len(data) // 100)  # At least 100 elements per worker
    if n_workers <= 1:
        return functools.reduce(func, data)
    
    chunks = chunk_list(data, n_workers)
    
    # Reduce each chunk in parallel
    try:
        if USE_THREADS:
            with ThreadPoolExecutor(max_workers=n_workers) as executor:
                chunk_results = list(executor.map(
                    lambda chunk: functools.reduce(func, chunk),
                    chunks
                ))
        else:
            with ProcessPoolExecutor(max_workers=n_workers) as executor:
                chunk_results = list(executor.map(
                    lambda chunk: functools.reduce(func, chunk),
                    chunks
                ))
        
        # Final reduction of chunk results
        return functools.reduce(func, chunk_results)
    except Exception as e:
        # Fallback to serial
        return functools.reduce(func, data)


# ============================================================================
# Configuration management
# ============================================================================

class ParallelConfig:
    """Global configuration for parallel execution."""
    enabled: bool = True
    threshold: int = PARALLEL_THRESHOLD
    num_workers: int = NUM_WORKERS
    use_threads: bool = USE_THREADS
    
    @classmethod
    def set_threshold(cls, threshold: int):
        """Set the threshold for parallel execution."""
        cls.threshold = max(1, threshold)
    
    @classmethod
    def set_workers(cls, num_workers: int):
        """Set the number of worker processes/threads."""
        cls.num_workers = max(1, min(num_workers, mp.cpu_count() * 2))
    
    @classmethod
    def enable(cls):
        """Enable parallel execution."""
        cls.enabled = True
    
    @classmethod
    def disable(cls):
        """Disable parallel execution (use serial)."""
        cls.enabled = False


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
# Monadic operations (with parallelization where applicable)
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
        if ParallelConfig.enabled:
            return parallel_map(negate, value, ParallelConfig.threshold)
        return [negate(x) for x in value]


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
        if ParallelConfig.enabled:
            return parallel_map(get_type, value, ParallelConfig.threshold)
        return [get_type(x) for x in value]


def where(value: Value) -> List[int]:
    """Return indices where counts are non-zero (^x)."""
    if is_atomic(value):
        raise_error("where requires a list", ErrorType.RANK)
    
    # This is inherently sequential but can be optimized
    result = []
    for i, count in enumerate(value):
        if not isinstance(count, (int, bool)):
            raise_error("where requires integer counts", ErrorType.TYPE)
        result.extend([i] * int(count))
    return result


def group(value: Value) -> Dictionary:
    """Group indices by value."""
    if is_atomic(value):
        raise_error("group requires a list", ErrorType.RANK)
    
    groups = {}
    for i, v in enumerate(value):
        key_str = str(v)
        if key_str not in groups:
            groups[key_str] = []
        groups[key_str].append(i)
    
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
        return sorted(value, key=str)


def sum_values(value: Value) -> Union[int, float]:
    """Sum all values in a list (+x) - uses parallel reduction for large arrays."""
    if is_atomic(value):
        return value
    
    if not value:
        return 0
    
    try:
        if ParallelConfig.enabled and len(value) >= ParallelConfig.threshold:
            # Parallel reduction for large arrays
            return parallel_reduce(lambda a, b: a + b, value, ParallelConfig.threshold)
        return sum(value)
    except TypeError:
        raise_error("cannot sum non-numeric elements", ErrorType.TYPE)


def minimum(value: Value) -> Value:
    """Get minimum value (&x) - uses parallel reduction."""
    if is_atomic(value):
        return value
    
    if not value:
        raise_error("empty list has no minimum", ErrorType.DOMAIN)
    
    try:
        if ParallelConfig.enabled and len(value) >= ParallelConfig.threshold:
            return parallel_reduce(lambda a, b: a if a < b else b, value, ParallelConfig.threshold)
        return min(value)
    except TypeError:
        raise_error("cannot compare mixed types for minimum", ErrorType.TYPE)


def maximum(value: Value) -> Value:
    """Get maximum value (*x) - uses parallel reduction."""
    if is_atomic(value):
        return value
    
    if not value:
        raise_error("empty list has no maximum", ErrorType.DOMAIN)
    
    try:
        if ParallelConfig.enabled and len(value) >= ParallelConfig.threshold:
            return parallel_reduce(lambda a, b: a if a > b else b, value, ParallelConfig.threshold)
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
        total = sum_values(value)  # Uses parallel sum for large arrays
        return total / len(value)
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
    """Transpose a matrix (.x) - can be parallelized for large matrices."""
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
    
    # For large matrices, could parallelize column extraction
    if ParallelConfig.enabled and len(value) >= ParallelConfig.threshold:
        ncols = len(value[0]) if value else 0
        def get_column(col_idx):
            return [row[col_idx] for row in value]
        return parallel_map(get_column, range(ncols), ParallelConfig.threshold)
    
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
# Dyadic operations (with parallelization)
# ============================================================================

def apply_dyadic(x: Value, y: Value, operation: Callable) -> Value:
    """
    Apply a dyadic operation with automatic rank extension and parallelization.
    Handles scalar-vector, vector-scalar, and vector-vector operations.
    """
    if is_atomic(x):
        if is_atomic(y):
            return operation(x, y)
        else:
            # Scalar-vector: parallelize for large vectors
            if ParallelConfig.enabled and len(y) >= ParallelConfig.threshold:
                return parallel_map(lambda element: operation(x, element), y, ParallelConfig.threshold)
            return [operation(x, element) for element in y]
    elif is_atomic(y):
        # Vector-scalar: parallelize for large vectors
        if ParallelConfig.enabled and len(x) >= ParallelConfig.threshold:
            return parallel_map(lambda element: operation(element, y), x, ParallelConfig.threshold)
        return [operation(element, y) for element in x]
    else:
        # Vector-vector: parallelize for large vectors
        if len(x) != len(y):
            raise_error("lists must have equal length for dyadic operations", ErrorType.LENGTH)
        
        if ParallelConfig.enabled and len(x) >= ParallelConfig.threshold:
            return parallel_starmap(operation, list(zip(x, y)), ParallelConfig.threshold)
        return [operation(a, b) for a, b in zip(x, y)]


def add(x: Value, y: Value) -> Value:
    """Add two values (x+y)."""
    def add_atoms(a, b):
        # Check booleans first, BEFORE checking int/float
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
            return (a / b) * 100
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
        if ParallelConfig.enabled and len(y) >= ParallelConfig.threshold:
            return parallel_map(lambda element: mod_atom(element, x), y, ParallelConfig.threshold)
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
            return [y[i % len(y)] for i in range(x)]
        else:
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
                # Index with list - preserve order and validate
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
            # Parallel indexing for large index lists
            if ParallelConfig.enabled and len(y) >= ParallelConfig.threshold:
                return parallel_map(lambda i: x[i], y, ParallelConfig.threshold)
            return [x[i] for i in y]


def dict_lookup(x: Value, y: Value) -> Value:
    """Dictionary lookup (x$y)."""
    if not isinstance(x, dict):
        raise_error("first argument must be a dictionary", ErrorType.TYPE)
    
    if is_atomic(y):
        return x.get(y, None)
    else:
        if ParallelConfig.enabled and len(y) >= ParallelConfig.threshold:
            return parallel_map(lambda k: x.get(k, None), y, ParallelConfig.threshold)
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
            for i, arg in enumerate(args):
                if i < len(self.params):
                    global_variables[self.params[i]] = arg
            
            result = evaluate_expression(self.body)
            return result
        finally:
            for param in self.params:
                if param in global_variables:
                    if param not in old_vars:
                        del global_variables[param]
                    else:
                        global_variables[param] = old_vars[param]
    
    def __repr__(self):
        return f"{{'{self.body}'}}"


def fold(operation: Callable, sequence: List) -> Value:
    """Fold (reduce) an operation over a sequence - uses parallel reduction."""
    if not sequence:
        raise_error("cannot fold empty sequence", ErrorType.DOMAIN)
    
    if ParallelConfig.enabled and len(sequence) >= ParallelConfig.threshold:
        return parallel_reduce(operation, sequence, ParallelConfig.threshold)
    
    return functools.reduce(lambda acc, element: operation(acc, element), sequence)


def scan(operation: Callable, sequence: List) -> List:
    """Scan (cumulative fold) an operation over a sequence."""
    if not sequence:
        return []
    return list(itertools.accumulate(sequence, lambda acc, element: operation(acc, element)))


def each(operation: Callable, sequence: Value) -> List:
    """Apply operation to each element - parallelized for large arrays."""
    if is_atomic(sequence):
        raise_error("each requires a sequence", ErrorType.RANK)
    
    if ParallelConfig.enabled and len(sequence) >= ParallelConfig.threshold:
        return parallel_map(operation, sequence, ParallelConfig.threshold)
    
    return [operation(element) for element in sequence]


# ============================================================================
# Parser and evaluator (unchanged from original)
# ============================================================================

def parse_value(token: str) -> Value:
    """Parse a token into a value."""
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1]
    
    if token.lower() == "true":
        return True
    elif token.lower() == "false":
        return False
    
    if '.' in token:
        try:
            return float(token)
        except ValueError:
            pass
    
    try:
        return int(token)
    except ValueError:
        pass
    
    return token


def evaluate_expression(expression: Any) -> Value:
    """Evaluate an expression."""
    if not expression:
        return None
    
    if isinstance(expression, list):
        if not expression:
            return []
        
        if len(expression) == 2:
            op, arg = expression
            if isinstance(op, str) and operation_registry.has_monadic(op):
                if isinstance(arg, str) and arg in global_variables:
                    evaluated_arg = global_variables[arg]
                else:
                    evaluated_arg = evaluate_expression(arg)
                return operation_registry.get_monadic(op)(evaluated_arg)
        
        if len(expression) == 3:
            left, op, right = expression
            if isinstance(op, str) and operation_registry.has_dyadic(op):
                if isinstance(left, str) and left in global_variables:
                    evaluated_left = global_variables[left]
                else:
                    evaluated_left = evaluate_expression(left)
                
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
    
    if isinstance(expression, (int, float, bool)):
        return expression
    
    if isinstance(expression, str):
        if expression.startswith('(') and expression.endswith(')'):
            if len(expression) == 2:
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
        
        if expression.startswith('[') and expression.endswith(']'):
            if len(expression) == 2:
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
        
        if expression.startswith('{') and expression.endswith('}'):
            body = expression[1:-1]
            return LambdaFunction(body)
        
        value = parse_value(expression)
        if isinstance(value, str):
            if not (expression.startswith('"') and expression.endswith('"')):
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
    print("K Interpreter (Parallel Edition)")
    print(f"Parallel execution: {'enabled' if ParallelConfig.enabled else 'disabled'}")
    print(f"Workers: {ParallelConfig.num_workers}, Threshold: {ParallelConfig.threshold} elements")
    print("Type 'exit' to quit, 'help' for operations, 'parallel' for parallel config")
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
            
            if line == "parallel":
                print(f"\nParallel Configuration:")
                print(f"  Enabled: {ParallelConfig.enabled}")
                print(f"  Workers: {ParallelConfig.num_workers}")
                print(f"  Threshold: {ParallelConfig.threshold} elements")
                print(f"  CPU cores: {mp.cpu_count()}")
                print("\nCommands:")
                print("  parallel on/off - enable/disable parallelization")
                print("  parallel threshold N - set threshold")
                print("  parallel workers N - set number of workers")
                print()
                continue
            
            if line.startswith("parallel "):
                parts = line.split()
                if len(parts) == 2:
                    if parts[1] == "on":
                        ParallelConfig.enable()
                        print("Parallel execution enabled")
                    elif parts[1] == "off":
                        ParallelConfig.disable()
                        print("Parallel execution disabled")
                elif len(parts) == 3:
                    if parts[1] == "threshold":
                        ParallelConfig.set_threshold(int(parts[2]))
                        print(f"Threshold set to {ParallelConfig.threshold}")
                    elif parts[1] == "workers":
                        ParallelConfig.set_workers(int(parts[2]))
                        print(f"Workers set to {ParallelConfig.num_workers}")
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
        repl()


if __name__ == "__main__":
    main()
