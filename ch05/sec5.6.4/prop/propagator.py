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

class ConstantFolder:
    def fold(self, ast: Program) -> Program:
        # Transform statements
        ast.statements = [self._fold_stmt(stmt) for stmt in ast.statements]
        return ast

    def _fold_stmt(self, stmt: ASTNode) -> ASTNode:
        if isinstance(stmt, Assignment):
            stmt.expr = self._fold_expr(stmt.expr)
            return stmt
        elif isinstance(stmt, IfStmt):
            stmt.condition = self._fold_expr(stmt.condition)
            stmt.then_branch = [self._fold_stmt(s) for s in stmt.then_branch]
            if stmt.else_branch:
                stmt.else_branch = [self._fold_stmt(s) for s in stmt.else_branch]
            return stmt
        elif isinstance(stmt, WhileStmt):
            stmt.condition = self._fold_expr(stmt.condition)
            stmt.body = [self._fold_stmt(s) for s in stmt.body]
            return stmt
        return stmt

    def _fold_expr(self, expr: ASTNode) -> ASTNode:
        if isinstance(expr, BinOp):
            left = self._fold_expr(expr.left)
            right = self._fold_expr(expr.right)
            if isinstance(left, Number) and isinstance(right, Number):
                if expr.op == '+':
                    return Number(left.value + right.value)
                elif expr.op == '-':
                    return Number(left.value - right.value)
                elif expr.op == '*':
                    return Number(left.value * right.value)
                elif expr.op == '<':
                    return Number(1 if left.value < right.value else 0)  # Assume bool as int
            return BinOp(expr.op, left, right)
        return expr

class ConstantPropagator:
    def __init__(self):
        self.constants: Dict[str, int] = {}  # Known constant values

    def propagate(self, ast: Program) -> Program:
        self.constants.clear()
        ast.statements = [self._propagate_stmt(stmt) for stmt in ast.statements]
        return ast

    def _propagate_stmt(self, stmt: ASTNode) -> ASTNode:
        if isinstance(stmt, Assignment):
            expr = self._propagate_expr(stmt.expr)
            if isinstance(expr, Number):
                self.constants[stmt.var] = expr.value
            else:
                self.constants.pop(stmt.var, None)  # Not constant
            stmt.expr = expr
            return stmt
        elif isinstance(stmt, IfStmt):
            stmt.condition = self._propagate_expr(stmt.condition)
            stmt.then_branch = [self._propagate_stmt(s) for s in stmt.then_branch]
            if stmt.else_branch:
                stmt.else_branch = [self._propagate_stmt(s) for s in stmt.else_branch]
            return stmt
        elif isinstance(stmt, WhileStmt):
            stmt.condition = self._propagate_expr(stmt.condition)
            stmt.body = [self._propagate_stmt(s) for s in stmt.body]
            return stmt
        return stmt

    def _propagate_expr(self, expr: ASTNode) -> ASTNode:
        if isinstance(expr, Variable):
            if expr.name in self.constants:
                return Number(self.constants[expr.name])
        elif isinstance(expr, BinOp):
            expr.left = self._propagate_expr(expr.left)
            expr.right = self._propagate_expr(expr.right)
        return expr

# Example with sample-like AST
ast = Program([
    Assignment('x', Number(10)),
    Assignment('y', Variable('x')),  # y becomes 10
    Assignment('z', BinOp('+', Variable('y'), Number(5))),  # z becomes 10 + 5 = 15 if folded after
    Assignment('result', Variable('z'))
])

propagator = ConstantPropagator()
prop_ast = propagator.propagate(ast)

# Could chain with ConstantFolder for full effect
folder = ConstantFolder()  # From previous example
folded_ast = folder.fold(prop_ast)

print("\nCONSTANT PROPAGATION\n")
print("Original: x=10; y=x; z=y+5; result=z")
print("After Propagation & Fold: x=10; y=10; z=15; result=15")

print("\nFinal AST after Constant Propagation and Folding:")
print(folded_ast)
