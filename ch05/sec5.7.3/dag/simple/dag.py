class ASTNode:
    """Node in an Abstract Syntax Tree - each occurrence creates a new node."""
    _id_counter = 0
    
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right
        ASTNode._id_counter += 1
        self.id = ASTNode._id_counter

    def __str__(self):
        if self.left is None and self.right is None:
            return str(self.value)
        return f"({self.left} {self.value} {self.right})"


class DAGNode:
    """Node in a Directed Acyclic Graph - identical subexpressions share nodes."""
    _id_counter = 0
    
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right
        DAGNode._id_counter += 1
        self.id = DAGNode._id_counter
        self.ref_count = 0  # Track how many times this node is referenced

    def __str__(self):
        if self.left is None and self.right is None:
            return str(self.value)
        return f"({self.left} {self.value} {self.right})"


def parse_expression(expression):
    """Parse an infix expression into an AST using the shunting-yard algorithm."""
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
    ops = []
    values = []

    def apply_operator():
        op = ops.pop()
        right = values.pop()
        left = values.pop()
        values.append(ASTNode(op, left, right))

    i = 0
    while i < len(expression):
        char = expression[i]
        if char.isalnum():
            start = i
            while i < len(expression) and expression[i].isalnum():
                i += 1
            values.append(ASTNode(expression[start:i]))
            continue
        elif char in precedence:
            while ops and ops[-1] != '(' and precedence[ops[-1]] >= precedence[char]:
                apply_operator()
            ops.append(char)
        elif char == '(':
            ops.append(char)
        elif char == ')':
            while ops and ops[-1] != '(':
                apply_operator()
            ops.pop()
        i += 1

    while ops:
        apply_operator()

    return values[0]


def ast_to_dag(ast):
    """
    Convert AST to DAG by detecting and sharing identical subexpressions.
    This is the key optimisation: instead of duplicating nodes, we reuse them!
    """
    # Maps canonical representation -> DAG node (for sharing)
    memo = {}

    def traverse(node):
        if node is None:
            return None
        
        # Leaf nodes (variables/constants) are always created fresh
        if node.left is None and node.right is None:
            canonical = f"LEAF:{node.value}"
            if canonical not in memo:
                memo[canonical] = DAGNode(node.value)
            dag_node = memo[canonical]
            dag_node.ref_count += 1
            return dag_node

        # Recursively process children first
        left = traverse(node.left)
        right = traverse(node.right)

        # Create canonical key for this subexpression
        # Two nodes with same operator and same children should share a DAG node
        canonical = f"{node.value}:{id(left)}:{id(right)}"
        
        if canonical in memo:
            # Found identical subexpression - reuse existing DAG node!
            dag_node = memo[canonical]
            dag_node.ref_count += 1
            return dag_node

        # New unique subexpression - create new DAG node
        dag_node = DAGNode(node.value, left, right)
        dag_node.ref_count = 1
        memo[canonical] = dag_node
        return dag_node

    return traverse(ast)


def count_nodes(root, visited=None):
    """Count total nodes in tree/DAG (accounting for sharing)."""
    if visited is None:
        visited = set()
    if root is None or id(root) in visited:
        return 0
    visited.add(id(root))
    return 1 + count_nodes(root.left, visited) + count_nodes(root.right, visited)


def render_tree(node, prefix="", is_left=True, visited=None, show_refs=False):
    """Render tree/DAG with visual indicators for shared nodes."""
    if visited is None:
        visited = {}
    if node is None:
        return ""
    
    node_id = id(node)
    
    # Check if we've seen this node before (indicates sharing in DAG)
    if node_id in visited:
        connector = "├── " if is_left else "└── "
        ref_info = f" [refs={node.ref_count}]" if show_refs and hasattr(node, 'ref_count') else ""
        return f"{prefix}{connector}⟲ {node.value} (shared from line {visited[node_id]}){ref_info}\n"
    
    # Track which line this node appears on
    line_num = len(visited) + 1
    visited[node_id] = line_num
    
    # Build node label
    connector = "├── " if is_left else "└── "
    node_label = f"{node.value}"
    if hasattr(node, 'id'):
        node_label = f"[{node.id}] {node_label}"
    if show_refs and hasattr(node, 'ref_count') and node.ref_count > 1:
        node_label += f" ★{node.ref_count}×"
    
    result = f"{prefix}{connector}{node_label}\n"

    # Render children
    if node.left or node.right:
        indent = prefix + ("│   " if is_left else "    ")
        if node.left:
            result += render_tree(node.left, indent, True, visited, show_refs)
        if node.right:
            result += render_tree(node.right, indent, False, visited, show_refs)
    
    return result


def print_statistics(ast, dag):
    """Show space savings from AST -> DAG conversion."""
    ast_nodes = count_nodes(ast)
    dag_nodes = count_nodes(dag)
    savings = ((ast_nodes - dag_nodes) / ast_nodes * 100) if ast_nodes > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"STATISTICS:")
    print(f"  AST nodes: {ast_nodes}")
    print(f"  DAG nodes: {dag_nodes}")
    print(f"  Space saved: {ast_nodes - dag_nodes} nodes ({savings:.1f}%)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Reset counters for clean IDs
    ASTNode._id_counter = 0
    DAGNode._id_counter = 0
    
    expression = "3 + a * (b - 1) + a * (b - 1)"
    print("="*60)
    print(f"Expression: {expression}")
    print("="*60)

    # Step 1: Parse to AST
    print("\n[STEP 1] Abstract Syntax Tree (AST)")
    print("Each occurrence creates a separate node - notice the duplicate subtrees:\n")
    ast = parse_expression(expression)
    print(render_tree(ast))

    # Step 2: Convert to DAG
    print("\n[STEP 2] Directed Acyclic Graph (DAG)")
    print("Identical subexpressions now share nodes (marked with ⟲):\n")
    dag = ast_to_dag(ast)
    print(render_tree(dag, show_refs=True))

    # Show the optimization benefit
    print_statistics(ast, dag)
    
    print("KEY INSIGHT:")
    print("  - In AST: 'a * (b - 1)' appears twice → stored twice")
    print("  - In DAG: 'a * (b - 1)' appears twice → stored ONCE (shared)")
    print("  - The ⟲ symbol shows where nodes are reused")
    print("  - The ★ symbol shows reference count (how many parents point to it)")

