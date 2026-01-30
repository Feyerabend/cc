
# test_attribute.py

from attribute import parse, print_ast

# Test cases
test_input1 = "array[3] = object.property + 5"
print("Test Input 1:", test_input1)
ast1 = parse(test_input1)
print("Parsed AST 1:")
print_ast(ast1)
print("\n")

test_input2 = "x = 3"
print("Test Input 2:", test_input2)
ast2 = parse(test_input2)
print("Parsed AST 2:")
print_ast(ast2)
print("\n")

test_input3 = "object.property"
print("Test Input 3:", test_input3)
ast3 = parse(test_input3)
print("Parsed AST 3:")
print_ast(ast3)
print("\n")

# Additional test for precedence: should be (a + b) = c
test_input4 = "a + b = c"
print("Test Input 4:", test_input4)
ast4 = parse(test_input4)
print("Parsed AST 4:")
print_ast(ast4)
print("\n")

# Test unary minus
test_input5 = "-x * 2"
print("Test Input 5:", test_input5)
ast5 = parse(test_input5)
print("Parsed AST 5:")
print_ast(ast5)
print("\n")

# Test chaining
test_input6 = "a.b[c].d"
print("Test Input 6:", test_input6)
ast6 = parse(test_input6)
print("Parsed AST 6:")
print_ast(ast6)
print("\n")

# Test right-assoc assignment: a = b = c should be a = (b = c)
test_input7 = "a = b = c"
print("Test Input 7:", test_input7)
ast7 = parse(test_input7)
print("Parsed AST 7:")
print_ast(ast7)
print("\n")

# Test with bitwise ops
test_input8 = "a & b | c ^ d % 2"
print("Test Input 8:", test_input8)
ast8 = parse(test_input8)
print("Parsed AST 8:")
print_ast(ast8)
print("\n")

# Test parentheses overriding precedence
test_input9 = "(a + b) * c"
print("Test Input 9:", test_input9)
ast9 = parse(test_input9)
print("Parsed AST 9:")
print_ast(ast9)
print("\n")

# Test nested array access
test_input10 = "arr[ x[ y ] ] = z"
print("Test Input 10:", test_input10)
ast10 = parse(test_input10)
print("Parsed AST 10:")
print_ast(ast10)
print("\n")

