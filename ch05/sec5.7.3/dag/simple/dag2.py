class ASTNode:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

    def __str__(self):
        if self.left is None and self.right is None:
            return str(self.value)
        return f"({self.left} {self.value} {self.right})"


class DAGNode:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

    def __str__(self):
        if self.left is None and self.right is None:
            return str(self.value)
        return f"({self.left} {self.value} {self.right})"


def parse_expression(expression):
    precedence = { '+': 1, '-': 1, '*': 2, '/': 2 }
    ops = []  # operators
    values = []  # operands

    def apply_operator():
        op = ops.pop()
        right = values.pop()
        left = values.pop()
        values.append(ASTNode(op, left, right))

    i = 0
    while i < len(expression):
        char = expression[i]
        if char.isalnum():  # numbers or variables
            start = i
            while i < len(expression) and expression[i].isalnum():
                i += 1
            values.append(ASTNode(expression[start:i]))
            continue
        elif char in precedence:  # operators
            while ops and ops[-1] != '(' and precedence[ops[-1]] >= precedence[char]:
                apply_operator()
            ops.append(char)
        elif char == '(':
            ops.append(char)
        elif char == ')':
            while ops and ops[-1] != '(': # .. until '('
                apply_operator()
            ops.pop()  # at last remove '('
        i += 1

    while ops:
        apply_operator()

    return values[0]


def ast_to_optimized_dag(ast):
    memo = { }  # store unique subexpressions and reuse them

    def traverse(node):
        if node is None:
            return None
        if node.left is None and node.right is None:  # leaf node
            return DAGNode(node.value)

        left = traverse(node.left)
        right = traverse(node.right)

        # unique key for the current subexpression
        key = (node.value, str(left), str(right))
        if key in memo:
            # reuse existing node if subexpression is already seen
            return memo[key]

        # else, create a new DAG node and memoize it
        dag_node = DAGNode(node.value, left, right)
        memo[key] = dag_node
        return dag_node

    return traverse(ast)


def render_tree_text(node, prefix="", visited=None, is_reused=False):
    if visited is None:
        visited = set()

    if node is None:
        return ""

    node_id = id(node)
    result = prefix

    # mark reused nodes
    if node_id in visited:
        result += f"{node.value} (REUSED)\n" # [* (REUSED)] where * is the node value
        return result

    visited.add(node_id)
    result += f"{node.value}\n"

    # indentation for child nodes
    indent = prefix + "    "
    result += render_tree_text(node.left, indent, visited)
    result += render_tree_text(node.right, indent, visited)

    return result

def linear_expression(node, visited=None):
    if visited is None:
        visited = set()
    
    if node is None:
        return ""
    
    node_id = id(node)
    
    if node_id in visited:
        return f"[{node.value} (REUSED)]"
    visited.add(node_id)
    
    if node.left is None and node.right is None:
        return str(node.value)
    
    left_expr = linear_expression(node.left, visited)
    right_expr = linear_expression(node.right, visited)
    return f"({left_expr} {node.value} {right_expr})"


if __name__ == "__main__":
    expression = "3 + a * (b - 1) + a * (b - 1)"
    print("Original Expression:", expression)

    # AST
    ast = parse_expression(expression)
    print("\nAST: ")
    print(linear_expression(ast))

    # convert to optimised DAG
    optimized_dag = ast_to_optimized_dag(ast)
    print("\nDAG: ")
    print(linear_expression(optimized_dag))

    print("\nAST Tree:")
    print(render_tree_text(ast))

    print("\nDAG Tree:")
    print(render_tree_text(optimized_dag))
    