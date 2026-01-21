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

class LivenessAnalyzer:
    def __init__(self):
        self.live_after: Dict[int, Set[str]] = {}
    
    def analyze(self, ast: Program) -> Dict:
        """Perform backward liveness analysis"""
        stmts = ast.statements
        n = len(stmts)
        
        # Init: nothing is live after the last statement
        live = set()
        dead_assignments = []
        
        # Backward pass
        for i in range(n - 1, -1, -1):
            stmt = stmts[i]
            
            if isinstance(stmt, Assignment):
                # If assigned variable is not live after, it's a dead assignment
                if stmt.var not in live:
                    dead_assignments.append({
                        'statement_index': i,
                        'variable': stmt.var,
                        'reason': 'assigned but never used afterward'
                    })
                
                # Variable is killed (assigned)
                live.discard(stmt.var)
                
                # Variables used in expression are live before
                used = self._get_used_vars(stmt.expr)
                live.update(used)
            
            elif isinstance(stmt, IfStmt):
                # Variables in condition are live
                used = self._get_used_vars(stmt.condition)
                live.update(used)
                
                # Merge liveness from both branches
                then_live = self._analyze_stmts(stmt.then_branch, live.copy())
                else_live = self._analyze_stmts(stmt.else_branch, live.copy()) if stmt.else_branch else live.copy()
                live = then_live | else_live
            
            elif isinstance(stmt, WhileStmt):
                # Variables in condition are live
                used = self._get_used_vars(stmt.condition)
                live.update(used)
                
                # Body can execute multiple times
                # Simplified: just union with body analysis
                body_live = self._analyze_stmts(stmt.body, live.copy())
                live = live | body_live
            
            self.live_after[i] = live.copy()
        
        return {
            'dead_assignments': dead_assignments,
            'liveness_info': {i: sorted(list(v)) for i, v in self.live_after.items()}
        }
    
    def _analyze_stmts(self, stmts: List[ASTNode], live: Set[str]) -> Set[str]:
        for stmt in reversed(stmts):
            if isinstance(stmt, Assignment):
                live.discard(stmt.var)
                live.update(self._get_used_vars(stmt.expr))
            elif isinstance(stmt, IfStmt):
                live.update(self._get_used_vars(stmt.condition))
                then_live = self._analyze_stmts(stmt.then_branch, live.copy())
                else_live = self._analyze_stmts(stmt.else_branch, live.copy()) if stmt.else_branch else live.copy()
                live = then_live | else_live
            elif isinstance(stmt, WhileStmt):
                live.update(self._get_used_vars(stmt.condition))
                body_live = self._analyze_stmts(stmt.body, live.copy())
                live = live | body_live
        return live
    
    def _get_used_vars(self, expr: ASTNode) -> Set[str]:
        if isinstance(expr, Variable):
            return {expr.name}
        elif isinstance(expr, BinOp):
            return self._get_used_vars(expr.left) | self._get_used_vars(expr.right)
        else:
            return set()



def load_ast_from_json(json_str: str) -> Program:
    def dict_to_ast(d):
        if isinstance(d, dict) and 'type' in d:
            node_type = d['type']
            if node_type == 'Program':
                return Program([dict_to_ast(s) for s in d['statements']])
            elif node_type == 'Assignment':
                return Assignment(d['var'], dict_to_ast(d['expr']))
            elif node_type == 'IfStmt':
                return IfStmt(
                    dict_to_ast(d['condition']),
                    [dict_to_ast(s) for s in d['then_branch']],
                    [dict_to_ast(s) for s in d['else_branch']] if d.get('else_branch') else None
                )
            elif node_type == 'WhileStmt':
                return WhileStmt(
                    dict_to_ast(d['condition']),
                    [dict_to_ast(s) for s in d['body']]
                )
            elif node_type == 'BinOp':
                return BinOp(d['op'], dict_to_ast(d['left']), dict_to_ast(d['right']))
            elif node_type == 'Variable':
                return Variable(d['name'])
            elif node_type == 'Number':
                return Number(d['value'])
        return d
    
    return dict_to_ast(json.loads(json_str))

if __name__ == "__main__":
    # Example AST (would normally come from parser)
    # Now hard coded for ease
    ast = Program([
        Assignment('x', Number(10)),
        Assignment('y', Number(20)),
        IfStmt(
            BinOp('<', Variable('x'), Variable('y')),
            [
                Assignment('z', BinOp('+', Variable('x'), Variable('y'))),
                Assignment('unused', Number(42))
            ],
            [
                Assignment('z', BinOp('-', Variable('x'), Variable('y')))
            ]
        ),
        Assignment('result', BinOp('*', Variable('z'), Number(2))),
        Assignment('dead', Number(99))
    ])
    
    print("\nDEAD CODE ANALYSIS\n")
    
    # Basic analysis
    analyzer = DeadCodeAnalyzer()
    results = analyzer.analyze(ast)
    
    print("\nBasic Analysis:")
    print(f"  Assigned variables: {results['assigned_variables']}")
    print(f"  Used variables: {results['used_variables']}")
    print(f"  Unused variables: {results['unused_variables']}")
    
    # Liveness analysis
    liveness = LivenessAnalyzer()
    liveness_results = liveness.analyze(ast)
    
    print("\nLiveness Analysis:")
    print("  Dead assignments (assigned but never used):")
    for dead in liveness_results['dead_assignments']:
        print(f"    Statement {dead['statement_index']}: variable '{dead['variable']}' - {dead['reason']}")
    
    print("\n  Live variables after each statement:")
    for i, live_vars in liveness_results['liveness_info'].items():
        print(f"    After statement {i}: {live_vars}")
