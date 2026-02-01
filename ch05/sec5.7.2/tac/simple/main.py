
from parser import ASTNode, parse_expression

def generate_tac(ast):
    """
    Generate Three-Address Code from an AST.
    Uses post-order traversal to ensure operands
    are computed first. Returns list of instructions
    and the final result variable.
    """
    instructions = []  # TAC instructions
    temp_counter = 1   # Temp var counter

    def traverse(node):
        """Post-order traversal to generate TAC."""
        nonlocal temp_counter
        if node.left is None and node.right is None:  # Operand leaf
            return str(node.value)

        left = traverse(node.left)
        right = traverse(node.right)

        temp_var = f"t{temp_counter}"
        temp_counter += 1
        instructions.append(f"{temp_var} = {left} {node.value} {right}")
        return temp_var

    final_result = traverse(ast)
    return instructions, final_result

def print_ast(node, level=0):
    """Print AST with indentation."""
    if node is not None:
        print("  " * level + str(node.value))
        print_ast(node.left, level + 1)
        print_ast(node.right, level + 1)


# Example usage
expression = "3 + 5 * (2 - 1)"
print("Expression:", expression)

# Parse to AST
ast = parse_expression(expression)
print("\nAbstract Syntax Tree:")
print_ast(ast)

# Generate and print TAC
tac_instructions, final_var = generate_tac(ast)
print("\nThree-Address Code (TAC):")
for idx, instr in enumerate(tac_instructions, 1):
    print(f"{idx}: {instr}")
print(f"\nFinal result in: {final_var}")


