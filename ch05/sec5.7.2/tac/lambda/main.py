# main.py
# Main demonstration: Lambda Calculus with Three-Address Code (TAC)
# 
# This showcases how TAC transforms complex lambda expressions into
# a simple, linear, three-address instruction format that's easier to
# analyze, optimize, and execute.

from parser import parse_lambda, print_ast
from tac import generate_tac, print_tac, optimize_tac
from executor import evaluate, print_value, execute_tac

def demo_expression(expr, description):
    """Demonstrate parsing, TAC generation, and evaluation for an expression."""
    print(f"\nDEMO: {description}")
    print(f"Expression: {expr}")
    
    # Parse to AST
    ast = parse_lambda(expr)
    print("\n--- Abstract Syntax Tree (Hierarchical) ---")
    print_ast(ast)
    
    # Generate TAC
    tac_instructions, final_var = generate_tac(ast)
    print("\n--- Three-Address Code (Linear) ---")
    print_tac(tac_instructions, final_var)
    
    # Evaluate using AST
    result = evaluate(ast)
    print(f"\nEvaluation Result: {print_value(result)}")
    
    return tac_instructions, final_var


def main():
    print("\n   LAMBDA CALCULUS with THREE-ADDRESS CODE (TAC)")
    print("   TAC transforms complex nested lambda expressions into")
    print("   simple, linear instruction sequences.\n")
    
    # Demo 1: Simple identity function
    demo_expression(
        "λx.x",
        "Identity Function"
    )
    
    # Demo 2: Nested lambdas (Church boolean TRUE)
    demo_expression(
        "λx.λy.x",
        "K Combinator (Church TRUE)"
    )
    
    # Demo 3: Lambda with application in body
    demo_expression(
        "λx.(x y)",
        "Lambda with Application"
    )
    
    # Demo 4: Complex nested structure
    demo_expression(
        "λf.λx.(f (f x))",
        "Church Numeral 2 (applies f twice)"
    )
    
    # Demo 5: Beta reduction example
    tac_instr, final = demo_expression(
        "(λx.x a)",
        "Identity Applied (Beta Reduction)"
    )
    
    # Demo 6: More complex reduction
    demo_expression(
        "((λx.λy.x a) b)",
        "K Combinator Applied (returns first argument)"
    )

    # Demo 7: Show TAC optimisation
    print("DEMO: TAC Optimisation\n")
    expr = "λx.λy.(x y)"
    ast = parse_lambda(expr)
    instructions, final = generate_tac(ast)
    
    print(f"\nOriginal TAC ({len(instructions)} instructions):")
    for i, instr in enumerate(instructions, 1):
        print(f"  {i}: {instr}")
    
    optimized = optimize_tac(instructions)
    print(f"\nOptimised TAC ({len(optimized)} instructions):")
    for i, instr in enumerate(optimized, 1):
        print(f"  {i}: {instr}")
    
    # Highlight key advantages of TAC
    print("\n\n     ADVANTAGES OF TAC FOR LAMBDA CALCULUS")
    print("  1. Makes evaluation order explicit")
    print("  2. Converts tree structure to linear sequence")
    print("  3. Uses systematic temporary variables")
    print("  4. Enables easy optimization (dead code elimination, etc.)")
    print("  5. Simplifies code analysis and transformation")
    print("  6. Each instruction has at most 3 addresses (operands + result)")

if __name__ == "__main__":
    main()
