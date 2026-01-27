#!/usr/bin/env python3

from compiler_core import Plugin, ASTNode, CompilerContext, MessageCollector, Visitor
from compiler_core import BlockNode, NestedBlockNode, AssignNode, CallNode, ReadNode, WriteNode
from compiler_core import CompoundNode, IfNode, WhileNode, OperationNode, VariableNode, NumberNode
from typing import Dict, Any, Set

class CodeCoveragePlugin(Plugin):
    def __init__(self):
        super().__init__(
            "code_coverage",
            "Instruments PL/0 code for coverage analysis",
            "1.0"
        )
        self.dependencies = ["static_analysis"]
        self.enabled = True
    
    def run(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> Dict[str, Any]:
        messages.debug("Starting code_coverage plugin", source="CodeCoverage")
        instrumenter = CoverageInstrumenter(messages)
        cov_data = instrumenter.analyze_and_instrument(ast)
        context.generated_outputs["cov_c_code"] = instrumenter.generate_instrumented_code()
        context.generated_outputs["cov_report"] = instrumenter.generate_report()
        messages.debug("Completed code_coverage plugin", source="CodeCoverage")
        return cov_data

class CoverageInstrumenter(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.covered_statements = set()
        self.total_statements = 0
    
    def analyze_and_instrument(self, ast: ASTNode) -> Dict[str, Any]:
        ast.accept(self)
        return {"total_statements": self.total_statements, "instrumented_points": len(self.covered_statements)}
    
    def generate_report(self) -> str:
        return f"Code Coverage Report\n{'=' * 20}\nTotal Statements: {self.total_statements}\nInstrumented Points: {len(self.covered_statements)}"
    
    def visit_assign(self, node: AssignNode):
        self.total_statements += 1
        self.covered_statements.add(id(node))
