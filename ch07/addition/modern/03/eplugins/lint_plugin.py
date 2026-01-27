#!/usr/bin/env python3

from compiler_core import Plugin, ASTNode, CompilerContext, MessageCollector, Visitor
from compiler_core import BlockNode, NestedBlockNode, AssignNode, CallNode, ReadNode, WriteNode
from compiler_core import CompoundNode, IfNode, WhileNode, OperationNode, VariableNode, NumberNode
from typing import Dict, Any, Set

class PL0LinterPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "pl0_linter",
            "Performs linting checks on PL/0 code",
            "1.0"
        )
        self.dependencies = ["static_analysis"]
        self.enabled = True
    
    def run(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> Dict[str, Any]:
        messages.debug("Starting PL/0 linter plugin", source="PL0Linter")
        linter = PL0Linter(messages)
        linter.lint(ast)
        
        # Store the linting report in context
        context.generated_outputs["lint_report"] = linter.generate_report()
        
        messages.debug("Completed PL/0 linter plugin", source="PL0Linter")
        return {
            "issues_found": linter.issues_found,
            "unused_variables": len(linter.unused_variables)
        }

class PL0Linter(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.issues_found = 0
        self.unused_variables = set()
        self.defined_variables = set()
        self.used_variables = set()
        self.reachable = True  # Tracks if current code is reachable
        self.current_scope_vars = set()
    
    def lint(self, ast: ASTNode):
        ast.accept(self)
    
    def generate_report(self) -> str:
        lines = [
            "PL/0 Linting Report",
            "=" * 30,
            "",
            f"Total Issues Found: {self.issues_found}",
            "",
            "Unused Variables:",
            f"  • {len(self.unused_variables)} variables detected"
        ]
        if self.unused_variables:
            lines.append("  • Details:")
            for var in sorted(self.unused_variables):
                lines.append(f"    - {var}")
        return "\n".join(lines)
    
    def _check_variable_name(self, var_name: str, node: ASTNode):
        # Check for valid variable names (simple check: alphanumeric, no spaces, not starting with digit)
        if not var_name.isidentifier() or var_name[0].isdigit():
            self.issues_found += 1
            self.messages.warning(f"Invalid variable name: '{var_name}'", source="PL0Linter")
    
    def visit_block(self, node: BlockNode):
        old_vars = self.current_scope_vars.copy()
        self.current_scope_vars.update(node.variables)
        self.defined_variables.update(node.variables)
        
        for var in node.variables:
            self._check_variable_name(var, node)
        
        for proc_name, proc_body in node.procedures:
            proc_body.accept(self)
        
        node.statement.accept(self)
        
        # Check for unused variables in this scope
        unused_in_scope = self.current_scope_vars - self.used_variables
        self.unused_variables.update(unused_in_scope)
        for var in unused_in_scope:
            self.issues_found += 1
            self.messages.info(f"Unused variable: {var}", source="PL0Linter")
        
        self.current_scope_vars = old_vars
    
    def visit_nested_block(self, node: NestedBlockNode):
        old_vars = self.current_scope_vars.copy()
        self.current_scope_vars.update(node.variables)
        self.defined_variables.update(node.variables)
        
        for var in node.variables:
            self._check_variable_name(var, node)
        
        for stmt in node.statements:
            stmt.accept(self)
        
        unused_in_scope = self.current_scope_vars - self.used_variables
        self.unused_variables.update(unused_in_scope)
        for var in unused_in_scope:
            self.issues_found += 1
            self.messages.info(f"Unused variable: {var}", source="PL0Linter")
        
        self.current_scope_vars = old_vars
    
    def visit_assign(self, node: AssignNode):
        if not self.reachable:
            self.issues_found += 1
            self.messages.warning("Unreachable code detected in assignment", source="PL0Linter")
        
        self._check_variable_name(node.var_name, node)
        self.used_variables.add(node.var_name)
        node.expression.accept(self)
    
    def visit_call(self, node: CallNode):
        if not self.reachable:
            self.issues_found += 1
            self.messages.warning("Unreachable code detected in procedure call", source="PL0Linter")
    
    def visit_read(self, node: ReadNode):
        if not self.reachable:
            self.issues_found += 1
            self.messages.warning("Unreachable code detected in read statement", source="PL0Linter")
        
        self._check_variable_name(node.var_name, node)
        self.used_variables.add(node.var_name)
    
    def visit_write(self, node: WriteNode):
        if not self.reachable:
            self.issues_found += 1
            self.messages.warning("Unreachable code detected in write statement", source="PL0Linter")
        
        node.expression.accept(self)
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        cond_result = self._analyze_expression(node.condition)
        node.condition.accept(self)
        
        if cond_result["is_constant"]:
            self.issues_found += 1
            self.messages.info(f"Constant condition in if statement: {cond_result['value']}", source="PL0Linter")
            if not cond_result["value"]:
                self.reachable = False
            node.then_statement.accept(self)
            self.reachable = True
        else:
            node.then_statement.accept(self)
    
    def visit_while(self, node: WhileNode):
        cond_result = self._analyze_expression(node.condition)
        node.condition.accept(self)
        
        if cond_result["is_constant"]:
            self.issues_found += 1
            self.messages.info(f"Constant condition in while loop: {cond_result['value']}", source="PL0Linter")
            if not cond_result["value"]:
                self.reachable = False
            node.body.accept(self)
            self.reachable = True
        else:
            node.body.accept(self)
    
    def visit_operation(self, node: OperationNode):
        node.left.accept(self)
        node.right.accept(self)
    
    def visit_variable(self, node: VariableNode):
        self.used_variables.add(node.name)
        if node.name not in self.defined_variables:
            self.issues_found += 1
            self.messages.error(f"Undefined variable: {node.name}", source="PL0Linter")
    
    def visit_number(self, node: NumberNode):
        pass
    
    def _analyze_expression(self, expr: ASTNode) -> Dict[str, Any]:
        if isinstance(expr, NumberNode):
            return {"is_constant": True, "value": expr.value}
        elif isinstance(expr, VariableNode):
            return {"is_constant": False}
        elif isinstance(expr, OperationNode):
            left_result = self._analyze_expression(expr.left)
            right_result = self._analyze_expression(expr.right)
            if left_result["is_constant"] and right_result["is_constant"]:
                result = self._evaluate_constant_operation(expr.operator, left_result["value"], right_result["value"])
                if result is not None:
                    return {"is_constant": True, "value": result}
            return {"is_constant": False}
        return {"is_constant": False}
    
    def _evaluate_constant_operation(self, operator: str, left: int, right: int) -> Any:
        try:
            if operator == "+":
                return left + right
            elif operator == "-":
                return left - right
            elif operator == "*":
                return left * right
            elif operator == "/":
                return left // right if right != 0 else None
            elif operator in ["=", "<", ">", "<=", ">="]:
                return int(eval(f"{left} {operator} {right}"))
        except Exception:
            return None
        return None
