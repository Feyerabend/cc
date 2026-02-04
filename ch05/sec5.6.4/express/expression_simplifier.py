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

class ExpressionSimplifier:
    def simplify(self, ast: Program) -> Program:
        ast.statements = [self._simplify_stmt(stmt) for stmt in ast.statements]
        return ast

    def _simplify_stmt(self, stmt: ASTNode) -> ASTNode:
        if isinstance(stmt, Assignment):
            stmt.expr = self._simplify_expr(stmt.expr)
        elif isinstance(stmt, IfStmt):
            stmt.condition = self._simplify_expr(stmt.condition)
            stmt.then_branch = [self._simplify_stmt(s) for s in stmt.then_branch]
            if stmt.else_branch:
                stmt.else_branch = [self._simplify_stmt(s) for s in stmt.else_branch]
        elif isinstance(stmt, WhileStmt):
            stmt.condition = self._simplify_expr(stmt.condition)
            stmt.body = [self._simplify_stmt(s) for s in stmt.body]
        return stmt

    def _simplify_expr(self, expr: ASTNode) -> ASTNode:
        if isinstance(expr, BinOp):
            left = self._simplify_expr(expr.left)
            right = self._simplify_expr(expr.right)
            if expr.op == '+' and isinstance(right, Number) and right.value == 0:
                return left
            elif expr.op == '+' and isinstance(left, Number) and left.value == 0:
                return right
            elif expr.op == '*' and isinstance(right, Number) and right.value == 1:
                return left
            elif expr.op == '*' and isinstance(left, Number) and left.value == 1:
                return right
            elif expr.op == '-' and left == right:  # x - x = 0 (simplified check)
                return Number(0)
            return BinOp(expr.op, left, right)
        return expr

# Sample AST
ast = Program([
    Assignment('x', Number(10)),
    Assignment('y', BinOp('+', Variable('x'), Number(0))),  # Simplifies to x
    Assignment('z', BinOp('*', Variable('y'), Number(1))),  # Simplifies to y
    Assignment('diff', BinOp('-', Variable('x'), Variable('x')))  # Simplifies to 0
])

print("Original AST:")
print(ast)

simplifier = ExpressionSimplifier()
simp_ast = simplifier.simplify(ast)


print("\nFinal AST after Expression Simplification:")
print(simp_ast)
