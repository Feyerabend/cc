from typing import Set, Dict, List, Optional
from dataclasses import dataclass

# ASTNode definitions (same as before)
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

class TypeChecker:
    def __init__(self):
        self.type_env: Dict[str, str] = {}
        self.errors: List[str] = []

    def check(self, ast: Program) -> Dict:
        self.type_env.clear()
        self.errors.clear()
        self._check_statements(ast.statements)
        return {
            'errors': self.errors,
            'type_environment': {var: typ for var, typ in sorted(self.type_env.items())}
        }

    def _check_statements(self, stmts: List[ASTNode]):
        for stmt in stmts:
            self._check_stmt(stmt)

    def _check_stmt(self, stmt: ASTNode):
        if isinstance(stmt, Assignment):
            expr_type = self._get_expr_type(stmt.expr)
            if expr_type is None:
                return  # Error already reported
            if stmt.var in self.type_env:
                if self.type_env[stmt.var] != expr_type:
                    self.errors.append(f"Type mismatch for variable '{stmt.var}': expected {self.type_env[stmt.var]}, got {expr_type}")
            else:
                self.type_env[stmt.var] = expr_type

        elif isinstance(stmt, IfStmt):
            cond_type = self._get_expr_type(stmt.condition)
            if cond_type != 'bool':
                self.errors.append(f"If condition must be bool, got {cond_type}")
            self._check_statements(stmt.then_branch)
            if stmt.else_branch:
                self._check_statements(stmt.else_branch)

        elif isinstance(stmt, WhileStmt):
            cond_type = self._get_expr_type(stmt.condition)
            if cond_type != 'bool':
                self.errors.append(f"While condition must be bool, got {cond_type}")
            self._check_statements(stmt.body)

    def _get_expr_type(self, expr: ASTNode) -> Optional[str]:
        if isinstance(expr, Number):
            return 'int'
        elif isinstance(expr, Variable):
            if expr.name not in self.type_env:
                self.errors.append(f"Undefined variable '{expr.name}'")
                return None
            return self.type_env[expr.name]
        elif isinstance(expr, BinOp):
            left_type = self._get_expr_type(expr.left)
            right_type = self._get_expr_type(expr.right)
            if left_type is None or right_type is None:
                return None
            if left_type != 'int' or right_type != 'int':
                self.errors.append(f"BinOp {expr.op} operands must be int, got {left_type} and {right_type}")
                return None
            if expr.op in ['+', '-', '*']:
                return 'int'
            elif expr.op == '<':
                return 'bool'
            else:
                self.errors.append(f"Unknown operator '{expr.op}'")
                return None
        return None

# print_ast function (same as before for consistency)
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
    elif isinstance(node, BinOp):
        print(prefix + f"BinOp: {node.op}")
        print_ast(node.left, indent + 1)
        print_ast(node.right, indent + 1)
    elif isinstance(node, Variable):
        print(prefix + f"Variable: {node.name}")
    elif isinstance(node, Number):
        print(prefix + f"Number: {node.value}")

# Example AST with intentional type errors
ast = Program([
    Assignment('early_use', Variable('not_defined_yet')),  # Undefined error
    Assignment('x', Number(10)),
    Assignment('y', Number(20)),
    IfStmt(
        BinOp('<', Variable('x'), Variable('y')),
        [
            Assignment('z', BinOp('+', Variable('x'), Variable('y')))
        ],
        [
            Assignment('z', BinOp('-', Variable('x'), Variable('y')))
        ]
    ),
    Assignment('result', BinOp('*', Variable('z'), Number(2))),
    Assignment('bool_var', BinOp('<', Number(1), Number(2))),
    WhileStmt(
        Variable('bool_var'),
        [
            Assignment('mismatch', Number(5))
        ]
    ),
    Assignment('mismatch', Variable('bool_var')),
    WhileStmt(
        BinOp('+', Number(1), Number(1)),
        []
    )
])

print("\nTYPE CHECKING EXAMPLE\n")
print("AST:")
print_ast(ast)

checker = TypeChecker()
results = checker.check(ast)

print("\nType Checking Results:")
if results['errors']:
    print("Errors found:")
    for error in results['errors']:
        print(f"- {error}")
else:
    print("No type errors.")
print("\nInferred Types:")
for var, typ in results['type_environment'].items():
    print(f"{var}: {typ}")
