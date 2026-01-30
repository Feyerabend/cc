
from attribute import parse, print_ast

env = {
    "x": "int",
    "a": "int",
    "b": "int",
    "c": "float",
}

# Test simple assignment
test_input1 = "x = 3 + 5"
print("Test Input 1:", test_input1)
ast1 = parse(test_input1, env)
print("Parsed AST 1:")
print_ast(ast1)
print("\n")

# Test with float
test_input2 = "c = 3.5 * 2"
print("Test Input 2:", test_input2)
ast2 = parse(test_input2, env)
print("Parsed AST 2:")
print_ast(ast2)
print("\n")

# Test chained assignment
test_input3 = "a = b = 4"
print("Test Input 3:", test_input3)
ast3 = parse(test_input3, env)
print("Parsed AST 3:")
print_ast(ast3)
print("\n")

# Test type mismatch (should raise error)
try:
    test_input4 = "a = 3.5"
    print("Test Input 4:", test_input4)
    ast4 = parse(test_input4, env)
    print("Parsed AST 4:")
    print_ast(ast4)
except Exception as e:
    print(f"Error: {e}")
print("\n")

# Test division
test_input5 = "-a / 2"
print("Test Input 5:", test_input5)
ast5 = parse(test_input5, env)
print("Parsed AST 5:")
print_ast(ast5)
print("\n")

# Test parentheses
test_input6 = "(a + b) * c"
print("Test Input 6:", test_input6)
ast6 = parse(test_input6, env)
print("Parsed AST 6:")
print_ast(ast6)
print("\n")

# Test undefined var (should raise error)
try:
    test_input7 = "undefined = 1"
    print("Test Input 7:", test_input7)
    ast7 = parse(test_input7, env)
    print("Parsed AST 7:")
    print_ast(ast7)
except Exception as e:
    print(f"Error: {e}")
print("\n")

