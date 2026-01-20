"""
Advanced Semantic Analysis Demo
Part 2: Function Verification & Control Flow Analysis
"""

from typing import Dict, List, Any, Optional, Set
from enum import Enum


#  TYPES & BASIC STRUCTURES 

class Type(Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOL = "bool"
    VOID = "void"

class FunctionSignature:
    def __init__(self, name: str, params: List[tuple], return_type: Type):
        self.name = name
        self.params = params  # List of (param_name, param_type)
        self.return_type = return_type
    
    def __repr__(self):
        params_str = ", ".join([f"{name}: {typ.value}" for name, typ in self.params])
        return f"{self.name}({params_str}) -> {self.return_type.value}"


#  PART 1: FUNCTION VERIFICATION 

class FunctionVerifier:
    def __init__(self):
        self.functions: Dict[str, FunctionSignature] = {}
        self.errors: List[str] = []
    
    def declare_function(self, name: str, params: List[tuple], return_type: Type) -> Optional[str]:
        if name in self.functions:
            return f"Error: Function '{name}' already declared"
        
        self.functions[name] = FunctionSignature(name, params, return_type)
        return None
    
    def verify_call(self, name: str, args: List[Type]) -> Optional[str]:
        if name not in self.functions:
            return f"Error: Undefined function '{name}'"
        
        func = self.functions[name]
        
        # Check argument count
        if len(args) != len(func.params):
            return f"Error: Function '{name}' expects {len(func.params)} arguments, got {len(args)}"
        
        # Check argument types
        for i, (arg_type, (param_name, param_type)) in enumerate(zip(args, func.params)):
            if arg_type != param_type:
                # Allow int -> float conversion
                if not (arg_type == Type.INT and param_type == Type.FLOAT):
                    return f"Error: Argument {i+1} of '{name}': expected {param_type.value}, got {arg_type.value}"
        
        return None
    
    def get_return_type(self, name: str) -> Optional[Type]:
        if name in self.functions:
            return self.functions[name].return_type
        return None
    
    def display(self):
        print("\n Function Table ")
        if not self.functions:
            print("  (No functions declared)")
        for name, func in self.functions.items():
            print(f"  {func}")


#  PART 2: CONTROL FLOW ANALYSIS 

class ControlFlowAnalyzer:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def analyze_block(self, statements: List[Dict[str, Any]], context: str = "block") -> Dict[str, Any]:
        """
        Analyze a block of statements
        Returns: {
            'has_return': bool,
            'unreachable_code': List[int],  # Line numbers
            'all_paths_return': bool
        }
        """
        result = {
            'has_return': False,
            'unreachable_code': [],
            'all_paths_return': False
        }
        
        found_return = False
        
        for i, stmt in enumerate(statements):
            stmt_type = stmt.get("type")
            
            # Check for unreachable code after return
            if found_return:
                result['unreachable_code'].append(i)
                self.warnings.append(f"Warning: Unreachable code at statement {i+1} in {context}")
            
            # Track returns
            if stmt_type == "return":
                found_return = True
                result['has_return'] = True
            
            # Analyze if-else statements
            elif stmt_type == "if_else":
                if_result = self.analyze_block(stmt.get("if_body", []), f"{context}/if")
                else_result = self.analyze_block(stmt.get("else_body", []), f"{context}/else")
                
                # Both branches must return for all paths to return
                if if_result['has_return'] and else_result['has_return']:
                    found_return = True
                    result['has_return'] = True
            
            # Analyze loops
            elif stmt_type == "while":
                loop_result = self.analyze_block(stmt.get("body", []), f"{context}/while")
                # Loops don't guarantee execution, so we can't assume return
            
            elif stmt_type == "for":
                loop_result = self.analyze_block(stmt.get("body", []), f"{context}/for")
        
        result['all_paths_return'] = found_return
        return result
    
    def check_function_returns(self, func_name: str, return_type: Type, body: List[Dict[str, Any]]) -> Optional[str]:
        if return_type == Type.VOID:
            return None  # Void functions don't need to return
        
        result = self.analyze_block(body, f"function {func_name}")
        
        if not result['all_paths_return']:
            return f"Error: Function '{func_name}' may not return a value on all paths"
        
        return None
    
    def check_infinite_loop(self, condition: str) -> Optional[str]:
        if condition == "true" or condition == "1":
            self.warnings.append("Warning: Potential infinite loop detected (condition always true)")
        return None
    
    def check_break_continue_context(self, stmt_type: str, in_loop: bool) -> Optional[str]:
        if stmt_type in ["break", "continue"] and not in_loop:
            return f"Error: '{stmt_type}' statement outside of loop"
        return None


#  PART 3: COMBINED ANALYSER 

class AdvancedSemanticAnalyzer:
    def __init__(self):
        self.func_verifier = FunctionVerifier()
        self.flow_analyzer = ControlFlowAnalyzer()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.in_loop = False  # Track if we're inside a loop
    
    def analyze_program(self, program: List[Dict[str, Any]]):
        for stmt in program:
            error = self.analyze_statement(stmt)
            if error:
                self.errors.append(error)
    
    def analyze_statement(self, stmt: Dict[str, Any]) -> Optional[str]:
        stmt_type = stmt.get("type")
        
        if stmt_type == "function_decl":
            return self.func_verifier.declare_function(
                stmt["name"],
                stmt["params"],
                Type[stmt["return_type"].upper()]
            )
        
        elif stmt_type == "function_def":
            # Declare function
            error = self.func_verifier.declare_function(
                stmt["name"],
                stmt["params"],
                Type[stmt["return_type"].upper()]
            )
            if error:
                return error
            
            # Analyze function body
            old_in_loop = self.in_loop
            for s in stmt.get("body", []):
                err = self.analyze_statement(s)
                if err:
                    self.errors.append(err)
            self.in_loop = old_in_loop
            
            # Check if function returns properly
            return_type = Type[stmt["return_type"].upper()]
            return self.flow_analyzer.check_function_returns(
                stmt["name"],
                return_type,
                stmt.get("body", [])
            )
        
        elif stmt_type == "function_call":
            arg_types = [Type[t.upper()] for t in stmt["arg_types"]]
            return self.func_verifier.verify_call(stmt["name"], arg_types)
        
        elif stmt_type == "while":
            self.flow_analyzer.check_infinite_loop(stmt.get("condition", ""))
            old_in_loop = self.in_loop
            self.in_loop = True
            for s in stmt.get("body", []):
                self.analyze_statement(s)
            self.in_loop = old_in_loop
        
        elif stmt_type in ["break", "continue"]:
            return self.flow_analyzer.check_break_continue_context(stmt_type, self.in_loop)
        
        return None
    
    def report(self):
        self.func_verifier.display()
        
        # Collect all errors and warnings
        all_errors = self.errors + self.func_verifier.errors + self.flow_analyzer.errors
        all_warnings = self.warnings + self.flow_analyzer.warnings
        
        print("\n Analysis Results ")
        
        if all_errors:
            print(f"\nErrors ({len(all_errors)}):")
            for i, error in enumerate(all_errors, 1):
                print(f"  {i}. {error}")
        else:
            print("\n✓ No errors found!")
        
        if all_warnings:
            print(f"\nWarnings ({len(all_warnings)}):")
            for i, warning in enumerate(all_warnings, 1):
                print(f"  {i}. {warning}")



def sample_valid_function():
    print("\n" + "-"*40)
    print("SAMPLE 1: Valid Function")
    print("-"*40)
    
    program = [
        {
            "type": "function_def",
            "name": "add",
            "params": [("a", Type.INT), ("b", Type.INT)],
            "return_type": "int",
            "body": [
                {"type": "return", "value": "a + b"}
            ]
        },
        {
            "type": "function_call",
            "name": "add",
            "arg_types": ["int", "int"]
        }
    ]
    
    analyzer = AdvancedSemanticAnalyzer()
    analyzer.analyze_program(program)
    analyzer.report()

def sample_wrong_arguments():
    """Example: Function called with wrong argument types"""
    print("\n" + "-"*40)
    print("SAMPLE 2: Wrong Argument Types")
    print("-"*40)
    
    program = [
        {
            "type": "function_decl",
            "name": "greet",
            "params": [("name", Type.STRING), ("age", Type.INT)],
            "return_type": "void"
        },
        {
            "type": "function_call",
            "name": "greet",
            "arg_types": ["int", "string"]  # Wrong order!
        }
    ]
    
    analyzer = AdvancedSemanticAnalyzer()
    analyzer.analyze_program(program)
    analyzer.report()

def sample_missing_return():
    """Example: Function doesn't return on all paths"""
    print("\n" + "-"*40)
    print("SAMPLE 3: Missing Return Path")
    print("-"*40)
    
    program = [
        {
            "type": "function_def",
            "name": "divide",
            "params": [("a", Type.INT), ("b", Type.INT)],
            "return_type": "int",
            "body": [
                {
                    "type": "if_else",
                    "if_body": [
                        {"type": "return", "value": "a / b"}
                    ],
                    "else_body": [
                        {"type": "print", "value": "Error"}
                        # Missing return here!
                    ]
                }
            ]
        }
    ]
    
    analyzer = AdvancedSemanticAnalyzer()
    analyzer.analyze_program(program)
    analyzer.report()

def sample_unreachable_code():
    """Example: Code after return is unreachable"""
    print("\n" + "-"*40)
    print("SAMPLE 4: Unreachable Code")
    print("-"*40)
    
    program = [
        {
            "type": "function_def",
            "name": "example",
            "params": [],
            "return_type": "int",
            "body": [
                {"type": "return", "value": "42"},
                {"type": "print", "value": "This will never execute"},  # Unreachable!
                {"type": "assign", "name": "x", "value": "10"}  # Unreachable!
            ]
        }
    ]
    
    analyzer = AdvancedSemanticAnalyzer()
    analyzer.analyze_program(program)
    analyzer.report()

def sample_break_outside_loop():
    """Example: Break statement outside loop"""
    print("\n" + "-"*40)
    print("SAMPLE 5: Break Outside Loop")
    print("-"*40)
    
    program = [
        {
            "type": "function_def",
            "name": "test",
            "params": [],
            "return_type": "void",
            "body": [
                {"type": "break"}  # Error: not in a loop!
            ]
        }
    ]
    
    analyzer = AdvancedSemanticAnalyzer()
    analyzer.analyze_program(program)
    analyzer.report()

def sample_all_paths_return():
    print("\n" + "-"*40)
    print("SAMPLE 6: All Paths Return (Valid)")
    print("-"*40)
    
    program = [
        {
            "type": "function_def",
            "name": "max",
            "params": [("a", Type.INT), ("b", Type.INT)],
            "return_type": "int",
            "body": [
                {
                    "type": "if_else",
                    "if_body": [
                        {"type": "return", "value": "a"}
                    ],
                    "else_body": [
                        {"type": "return", "value": "b"}
                    ]
                }
            ]
        }
    ]
    
    analyzer = AdvancedSemanticAnalyzer()
    analyzer.analyze_program(program)
    analyzer.report()



if __name__ == "__main__":
    sample_valid_function()
    sample_wrong_arguments()
    sample_missing_return()
    sample_unreachable_code()
    sample_break_outside_loop()
    sample_all_paths_return()
