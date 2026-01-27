#!/usr/bin/env python3

from compiler_core import Plugin, ASTNode, CompilerContext, MessageCollector, Visitor
from compiler_core import BlockNode, NestedBlockNode, AssignNode, CallNode, ReadNode, WriteNode
from compiler_core import CompoundNode, IfNode, WhileNode, OperationNode, VariableNode, NumberNode
from typing import Dict, Any, Set

class CodeMetricsPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "code_metrics",
            "Computes code quality metrics for PL/0 programs",
            "1.0"
        )
        self.dependencies = ["static_analysis", "statement_counter"]
        self.enabled = True
    
    def run(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> Dict[str, Any]:
        messages.debug("Starting code_metrics plugin", source="CodeMetrics")
        analyzer = MetricsAnalyzer(messages)
        metrics = analyzer.analyze(ast)
        context.generated_outputs["metrics_report"] = analyzer.generate_report()
        messages.debug("Completed code_metrics plugin", source="CodeMetrics")
        return metrics

class MetricsAnalyzer(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.metrics = {
            "procedure_count": 0,
            "variable_usage": {},
            "statement_density": {},
            "complexity_scores": {}
        }
        self.current_procedure = None
        self.statement_count = 0
    
    def analyze(self, ast: ASTNode) -> Dict[str, Any]:
        ast.accept(self)
        return self.metrics
    
    def generate_report(self) -> str:
        lines = [
            "Code Metrics Report",
            "=" * 20,
            f"Total Procedures: {self.metrics['procedure_count']}",
            "Variable Usage:"
        ]
        for var, count in self.metrics["variable_usage"].items():
            lines.append(f"  • {var}: {count} uses")
        lines.append("Procedure Complexity:")
        for proc, score in self.metrics["complexity_scores"].items():
            lines.append(f"  • {proc}: {score} statements")
        return "\n".join(lines)
    
    def visit_block(self, node: BlockNode):
        self.metrics["procedure_count"] += len(node.procedures)
        for proc_name, proc_body in node.procedures:
            self.current_procedure = proc_name
            old_count = self.statement_count
            proc_body.accept(self)
            self.metrics["complexity_scores"][proc_name] = self.statement_count - old_count
            self.current_procedure = None
        node.statement.accept(self)
    
    def visit_variable(self, node: VariableNode):
        self.metrics["variable_usage"][node.name] = self.metrics["variable_usage"].get(node.name, 0) + 1
