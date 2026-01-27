#!/usr/bin/env python3

from compiler_core import Plugin, ASTNode, CompilerContext, MessageCollector, Visitor, BlockNode, NestedBlockNode, AssignNode, CallNode, ReadNode, WriteNode, CompoundNode, IfNode, WhileNode, OperationNode, VariableNode, NumberNode

class StatementCounterPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "statement_counter",
            "Counts the number of statements in the AST",
            "1.0"
        )
        self.dependencies = ["static_analysis"]  # Ensure variables are checked first
    
    def run(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> dict:
        counter = StatementCounter(messages)
        count = counter.count_statements(ast)
        context.generated_outputs["statement_report"] = f"Total statements: {count}"
        return {"total_statements": count}

class StatementCounter(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.count = 0
    
    def count_statements(self, ast: ASTNode) -> int:
        ast.accept(self)
        return self.count
    
    def visit_block(self, node: BlockNode):
        for _, proc_body in node.procedures:
            proc_body.accept(self)
        node.statement.accept(self)
    
    def visit_nested_block(self, node: NestedBlockNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_assign(self, node: AssignNode):
        self.count += 1
        node.expression.accept(self)
    
    def visit_call(self, node: CallNode):
        self.count += 1
    
    def visit_read(self, node: ReadNode):
        self.count += 1
    
    def visit_write(self, node: WriteNode):
        self.count += 1
        node.expression.accept(self)
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        self.count += 1
        node.condition.accept(self)
        node.then_statement.accept(self)
    
    def visit_while(self, node: WhileNode):
        self.count += 1
        node.condition.accept(self)
        node.body.accept(self)
    
    def visit_operation(self, node: OperationNode):
        node.left.accept(self)
        node.right.accept(self)
    
    def visit_variable(self, node: VariableNode):
        pass
    
    def visit_number(self, node: NumberNode):
        pass
