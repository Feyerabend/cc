from ast_nodes import *
from error_reporter import ErrorReporter, ErrorSeverity, ErrorCategory, get_suggestion

class SemanticAnalyzer:
    def __init__(self, ast, error_reporter=None):
        self.ast = ast
        self.error_reporter = error_reporter or ErrorReporter()
        self.symbol_table = {}
        self.scopes = [{}]  # Stack of scopes for future scope support
    
    def analyze(self):
        """Analyze the AST and report all semantic errors"""
        self.visit(self.ast)
        return not self.error_reporter.has_errors()
    
    def visit(self, node):
        if node is None:
            return
        
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
            self.error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.SEMANTIC,
                f"Variable '{node.identifier}' is already declared",
                suggestion=get_suggestion("redeclared_variable")
            )
        else:
            self.symbol_table[node.identifier] = {
                'type': 'variable',
                'initialized': True,
                'used': False
            }
        
        self.visit(node.expression)
    
    def visit_AssignStatement(self, node):
        if node.identifier not in self.symbol_table:
            self.error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.SEMANTIC,
                f"Variable '{node.identifier}' is not declared",
                suggestion=get_suggestion("undeclared_variable")
            )
        else:
            self.symbol_table[node.identifier]['initialized'] = True
        
        self.visit(node.expression)
    
    def visit_PrintStatement(self, node):
        self.visit(node.expression)
    
    def visit_InputStatement(self, node):
        if node.identifier not in self.symbol_table:
            self.error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.SEMANTIC,
                f"Variable '{node.identifier}' is not declared for input",
                suggestion=get_suggestion("undeclared_variable")
            )
        else:
            self.symbol_table[node.identifier]['initialized'] = True
    
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
        
        # Type checking for specific operations
        if node.op in ("DIVIDE", "MOD"):
            # Check for potential division by zero with literals
            if isinstance(node.right, NumberLiteral) and node.right.value == 0:
                self.error_reporter.report(
                    ErrorSeverity.WARNING,
                    ErrorCategory.SEMANTIC,
                    f"Division by zero detected",
                    suggestion=get_suggestion("division_by_zero")
                )
    
    def visit_UnaryOp(self, node):
        self.visit(node.operand)
    
    def visit_Identifier(self, node):
        if node.name not in self.symbol_table:
            self.error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.SEMANTIC,
                f"Variable '{node.name}' is not declared",
                suggestion=get_suggestion("undeclared_variable")
            )
        else:
            var_info = self.symbol_table[node.name]
            if not var_info['initialized']:
                self.error_reporter.report(
                    ErrorSeverity.WARNING,
                    ErrorCategory.SEMANTIC,
                    f"Variable '{node.name}' may be used before initialization",
                    suggestion="Make sure the variable is assigned a value before use."
                )
            var_info['used'] = True
    
    def visit_NumberLiteral(self, node):
        pass
    
    def visit_StringLiteral(self, node):
        pass
    
    def check_unused_variables(self):
        """Check for declared but unused variables"""
        for var_name, var_info in self.symbol_table.items():
            if not var_info['used']:
                self.error_reporter.report(
                    ErrorSeverity.WARNING,
                    ErrorCategory.SEMANTIC,
                    f"Variable '{var_name}' is declared but never used",
                    suggestion="Remove unused variables or use them in your code."
                )

if __name__ == "__main__":
    from lexer import tokenize
    from parser import Parser
    from error_reporter import ErrorReporter
    
    code = '''
let x = 42;
y = 10;
print(x + z);
let x = 5;
let unused = 100;
'''
    
    reporter = ErrorReporter(code)
    tokens = tokenize(code, reporter)
    parser = Parser(tokens, reporter)
    ast = parser.parse()
    
    if not reporter.has_fatal_errors():
        analyzer = SemanticAnalyzer(ast, reporter)
        analyzer.analyze()
        analyzer.check_unused_variables()
    
    reporter.print_report()
