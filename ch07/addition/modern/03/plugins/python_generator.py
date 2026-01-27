#!/usr/bin/env python3

from compiler_core import Plugin, ASTNode, CompilerContext, MessageCollector, Visitor
from compiler_core import BlockNode, NestedBlockNode, AssignNode, CallNode, ReadNode, WriteNode
from compiler_core import CompoundNode, IfNode, WhileNode, OperationNode, VariableNode, NumberNode
from typing import Dict, Any, List, Optional, Tuple

class PythonGeneratorPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "python_generator",
            "Performs optimization analysis and generates Python code",
            "1.0"
        )
        self.dependencies = ["static_analysis"]  # Ensure variables are checked first
        self.enabled = True  # Explicitly enable the plugin
    
    def run(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> Dict[str, Any]:
        messages.debug("Starting python_generator plugin", source="PythonGenerator")
        optimizer = ASTOptimizer(messages)
        optimized_ast = optimizer.optimize(ast)
        
        # Generate Python code from optimized AST
        generator = PythonCodeGenerator(messages)
        py_code = generator.generate(optimized_ast)
        
        # Store the generated code and report in context
        context.generated_outputs["py_code"] = py_code
        context.generated_outputs["py_opt_analysis"] = optimizer.generate_report()
        
        messages.debug("Completed python_generator plugin", source="PythonGenerator")
        return {
            "optimizations_applied": optimizer.optimizations_applied,
            "lines_generated": len(py_code.split('\n'))
        }

class ASTOptimizer(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.optimizations_applied = {
            "constant_propagation": 0,
            "dead_code_elimination": 0
        }
        self.constant_values = {}  # Track constant variables
        self.optimized_nodes = {}  # Store optimized AST nodes
        self.current_scope_vars = set()
        self.live_variables = set()
    
    def optimize(self, ast: ASTNode) -> ASTNode:
        ast.accept(self)
        return self.optimized_nodes.get(id(ast), ast)
    
    def generate_report(self) -> str:
        lines = [
            "Python Optimization Analysis Report",
            "=" * 35,
            "",
            "Optimizations Applied:",
            f"  • Constant Propagation: {self.optimizations_applied['constant_propagation']}",
            f"  • Dead Code Elimination: {self.optimizations_applied['dead_code_elimination']}",
            "",
            "Constant Variables Detected:",
            f"  • {len(self.constant_values)} variables with constant values",
        ]
        if self.constant_values:
            lines.append("  • Values:")
            for var, val in self.constant_values.items():
                lines.append(f"    - {var}: {val}")
        return "\n".join(lines)
    
    def visit_block(self, node: BlockNode):
        old_vars = self.current_scope_vars.copy()
        self.current_scope_vars.update(node.variables)
        
        optimized_procedures = []
        for proc_name, proc_body in node.procedures:
            optimized_body = self.optimize(proc_body)
            optimized_procedures.append((proc_name, optimized_body))
        
        optimized_statement = self.optimize(node.statement)
        optimized_node = BlockNode(node.variables, optimized_procedures, optimized_statement)
        self.optimized_nodes[id(node)] = optimized_node
        
        self.current_scope_vars = old_vars
    
    def visit_nested_block(self, node: NestedBlockNode):
        old_vars = self.current_scope_vars.copy()
        self.current_scope_vars.update(node.variables)
        
        optimized_statements = []
        for stmt in node.statements:
            optimized_stmt = self.optimize(stmt)
            if optimized_stmt:
                optimized_statements.append(optimized_stmt)
        
        optimized_node = NestedBlockNode(node.variables, optimized_statements)
        self.optimized_nodes[id(node)] = optimized_node
        self.current_scope_vars = old_vars
    
    def visit_assign(self, node: AssignNode):
        self.live_variables.add(node.var_name)
        expr_result = self._analyze_expression(node.expression)
        
        if expr_result["is_constant"]:
            self.constant_values[node.var_name] = expr_result["value"]
            self.optimizations_applied["constant_propagation"] += 1
            self.messages.info(f"Constant propagation for {node.var_name} = {expr_result['value']}")
        
        optimized_expr = self.optimize(node.expression)
        optimized_node = AssignNode(node.var_name, optimized_expr)
        self.optimized_nodes[id(node)] = optimized_node
    
    def visit_call(self, node: CallNode):
        self.constant_values.clear()  # Conservative: calls may modify variables
        self.optimized_nodes[id(node)] = node
    
    def visit_read(self, node: ReadNode):
        self.live_variables.add(node.var_name)
        if node.var_name in self.constant_values:
            del self.constant_values[node.var_name]  # Input invalidates constant
        self.optimized_nodes[id(node)] = node
    
    def visit_write(self, node: WriteNode):
        optimized_expr = self.optimize(node.expression)
        self.optimized_nodes[id(node)] = WriteNode(optimized_expr)
    
    def visit_compound(self, node: CompoundNode):
        optimized_statements = []
        for stmt in node.statements:
            optimized_stmt = self.optimize(stmt)
            if optimized_stmt:
                optimized_statements.append(optimized_stmt)
        
        optimized_node = CompoundNode(optimized_statements)
        self.optimized_nodes[id(node)] = optimized_node
    
    def visit_if(self, node: IfNode):
        cond_result = self._analyze_expression(node.condition)
        if cond_result["is_constant"]:
            self.optimizations_applied["dead_code_elimination"] += 1
            self.messages.info("Eliminating if statement with constant condition")
            if cond_result["value"]:
                optimized_node = self.optimize(node.then_statement)
            else:
                optimized_node = None  # Eliminate the entire if
        else:
            optimized_cond = self.optimize(node.condition)
            optimized_then = self.optimize(node.then_statement)
            optimized_node = IfNode(optimized_cond, optimized_then)
        
        if optimized_node:
            self.optimized_nodes[id(node)] = optimized_node
    
    def visit_while(self, node: WhileNode):
        optimized_cond = self.optimize(node.condition)
        optimized_body = self.optimize(node.body)
        optimized_node = WhileNode(optimized_cond, optimized_body)
        self.optimized_nodes[id(node)] = optimized_node
    
    def visit_operation(self, node: OperationNode):
        left_result = self._analyze_expression(node.left)
        right_result = self._analyze_expression(node.right)
        
        if left_result["is_constant"] and right_result["is_constant"]:
            result = self._evaluate_constant_operation(node.operator, left_result["value"], right_result["value"])
            if result is not None:
                self.optimizations_applied["constant_propagation"] += 1
                self.messages.info(f"Constant folding: {node.left} {node.operator} {node.right} = {result}")
                optimized_node = NumberNode(result)
            else:
                optimized_node = OperationNode(node.operator, self.optimize(node.left), self.optimize(node.right))
        else:
            optimized_node = OperationNode(node.operator, self.optimize(node.left), self.optimize(node.right))
        
        self.optimized_nodes[id(node)] = optimized_node
    
    def visit_variable(self, node: VariableNode):
        self.live_variables.add(node.name)
        if node.name in self.constant_values:
            self.optimizations_applied["constant_propagation"] += 1
            self.messages.info(f"Propagating constant {node.name} = {self.constant_values[node.name]}")
            optimized_node = NumberNode(self.constant_values[node.name])
        else:
            optimized_node = node
        self.optimized_nodes[id(node)] = optimized_node
    
    def visit_number(self, node: NumberNode):
        self.optimized_nodes[id(node)] = node
    
    def _analyze_expression(self, expr: ASTNode) -> Dict[str, Any]:
        if isinstance(expr, NumberNode):
            return {"is_constant": True, "value": expr.value}
        elif isinstance(expr, VariableNode):
            if expr.name in self.constant_values:
                return {"is_constant": True, "value": self.constant_values[expr.name]}
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
    
    def _evaluate_constant_operation(self, operator: str, left: int, right: int) -> Optional[int]:
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

class PythonCodeGenerator(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.code = []
        self.indent_level = 0
    
    def generate(self, ast: ASTNode) -> str:
        self.code.append("#!/usr/bin/env python3")
        self.code.append("")
        ast.accept(self)
        return "\n".join(self.code)
    
    def add_line(self, line: str):
        self.code.append("    " * self.indent_level + line)
    
    def visit_block(self, node: BlockNode):
        for proc_name, proc_body in node.procedures:
            self.add_line(f"def {proc_name}():")
            self.indent_level += 1
            proc_body.accept(self)
            self.indent_level -= 1
            self.add_line("")
        node.statement.accept(self)
    
    def visit_nested_block(self, node: NestedBlockNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_assign(self, node: AssignNode):
        expr_code = node.expression.accept(self)
        self.add_line(f"{node.var_name} = {expr_code}")
    
    def visit_call(self, node: CallNode):
        self.add_line(f"{node.proc_name}()")
    
    def visit_read(self, node: ReadNode):
        self.add_line(f"{node.var_name} = int(input())")
    
    def visit_write(self, node: WriteNode):
        expr_code = node.expression.accept(self)
        self.add_line(f"print({expr_code})")
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        cond_code = node.condition.accept(self)
        self.add_line(f"if {cond_code}:")
        self.indent_level += 1
        node.then_statement.accept(self)
        self.indent_level -= 1
    
    def visit_while(self, node: WhileNode):
        cond_code = node.condition.accept(self)
        self.add_line(f"while {cond_code}:")
        self.indent_level += 1
        node.body.accept(self)
        self.indent_level -= 1
    
    def visit_operation(self, node: OperationNode):
        left_code = node.left.accept(self)
        right_code = node.right.accept(self)
        # Map PL/0 operators to Python (e.g., "=" for equality is "==" in Python)
        py_operator = "==" if node.operator == "=" else node.operator
        return f"({left_code} {py_operator} {right_code})"
    
    def visit_variable(self, node: VariableNode):
        return node.name
    
    def visit_number(self, node: NumberNode):
        return str(node.value)
