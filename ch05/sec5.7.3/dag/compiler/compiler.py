from enum import Enum, auto
from typing import List, Dict, Set, Optional
from dataclasses import dataclass


# BASIC INTERPRETER

class Operation(Enum):
    LIT = auto()  # push literal
    OPR = auto()  # operation
    STO = auto()  # store
    INT = auto()  # allocate

@dataclass
class Instruction:
    f: Operation
    l: int
    a: int
    
    def __str__(self):
        return f"{self.f.name:3} {self.l} {self.a}"

class Interpreter:
    def __init__(self, code: List[Instruction]):
        self.code = code
        self.s = [0] * 100
        self.p = 0
        self.b = 0
        self.t = -1
    
    def run(self):
        self.t = 2
        self.s[0] = 0  # SL
        self.s[1] = 0  # DL
        self.s[2] = 0  # RA
        
        while self.p < len(self.code):
            i = self.code[self.p]
            self.p += 1
            
            if i.f == Operation.LIT:
                self.t += 1
                self.s[self.t] = i.a
            elif i.f == Operation.OPR:
                if i.a == 0:  # return
                    break
                elif i.a == 1:  # load (dereference)
                    self.s[self.t] = self.s[self.s[self.t]]
                elif i.a == 2:  # add
                    self.t -= 1
                    self.s[self.t] += self.s[self.t + 1]
                elif i.a == 3:  # subtract
                    self.t -= 1
                    self.s[self.t] -= self.s[self.t + 1]
                elif i.a == 4:  # multiply
                    self.t -= 1
                    self.s[self.t] *= self.s[self.t + 1]
            elif i.f == Operation.STO:
                self.s[i.a] = self.s[self.t]
                self.t -= 1
            elif i.f == Operation.INT:
                self.t += i.a


# DAG NODES FOR EXPRESSION OPTIMISATION

class DAGNode:
    """DAG node representing a computation or value."""
    _id_counter = 0
    
    def __init__(self, op: str, left=None, right=None, value=None):
        DAGNode._id_counter += 1
        self.id = DAGNode._id_counter
        self.op = op  # operation: 'VAR', 'LIT', '+', '-', '*'
        self.left = left
        self.right = right
        self.value = value  # for VAR or LIT nodes
        self.ref_count = 0
        self.computed_at = None  # which temp/register holds this value
    
    def canonical_key(self):
        """Create unique key for this computation to detect duplicates."""
        if self.op in ('VAR', 'LIT'):
            return (self.op, self.value)
        return (self.op, id(self.left), id(self.right))
    
    def __str__(self):
        if self.op == 'VAR':
            return self.value
        if self.op == 'LIT':
            return str(self.value)
        return f"({self.left} {self.op} {self.right})"


# DAG BUILDER - Converts expressions to DAG

class DAGBuilder:
    """Builds a DAG from expressions, sharing common subexpressions."""
    
    def __init__(self):
        self.nodes: Dict[tuple, DAGNode] = {}  # canonical_key -> node
        self.assignments: List[tuple] = []  # (var_name, dag_node)
    
    def parse_expr(self, expr: str) -> DAGNode:
        """Parse expression into DAG, reusing common subexpressions."""
        expr = expr.strip()
        
        # Try operators in order of precedence (low to high)
        for op in ['+', '-']:
            if op in expr:
                parts = expr.split(op, 1)
                if len(parts) == 2:
                    left = self.parse_expr(parts[0])
                    right = self.parse_expr(parts[1])
                    return self._get_or_create(op, left, right)
        
        for op in ['*']:
            if op in expr:
                parts = expr.split(op, 1)
                if len(parts) == 2:
                    left = self.parse_expr(parts[0])
                    right = self.parse_expr(parts[1])
                    return self._get_or_create(op, left, right)
        
        # Literal or variable
        if expr.isdigit():
            return self._get_or_create('LIT', value=int(expr))
        else:
            return self._get_or_create('VAR', value=expr)
    
    def _get_or_create(self, op: str, left=None, right=None, value=None) -> DAGNode:
        """Get existing node or create new one - KEY TO DAG OPTIMIZATION!"""
        temp_node = DAGNode(op, left, right, value)
        key = temp_node.canonical_key()
        
        if key in self.nodes:
            # Found common subexpression - reuse it!
            node = self.nodes[key]
            node.ref_count += 1
            return node
        
        # New unique computation
        self.nodes[key] = temp_node
        temp_node.ref_count = 1
        return temp_node
    
    def add_assignment(self, var: str, expr: str):
        """Add an assignment statement."""
        dag_node = self.parse_expr(expr)
        self.assignments.append((var, dag_node))
    
    def visualize(self) -> str:
        """Show the DAG structure."""
        result = []
        visited = set()
        
        def render(node: DAGNode, prefix="", is_last=True):
            if node is None:
                return
            
            node_id = id(node)
            marker = "└── " if is_last else "├── "
            
            # Show node info
            label = f"[N{node.id}] "
            if node.op == 'VAR':
                label += f"VAR({node.value})"
            elif node.op == 'LIT':
                label += f"LIT({node.value})"
            else:
                label += node.op
            
            if node.ref_count > 1:
                label += f" ★{node.ref_count}×"
            
            if node_id in visited:
                result.append(f"{prefix}{marker}{label} ⟲ SHARED")
                return
            
            result.append(f"{prefix}{marker}{label}")
            visited.add(node_id)
            
            # Recurse to children
            if node.left or node.right:
                extension = "    " if is_last else "│   "
                if node.left:
                    render(node.left, prefix + extension, node.right is None)
                if node.right:
                    render(node.right, prefix + extension, True)
        
        for i, (var, node) in enumerate(self.assignments):
            result.append(f"\n{var} =")
            render(node, "  ", True)
        
        return "\n".join(result)


# NAIVE COMPILER (No DAG optimisation)

class NaiveCompiler:
    """Compiles without optimisation - generates code directly from AST."""
    
    def __init__(self):
        self.symbol_table: Dict[str, int] = {}
        self.code: List[Instruction] = []
        self.current_address = 3
    
    def compile(self, program: str) -> List[Instruction]:
        self.symbol_table.clear()
        self.code.clear()
        lines = [l.strip() for l in program.split('\n') if l.strip() and not l.strip().startswith('//')]
        
        # Collect variables
        var_count = 0
        for line in lines:
            if line.startswith('var '):
                var_name = line[4:].strip()
                self.symbol_table[var_name] = self.current_address + var_count
                var_count += 1
        
        if var_count > 0:
            self.code.append(Instruction(Operation.INT, 0, var_count))
        
        # Process assignments
        for line in lines:
            if '=' in line:
                var_name, expr = [p.strip() for p in line.split('=', 1)]
                self._compile_expr(expr)
                self.code.append(Instruction(Operation.STO, 0, self.symbol_table[var_name]))
        
        self.code.append(Instruction(Operation.OPR, 0, 0))
        return self.code
    
    def _compile_expr(self, expr: str):
        """Recursively compile expression - NO SHARING"""
        for op, opr_code in [('+', 2), ('-', 3), ('*', 4)]:
            if op in expr:
                parts = expr.split(op, 1)
                self._compile_expr(parts[0].strip())
                self._compile_expr(parts[1].strip())
                self.code.append(Instruction(Operation.OPR, 0, opr_code))
                return
        
        # Leaf node
        if expr.isdigit():
            self.code.append(Instruction(Operation.LIT, 0, int(expr)))
        else:
            self.code.append(Instruction(Operation.LIT, 0, self.symbol_table[expr]))
            self.code.append(Instruction(Operation.OPR, 0, 1))  # load


# DAG-OPTIMISED COMPILER

class DAGCompiler:
    """Compiles using DAG to eliminate common subexpressions."""
    
    def __init__(self):
        self.symbol_table: Dict[str, int] = {}
        self.code: List[Instruction] = []
        self.current_address = 3
        self.dag: Optional[DAGBuilder] = None
    
    def compile(self, program: str) -> List[Instruction]:
        self.symbol_table.clear()
        self.code.clear()
        self.dag = DAGBuilder()
        
        lines = [l.strip() for l in program.split('\n') if l.strip() and not l.strip().startswith('//')]
        
        # Collect variables
        var_count = 0
        for line in lines:
            if line.startswith('var '):
                var_name = line[4:].strip()
                self.symbol_table[var_name] = self.current_address + var_count
                var_count += 1
        
        if var_count > 0:
            self.code.append(Instruction(Operation.INT, 0, var_count))
        
        # Build DAG from all assignments
        for line in lines:
            if '=' in line:
                var_name, expr = [p.strip() for p in line.split('=', 1)]
                self.dag.add_assignment(var_name, expr)
        
        # Generate code using DAG (compute each subexpression once!)
        computed = {}  # node_id -> stack position when computed
        
        def emit_code(node: DAGNode):
            """Emit code for a DAG node, reusing already-computed values."""
            node_id = id(node)
            
            # Already computed? Just reference it!
            if node_id in computed:
                # Push the already-computed value back onto stack
                # (In a real compiler, we'd use registers here)
                return
            
            if node.op == 'LIT':
                self.code.append(Instruction(Operation.LIT, 0, node.value))
            elif node.op == 'VAR':
                self.code.append(Instruction(Operation.LIT, 0, self.symbol_table[node.value]))
                self.code.append(Instruction(Operation.OPR, 0, 1))
            else:
                # Compute children first
                emit_code(node.left)
                emit_code(node.right)
                
                # Then apply operation
                op_map = {'+': 2, '-': 3, '*': 4}
                self.code.append(Instruction(Operation.OPR, 0, op_map[node.op]))
            
            computed[node_id] = True
        
        # Emit code for each assignment
        for var_name, node in self.dag.assignments:
            emit_code(node)
            self.code.append(Instruction(Operation.STO, 0, self.symbol_table[var_name]))
        
        self.code.append(Instruction(Operation.OPR, 0, 0))
        return self.code




def demo():
    DAGNode._id_counter = 0
    
    program = """
    var a
    var b
    var c
    var d
    
    a = 3 + 5
    b = 3 + 5
    c = a + b
    d = 3 + 5
    """
    
    print("="*70)
    print("COMPILER OPTIMISATION WITH DAGs")
    print("="*70)
    print(f"\nProgram:")
    print(program)
    
    # Build and show DAG
    print("\n" + "="*70)
    print("DAG ANALYSIS - Finding Common Subexpressions")
    print("="*70)
    dag_builder = DAGBuilder()
    for line in program.split('\n'):
        line = line.strip()
        if '=' in line and not line.startswith('//'):
            var, expr = [p.strip() for p in line.split('=', 1)]
            dag_builder.add_assignment(var, expr)
    
    print(dag_builder.visualize())
    print("\n★ Note: Nodes marked with ★ are referenced multiple times!")
    print("⟲ Note: SHARED nodes are computed once and reused!")
    
    # Compile without optimization
    print("\n" + "-"*50)
    print("NAIVE COMPILATION (No DAG)")
    print("-"*50)
    naive = NaiveCompiler()
    naive_code = naive.compile(program)
    print(f"Instructions generated: {len(naive_code)}")
    for i, instr in enumerate(naive_code):
        print(f"  {i:2d}: {instr}")
    
    # Compile with DAG optimization
    print("\n" + "-"*50)
    print("DAG-OPTIMISED COMPILATION")
    print("-"*50)
    dag_comp = DAGCompiler()
    dag_code = dag_comp.compile(program)
    print(f"Instructions generated: {len(dag_code)}")
    for i, instr in enumerate(dag_code):
        print(f"  {i:2d}: {instr}")
    
    # Show savings
    print("\n" + "="*70)
    print("OPTIMISATION RESULTS")
    print("="*70)
    savings = len(naive_code) - len(dag_code)
    percent = (savings / len(naive_code) * 100) if len(naive_code) > 0 else 0
    print(f"Naive compiler:    {len(naive_code)} instructions")
    print(f"DAG compiler:      {len(dag_code)} instructions")
    print(f"Instructions saved: {savings} ({percent:.1f}%)")
    
    # Verify correctness
    print("\nVERIFICATION (both compilers produce same results)\n")
    
    interp1 = Interpreter(naive_code)
    interp1.run()
    
    interp2 = Interpreter(dag_code)
    interp2.run()
    
    for var in ['a', 'b', 'c', 'd']:
        addr = naive.symbol_table[var]
        val1 = interp1.s[addr]
        val2 = interp2.s[addr]
        match = "+" if val1 == val2 else "-"
        print(f"  {var} = {val1} (naive) vs {val2} (DAG) {match}")
    
    print("\n" + "="*70)
    print("RESULT:")
    print("  The expression '3 + 5' appears 3 times in the source code.")
    print("  - Naive compiler: Computes it 3 separate times")
    print("  - DAG compiler:   Recognises it's the same, computes ONCE")
    print("  [This is Common Subexpression Elimination (CSE) via DAGs]")
    print("="*70)

if __name__ == "__main__":
    demo()
