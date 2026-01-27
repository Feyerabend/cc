#!/usr/bin/env python3

from typing import Dict, Any, List, Set
from compiler_core import *


def register_builtin_plugins(registry):
    """Register all built-in plugins with the registry"""
    registry.register(StaticAnalysisPlugin())
    registry.register(TACGeneratorPlugin())
    registry.register(CCodeGeneratorPlugin())


class StaticAnalysisPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "static_analysis",
            "Analyzes variable usage and declarations",
            "1.0"
        )
    
    def run(self, ast, context, messages):
        analyzer = StaticAnalyzer(messages)
        return analyzer.analyze(ast)


class StaticAnalyzer(Visitor):
    def __init__(self, messages):
        self.messages = messages
        self.scopes = [set()]
        self.declared_vars = set()
        self.used_vars = set()
        self.undefined_vars = set()
        self.procedures = set()
        
    def analyze(self, ast: ASTNode) -> Dict[str, Any]:
        ast.accept(self)
        return {
            "declared_variables": list(self.declared_vars),
            "used_variables": list(self.used_vars),
            "undefined_variables": list(self.undefined_vars),
            "procedures": list(self.procedures)
        }
    
    def enter_scope(self):
        self.scopes.append(set())
    
    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
    
    def declare_variable(self, name: str):
        self.scopes[-1].add(name)
        self.declared_vars.add(name)
    
    def use_variable(self, name: str):
        self.used_vars.add(name)
        for scope in reversed(self.scopes):
            if name in scope:
                return
        self.undefined_vars.add(name)
        self.messages.warning(f"Variable '{name}' used but not declared", source="StaticAnalysis")
    
    def visit_block(self, node: BlockNode):
        self.enter_scope()
        for var in node.variables:
            self.declare_variable(var)
        for proc_name, proc_body in node.procedures:
            self.procedures.add(proc_name)
            proc_body.accept(self)
        node.statement.accept(self)
        self.exit_scope()
    
    def visit_nested_block(self, node: NestedBlockNode):
        self.enter_scope()
        for var in node.variables:
            self.declare_variable(var)
        for stmt in node.statements:
            stmt.accept(self)
        self.exit_scope()
    
    def visit_assign(self, node: AssignNode):
        self.use_variable(node.var_name)
        node.expression.accept(self)
    
    def visit_call(self, node: CallNode):
        if node.proc_name not in self.procedures:
            self.messages.warning(f"Procedure '{node.proc_name}' called but not declared", source="StaticAnalysis")
    
    def visit_read(self, node: ReadNode):
        self.use_variable(node.var_name)
    
    def visit_write(self, node: WriteNode):
        node.expression.accept(self)
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        node.condition.accept(self)
        node.then_statement.accept(self)
    
    def visit_while(self, node: WhileNode):
        node.condition.accept(self)
        node.body.accept(self)
    
    def visit_operation(self, node: OperationNode):
        node.left.accept(self)
        node.right.accept(self)
    
    def visit_variable(self, node: VariableNode):
        self.use_variable(node.name)
    
    def visit_number(self, node: NumberNode):
        pass


class TACGeneratorPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "tac_generator",
            "Generates Three-Address Code",
            "1.0"
        )        
        self.dependencies = ["static_analysis"]  # Depends on static analysis
    
    def run(self, ast, context, messages):
        generator = TACGenerator(messages)
        tac_code = generator.generate(ast)
        context.generated_outputs["tac_code"] = "\n".join(tac_code)
        return {"generated": True, "instructions": len(tac_code)}


class TACGenerator(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.code = []
        self.temp_counter = 0
        self.label_counter = 0
    
    def generate(self, ast: ASTNode) -> List[str]:
        ast.accept(self)
        return self.code
    
    def new_temp(self) -> str:
        temp = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp
    
    def new_label(self) -> str:
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label
    
    def visit_block(self, node: BlockNode):
        for var in node.variables:
            self.code.append(f"DECLARE {var}")
        for proc_name, proc_body in node.procedures:
            self.code.append(f"PROC {proc_name}:")
            proc_body.accept(self)
            self.code.append(f"ENDPROC {proc_name}")
        node.statement.accept(self)
    
    def visit_assign(self, node: AssignNode):
        expr_result = node.expression.accept(self)
        self.code.append(f"{node.var_name} := {expr_result}")
    
    def visit_call(self, node: CallNode):
        self.code.append(f"CALL {node.proc_name}")
    
    def visit_read(self, node: ReadNode):
        self.code.append(f"READ {node.var_name}")
    
    def visit_write(self, node: WriteNode):
        expr_result = node.expression.accept(self)
        self.code.append(f"WRITE {expr_result}")
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_nested_block(self, node: NestedBlockNode):
        for var in node.variables:
            self.code.append(f"DECLARE {var}")
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        cond_result = node.condition.accept(self)
        else_label = self.new_label()
        self.code.append(f"IF NOT {cond_result} GOTO {else_label}")
        node.then_statement.accept(self)
        self.code.append(f"LABEL {else_label}")
    
    def visit_while(self, node: WhileNode):
        start_label = self.new_label()
        end_label = self.new_label()
        self.code.append(f"LABEL {start_label}")
        cond_result = node.condition.accept(self)
        self.code.append(f"IF NOT {cond_result} GOTO {end_label}")
        node.body.accept(self)
        self.code.append(f"GOTO {start_label}")
        self.code.append(f"LABEL {end_label}")
    
    def visit_operation(self, node: OperationNode):
        left_result = node.left.accept(self)
        right_result = node.right.accept(self)
        temp = self.new_temp()
        self.code.append(f"{temp} := {left_result} {node.operator} {right_result}")
        return temp
    
    def visit_variable(self, node: VariableNode):
        return node.name
    
    def visit_number(self, node: NumberNode):
        return str(node.value)


class CCodeGeneratorPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "c_code_generator",
            "Generates C code from the AST",
            "1.0"
        )
        self.dependencies = ["static_analysis"]  # Depends on static analysis
    
    def run(self, ast, context, messages):
        generator = CCodeGenerator(messages)
        c_code = generator.generate(ast)
        context.generated_outputs["c_code"] = c_code
        return {"generated": True, "lines": len(c_code.split('\n'))}


class CCodeGenerator(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.code = []
        self.indent_level = 0
    
    def generate(self, ast: ASTNode) -> str:
        self.code.append("#include <stdio.h>")
        self.code.append("")
        self.code.append("int main() {")
        self.indent_level += 1
        ast.accept(self)
        self.indent_level -= 1
        self.code.append("    return 0;")
        self.code.append("}")
        return "\n".join(self.code)
    
    def add_line(self, line: str):
        self.code.append("    " * self.indent_level + line)
    
    def visit_block(self, node: BlockNode):
        for var in node.variables:
            self.add_line(f"int {var};")
        for proc_name, proc_body in node.procedures:
            self.add_line(f"void {proc_name}() {{")
            self.indent_level += 1
            proc_body.accept(self)
            self.indent_level -= 1
            self.add_line("}")
        node.statement.accept(self)
    
    def visit_assign(self, node: AssignNode):
        expr_code = node.expression.accept(self)
        self.add_line(f"{node.var_name} = {expr_code};")
    
    def visit_call(self, node: CallNode):
        self.add_line(f"{node.proc_name}();")
    
    def visit_read(self, node: ReadNode):
        self.add_line(f"scanf(\"%d\", &{node.var_name});")
    
    def visit_write(self, node: WriteNode):
        expr_code = node.expression.accept(self)
        self.add_line(f"printf(\"%d\\n\", {expr_code});")
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_nested_block(self, node: NestedBlockNode):
        for var in node.variables:
            self.add_line(f"int {var};")
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        cond_code = node.condition.accept(self)
        self.add_line(f"if ({cond_code}) {{")
        self.indent_level += 1
        node.then_statement.accept(self)
        self.indent_level -= 1
        self.add_line("}")
    
    def visit_while(self, node: WhileNode):
        cond_code = node.condition.accept(self)
        self.add_line(f"while ({cond_code}) {{")
        self.indent_level += 1
        node.body.accept(self)
        self.indent_level -= 1
        self.add_line("}")
    
    def visit_operation(self, node: OperationNode):
        left_code = node.left.accept(self)
        right_code = node.right.accept(self)
        return f"({left_code} {node.operator} {right_code})"
    
    def visit_variable(self, node: VariableNode):
        return node.name
    
    def visit_number(self, node: NumberNode):
        return str(node.value)