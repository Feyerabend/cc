#!/usr/bin/env python3

from compiler_core import Plugin, ASTNode, CompilerContext, MessageCollector, Visitor
from compiler_core import BlockNode, NestedBlockNode, AssignNode, CallNode, ReadNode, WriteNode
from compiler_core import CompoundNode, IfNode, WhileNode, OperationNode, VariableNode, NumberNode
from typing import Dict, Any, Set, Optional, List, Tuple
from enum import Enum


class PL0Type(Enum):
    """PL/0 data types"""
    INTEGER = "integer"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"
    ERROR = "error"
    VOID = "void"  # For procedures

class TypeInferencePlugin(Plugin):
    def __init__(self):
        super().__init__(
            "type_inference",
            "Infers and checks variable types in PL/0 programs",
            "1.0"
        )
        self.dependencies = ["static_analysis"]
        self.enabled = True
    
    def run(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> Dict[str, Any]:
        messages.debug("Starting type_inference plugin", source="TypeInference")
        type_checker = TypeChecker(messages)
        type_data = type_checker.check_types(ast)
        
        # Generate outputs
        context.generated_outputs["type_report"] = type_checker.generate_report()
        context.generated_outputs["type_analysis"] = type_checker.generate_detailed_analysis()
        context.generated_outputs["type_errors"] = type_checker.generate_error_summary()
        
        messages.debug("Completed type_inference plugin", source="TypeInference")
        return type_data

class TypeChecker(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.variable_types = {}  # var_name -> PL0Type
        self.procedure_types = {}  # proc_name -> PL0Type (always VOID in PL/0)
        self.current_scope = []  # Stack of scopes for nested blocks
        self.scope_variables = [set()]  # Variables declared in each scope
        self.type_errors = []  # List of error messages
        self.type_warnings = []  # List of warning messages
        self.expression_types = {}  # Cache expression types for analysis
        self.variable_usage = {}  # Track variable usage patterns
        self.current_procedure = None
    
    def check_types(self, ast: ASTNode) -> Dict[str, Any]:
        """Main type checking entry point"""
        ast.accept(self)
        return {
            "type_errors": len(self.type_errors),
            "type_warnings": len(self.type_warnings),
            "inferred_types": len(self.variable_types),
            "procedures": len(self.procedure_types),
            "scopes_analyzed": len(self.scope_variables)
        }
    
    def enter_scope(self):
        """Enter a new scope"""
        self.current_scope.append(len(self.scope_variables))
        self.scope_variables.append(set())
    
    def exit_scope(self):
        """Exit current scope"""
        if self.current_scope:
            self.current_scope.pop()
            self.scope_variables.pop()
    
    def declare_variable(self, var_name: str, var_type: PL0Type):
        """Declare a variable in the current scope"""
        if self.scope_variables and var_name in self.scope_variables[-1]:
            self.add_error(f"Variable '{var_name}' already declared in current scope")
        else:
            self.variable_types[var_name] = var_type
            if self.scope_variables:
                self.scope_variables[-1].add(var_name)
            self.variable_usage[var_name] = {"declarations": 1, "assignments": 0, "uses": 0}
    
    def lookup_variable(self, var_name: str) -> PL0Type:
        """Look up variable type"""
        if var_name in self.variable_types:
            self.variable_usage.setdefault(var_name, {"declarations": 0, "assignments": 0, "uses": 0})
            self.variable_usage[var_name]["uses"] += 1
            return self.variable_types[var_name]
        else:
            self.add_error(f"Variable '{var_name}' used before declaration")
            return PL0Type.ERROR
    
    def add_error(self, message: str):
        """Add a type error"""
        self.type_errors.append(message)
        self.messages.error(message, source="TypeChecker")
    
    def add_warning(self, message: str):
        """Add a type warning"""
        self.type_warnings.append(message)
        self.messages.warning(message, source="TypeChecker")
    
    def generate_report(self) -> str:
        """Generate summary type report"""
        lines = [
            "Type Inference Report",
            "=" * 22,
            f"Type Errors: {len(self.type_errors)}",
            f"Type Warnings: {len(self.type_warnings)}",
            f"Variables Analyzed: {len(self.variable_types)}",
            f"Procedures Analyzed: {len(self.procedure_types)}",
            "",
            "Variable Types:"
        ]
        
        for var, var_type in sorted(self.variable_types.items()):
            usage = self.variable_usage.get(var, {})
            usage_info = f"(used {usage.get('uses', 0)} times)"
            lines.append(f"  • {var}: {var_type.value} {usage_info}")
        
        if self.procedure_types:
            lines.append("")
            lines.append("Procedures:")
            for proc, proc_type in sorted(self.procedure_types.items()):
                lines.append(f"  • {proc}: {proc_type.value}")
        
        return "\n".join(lines)
    
    def generate_detailed_analysis(self) -> str:
        """Generate detailed type analysis"""
        lines = [
            "Detailed Type Analysis",
            "=" * 25,
            "",
            "Variable Usage Patterns:"
        ]
        
        for var, usage in sorted(self.variable_usage.items()):
            var_type = self.variable_types.get(var, PL0Type.UNKNOWN)
            lines.append(f"  {var} ({var_type.value}):")
            lines.append(f"    Declarations: {usage.get('declarations', 0)}")
            lines.append(f"    Assignments: {usage.get('assignments', 0)}")
            lines.append(f"    Uses: {usage.get('uses', 0)}")
            
            # Analysis
            if usage.get('declarations', 0) > 1:
                lines.append(f"    W  Multiple declarations detected")
            if usage.get('assignments', 0) == 0 and usage.get('uses', 0) > 0:
                lines.append(f"    W  Used but never assigned")
            if usage.get('uses', 0) == 0:
                lines.append(f"    W  Declared but never used")
        
        if self.expression_types:
            lines.append("")
            lines.append("Expression Type Summary:")
            type_counts = {}
            for expr_type in self.expression_types.values():
                type_counts[expr_type] = type_counts.get(expr_type, 0) + 1
            for expr_type, count in sorted(type_counts.items()):
                lines.append(f"  {expr_type.value}: {count} expressions")
        
        return "\n".join(lines)
    
    def generate_error_summary(self) -> str:
        """Generate error and warning summary"""
        lines = [
            "Type Errors and Warnings",
            "=" * 25
        ]
        
        if self.type_errors:
            lines.append("")
            lines.append("Errors:")
            for i, error in enumerate(self.type_errors, 1):
                lines.append(f"  {i}. {error}")
        
        if self.type_warnings:
            lines.append("")
            lines.append("Warnings:")
            for i, warning in enumerate(self.type_warnings, 1):
                lines.append(f"  {i}. {warning}")
        
        if not self.type_errors and not self.type_warnings:
            lines.append("")
            lines.append("  No type errors or warnings found!")
        
        return "\n".join(lines)
    
    def infer_expression_type(self, expr: ASTNode) -> PL0Type:
        """Infer the type of an expression"""
        if isinstance(expr, NumberNode):
            expr_type = PL0Type.INTEGER
        elif isinstance(expr, VariableNode):
            expr_type = self.lookup_variable(expr.name)
        elif isinstance(expr, OperationNode):
            left_type = self.infer_expression_type(expr.left)
            right_type = self.infer_expression_type(expr.right)
            
            # Type checking for operations
            if expr.operator in ["+", "-", "*", "/"]:
                if left_type != PL0Type.INTEGER or right_type != PL0Type.INTEGER:
                    self.add_error(f"Arithmetic operation '{expr.operator}' requires integer operands")
                    expr_type = PL0Type.ERROR
                else:
                    expr_type = PL0Type.INTEGER
            elif expr.operator in ["=", "<", ">", "<=", ">="]:
                if left_type != right_type:
                    self.add_error(f"Comparison '{expr.operator}' requires operands of same type")
                    expr_type = PL0Type.ERROR
                elif left_type == PL0Type.ERROR or right_type == PL0Type.ERROR:
                    expr_type = PL0Type.ERROR
                else:
                    expr_type = PL0Type.BOOLEAN
            else:
                self.add_error(f"Unknown operator: {expr.operator}")
                expr_type = PL0Type.ERROR
        else:
            expr_type = PL0Type.UNKNOWN
        
        # Cache the expression type
        self.expression_types[id(expr)] = expr_type
        return expr_type
    
    # Visitor methods
    def visit_block(self, node: BlockNode):
        """Handle program blocks"""
        self.enter_scope()
        
        # Declare all variables as integers (PL/0 only has integer variables)
        for var_name in node.variables:
            self.declare_variable(var_name, PL0Type.INTEGER)
        
        # Process procedures
        for proc_name, proc_body in node.procedures:
            # Declare procedure
            self.procedure_types[proc_name] = PL0Type.VOID
            
            # Enter procedure scope
            old_procedure = self.current_procedure
            self.current_procedure = proc_name
            self.enter_scope()
            
            # Process procedure body
            proc_body.accept(self)
            
            # Exit procedure scope
            self.exit_scope()
            self.current_procedure = old_procedure
        
        # Process main statement
        node.statement.accept(self)
        
        self.exit_scope()
    
    def visit_nested_block(self, node: NestedBlockNode):
        """Handle nested blocks with local variables"""
        self.enter_scope()
        
        # Declare local variables
        for var_name in node.variables:
            self.declare_variable(var_name, PL0Type.INTEGER)
        
        # Process statements
        for stmt in node.statements:
            stmt.accept(self)
        
        self.exit_scope()
    
    def visit_assign(self, node: AssignNode):
        """Handle assignment statements"""
        # Check if variable is declared
        var_type = self.lookup_variable(node.var_name)
        
        # Infer expression type
        expr_type = self.infer_expression_type(node.expression)
        
        # Type compatibility check
        if var_type != PL0Type.ERROR and expr_type != PL0Type.ERROR:
            if var_type != expr_type:
                self.add_error(f"Type mismatch in assignment to '{node.var_name}': "
                             f"expected {var_type.value}, got {expr_type.value}")
        
        # Record assignment
        if node.var_name in self.variable_usage:
            self.variable_usage[node.var_name]["assignments"] += 1
        
        # Visit expression
        node.expression.accept(self)
    
    def visit_call(self, node: CallNode):
        """Handle procedure calls"""
        if node.proc_name not in self.procedure_types:
            self.add_error(f"Procedure '{node.proc_name}' not declared")
    
    def visit_read(self, node: ReadNode):
        """Handle read statements"""
        var_type = self.lookup_variable(node.var_name)
        
        # READ can only read integers in PL/0
        if var_type != PL0Type.INTEGER and var_type != PL0Type.ERROR:
            self.add_error(f"READ statement requires integer variable, got {var_type.value}")
        
        # Record assignment (READ assigns a value)
        if node.var_name in self.variable_usage:
            self.variable_usage[node.var_name]["assignments"] += 1
    
    def visit_write(self, node: WriteNode):
        """Handle write statements"""
        expr_type = self.infer_expression_type(node.expression)
        
        # WRITE can output integers or booleans, but typically integers
        if expr_type == PL0Type.ERROR:
            self.add_error("Invalid expression in WRITE statement")
        elif expr_type == PL0Type.BOOLEAN:
            self.add_warning("Writing boolean value (will be 0 or 1)")
        
        node.expression.accept(self)
    
    def visit_compound(self, node: CompoundNode):
        """Handle compound statements"""
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        """Handle if statements"""
        # Check condition type
        cond_type = self.infer_expression_type(node.condition)
        if cond_type != PL0Type.BOOLEAN and cond_type != PL0Type.ERROR:
            self.add_error(f"IF condition must be boolean, got {cond_type.value}")
        
        # Visit condition and then statement
        node.condition.accept(self)
        node.then_statement.accept(self)
    
    def visit_while(self, node: WhileNode):
        """Handle while statements"""
        # Check condition type
        cond_type = self.infer_expression_type(node.condition)
        if cond_type != PL0Type.BOOLEAN and cond_type != PL0Type.ERROR:
            self.add_error(f"WHILE condition must be boolean, got {cond_type.value}")
        
        # Visit condition and body
        node.condition.accept(self)
        node.body.accept(self)
    
    def visit_operation(self, node: OperationNode):
        """Handle operations"""
        # Type inference is done in infer_expression_type
        node.left.accept(self)
        node.right.accept(self)
    
    def visit_variable(self, node: VariableNode):
        """Handle variable references"""
        # Type checking is done in infer_expression_type
        self.lookup_variable(node.name)
    
    def visit_number(self, node: NumberNode):
        """Handle number literals"""
        # Numbers are always integers in PL/0
        pass
