from ast_nodes import *

class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast = ast
        self.symbol_table = {}
        self.errors = []
    
    def analyze(self):
        self.visit(self.ast)
        return self.errors
    
    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.generic_visit)
        return method(node)
    
    def generic_visit(self, node):
        for attr, value in node.__dict__.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        self.visit(item)
            elif isinstance(value, ASTNode):
                self.visit(value)
    
    def visit_Program(self, node):
        for statement in node.statements:
            self.visit(statement)
    
    def visit_LetStatement(self, node):
        if node.identifier in self.symbol_table:
            self.errors.append(f"Variable '{node.identifier}' already declared")
        else:
            self.symbol_table[node.identifier] = 'variable'
        self.visit(node.expression)
    
    def visit_AssignStatement(self, node):
        if node.identifier not in self.symbol_table:
            self.errors.append(f"Variable '{node.identifier}' not declared")
        self.visit(node.expression)
    
    def visit_PrintStatement(self, node):
        self.visit(node.expression)
    
    def visit_InputStatement(self, node):
        if node.identifier not in self.symbol_table:
            self.errors.append(f"Variable '{node.identifier}' not declared")
    
    def visit_IfStatement(self, node):
        self.visit(node.condition)
        self.visit(node.then_block)
        if node.else_block:
            self.visit(node.else_block)
    
    def visit_WhileStatement(self, node):
        self.visit(node.condition)
        self.visit(node.body)
    
    def visit_Block(self, node):
        for statement in node.statements:
            self.visit(statement)
    
    def visit_BinaryOp(self, node):
        self.visit(node.left)
        self.visit(node.right)
    
    def visit_UnaryOp(self, node):
        self.visit(node.operand)
    
    def visit_Identifier(self, node):
        if node.name not in self.symbol_table:
            self.errors.append(f"Variable '{node.name}' not declared")
    
    def visit_NumberLiteral(self, node):
        pass
    
    def visit_StringLiteral(self, node):
        pass

if __name__ == "__main__":
    from lexer import tokenize
    from parser import Parser
    
    code = '''
let x = 42;
y = 10;
print(x + z);
'''
    tokens = tokenize(code)
    parser = Parser(tokens)
    ast = parser.parse()
    
    analyzer = SemanticAnalyzer(ast)
    errors = analyzer.analyze()
    
    if errors:
        print("Semantic errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Semantic analysis passed!")
