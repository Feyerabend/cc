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

class LICMOptimizer:
    def optimize(self, ast: Program) -> Program:
        ast.statements = self._optimize_statements(ast.statements)
        return ast

    def _optimize_statements(self, stmts: List[ASTNode]) -> List[ASTNode]:
        new_stmts = []
        for stmt in stmts:
            if isinstance(stmt, WhileStmt):
                hoisted, new_body = self._perform_licm(stmt)
                new_stmts.extend(hoisted)
                stmt.body = self._optimize_statements(new_body)  # Recurse on body
                new_stmts.append(stmt)
            elif isinstance(stmt, IfStmt):
                stmt.then_branch = self._optimize_statements(stmt.then_branch)
                if stmt.else_branch:
                    stmt.else_branch = self._optimize_statements(stmt.else_branch)
                new_stmts.append(stmt)
            else:
                new_stmts.append(stmt)
        return new_stmts

    def _perform_licm(self, loop: WhileStmt) -> tuple[List[ASTNode], List[ASTNode]]:
        hoisted = []
        new_body = loop.body[:]  # Copy
        condition_used = self._get_used_vars(loop.condition)

        while True:
            modified_vars = self._find_modified_vars(new_body)
            assign_counts = self._count_assignments(new_body)

            something_hoisted = False
            temp_body = []

            for stmt in new_body:
                if isinstance(stmt, Assignment):
                    used = self._get_used_vars(stmt.expr)
                    if (assign_counts.get(stmt.var, 0) == 1 and
                        used.isdisjoint(modified_vars) and
                        stmt.var not in condition_used):
                        hoisted.append(stmt)
                        something_hoisted = True
                    else:
                        temp_body.append(stmt)
                else:
                    temp_body.append(stmt)

            new_body = temp_body

            if not something_hoisted:
                break

        return hoisted, new_body

    def _find_modified_vars(self, stmts: List[ASTNode]) -> Set[str]:
        modified = set()
        for stmt in stmts:
            if isinstance(stmt, Assignment):
                modified.add(stmt.var)
            elif isinstance(stmt, IfStmt):
                modified.update(self._find_modified_vars(stmt.then_branch))
                if stmt.else_branch:
                    modified.update(self._find_modified_vars(stmt.else_branch))
            elif isinstance(stmt, WhileStmt):
                modified.update(self._find_modified_vars(stmt.body))
        return modified

    def _count_assignments(self, stmts: List[ASTNode]) -> Dict[str, int]:
        counts = {}
        for stmt in stmts:
            if isinstance(stmt, Assignment):
                counts[stmt.var] = counts.get(stmt.var, 0) + 1
            elif isinstance(stmt, IfStmt):
                branches = [stmt.then_branch]
                if stmt.else_branch:
                    branches.append(stmt.else_branch)
                for branch in branches:
                    sub_counts = self._count_assignments(branch)
                    for v, c in sub_counts.items():
                        counts[v] = counts.get(v, 0) + c
            elif isinstance(stmt, WhileStmt):
                sub_counts = self._count_assignments(stmt.body)
                for v, c in sub_counts.items():
                    counts[v] = counts.get(v, 0) + c
        return counts

    def _get_used_vars(self, node: ASTNode) -> Set[str]:
        used = set()
        if isinstance(node, Variable):
            used.add(node.name)
        elif isinstance(node, BinOp):
            used.update(self._get_used_vars(node.left))
            used.update(self._get_used_vars(node.right))
        elif isinstance(node, Assignment):
            used.update(self._get_used_vars(node.expr))
        elif isinstance(node, IfStmt):
            used.update(self._get_used_vars(node.condition))
            for stmt in node.then_branch:
                used.update(self._get_used_vars(stmt))
            if node.else_branch:
                for stmt in node.else_branch:
                    used.update(self._get_used_vars(stmt))
        elif isinstance(node, WhileStmt):
            used.update(self._get_used_vars(node.condition))
            for stmt in node.body:
                used.update(self._get_used_vars(stmt))
        elif isinstance(node, Program):
            for stmt in node.statements:
                used.update(self._get_used_vars(stmt))
        elif isinstance(node, Number):
            pass
        return used

def print_ast(node: ASTNode, indent: int = 0):
    prefix = '  ' * indent
    if isinstance(node, Program):
        print(prefix + "Program:")
        for stmt in node.statements:
            print_ast(stmt, indent + 1)
    elif isinstance(node, Assignment):
        print(prefix + f"Assignment: {node.var} =")
        print_ast(node.expr, indent + 1)
    elif isinstance(node, WhileStmt):
        print(prefix + "WhileStmt:")
        print(prefix + "  Condition:")
        print_ast(node.condition, indent + 2)
        print(prefix + "  Body:")
        for stmt in node.body:
            print_ast(stmt, indent + 2)
    elif isinstance(node, BinOp):
        print(prefix + f"BinOp: {node.op}")
        print_ast(node.left, indent + 1)
        print_ast(node.right, indent + 1)
    elif isinstance(node, Variable):
        print(prefix + f"Variable: {node.name}")
    elif isinstance(node, Number):
        print(prefix + f"Number: {node.value}")
    elif isinstance(node, IfStmt):
        print(prefix + "IfStmt:")
        print(prefix + "  Condition:")
        print_ast(node.condition, indent + 2)
        print(prefix + "  Then Branch:")
        for stmt in node.then_branch:
            print_ast(stmt, indent + 2)
        if node.else_branch:
            print(prefix + "  Else Branch:")
            for stmt in node.else_branch:
                print_ast(stmt, indent + 2)


ast = Program([
    Assignment('a', Number(5)),
    Assignment('b', Number(10)),
    Assignment('i', Number(0)),
    WhileStmt(
        BinOp('<', Variable('i'), Number(10)),
        [
            Assignment('invariant', BinOp('+', Variable('a'), Variable('b'))),
            Assignment('invariant2', BinOp('*', Variable('invariant'), Number(2))),
            Assignment('z', BinOp('+', Variable('invariant2'), Variable('i'))),
            Assignment('i', BinOp('+', Variable('i'), Number(1)))
        ]
    ),
    Assignment('result', Variable('z'))
])


print("Before LICM:")
print_ast(ast)

optimizer = LICMOptimizer()
optimized_ast = optimizer.optimize(ast)

print("\nAfter LICM:")
print_ast(optimized_ast)

