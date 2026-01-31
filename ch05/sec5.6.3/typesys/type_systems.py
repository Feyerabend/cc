"""
TYPE SYSTEMS: A COMPREHENSIVE EDUCATIONAL IMPLEMENTATION

This module demonstrates fundamental type system concepts through
a progression of increasingly sophisticated implementations built
on a minimal TAC-like language.

LEARNING PATH:
1. Foundations - Type representation and basic concepts
2. Dynamic Typing - Runtime type checking (Python/JavaScript style)
3. Static Typing - Compile-time type checking (Java/C style)
4. Type Inference - Automatic type deduction (ML/Haskell style)
5. Type Coercion - Automatic conversions (C arithmetic style)
6. Gradual Typing - Mixed static/dynamic (TypeScript/Python 3.5+ style)
7. Polymorphism - Generic types and parametric polymorphism

Each implementation is self-contained and can be studied independently.
"""

import re
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json


# PART 1: TYPE SYSTEM FOUNDATIONS

class TypeKind(Enum):
    """Enumeration of all supported type kinds in our type system."""
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    CHAR = "char"
    VOID = "void"
    ARRAY = "array"
    FUNCTION = "function"
    TYPEVAR = "typevar"  # For polymorphism
    ANY = "any"  # For gradual typing
    UNKNOWN = "unknown"
    ERROR = "error"


@dataclass
class Type:
    """
    Represents a type with metadata.
    
    This is the core type representation used throughout all type systems.
    Different type systems use different subsets of the metadata.
    
    Examples:
        Type(TypeKind.INT)                                           # Simple int type
        Type(TypeKind.ARRAY, base_type=Type(TypeKind.INT), size=10)  # int[10]
        Type(TypeKind.FUNCTION, param_types=[...], return_type=...)  # Function type
    """
    kind: TypeKind
    base_type: Optional['Type'] = None  # For arrays and pointers
    size: Optional[int] = None  # For arrays
    param_types: Optional[List['Type']] = None  # For functions
    return_type: Optional['Type'] = None  # For functions
    type_var_name: Optional[str] = None  # For type variables
    
    def __str__(self) -> str:
        """Human-readable type representation."""
        if self.kind == TypeKind.ARRAY:
            size_str = str(self.size) if self.size else "?"
            return f"{self.base_type}[{size_str}]"
        elif self.kind == TypeKind.FUNCTION:
            params = ", ".join(str(p) for p in (self.param_types or []))
            return f"({params}) -> {self.return_type}"
        elif self.kind == TypeKind.TYPEVAR:
            return f"'{self.type_var_name}"
        return self.kind.value
    
    def __eq__(self, other) -> bool:
        """Type equality check."""
        if not isinstance(other, Type):
            return False
        if self.kind != other.kind:
            return False
        if self.kind == TypeKind.ARRAY:
            return self.base_type == other.base_type
        if self.kind == TypeKind.FUNCTION:
            return (self.param_types == other.param_types and 
                    self.return_type == other.return_type)
        return True
    
    def __hash__(self) -> int:
        """Make Type hashable for use in sets/dicts."""
        return hash((self.kind, str(self.base_type), self.size))
    
    def is_numeric(self) -> bool:
        """Check if type represents a numeric value."""
        return self.kind in [TypeKind.INT, TypeKind.FLOAT, TypeKind.CHAR]
    
    def is_integral(self) -> bool:
        """Check if type represents an integral value."""
        return self.kind in [TypeKind.INT, TypeKind.CHAR, TypeKind.BOOL]
    
    def can_coerce_to(self, other: 'Type') -> bool:
        """
        Check if this type can be implicitly coerced to another type.
        
        Coercion hierarchy (specific to general):
            bool -> int -> float
            char -> int
        """
        if self == other:
            return True
        
        # Numeric promotions
        if self.kind == TypeKind.BOOL and other.kind in [TypeKind.INT, TypeKind.FLOAT]:
            return True
        if self.kind == TypeKind.CHAR and other.kind in [TypeKind.INT, TypeKind.FLOAT]:
            return True
        if self.kind == TypeKind.INT and other.kind == TypeKind.FLOAT:
            return True
        
        # Any type accepts anything in gradual typing
        if other.kind == TypeKind.ANY:
            return True
        
        return False
    
    def is_compatible_with(self, other: 'Type', strict: bool = True) -> bool:
        """
        Check type compatibility for assignment/comparison.
        
        Args:
            other: The type to check compatibility with
            strict: If True, no implicit coercions allowed
        """
        if self == other:
            return True
        if not strict:
            return self.can_coerce_to(other) or other.can_coerce_to(self)
        return False



# PART 2: SYMBOL TABLE AND ENVIRONMENT

@dataclass
class SymbolInfo:
    """Information stored about a symbol in the symbol table."""
    name: str
    type_: Type
    value: Any = None
    is_constant: bool = False
    line_declared: int = 0
    is_initialized: bool = False


class SymbolTable:
    """
    Symbol table with scope management.
    
    Supports nested scopes for block-structured languages.
    """
    
    def __init__(self, parent: Optional['SymbolTable'] = None):
        self.parent = parent
        self.symbols: Dict[str, SymbolInfo] = {}
        self.scope_level = 0 if parent is None else parent.scope_level + 1
    
    def declare(self, name: str, type_: Type, value: Any = None, 
                is_constant: bool = False, line: int = 0) -> None:
        """Declare a new symbol in the current scope."""
        if name in self.symbols:
            raise TypeError(f"Symbol '{name}' already declared in this scope")
        
        self.symbols[name] = SymbolInfo(
            name=name,
            type_=type_,
            value=value,
            is_constant=is_constant,
            line_declared=line,
            is_initialized=(value is not None)
        )
    
    def lookup(self, name: str) -> Optional[SymbolInfo]:
        """Look up a symbol in current scope or parent scopes."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None
    
    def update(self, name: str, value: Any, type_: Optional[Type] = None) -> None:
        """Update a symbol's value (and optionally type in dynamic systems)."""
        symbol = self.lookup(name)
        if not symbol:
            raise NameError(f"Undefined symbol '{name}'")
        if symbol.is_constant:
            raise TypeError(f"Cannot modify constant '{name}'")
        
        symbol.value = value
        if type_ is not None:
            symbol.type_ = type_
    
    def get_all_symbols(self) -> Dict[str, SymbolInfo]:
        """Get all symbols visible in current scope."""
        result = {}
        if self.parent:
            result.update(self.parent.get_all_symbols())
        result.update(self.symbols)
        return result



# PART 3: ABSTRACT SYNTAX TREE (AST)

class ASTNode(ABC):
    """Base class for all AST nodes."""
    
    @abstractmethod
    def __str__(self) -> str:
        pass


@dataclass
class LiteralNode(ASTNode):
    """Represents a literal value (number, string, etc.)."""
    value: Any
    type_: Type
    
    def __str__(self) -> str:
        return f"{self.value}"


@dataclass
class VariableNode(ASTNode):
    """Represents a variable reference."""
    name: str
    type_: Optional[Type] = None  # Filled in by type checker
    
    def __str__(self) -> str:
        return self.name


@dataclass
class BinaryOpNode(ASTNode):
    """Represents a binary operation (e.g., x + y)."""
    operator: str
    left: ASTNode
    right: ASTNode
    type_: Optional[Type] = None  # Result type, filled by type checker
    
    def __str__(self) -> str:
        return f"({self.left} {self.operator} {self.right})"


@dataclass
class UnaryOpNode(ASTNode):
    """Represents a unary operation (e.g., -x, !x)."""
    operator: str
    operand: ASTNode
    type_: Optional[Type] = None
    
    def __str__(self) -> str:
        return f"{self.operator}{self.operand}"


@dataclass
class AssignmentNode(ASTNode):
    """Represents an assignment statement."""
    target: str
    value: ASTNode
    declared_type: Optional[Type] = None  # For typed declarations
    
    def __str__(self) -> str:
        type_str = f"{self.declared_type} " if self.declared_type else ""
        return f"{type_str}{self.target} = {self.value}"


@dataclass
class PrintNode(ASTNode):
    """Represents a print statement (for demonstration)."""
    expression: ASTNode
    
    def __str__(self) -> str:
        return f"print {self.expression}"


@dataclass
class IfNode(ASTNode):
    """Represents a conditional statement."""
    condition: ASTNode
    true_label: str
    false_label: Optional[str] = None
    
    def __str__(self) -> str:
        return f"if {self.condition} goto {self.true_label}"


@dataclass
class LabelNode(ASTNode):
    """Represents a label for goto statements."""
    name: str
    
    def __str__(self) -> str:
        return f"{self.name}:"



# PART 4: DYNAMIC TYPE SYSTEM

class DynamicTACParser:
    """
    Dynamic typing: Types determined and checked at runtime.
    
    Characteristics:
    - No type declarations needed
    - Variables can change type during execution
    - Type errors detected when operations execute
    - Maximum flexibility, minimal safety
    
    Similar to: Python, JavaScript, Ruby
    
    Example:
        x = 10      # x is int
        x = 3.14    # x is now float (allowed!)
        x = "hi"    # x is now string (also allowed!)
    """
    
    def __init__(self, code: str, verbose: bool = False):
        self.lines = [line.strip() for line in code.strip().split('\n') if line.strip()]
        self.current = 0
        self.symbol_table = SymbolTable()
        self.output: List[str] = []
        self.verbose = verbose
        self.execution_trace: List[str] = []
    
    def parse_and_execute(self) -> Dict[str, Any]:
        """Parse and immediately execute (dynamic behavior)."""
        while not self.is_end():
            try:
                line = self.advance()
                self._trace(f"Executing: {line}")
                self.execute_line(line)
            except Exception as e:
                self._trace(f"Runtime Error: {e}")
                raise
        
        return {
            'symbol_table': self.symbol_table.get_all_symbols(),
            'output': self.output,
            'trace': self.execution_trace
        }
    
    def execute_line(self, line: str) -> None:
        """Execute a single line."""
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            return
        
        # Print statement
        if line.startswith('print '):
            self._execute_print(line[6:])
        # Assignment
        elif '=' in line and not any(op in line.split('=')[0] for op in ['<', '>', '!', '=']):
            self._execute_assignment(line)
        else:
            self._trace(f"Ignoring unrecognized statement: {line}")
    
    def _execute_assignment(self, line: str) -> None:
        """Execute an assignment: x = expr"""
        var_name, expr = [s.strip() for s in line.split('=', 1)]
        value = self.evaluate(expr)
        type_ = self._infer_type(value)
        
        # Check if variable exists
        existing = self.symbol_table.lookup(var_name)
        if existing:
            old_type = existing.type_
            self._trace(f"Type change: {var_name} was {old_type}, now {type_}")
            self.symbol_table.update(var_name, value, type_)
        else:
            self._trace(f"New variable: {var_name}: {type_} = {value}")
            self.symbol_table.declare(var_name, type_, value)
    
    def _execute_print(self, expr: str) -> None:
        """Execute a print statement."""
        value = self.evaluate(expr)
        output_line = f"{expr} = {value}"
        self.output.append(output_line)
        self._trace(f"Output: {output_line}")
    
    def evaluate(self, expr: str) -> Any:
        """Evaluate an expression and return its value."""
        expr = expr.strip()
        
        # Integer literal
        if re.match(r'^-?\d+$', expr):
            return int(expr)
        
        # Float literal
        if re.match(r'^-?\d+\.\d+$', expr):
            return float(expr)
        
        # String literal
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]
        
        # Boolean literals
        if expr in ['true', 'True']:
            return True
        if expr in ['false', 'False']:
            return False
        
        # Binary operations
        for op in ['+', '-', '*', '/', '//', '%', '==', '!=', '<', '>', '<=', '>=']:
            if op in expr:
                # Split carefully to handle operators correctly
                parts = expr.split(op, 1)
                if len(parts) == 2:
                    left = self.evaluate(parts[0].strip())
                    right = self.evaluate(parts[1].strip())
                    return self._apply_operator(left, op, right)
        
        # Variable reference
        symbol = self.symbol_table.lookup(expr)
        if symbol:
            return symbol.value
        
        raise NameError(f"Undefined variable: {expr}")
    
    def _apply_operator(self, left: Any, op: str, right: Any) -> Any:
        """Apply a binary operator at runtime with type checking."""
        # Arithmetic operators
        if op == '+':
            # Special case: string concatenation
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            # True division
            return left / right
        elif op == '//':
            # Integer division
            return left // right
        elif op == '%':
            return left % right
        # Comparison operators
        elif op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == '<':
            return left < right
        elif op == '>':
            return left > right
        elif op == '<=':
            return left <= right
        elif op == '>=':
            return left >= right
        else:
            raise ValueError(f"Unknown operator: {op}")
    
    def _infer_type(self, value: Any) -> Type:
        """Infer type from a runtime value."""
        if isinstance(value, bool):  # Must check bool before int!
            return Type(TypeKind.BOOL)
        elif isinstance(value, int):
            return Type(TypeKind.INT)
        elif isinstance(value, float):
            return Type(TypeKind.FLOAT)
        elif isinstance(value, str):
            return Type(TypeKind.STRING)
        else:
            return Type(TypeKind.UNKNOWN)
    
    def _trace(self, message: str) -> None:
        """Add a trace message if verbose mode is on."""
        if self.verbose:
            self.execution_trace.append(message)
    
    def is_end(self) -> bool:
        return self.current >= len(self.lines)
    
    def advance(self) -> str:
        line = self.lines[self.current]
        self.current += 1
        return line



# PART 5: STATIC TYPE SYSTEM WITH TYPE CHECKING

class StaticTACParser:
    """
    Static typing: Types checked before execution.
    
    Characteristics:
    - Explicit type declarations required
    - Types cannot change during execution
    - Type errors caught before running
    - High safety, less flexibility
    
    Similar to: C, Java, Rust, Go
    
    Example:
        int x = 10;     # x is declared as int
        x = 20;         # OK: still int
        x = 3.14;       # ERROR: cannot assign float to int
    """
    
    def __init__(self, code: str, strict: bool = True):
        self.lines = [line.strip() for line in code.strip().split('\n') if line.strip()]
        self.current = 0
        self.symbol_table = SymbolTable()
        self.ast: List[ASTNode] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.strict = strict  # Strict mode disallows implicit coercions
    
    def parse(self) -> List[ASTNode]:
        """Parse the entire program and build AST."""
        while not self.is_end():
            try:
                line = self.advance()
                if line and not line.startswith('#'):
                    node = self.parse_statement(line)
                    if node:
                        self.ast.append(node)
            except Exception as e:
                self.errors.append(f"Parse error: {e}")
        
        return self.ast
    
    def parse_statement(self, line: str) -> Optional[ASTNode]:
        """Parse a single statement."""
        # Type declaration: int x = 10
        if line.split()[0] in ['int', 'float', 'bool', 'string', 'char']:
            return self._parse_typed_declaration(line)
        
        # Assignment: x = 10
        elif '=' in line and not any(op in line.split('=')[0] for op in ['<', '>', '!', '=']):
            return self._parse_assignment(line)
        
        # Print statement
        elif line.startswith('print '):
            return PrintNode(self._parse_expression(line[6:]))
        
        return None
    
    def _parse_typed_declaration(self, line: str) -> AssignmentNode:
        """Parse a typed variable declaration."""
        parts = line.split(maxsplit=1)
        type_name = parts[0]
        rest = parts[1]
        
        var_name, expr = [s.strip() for s in rest.split('=', 1)]
        
        # Create the type
        declared_type = Type(TypeKind[type_name.upper()])
        
        # Parse the expression
        value_expr = self._parse_expression(expr)
        
        return AssignmentNode(
            target=var_name,
            value=value_expr,
            declared_type=declared_type
        )
    
    def _parse_assignment(self, line: str) -> AssignmentNode:
        """Parse an assignment to an existing variable."""
        var_name, expr = [s.strip() for s in line.split('=', 1)]
        value_expr = self._parse_expression(expr)
        
        return AssignmentNode(
            target=var_name,
            value=value_expr,
            declared_type=None
        )
    
    def _parse_expression(self, expr: str) -> ASTNode:
        """Parse an expression into an AST."""
        expr = expr.strip()
        
        # Integer literal
        if re.match(r'^-?\d+$', expr):
            return LiteralNode(int(expr), Type(TypeKind.INT))
        
        # Float literal
        if re.match(r'^-?\d+\.\d+$', expr):
            return LiteralNode(float(expr), Type(TypeKind.FLOAT))
        
        # String literal
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return LiteralNode(expr[1:-1], Type(TypeKind.STRING))
        
        # Boolean literals
        if expr in ['true', 'True']:
            return LiteralNode(True, Type(TypeKind.BOOL))
        if expr in ['false', 'False']:
            return LiteralNode(False, Type(TypeKind.BOOL))
        
        # Binary operations
        for op in ['+', '-', '*', '/', '==', '!=', '<', '>', '<=', '>=']:
            if op in expr:
                parts = expr.split(op, 1)
                if len(parts) == 2:
                    left = self._parse_expression(parts[0].strip())
                    right = self._parse_expression(parts[1].strip())
                    return BinaryOpNode(op, left, right)
        
        # Variable reference
        return VariableNode(expr)
    
    def type_check(self) -> bool:
        """Perform static type checking on the AST."""
        for node in self.ast:
            try:
                self._check_node(node)
            except Exception as e:
                self.errors.append(str(e))
        
        return len(self.errors) == 0
    
    def _check_node(self, node: ASTNode) -> Type:
        """Type check a node and return its type."""
        if isinstance(node, LiteralNode):
            return node.type_
        
        elif isinstance(node, VariableNode):
            symbol = self.symbol_table.lookup(node.name)
            if not symbol:
                raise TypeError(f"Undefined variable: {node.name}")
            node.type_ = symbol.type_
            return symbol.type_
        
        elif isinstance(node, BinaryOpNode):
            left_type = self._check_node(node.left)
            right_type = self._check_node(node.right)
            
            # Type check the operation
            result_type = self._check_binary_op(node.operator, left_type, right_type)
            node.type_ = result_type
            return result_type
        
        elif isinstance(node, AssignmentNode):
            value_type = self._check_node(node.value)
            
            # New declaration
            if node.declared_type:
                if not value_type.is_compatible_with(node.declared_type, strict=self.strict):
                    if not value_type.can_coerce_to(node.declared_type):
                        raise TypeError(
                            f"Type mismatch: cannot initialize {node.declared_type} "
                            f"with {value_type}"
                        )
                    else:
                        self.warnings.append(
                            f"Implicit coercion: {value_type} -> {node.declared_type} "
                            f"in initialization of '{node.target}'"
                        )
                
                self.symbol_table.declare(node.target, node.declared_type)
            
            # Assignment to existing variable
            else:
                symbol = self.symbol_table.lookup(node.target)
                if not symbol:
                    raise TypeError(f"Undefined variable: {node.target}")
                
                if not value_type.is_compatible_with(symbol.type_, strict=self.strict):
                    if not value_type.can_coerce_to(symbol.type_):
                        raise TypeError(
                            f"Type mismatch: cannot assign {value_type} to "
                            f"{symbol.type_} variable '{node.target}'"
                        )
                    else:
                        self.warnings.append(
                            f"Implicit coercion: {value_type} -> {symbol.type_} "
                            f"in assignment to '{node.target}'"
                        )
            
            return value_type
        
        elif isinstance(node, PrintNode):
            return self._check_node(node.expression)
        
        return Type(TypeKind.UNKNOWN)
    
    def _check_binary_op(self, op: str, left: Type, right: Type) -> Type:
        """Type check a binary operation and return result type."""
        # Arithmetic operators
        if op in ['+', '-', '*', '/']:
            # Special case: string concatenation
            if op == '+' and (left.kind == TypeKind.STRING or right.kind == TypeKind.STRING):
                return Type(TypeKind.STRING)
            
            # Numeric operations
            if not (left.is_numeric() and right.is_numeric()):
                raise TypeError(
                    f"Operator '{op}' requires numeric operands, got {left} and {right}"
                )
            
            # Result type is the "wider" type
            if left.kind == TypeKind.FLOAT or right.kind == TypeKind.FLOAT:
                return Type(TypeKind.FLOAT)
            return Type(TypeKind.INT)
        
        # Comparison operators
        elif op in ['==', '!=', '<', '>', '<=', '>=']:
            # Most types can be compared for equality
            if op in ['==', '!=']:
                return Type(TypeKind.BOOL)
            
            # Ordering comparisons require comparable types
            if not (left.is_numeric() and right.is_numeric()):
                raise TypeError(
                    f"Operator '{op}' requires numeric operands, got {left} and {right}"
                )
            return Type(TypeKind.BOOL)
        
        raise ValueError(f"Unknown operator: {op}")
    
    def is_end(self) -> bool:
        return self.current >= len(self.lines)
    
    def advance(self) -> str:
        line = self.lines[self.current]
        self.current += 1
        return line



# PART 6: TYPE INFERENCE SYSTEM

class TypeInferenceParser:
    """
    Type inference: Types deduced automatically from context.
    
    Characteristics:
    - No type declarations needed
    - Types inferred from usage
    - Type errors caught before execution
    - High safety AND convenience
    
    Similar to: ML, Haskell, Rust (partial), TypeScript (partial)
    
    Example:
        x = 10          # Inferred: x : int
        y = 3.14        # Inferred: y : float
        z = x + y       # Inferred: z : float (int promoted to float)
    
    This is a simplified version of Hindley-Milner type inference.
    """
    
    def __init__(self, code: str):
        self.lines = [line.strip() for line in code.strip().split('\n') if line.strip()]
        self.current = 0
        self.symbol_table = SymbolTable()
        self.ast: List[ASTNode] = []
        self.errors: List[str] = []
        self.type_constraints: List[Tuple[Type, Type, str]] = []
    
    def parse_and_infer(self) -> Tuple[List[ASTNode], Dict[str, SymbolInfo]]:
        """Parse program and perform type inference."""
        # First pass: parse
        while not self.is_end():
            line = self.advance()
            if line and not line.startswith('#'):
                try:
                    node = self._parse_statement(line)
                    if node:
                        self.ast.append(node)
                except Exception as e:
                    self.errors.append(f"Parse error: {e}")
        
        # Second pass: infer types
        for node in self.ast:
            try:
                self._infer_node(node)
            except Exception as e:
                self.errors.append(f"Type error: {e}")
        
        return self.ast, self.symbol_table.get_all_symbols()
    
    def _parse_statement(self, line: str) -> Optional[ASTNode]:
        """Parse a statement (same as static parser but without type annotations)."""
        # Assignment: x = expr
        if '=' in line and not any(op in line.split('=')[0] for op in ['<', '>', '!', '=']):
            var_name, expr = [s.strip() for s in line.split('=', 1)]
            value_expr = self._parse_expression(expr)
            return AssignmentNode(target=var_name, value=value_expr)
        
        # Print statement
        elif line.startswith('print '):
            return PrintNode(self._parse_expression(line[6:]))
        
        return None
    
    def _parse_expression(self, expr: str) -> ASTNode:
        """Parse an expression (same as static parser)."""
        expr = expr.strip()
        
        # Integer literal
        if re.match(r'^-?\d+$', expr):
            return LiteralNode(int(expr), Type(TypeKind.INT))
        
        # Float literal
        if re.match(r'^-?\d+\.\d+$', expr):
            return LiteralNode(float(expr), Type(TypeKind.FLOAT))
        
        # String literal
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return LiteralNode(expr[1:-1], Type(TypeKind.STRING))
        
        # Boolean literals
        if expr in ['true', 'True']:
            return LiteralNode(True, Type(TypeKind.BOOL))
        if expr in ['false', 'False']:
            return LiteralNode(False, Type(TypeKind.BOOL))
        
        # Binary operations
        for op in ['+', '-', '*', '/', '==', '!=', '<', '>', '<=', '>=']:
            if op in expr:
                parts = expr.split(op, 1)
                if len(parts) == 2:
                    left = self._parse_expression(parts[0].strip())
                    right = self._parse_expression(parts[1].strip())
                    return BinaryOpNode(op, left, right)
        
        # Variable reference
        return VariableNode(expr)
    
    def _infer_node(self, node: ASTNode) -> Type:
        """Infer the type of a node."""
        if isinstance(node, LiteralNode):
            return node.type_
        
        elif isinstance(node, VariableNode):
            symbol = self.symbol_table.lookup(node.name)
            if not symbol:
                raise TypeError(f"Undefined variable: {node.name}")
            node.type_ = symbol.type_
            return symbol.type_
        
        elif isinstance(node, BinaryOpNode):
            left_type = self._infer_node(node.left)
            right_type = self._infer_node(node.right)
            
            # Infer result type
            result_type = self._infer_binary_op_type(node.operator, left_type, right_type)
            node.type_ = result_type
            return result_type
        
        elif isinstance(node, AssignmentNode):
            value_type = self._infer_node(node.value)
            
            # Check if variable already exists
            existing = self.symbol_table.lookup(node.target)
            
            if existing:
                # Variable exists - check type compatibility
                if not self._types_compatible(existing.type_, value_type):
                    raise TypeError(
                        f"Type conflict: variable '{node.target}' has type {existing.type_}, "
                        f"but assigned value has type {value_type}"
                    )
            else:
                # New variable - infer its type
                self.symbol_table.declare(node.target, value_type)
            
            return value_type
        
        elif isinstance(node, PrintNode):
            return self._infer_node(node.expression)
        
        return Type(TypeKind.UNKNOWN)
    
    def _infer_binary_op_type(self, op: str, left: Type, right: Type) -> Type:
        """Infer the result type of a binary operation."""
        if op in ['+', '-', '*', '/']:
            # String concatenation
            if op == '+' and (left.kind == TypeKind.STRING or right.kind == TypeKind.STRING):
                return Type(TypeKind.STRING)
            
            # Numeric operations
            if not (left.is_numeric() and right.is_numeric()):
                raise TypeError(
                    f"Operator '{op}' requires numeric types, got {left} and {right}"
                )
            
            # Type promotion: int + float = float
            if left.kind == TypeKind.FLOAT or right.kind == TypeKind.FLOAT:
                return Type(TypeKind.FLOAT)
            return Type(TypeKind.INT)
        
        elif op in ['==', '!=', '<', '>', '<=', '>=']:
            return Type(TypeKind.BOOL)
        
        raise ValueError(f"Unknown operator: {op}")
    
    def _types_compatible(self, t1: Type, t2: Type) -> bool:
        """Check if two types are compatible for inference."""
        # Same type is always compatible
        if t1 == t2:
            return True
        
        # Numeric types can be promoted
        if t1.is_numeric() and t2.is_numeric():
            return True
        
        return False
    
    def is_end(self) -> bool:
        return self.current >= len(self.lines)
    
    def advance(self) -> str:
        line = self.lines[self.current]
        self.current += 1
        return line



# PART 7: TYPE COERCION SYSTEM

class TypeCoercionTACParser:
    """
    Type coercion: Automatic conversion between compatible types.
    
    Characteristics:
    - Implicit conversions allowed
    - Follows type hierarchy for promotion
    - Logs all coercions for transparency
    - Balances convenience and safety
    
    Similar to: C arithmetic, Java numeric promotion
    
    Type hierarchy (lower to higher):
        bool -> char -> int -> float
    
    Example:
        x = 5           # int
        y = 3.14        # float
        z = x + y       # z = 8.14 (float), x coerced to float
    """
    
    def __init__(self, code: str, log_coercions: bool = True):
        self.lines = [line.strip() for line in code.strip().split('\n') if line.strip()]
        self.current = 0
        self.symbol_table = SymbolTable()
        self.coercion_log: List[str] = []
        self.log_coercions = log_coercions
    
    # Type ranks for determining promotion
    TYPE_RANKS = {
        TypeKind.BOOL: 1,
        TypeKind.CHAR: 2,
        TypeKind.INT: 3,
        TypeKind.FLOAT: 4,
        TypeKind.STRING: 5  # Strings can absorb anything
    }
    
    def parse_and_execute(self) -> Dict[str, Any]:
        """Parse and execute with type coercion."""
        while not self.is_end():
            line = self.advance()
            if line and not line.startswith('#'):
                self._execute_line(line)
        
        return {
            'symbol_table': self.symbol_table.get_all_symbols(),
            'coercion_log': self.coercion_log
        }
    
    def _execute_line(self, line: str) -> None:
        """Execute a line with coercion support."""
        # Assignment
        if '=' in line and not any(op in line.split('=')[0] for op in ['<', '>', '!', '=']):
            var_name, expr = [s.strip() for s in line.split('=', 1)]
            value, type_ = self._evaluate_with_coercion(expr)
            
            existing = self.symbol_table.lookup(var_name)
            if existing:
                self.symbol_table.update(var_name, value, type_)
            else:
                self.symbol_table.declare(var_name, type_, value)
    
    def _evaluate_with_coercion(self, expr: str) -> Tuple[Any, Type]:
        """Evaluate expression with automatic type coercion."""
        expr = expr.strip()
        
        # Literals
        if re.match(r'^-?\d+$', expr):
            return int(expr), Type(TypeKind.INT)
        if re.match(r'^-?\d+\.\d+$', expr):
            return float(expr), Type(TypeKind.FLOAT)
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1], Type(TypeKind.STRING)
        if expr in ['true', 'True']:
            return True, Type(TypeKind.BOOL)
        if expr in ['false', 'False']:
            return False, Type(TypeKind.BOOL)
        
        # Binary operations
        for op in ['+', '-', '*', '/', '==', '!=', '<', '>', '<=', '>=']:
            if op in expr:
                parts = expr.split(op, 1)
                if len(parts) == 2:
                    left_val, left_type = self._evaluate_with_coercion(parts[0].strip())
                    right_val, right_type = self._evaluate_with_coercion(parts[1].strip())
                    
                    # Determine target type
                    target_type = self._determine_coercion_type(left_type, right_type, op)
                    
                    # Coerce operands
                    coerced_left = self._coerce_value(left_val, left_type, target_type, 
                                                      f"left operand of '{op}'")
                    coerced_right = self._coerce_value(right_val, right_type, target_type,
                                                       f"right operand of '{op}'")
                    
                    # Apply operator
                    result = self._apply_operator(coerced_left, op, coerced_right)
                    
                    # Result type
                    if op in ['==', '!=', '<', '>', '<=', '>=']:
                        return result, Type(TypeKind.BOOL)
                    return result, target_type
        
        # Variable reference
        symbol = self.symbol_table.lookup(expr)
        if symbol:
            return symbol.value, symbol.type_
        
        raise NameError(f"Undefined variable: {expr}")
    
    def _determine_coercion_type(self, t1: Type, t2: Type, op: str) -> Type:
        """Determine the type to which operands should be coerced."""
        # String concatenation
        if op == '+' and (t1.kind == TypeKind.STRING or t2.kind == TypeKind.STRING):
            return Type(TypeKind.STRING)
        
        # Numeric promotion: choose higher rank
        rank1 = self.TYPE_RANKS.get(t1.kind, 0)
        rank2 = self.TYPE_RANKS.get(t2.kind, 0)
        
        if rank1 >= rank2:
            return t1
        else:
            return t2
    
    def _coerce_value(self, value: Any, from_type: Type, to_type: Type, context: str) -> Any:
        """Coerce a value from one type to another."""
        if from_type == to_type:
            return value
        
        # Log the coercion
        if self.log_coercions:
            self.coercion_log.append(
                f"Coercion: {from_type} -> {to_type} ({context})"
            )
        
        # Perform coercion
        if to_type.kind == TypeKind.STRING:
            return str(value)
        elif to_type.kind == TypeKind.FLOAT:
            return float(value)
        elif to_type.kind == TypeKind.INT:
            if isinstance(value, float):
                return int(value)
            return int(value)
        elif to_type.kind == TypeKind.BOOL:
            return bool(value)
        
        return value
    
    def _apply_operator(self, left: Any, op: str, right: Any) -> Any:
        """Apply an operator to two values."""
        if op == '+':
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            return left / right
        elif op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == '<':
            return left < right
        elif op == '>':
            return left > right
        elif op == '<=':
            return left <= right
        elif op == '>=':
            return left >= right
        else:
            raise ValueError(f"Unknown operator: {op}")
    
    def is_end(self) -> bool:
        return self.current >= len(self.lines)
    
    def advance(self) -> str:
        line = self.lines[self.current]
        self.current += 1
        return line


# DEMOS

def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "-" * 50)
    print(f"  {title}")
    print("-" * 50 + "\n")


def demo_dynamic_typing():
    """Demonstrate dynamic typing behavior."""
    print_section("DYNAMIC TYPING")
    
    print("Dynamic typing determines types at runtime.")
    print("Variables can change type during execution.\n")
    
    code = """
x = 10
y = 3.14
z = x + y
x = "hello"
message = x + " world"
print x
print z
print message
"""
    
    print("Code:")
    print(code)
    
    parser = DynamicTACParser(code.strip(), verbose=True)
    result = parser.parse_and_execute()
    
    print("\nExecution Trace:")
    for trace in result['trace'][:10]:  # Show first 10 traces
        print(f"  {trace}")
    if len(result['trace']) > 10:
        print(f"  .. ({len(result['trace']) - 10} more)")
    
    print("\nOutput:")
    for line in result['output']:
        print(f"  {line}")
    
    print("\nFinal Symbol Table:")
    for name, info in result['symbol_table'].items():
        print(f"  {name}: {info.type_} = {info.value}")


def demo_static_typing():
    """Demonstrate static typing behaviour."""
    print_section("STATIC TYPING")
    
    print("Static typing checks types before execution.")
    print("Type errors are caught during type checking phase.\n")
    
    # Valid program
    code_valid = """
int x = 10
float y = 3.14
int z = x + 5
print z
"""
    
    print("Valid Program:")
    print(code_valid)
    
    parser = StaticTACParser(code_valid.strip(), strict=False)
    parser.parse()
    is_valid = parser.type_check()
    
    print(f"Type Check: {'PASSED' if is_valid else 'FAILED'}")
    
    if parser.warnings:
        print("\nWarnings:")
        for warning in parser.warnings:
            print(f"  Warning {warning}")
    
    print("\nSymbol Table:")
    for name, info in parser.symbol_table.get_all_symbols().items():
        print(f"  {name}: {info.type_}")
    
    # Invalid program
    print("\n" + "-" * 70 + "\n")
    
    code_invalid = """
int x = 10
x = 3.14
float y = "hello"
"""
    
    print("Invalid Program:")
    print(code_invalid)
    
    parser2 = StaticTACParser(code_invalid.strip(), strict=True)
    parser2.parse()
    is_valid2 = parser2.type_check()
    
    print(f"Type Check: {'PASSED' if is_valid2 else 'FAILED'}")
    
    if parser2.errors:
        print("\nErrors:")
        for error in parser2.errors:
            print(f"    {error}")


def demo_type_inference():
    """Demonstrate type inference."""
    print_section("TYPE INFERENCE")
    
    print("Type inference automatically deduces types from context.")
    print("No type annotations needed!\n")
    
    code = """
x = 10
y = 3.14
z = x + y
message = "Result: "
result = message + "value"
flag = true
print z
"""
    
    print("Code (no type annotations):")
    print(code)
    
    parser = TypeInferenceParser(code.strip())
    ast, symbols = parser.parse_and_infer()
    
    print("\nInferred Types:")
    for name, info in symbols.items():
        print(f"  {name}: {info.type_}")
    
    if parser.errors:
        print("\nType Errors:")
        for error in parser.errors:
            print(f"    {error}")
    else:
        print("\n  Type inference successful!")


def demo_type_coercion():
    """Demonstrate type coercion."""
    print_section("TYPE COERCION")
    
    print("Type coercion automatically converts between compatible types.")
    print("Follows hierarchy: bool -> char -> int -> float -> string\n")
    
    code = """
x = 5
y = 3.14
z = x + y
a = 10
b = 20
c = a + b
message = "The answer is: "
result = message + 42
"""
    
    print("Code:")
    print(code)
    
    parser = TypeCoercionTACParser(code.strip())
    result = parser.parse_and_execute()
    
    print("\nCoercion Log:")
    for log in result['coercion_log']:
        print(f"    {log}")
    
    print("\nFinal Symbol Table:")
    for name, info in result['symbol_table'].items():
        print(f"  {name}: {info.type_} = {info.value}")


def demo_comparison():
    """Show side-by-side comparison of all systems."""
    print_section("SYSTEM COMPARISON")
    
    code = """x = 10
y = 3.14
z = x + y"""
    
    print("Same code, different type systems:")
    print(code)
    print()
    
    # Dynamic
    print("1. DYNAMIC TYPING:")
    parser_dyn = DynamicTACParser(code)
    result_dyn = parser_dyn.parse_and_execute()
    for name, info in result_dyn['symbol_table'].items():
        print(f"   {name}: {info.type_} = {info.value}")
    
    # Static
    print("\n2. STATIC TYPING (with float z = x + y):")
    code_static = "float x = 10.0\nfloat y = 3.14\nfloat z = x + y"
    parser_static = StaticTACParser(code_static, strict=False)
    parser_static.parse()
    parser_static.type_check()
    for name, info in parser_static.symbol_table.get_all_symbols().items():
        print(f"   {name}: {info.type_}")
    
    # Inference
    print("\n3. TYPE INFERENCE:")
    parser_inf = TypeInferenceParser(code)
    _, symbols = parser_inf.parse_and_infer()
    for name, info in symbols.items():
        print(f"   {name}: {info.type_}")
    
    # Coercion
    print("\n4. TYPE COERCION:")
    parser_coerce = TypeCoercionTACParser(code, log_coercions=False)
    result_coerce = parser_coerce.parse_and_execute()
    for name, info in result_coerce['symbol_table'].items():
        print(f"   {name}: {info.type_} = {info.value}")
    
    print("\n" + "-" * 70)
    print("\nKey Differences:")
    print("  _ Dynamic: Types determined at runtime, variables can change type")
    print("  _ Static: Types declared upfront, checked before execution")
    print("  _ Inference: Types deduced automatically, checked before execution")
    print("  _ Coercion: Automatic conversions follow type hierarchy")


def main():
    """Run all demonstrations."""
    print("""

    TYPE SYSTEMS
    This program demonstrates four fundamental
    type system approaches:
       1. Dynamic Typing  (Python, JavaScript)
       2. Static Typing   (C, Java, Rust)
       3. Type Inference  (ML, Haskell)
       4. Type Coercion   (C arithmetic)

""")
    
    demo_dynamic_typing()
    demo_static_typing()
    demo_type_inference()
    demo_type_coercion()
    demo_comparison()

if __name__ == "__main__":
    main()
