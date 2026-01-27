#!/usr/bin/env python3

from compiler_core import Plugin, ASTNode, CompilerContext, MessageCollector, Visitor
from compiler_core import BlockNode, NestedBlockNode, AssignNode, CallNode, ReadNode, WriteNode
from compiler_core import CompoundNode, IfNode, WhileNode, OperationNode, VariableNode, NumberNode
from typing import Dict, Any, Set, List

class ASTPrettyPrinterPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "ast_pretty_printer",
            "Generates a formatted string representation of the AST",
            "1.0"
        )
        self.dependencies = ["static_analysis"]  # depends on static analysis for validated AST
    
    def run(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> dict:
        printer = ASTPrettyPrinter(messages)
        ast_string = printer.print_ast(ast)
        context.generated_outputs["ast_structure"] = ast_string
        return {"generated": True, "lines": len(ast_string.split('\n'))}

class ASTPrettyPrinter(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.output = []
        self.indent_level = 0
    
    def print_ast(self, ast: ASTNode) -> str:
        self.output = []
        ast.accept(self)
        return "\n".join(self.output)
    
    def add_line(self, line: str):
        self.output.append("  " * self.indent_level + line)
    
    def visit_block(self, node: BlockNode):
        self.add_line("BlockNode:")
        self.indent_level += 1
        if node.variables:
            self.add_line(f"Variables: {', '.join(node.variables)}")
        if node.procedures:
            self.add_line("Procedures:")
            self.indent_level += 1
            for proc_name, proc_body in node.procedures:
                self.add_line(f"Procedure '{proc_name}':")
                self.indent_level += 1
                proc_body.accept(self)
                self.indent_level -= 1
            self.indent_level -= 1
        self.add_line("Statement:")
        self.indent_level += 1
        node.statement.accept(self)
        self.indent_level -= 1
    
    def visit_nested_block(self, node: NestedBlockNode):
        self.add_line("NestedBlockNode:")
        self.indent_level += 1
        if node.variables:
            self.add_line(f"Variables: {', '.join(node.variables)}")
        self.add_line("Statements:")
        self.indent_level += 1
        for stmt in node.statements:
            stmt.accept(self)
        self.indent_level -= 2
    
    def visit_assign(self, node: AssignNode):
        self.add_line(f"AssignNode: {node.var_name}")
        self.indent_level += 1
        self.add_line("Expression:")
        self.indent_level += 1
        node.expression.accept(self)
        self.indent_level -= 2
    
    def visit_call(self, node: CallNode):
        self.add_line(f"CallNode: {node.proc_name}")
    
    def visit_read(self, node: ReadNode):
        self.add_line(f"ReadNode: {node.var_name}")
    
    def visit_write(self, node: WriteNode):
        self.add_line("WriteNode:")
        self.indent_level += 1
        self.add_line("Expression:")
        self.indent_level += 1
        node.expression.accept(self)
        self.indent_level -= 2
    
    def visit_compound(self, node: CompoundNode):
        self.add_line("CompoundNode:")
        self.indent_level += 1
        self.add_line("Statements:")
        self.indent_level += 1
        for stmt in node.statements:
            stmt.accept(self)
        self.indent_level -= 2
    
    def visit_if(self, node: IfNode):
        self.add_line("IfNode:")
        self.indent_level += 1
        self.add_line("Condition:")
        self.indent_level += 1
        node.condition.accept(self)
        self.indent_level -= 1
        self.add_line("Then:")
        self.indent_level += 1
        node.then_statement.accept(self)
        self.indent_level -= 2
    
    def visit_while(self, node: WhileNode):
        self.add_line("WhileNode:")
        self.indent_level += 1
        self.add_line("Condition:")
        self.indent_level += 1
        node.condition.accept(self)
        self.indent_level -= 1
        self.add_line("Body:")
        self.indent_level += 1
        node.body.accept(self)
        self.indent_level -= 2
    
    def visit_operation(self, node: OperationNode):
        self.add_line(f"OperationNode: {node.operator}")
        self.indent_level += 1
        self.add_line("Left:")
        self.indent_level += 1
        node.left.accept(self)
        self.indent_level -= 1
        self.add_line("Right:")
        self.indent_level += 1
        node.right.accept(self)
        self.indent_level -= 2
    
    def visit_variable(self, node: VariableNode):
        self.add_line(f"VariableNode: {node.name}")
    
    def visit_number(self, node: NumberNode):
        self.add_line(f"NumberNode: {node.value}")
