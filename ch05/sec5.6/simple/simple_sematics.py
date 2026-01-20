"""
Simple Semantic Analyser Demo
Demonstrates key semantic analysis concepts in compiler pipelines
"""

from typing import Dict, List, Any, Optional
from enum import Enum


#  PART 1: SYMBOL TABLE MANAGEMENT 

class SymbolType(Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOL = "bool"
    FUNCTION = "function"

class Symbol:
    def __init__(self, name: str, symbol_type: SymbolType, scope: str, value: Any = None):
        self.name = name
        self.type = symbol_type
        self.scope = scope
        self.value = value
        self.memory_location = id(self)  # Simplified memory location
    
    def __repr__(self):
        return f"Symbol({self.name}, {self.type.value}, scope={self.scope})"

class SymbolTable:
    def __init__(self):
        self.scopes: Dict[str, Dict[str, Symbol]] = {"global": {}}
        self.current_scope = "global"
    
    def enter_scope(self, scope_name: str):
        self.current_scope = scope_name
        if scope_name not in self.scopes:
            self.scopes[scope_name] = {}
    
    def exit_scope(self):
        self.current_scope = "global"
    
    def declare(self, name: str, symbol_type: SymbolType, value: Any = None) -> Optional[str]:
        if name in self.scopes[self.current_scope]:
            return f"Error: Redeclaration of '{name}' in scope '{self.current_scope}'"
        
        symbol = Symbol(name, symbol_type, self.current_scope, value)
        self.scopes[self.current_scope][name] = symbol
        return None
    
    def lookup(self, name: str) -> Optional[Symbol]:
        # Check current scope first
        if name in self.scopes[self.current_scope]:
            return self.scopes[self.current_scope][name]
        # Fall back to global scope
        if name in self.scopes["global"]:
            return self.scopes["global"][name]
        return None
    
    def display(self):
        print("\n Symbol Table ")
        for scope, symbols in self.scopes.items():
            if symbols:
                print(f"\nScope: {scope}")
                for name, symbol in symbols.items():
                    print(f"  {symbol}")


#  PART 2: TYPE CHECKER 

class TypeChecker:
    @staticmethod
    def check_binary_op(left_type: SymbolType, operator: str, right_type: SymbolType) -> Optional[str]:
        # Arithmetic operators
        if operator in ['+', '-', '*', '/']:
            if left_type == SymbolType.STRING and operator == '+' and right_type == SymbolType.STRING:
                return None  # String concatenation
            if left_type in [SymbolType.INT, SymbolType.FLOAT] and \
               right_type in [SymbolType.INT, SymbolType.FLOAT]:
                return None  # Numeric operation
            return f"Error: Cannot apply '{operator}' to {left_type.value} and {right_type.value}"
        
        # Comparison operators
        if operator in ['==', '!=', '<', '>', '<=', '>=']:
            if left_type == right_type:
                return None
            return f"Error: Cannot compare {left_type.value} with {right_type.value}"
        
        return f"Error: Unknown operator '{operator}'"
    
    @staticmethod
    def check_assignment(var_type: SymbolType, value_type: SymbolType) -> Optional[str]:
        if var_type == value_type:
            return None
        # Allow int to float promotion
        if var_type == SymbolType.FLOAT and value_type == SymbolType.INT:
            return None
        return f"Error: Cannot assign {value_type.value} to {var_type.value}"

#  PART 3: SCOPE CHECKER 

class ScopeChecker:
    @staticmethod
    def check_undefined(symbol_table: SymbolTable, name: str) -> Optional[str]:
        if symbol_table.lookup(name) is None:
            return f"Error: Undefined variable '{name}'"
        return None
    
    @staticmethod
    def check_scope_access(symbol_table: SymbolTable, name: str, current_scope: str) -> Optional[str]:
        symbol = symbol_table.lookup(name)
        if symbol is None:
            return f"Error: Variable '{name}' not accessible in scope '{current_scope}'"
        # Variables in local scope or global scope are accessible
        if symbol.scope == current_scope or symbol.scope == "global":
            return None
        return f"Error: Variable '{name}' from scope '{symbol.scope}' not accessible in '{current_scope}'"


#  PART 4: SEMANTIC ANALYSER

class SemanticAnalyzer:    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.type_checker = TypeChecker()
        self.scope_checker = ScopeChecker()
        self.errors: List[str] = []
    
    def analyze_program(self, statements: List[Dict[str, Any]]):
        for stmt in statements:
            error = self.analyze_statement(stmt)
            if error:
                self.errors.append(error)
    
    def analyze_statement(self, stmt: Dict[str, Any]) -> Optional[str]:
        stmt_type = stmt.get("type")
        
        if stmt_type == "declare":
            return self.symbol_table.declare(
                stmt["name"], 
                SymbolType[stmt["var_type"].upper()]
            )
        
        elif stmt_type == "assign":
            # Check if variable exists
            error = self.scope_checker.check_undefined(self.symbol_table, stmt["name"])
            if error:
                return error
            
            # Check type compatibility
            var_symbol = self.symbol_table.lookup(stmt["name"])
            value_type = SymbolType[stmt["value_type"].upper()]
            return self.type_checker.check_assignment(var_symbol.type, value_type)
        
        elif stmt_type == "binary_op":
            # Check if operands exist
            for operand in [stmt["left"], stmt["right"]]:
                if isinstance(operand, str):  # Variable
                    error = self.scope_checker.check_undefined(self.symbol_table, operand)
                    if error:
                        return error
            
            # Get types
            left_type = SymbolType[stmt["left_type"].upper()]
            right_type = SymbolType[stmt["right_type"].upper()]
            
            return self.type_checker.check_binary_op(left_type, stmt["operator"], right_type)
        
        elif stmt_type == "enter_scope":
            self.symbol_table.enter_scope(stmt["scope"])
        
        elif stmt_type == "exit_scope":
            self.symbol_table.exit_scope()
        
        return None
    
    def report(self):
        self.symbol_table.display()
        print("\nSemantic Analysis Results")
        if self.errors:
            print(f"Found {len(self.errors)} error(s):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        else:
            print("No semantic errors found!")



#  SAMPLE PROGRAMS 

def sample_valid_program():
    print("\n" + "-"*40)
    print("SAMPLE 1: Valid Program")
    print("-"*40)
    
    program = [
        {"type": "declare", "name": "x", "var_type": "int"},
        {"type": "declare", "name": "y", "var_type": "int"},
        {"type": "assign", "name": "x", "value_type": "int"},
        {"type": "binary_op", "left": "x", "left_type": "int", 
         "operator": "+", "right": "y", "right_type": "int"},
    ]
    
    analyzer = SemanticAnalyzer()
    analyzer.analyze_program(program)
    analyzer.report()

def sample_redeclaration_error():
    """Example: Redeclaration error"""
    print("\n" + "-"*40)
    print("SAMPLE 2: Redeclaration Error")
    print("-"*40)
    
    program = [
        {"type": "declare", "name": "x", "var_type": "int"},
        {"type": "declare", "name": "x", "var_type": "float"},  # Error!
    ]
    
    analyzer = SemanticAnalyzer()
    analyzer.analyze_program(program)
    analyzer.report()

def sample_type_error():
    """Example: Type mismatch error"""
    print("\n" + "-"*40)
    print("SAMPLE 3: Type Mismatch Error")
    print("-"*40)
    
    program = [
        {"type": "declare", "name": "name", "var_type": "string"},
        {"type": "declare", "name": "age", "var_type": "int"},
        {"type": "binary_op", "left": "name", "left_type": "string", 
         "operator": "+", "right": "age", "right_type": "int"},  # Error!
    ]
    
    analyzer = SemanticAnalyzer()
    analyzer.analyze_program(program)
    analyzer.report()

def sample_undefined_variable():
    """Example: Undefined variable error"""
    print("\n" + "-"*40)
    print("SAMPLE 4: Undefined Variable Error")
    print("-"*40)
    
    program = [
        {"type": "declare", "name": "x", "var_type": "int"},
        {"type": "assign", "name": "y", "value_type": "int"},  # Error: y not declared
    ]
    
    analyzer = SemanticAnalyzer()
    analyzer.analyze_program(program)
    analyzer.report()

def sample_scope_example():
    print("\n" + "-"*40)
    print("SAMPLE 5: Scope Example")
    print("-"*40)
    
    program = [
        {"type": "declare", "name": "global_var", "var_type": "int"},
        {"type": "enter_scope", "scope": "function_main"},
        {"type": "declare", "name": "local_var", "var_type": "string"},
        {"type": "assign", "name": "global_var", "value_type": "int"},  # OK: global accessible
        {"type": "exit_scope"},
    ]
    
    analyzer = SemanticAnalyzer()
    analyzer.analyze_program(program)
    analyzer.report()



if __name__ == "__main__":
    sample_valid_program()
    sample_redeclaration_error()
    sample_type_error()
    sample_undefined_variable()
    sample_scope_example()
