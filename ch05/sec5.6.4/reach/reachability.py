import json
from typing import Set, Dict, List
from dataclasses import dataclass

# Import or redefine AST nodes (in practice, import from parser module)
@dataclass
class ASTNode:
    pass

@dataclass
class Number(ASTNode):
    value: int

@dataclass
class Variable(ASTNode):
    name: str

@dataclass
class BinOp(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode

@dataclass
class Assignment(ASTNode):
    var: str
    expr: ASTNode

@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    then_branch: List[ASTNode]
    else_branch: List[ASTNode] = None

@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode
    body: List[ASTNode]

@dataclass
class Program(ASTNode):
    statements: List[ASTNode]


class DeadCodeAnalyzer:
    def __init__(self):
        self.assigned_vars: Set[str] = set()
        self.used_vars: Set[str] = set()
        self.warnings: List[str] = []
    
    def analyze(self, ast: Program) -> Dict:
        self.assigned_vars.clear()
        self.used_vars.clear()
        self.warnings.clear()
        
        # First pass: collect assignments and usages
        self._analyze_statements(ast.statements)
        
        # Find unused variables
        unused = self.assigned_vars - self.used_vars
        
        return {
            'unused_variables': sorted(list(unused)),
            'assigned_variables': sorted(list(self.assigned_vars)),
            'used_variables': sorted(list(self.used_vars)),
            'warnings': self.warnings
        }
    
    def _analyze_statements(self, stmts: List[ASTNode]):
        for stmt in stmts:
            self._analyze_stmt(stmt)
    
    def _analyze_stmt(self, stmt: ASTNode):
        if isinstance(stmt, Assignment):
            # Variable is assigned
            self.assigned_vars.add(stmt.var)
            # Analyze the expression for variable uses
            self._analyze_expr(stmt.expr)
        
        elif isinstance(stmt, IfStmt):
            # Condition uses variables
            self._analyze_expr(stmt.condition)
            
            # Analyze both branches
            self._analyze_statements(stmt.then_branch)
            if stmt.else_branch:
                self._analyze_statements(stmt.else_branch)
        
        elif isinstance(stmt, WhileStmt):
            # Condition uses variables
            self._analyze_expr(stmt.condition)
            # Body statements
            self._analyze_statements(stmt.body)
    
    def _analyze_expr(self, expr: ASTNode):
        if isinstance(expr, Variable):
            self.used_vars.add(expr.name)
        
        elif isinstance(expr, BinOp):
            self._analyze_expr(expr.left)
            self._analyze_expr(expr.right)
        
        elif isinstance(expr, Number):
            pass  # Numbers don't use variables

class ReachabilityAnalyzer:
    def __init__(self):
        self.unreachable: List[Dict] = []

    def analyze(self, ast: Program) -> Dict:
        self.unreachable.clear()
        self._analyze_statements(ast.statements, reachable=True)
        return {'unreachable_statements': self.unreachable}

    def _analyze_statements(self, stmts: List[ASTNode], reachable: bool):
        for i, stmt in enumerate(stmts):
            if not reachable:
                self.unreachable.append({'index': i, 'reason': 'unreachable after previous infinite loop or always-false condition'})
            if isinstance(stmt, IfStmt):
                # Simplified: assume we can't evaluate condition statically
                self._analyze_statements(stmt.then_branch, reachable)
                if stmt.else_branch:
                    self._analyze_statements(stmt.else_branch, reachable)
            elif isinstance(stmt, WhileStmt):
                # Simplified: if condition is constant true, body is reachable, but after is not
                if isinstance(stmt.condition, Number) and stmt.condition.value != 0:  # Assume non-zero is true
                    self._analyze_statements(stmt.body, reachable)
                    reachable = False  # Nothing after infinite loop
                else:
                    self._analyze_statements(stmt.body, reachable)
            # Other statements don't affect reachability

# Example AST with unreachable code
ast = Program([
    Assignment('x', Number(10)),
    WhileStmt(Number(1), [Assignment('y', BinOp('+', Variable('y'), Number(1)))]),  # Infinite loop (condition=1=true)
    Assignment('unreachable', Number(99))  # Unreachable
])

analyzer = ReachabilityAnalyzer()
results = analyzer.analyze(ast)

print("\nREACHABILITY ANALYSIS\n")
print("Unreachable statements:")
for ur in results['unreachable_statements']:
    print(f"Statement {ur['index']}: {ur['reason']}")

