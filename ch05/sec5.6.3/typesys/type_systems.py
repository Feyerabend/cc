"""
TYPE SYSTEMS TUTORIAL

This module demonstrates various type system concepts through extending
the TAC (Three-Address Code) interpreter with different type system features.

Topics Covered:
1. Dynamic vs Static Typing
2. Type Inference
3. Type Coercion
4. Strong vs Weak Typing
5. Type Checking Algorithms
"""

import re
from enum import Enum
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass


# PART 1: TYPE SYSTEM FOUNDATIONS

class TypeKind(Enum):
    """Enumeration of supported types in our type system"""
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    ARRAY = "array"
    UNKNOWN = "unknown"
    ERROR = "error"


@dataclass
class Type:
    """Represents a type with additional metadata"""
    kind: TypeKind
    base_type: Optional['Type'] = None  # For arrays
    size: Optional[int] = None  # For arrays
    
    def __str__(self):
        if self.kind == TypeKind.ARRAY:
            return f"array[{self.base_type}, {self.size}]"
        return self.kind.value
    
    def is_numeric(self):
        return self.kind in [TypeKind.INT, TypeKind.FLOAT]
    
    def can_coerce_to(self, other: 'Type') -> bool:
        """Check if this type can be coerced to another type"""
        if self.kind == other.kind:
            return True
        # int can be coerced to float
        if self.kind == TypeKind.INT and other.kind == TypeKind.FLOAT:
            return True
        return False



# PART 2: DYNAMIC TYPE SYSTEM (Original TAC Behavior)

class DynamicTACParser:
    """
    Dynamic typing: Types are determined at runtime during execution.
    Variables can change types throughout program execution.
    
    Example:
        x = 10      # x is int
        x = 3.14    # x is now float (allowed in dynamic typing)
    """
    
    def __init__(self, code: str):
        self.tokens = code.splitlines()
        self.current = 0
        self.symbol_table: Dict[str, Dict[str, Any]] = {}
        self.output: List[str] = []
    
    def parse_and_execute(self):
        """Parse and execute immediately (dynamic behavior)"""
        while not self.is_end():
            statement = self.parse_statement()
            if statement:
                self.execute_statement(statement)
        return self.output
    
    def parse_statement(self):
        line = self.peek()
        if not line or not line.strip():
            self.advance()
            return None
        
        line = line.strip()
        
        if "=" in line and not line.startswith("if"):
            return self.parse_assignment()
        elif line.startswith("print"):
            return self.parse_print()
        
        self.advance()
        return None
    
    def parse_assignment(self):
        line = self.advance().strip()
        left, right = map(str.strip, line.split("=", 1))
        return {"type": "assignment", "left": left, "right": right}
    
    def parse_print(self):
        line = self.advance().strip()
        _, value = line.split(maxsplit=1)
        return {"type": "print", "value": value}
    
    def execute_statement(self, stmt):
        if stmt["type"] == "assignment":
            value = self.evaluate_expression(stmt["right"])
            var_type = self.infer_type_from_value(value)
            self.symbol_table[stmt["left"]] = {
                "type": var_type,
                "value": value
            }
        elif stmt["type"] == "print":
            var_name = stmt["value"]
            if var_name in self.symbol_table:
                self.output.append(f"{var_name} = {self.symbol_table[var_name]['value']} ({self.symbol_table[var_name]['type']})")
    
    def evaluate_expression(self, expr: str):
        expr = expr.strip()
        
        # Check if it's a number
        if re.match(r'^\d+$', expr):
            return int(expr)
        if re.match(r'^\d+\.\d+$', expr):
            return float(expr)
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        
        # Check for binary operations
        for op in ['+', '-', '*', '/']:
            if op in expr:
                parts = expr.split(op, 1)
                left = self.evaluate_expression(parts[0].strip())
                right = self.evaluate_expression(parts[1].strip())
                
                if op == '+':
                    return left + right
                elif op == '-':
                    return left - right
                elif op == '*':
                    return left * right
                elif op == '/':
                    return left / right if isinstance(right, float) or left % right != 0 else left // right
        
        # It's a variable
        if expr in self.symbol_table:
            return self.symbol_table[expr]["value"]
        
        return None
    
    def infer_type_from_value(self, value) -> TypeKind:
        """Infer type from runtime value (dynamic typing)"""
        if isinstance(value, int):
            return TypeKind.INT
        elif isinstance(value, float):
            return TypeKind.FLOAT
        elif isinstance(value, str):
            return TypeKind.STRING
        elif isinstance(value, bool):
            return TypeKind.BOOL
        return TypeKind.UNKNOWN
    
    def peek(self):
        return self.tokens[self.current] if not self.is_end() else None
    
    def advance(self):
        if not self.is_end():
            self.current += 1
            return self.tokens[self.current - 1]
        return None
    
    def is_end(self):
        return self.current >= len(self.tokens)



# PART 3: STATIC TYPE SYSTEM WITH TYPE CHECKING

class StaticTACParser:
    """
    Static typing: Types are checked before execution.
    Variables must maintain their declared type throughout execution.
    
    Example:
        int x = 10      # x is declared as int
        x = 3.14        # ERROR: Cannot assign float to int variable
    """
    
    def __init__(self, code: str):
        self.tokens = code.splitlines()
        self.current = 0
        self.symbol_table: Dict[str, Type] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.ast: List[Dict] = []
    
    def parse(self):
        """Parse the entire program and build AST"""
        while not self.is_end():
            stmt = self.parse_statement()
            if stmt:
                self.ast.append(stmt)
        return self.ast
    
    def type_check(self):
        """Perform static type checking on the AST"""
        for stmt in self.ast:
            self.check_statement(stmt)
        
        return len(self.errors) == 0
    
    def parse_statement(self):
        line = self.peek()
        if not line or not line.strip():
            self.advance()
            return None
        
        line = line.strip()
        
        # Type declaration: int x = 10
        if line.startswith(('int ', 'float ', 'string ', 'bool ')):
            return self.parse_typed_declaration()
        
        # Assignment: x = 10
        if "=" in line and not line.startswith("if"):
            return self.parse_assignment()
        
        self.advance()
        return None
    
    def parse_typed_declaration(self):
        """Parse explicit type declaration: int x = 10"""
        line = self.advance().strip()
        parts = line.split(maxsplit=1)
        type_name = parts[0]
        rest = parts[1]
        
        var_name, expr = map(str.strip, rest.split("=", 1))
        
        declared_type = Type(kind=TypeKind[type_name.upper()])
        self.symbol_table[var_name] = declared_type
        
        return {
            "type": "typed_declaration",
            "var_name": var_name,
            "declared_type": declared_type,
            "expr": expr
        }
    
    def parse_assignment(self):
        line = self.advance().strip()
        left, right = map(str.strip, line.split("=", 1))
        
        return {
            "type": "assignment",
            "var_name": left,
            "expr": right
        }
    
    def check_statement(self, stmt):
        """Type check a statement"""
        if stmt["type"] == "typed_declaration":
            # Check if the expression type matches the declared type
            expr_type = self.infer_expression_type(stmt["expr"])
            
            if not expr_type.can_coerce_to(stmt["declared_type"]):
                self.errors.append(
                    f"Type mismatch: Cannot assign {expr_type} to {stmt['declared_type']} "
                    f"for variable '{stmt['var_name']}'"
                )
            elif expr_type.kind != stmt["declared_type"].kind:
                self.warnings.append(
                    f"Implicit type coercion: {expr_type} -> {stmt['declared_type']} "
                    f"for variable '{stmt['var_name']}'"
                )
        
        elif stmt["type"] == "assignment":
            var_name = stmt["var_name"]
            
            # Check if variable was declared
            if var_name not in self.symbol_table:
                self.errors.append(f"Undeclared variable: '{var_name}'")
                return
            
            # Check if assigned type matches declared type
            expr_type = self.infer_expression_type(stmt["expr"])
            declared_type = self.symbol_table[var_name]
            
            if not expr_type.can_coerce_to(declared_type):
                self.errors.append(
                    f"Type mismatch: Cannot assign {expr_type} to {declared_type} "
                    f"for variable '{var_name}'"
                )
    
    def infer_expression_type(self, expr: str) -> Type:
        """Infer the type of an expression"""
        expr = expr.strip()
        
        # Integer literal
        if re.match(r'^\d+$', expr):
            return Type(kind=TypeKind.INT)
        
        # Float literal
        if re.match(r'^\d+\.\d+$', expr):
            return Type(kind=TypeKind.FLOAT)
        
        # String literal
        if expr.startswith('"') and expr.endswith('"'):
            return Type(kind=TypeKind.STRING)
        
        # Binary operation
        for op in ['+', '-', '*', '/']:
            if op in expr:
                parts = expr.split(op, 1)
                left_type = self.infer_expression_type(parts[0].strip())
                right_type = self.infer_expression_type(parts[1].strip())
                
                # Type coercion rules for arithmetic
                if left_type.is_numeric() and right_type.is_numeric():
                    if left_type.kind == TypeKind.FLOAT or right_type.kind == TypeKind.FLOAT:
                        return Type(kind=TypeKind.FLOAT)
                    return Type(kind=TypeKind.INT)
                
                # String concatenation
                if op == '+' and (left_type.kind == TypeKind.STRING or right_type.kind == TypeKind.STRING):
                    return Type(kind=TypeKind.STRING)
                
                return Type(kind=TypeKind.ERROR)
        
        # Variable reference
        if expr in self.symbol_table:
            return self.symbol_table[expr]
        
        return Type(kind=TypeKind.UNKNOWN)
    
    def peek(self):
        return self.tokens[self.current] if not self.is_end() else None
    
    def advance(self):
        if not self.is_end():
            self.current += 1
            return self.tokens[self.current - 1]
        return None
    
    def is_end(self):
        return self.current >= len(self.tokens)



# PART 4: TYPE INFERENCE SYSTEM (Hindley-Milner Style)

class TypeInferenceParser:
    """
    Type inference: Types are automatically deduced from context.
    No explicit type declarations needed, but types are still checked.
    
    Example:
        x = 10          # x inferred as int
        y = x + 3.14    # y inferred as float (int coerces to float)
    """
    
    def __init__(self, code: str):
        self.tokens = code.splitlines()
        self.current = 0
        self.symbol_table: Dict[str, Type] = {}
        self.type_constraints: List[tuple] = []
        self.errors: List[str] = []
    
    def parse_and_infer(self):
        """Parse program and infer all types"""
        ast = []
        
        while not self.is_end():
            stmt = self.parse_statement()
            if stmt:
                ast.append(stmt)
        
        # Perform type inference
        self.infer_types(ast)
        
        return ast, self.symbol_table
    
    def parse_statement(self):
        line = self.peek()
        if not line or not line.strip():
            self.advance()
            return None
        
        line = line.strip()
        
        if "=" in line:
            return self.parse_assignment()
        
        self.advance()
        return None
    
    def parse_assignment(self):
        line = self.advance().strip()
        left, right = map(str.strip, line.split("=", 1))
        
        return {
            "type": "assignment",
            "var_name": left,
            "expr": right
        }
    
    def infer_types(self, ast):
        """Infer types for all variables"""
        for stmt in ast:
            if stmt["type"] == "assignment":
                var_name = stmt["var_name"]
                expr_type = self.infer_expression_type(stmt["expr"])
                
                if var_name in self.symbol_table:
                    # Variable already has a type - check compatibility
                    existing_type = self.symbol_table[var_name]
                    if not self.types_compatible(existing_type, expr_type):
                        self.errors.append(
                            f"Type conflict for '{var_name}': "
                            f"inferred as {existing_type} and {expr_type}"
                        )
                else:
                    # First assignment - establish type
                    self.symbol_table[var_name] = expr_type
    
    def infer_expression_type(self, expr: str) -> Type:
        """Infer type of expression through analysis"""
        expr = expr.strip()
        
        # Literals
        if re.match(r'^\d+$', expr):
            return Type(kind=TypeKind.INT)
        if re.match(r'^\d+\.\d+$', expr):
            return Type(kind=TypeKind.FLOAT)
        if expr.startswith('"') and expr.endswith('"'):
            return Type(kind=TypeKind.STRING)
        
        # Binary operations
        for op in ['+', '-', '*', '/']:
            if op in expr:
                parts = expr.split(op, 1)
                left_type = self.infer_expression_type(parts[0].strip())
                right_type = self.infer_expression_type(parts[1].strip())
                
                # Numeric promotion rules
                if left_type.is_numeric() and right_type.is_numeric():
                    if left_type.kind == TypeKind.FLOAT or right_type.kind == TypeKind.FLOAT:
                        return Type(kind=TypeKind.FLOAT)
                    return Type(kind=TypeKind.INT)
                
                if op == '+' and left_type.kind == TypeKind.STRING:
                    return Type(kind=TypeKind.STRING)
        
        # Variable reference
        if expr in self.symbol_table:
            return self.symbol_table[expr]
        
        return Type(kind=TypeKind.UNKNOWN)
    
    def types_compatible(self, t1: Type, t2: Type) -> bool:
        """Check if two types are compatible"""
        if t1.kind == t2.kind:
            return True
        # Allow int/float compatibility
        if {t1.kind, t2.kind} == {TypeKind.INT, TypeKind.FLOAT}:
            return True
        return False
    
    def peek(self):
        return self.tokens[self.current] if not self.is_end() else None
    
    def advance(self):
        if not self.is_end():
            self.current += 1
            return self.tokens[self.current - 1]
        return None
    
    def is_end(self):
        return self.current >= len(self.tokens)


# PART 5: ENHANCED TAC WITH TYPE COERCION

class TypeCoercionTACParser:
    """
    Demonstrates explicit type coercion rules.
    Handles mixed-type arithmetic with well-defined promotion rules.
    
    Coercion Hierarchy: int -> float -> string
    """
    
    def __init__(self, code: str):
        self.tokens = code.splitlines()
        self.current = 0
        self.symbol_table: Dict[str, Dict[str, Any]] = {}
        self.coercion_log: List[str] = []
    
    def parse_and_execute(self):
        """Execute with type coercion tracking"""
        while not self.is_end():
            stmt = self.parse_statement()
            if stmt:
                self.execute_with_coercion(stmt)
        
        return self.symbol_table, self.coercion_log
    
    def parse_statement(self):
        line = self.peek()
        if not line or not line.strip():
            self.advance()
            return None
        
        line = line.strip()
        
        if "=" in line:
            line_text = self.advance().strip()
            left, right = map(str.strip, line_text.split("=", 1))
            return {"type": "assignment", "left": left, "right": right}
        
        self.advance()
        return None
    
    def execute_with_coercion(self, stmt):
        """Execute statement with type coercion"""
        if stmt["type"] == "assignment":
            value, result_type = self.evaluate_with_coercion(stmt["right"])
            
            self.symbol_table[stmt["left"]] = {
                "value": value,
                "type": result_type
            }
    
    def evaluate_with_coercion(self, expr: str):
        """Evaluate expression with automatic type coercion"""
        expr = expr.strip()
        
        # Literals
        if re.match(r'^\d+$', expr):
            return int(expr), TypeKind.INT
        if re.match(r'^\d+\.\d+$', expr):
            return float(expr), TypeKind.FLOAT
        
        # Binary operations with coercion
        for op in ['+', '-', '*', '/']:
            if op in expr:
                parts = expr.split(op, 1)
                left_val, left_type = self.evaluate_with_coercion(parts[0].strip())
                right_val, right_type = self.evaluate_with_coercion(parts[1].strip())
                
                # Determine result type (promote to higher type)
                result_type = self.coerce_types(left_type, right_type)
                
                # Log coercion if it occurred
                if left_type != result_type or right_type != result_type:
                    self.coercion_log.append(
                        f"Coercion in '{expr}': {left_type.value} {op} {right_type.value} -> {result_type.value}"
                    )
                
                # Perform coercion
                left_val = self.coerce_value(left_val, left_type, result_type)
                right_val = self.coerce_value(right_val, right_type, result_type)
                
                # Perform operation
                if op == '+':
                    return left_val + right_val, result_type
                elif op == '-':
                    return left_val - right_val, result_type
                elif op == '*':
                    return left_val * right_val, result_type
                elif op == '/':
                    return left_val / right_val, TypeKind.FLOAT
        
        # Variable reference
        if expr in self.symbol_table:
            entry = self.symbol_table[expr]
            return entry["value"], entry["type"]
        
        return None, TypeKind.UNKNOWN
    
    def coerce_types(self, t1: TypeKind, t2: TypeKind) -> TypeKind:
        """Determine the result type after coercion"""
        # Float takes precedence over int
        if t1 == TypeKind.FLOAT or t2 == TypeKind.FLOAT:
            return TypeKind.FLOAT
        if t1 == TypeKind.INT or t2 == TypeKind.INT:
            return TypeKind.INT
        return t1
    
    def coerce_value(self, value, from_type: TypeKind, to_type: TypeKind):
        """Coerce a value from one type to another"""
        if from_type == to_type:
            return value
        
        if to_type == TypeKind.FLOAT and from_type == TypeKind.INT:
            return float(value)
        if to_type == TypeKind.INT and from_type == TypeKind.FLOAT:
            return int(value)
        
        return value
    
    def peek(self):
        return self.tokens[self.current] if not self.is_end() else None
    
    def advance(self):
        if not self.is_end():
            self.current += 1
            return self.tokens[self.current - 1]
        return None
    
    def is_end(self):
        return self.current >= len(self.tokens)


# DEMONSTRATION AND TESTING

def demo_dynamic_typing():
    print("\nDYNAMIC TYPING DEMONSTRATION\n")
    print("In dynamic typing, types are checked at runtime.")
    print("Variables can change types during execution.\n")
    
    code = """x = 10
y = 3.14
t1 = x + 5
t2 = y + 2.86
print t1
print t2"""
    
    print("Code:")
    print(code)
    print("\nExecution:")
    
    parser = DynamicTACParser(code)
    output = parser.parse_and_execute()
    
    for line in output:
        print(f"  {line}")
    
    print("\nSymbol Table:")
    for var, info in parser.symbol_table.items():
        print(f"  {var}: {info['type'].value} = {info['value']}")
    print()


def demo_static_typing():
    print("\nSTATIC TYPING DEMONSTRATION\n")
    print("In static typing, types are checked before execution.")
    print("Type errors are caught during the type-checking phase.\n")
    
    # Valid program
    code_valid = """int x = 10
float y = 3.14
int t1 = x + 5"""
    
    print("Valid Program:")
    print(code_valid)
    
    parser = StaticTACParser(code_valid)
    parser.parse()
    is_valid = parser.type_check()
    
    print(f"\nType Check Result: {'PASSED' if is_valid else 'FAILED'}")
    
    if parser.warnings:
        print("\nWarnings:")
        for warning in parser.warnings:
            print(f"  Warning: {warning}")
    
    print("\nSymbol Table:")
    for var, typ in parser.symbol_table.items():
        print(f"  {var}: {typ}")
    
    # Invalid program
    print("- - -\n")
    code_invalid = """int x = 10
x = 3.14
float y = "hello" """
    
    print("Invalid Program:")
    print(code_invalid)
    
    parser2 = StaticTACParser(code_invalid)
    parser2.parse()
    is_valid2 = parser2.type_check()
    
    print(f"\nType Check Result: {'PASSED' if is_valid2 else 'FAILED'}")
    
    if parser2.errors:
        print("\nErrors:")
        for error in parser2.errors:
            print(f"  Error: {error}")
    print()


def demo_type_inference():
    print("\nTYPE INFERENCE DEMONSTRATION\n")
    print("Type inference automatically deduces types from context.")
    print("No explicit type annotations needed!\n")
    
    code = """x = 10
y = 3.14
t1 = x + 5
t2 = y + 2.86
t3 = x + y"""
    
    print("Code (no type annotations):")
    print(code)
    
    parser = TypeInferenceParser(code)
    ast, symbol_table = parser.parse_and_infer()
    
    print("\nInferred Types:")
    for var, typ in symbol_table.items():
        print(f"  {var}: {typ}")
    
    if parser.errors:
        print("\nType Errors:")
        for error in parser.errors:
            print(f"  ✗ {error}")
    print()


def demo_type_coercion():
    print("\nTYPE COERCION DEMONSTRATION\n")
    print("Type coercion automatically converts between compatible types.")
    print("Follows the hierarchy: int -> float\n")
    
    code = """x = 5
y = 3.14
t1 = x + y
t2 = x + 10
t3 = y + 2.86"""
    
    print("Code:")
    print(code)
    
    parser = TypeCoercionTACParser(code)
    symbol_table, coercion_log = parser.parse_and_execute()
    
    print("\nCoercion Log:")
    for log in coercion_log:
        print(f"  Log: {log}")
    
    print("\nFinal Symbol Table:")
    for var, info in symbol_table.items():
        print(f"  {var}: {info['type'].value} = {info['value']}")
    print()


def main():    
    demo_dynamic_typing()
    demo_static_typing()
    demo_type_inference()
    demo_type_coercion()


if __name__ == "__main__":
    main()
