#!/usr/bin/env python3
"""
K Interpreter Examples and Test Cases

This file demonstrates the features of the K interpreter with practical examples.
Run individual examples or use them as a test suite.
"""

from k_interpreter import (
    evaluate_expression,
    register_standard_operations,
    global_variables,
    KError
)


def run_example(description, expression, expected=None):
    """Run a single example and print the result."""
    try:
        result = evaluate_expression(expression)
        status = "✓" if expected is None or result == expected else "✗"
        print(f"{status} {description}")
        print(f"  Expression: {expression}")
        print(f"  Result: {result}")
        if expected is not None and result != expected:
            print(f"  Expected: {expected}")
        print()
        return result
    except KError as e:
        print(f"✗ {description}")
        print(f"  Expression: {expression}")
        print(f"  Error: {e}")
        print()
        return None


def section(title):
    """Print a section header."""
    print("=" * 70)
    print(f" {title}")
    print("=" * 70)
    print()


def main():
    """Run all examples."""
    # Initialize the interpreter
    register_standard_operations()
    global_variables.clear()
    
    section("1. Basic Arithmetic")
    
    run_example(
        "Addition of scalars",
        [3, "+", 4],
        7
    )
    
    run_example(
        "Subtraction",
        [10, "-", 3],
        7
    )
    
    run_example(
        "Multiplication",
        [6, "*", 7],
        42
    )
    
    run_example(
        "Percentage division (returns as percentage)",
        [75, "%", 100],
        75.0
    )
    
    section("2. Vector Operations")
    
    run_example(
        "Add scalar to vector",
        [[1, 2, 3], "+", 10],
        [11, 12, 13]
    )
    
    run_example(
        "Element-wise addition",
        [[1, 2, 3], "+", [10, 20, 30]],
        [11, 22, 33]
    )
    
    run_example(
        "Multiply vector by scalar",
        [[1, 2, 3, 4], "*", 2],
        [2, 4, 6, 8]
    )
    
    run_example(
        "Element-wise multiplication",
        [[2, 3, 4], "*", [5, 6, 7]],
        [10, 18, 28]
    )
    
    section("3. Monadic Operations")
    
    run_example(
        "Generate sequence (iota)",
        ["!", 5],
        [0, 1, 2, 3, 4]
    )
    
    run_example(
        "Negate numbers",
        ["-", [1, -2, 3, -4]],
        [-1, 2, -3, 4]
    )
    
    run_example(
        "Length of list",
        ["#", [10, 20, 30, 40, 50]],
        5
    )
    
    run_example(
        "Sum of list",
        ["+", [1, 2, 3, 4, 5]],
        15
    )
    
    run_example(
        "Reverse list",
        ["|", [1, 2, 3, 4, 5]],
        [5, 4, 3, 2, 1]
    )
    
    run_example(
        "First element",
        ["@", [10, 20, 30]],
        10
    )
    
    run_example(
        "Sort list",
        ["`", [3, 1, 4, 1, 5, 9, 2, 6]],
        [1, 1, 2, 3, 4, 5, 6, 9]
    )
    
    run_example(
        "Unique elements",
        ["?", [1, 2, 2, 3, 1, 4, 3, 5]],
        [1, 2, 3, 4, 5]
    )
    
    run_example(
        "Minimum value",
        ["&", [5, 2, 8, 1, 9]],
        1
    )
    
    run_example(
        "Maximum value",
        ["*", [5, 2, 8, 1, 9]],
        9
    )
    
    run_example(
        "Average",
        ["%", [10, 20, 30, 40, 50]],
        30.0
    )
    
    section("4. List Manipulation")
    
    run_example(
        "Take 3 elements",
        [3, "#", [10, 20, 30, 40, 50]],
        [10, 20, 30]
    )
    
    run_example(
        "Take with wrapping (more than length)",
        [7, "#", [1, 2, 3]],
        [1, 2, 3, 1, 2, 3, 1]
    )
    
    run_example(
        "Drop 2 elements",
        [2, "_", [10, 20, 30, 40, 50]],
        [30, 40, 50]
    )
    
    run_example(
        "Concatenate lists",
        [[1, 2, 3], ",", [4, 5, 6]],
        [1, 2, 3, 4, 5, 6]
    )
    
    run_example(
        "Flatten nested list",
        [";", [[1, 2], [3, 4], [5, 6]]],
        [1, 2, 3, 4, 5, 6]
    )
    
    section("5. Indexing and Selection")
    
    run_example(
        "Index single element",
        [[10, 20, 30, 40, 50], "@", 2],
        30
    )
    
    run_example(
        "Index multiple elements",
        [[10, 20, 30, 40, 50], "@", [0, 2, 4]],
        [10, 30, 50]
    )
    
    run_example(
        "Find indices of value",
        [3, "?", [1, 3, 2, 3, 4, 3, 5]],
        [1, 3, 5]
    )
    
    run_example(
        "Where (replicate indices)",
        ["^", [2, 0, 3, 1]],
        [0, 0, 2, 2, 2, 3]
    )
    
    section("6. Comparison Operations")
    
    run_example(
        "Equality check",
        [[1, 2, 3, 4], "=", [1, 0, 3, 0]],
        [True, False, True, False]
    )
    
    run_example(
        "Inequality check",
        [[1, 2, 3], "~", [1, 0, 3]],
        [False, True, False]
    )
    
    run_example(
        "Compare with scalar",
        [[1, 2, 3, 4, 5], "=", 3],
        [False, False, True, False, False]
    )
    
    section("7. String Operations")
    
    run_example(
        "String concatenation",
        ['"hello"', "+", '"world"'],
        "helloworld"
    )
    
    run_example(
        "String reversal",
        ["|", '"hello"'],
        "olleh"
    )
    
    run_example(
        "String length",
        ["#", '"hello"'],
        5
    )
    
    run_example(
        "String indexing",
        ['"hello"', "@", [0, 4, 1, 3]],
        "helo"
    )
    
    run_example(
        "Find substring positions",
        ['"l"', "?", '"hello"'],
        [2, 3]
    )
    
    section("8. Matrix Operations")
    
    run_example(
        "Transpose matrix",
        [".", [[1, 2, 3], [4, 5, 6]]],
        [[1, 4], [2, 5], [3, 6]]
    )
    
    section("9. List Literals")
    
    run_example(
        "Create list with semicolons",
        "(1;2;3;4;5)",
        [1, 2, 3, 4, 5]
    )
    
    run_example(
        "Nested lists",
        "((1;2);(3;4);(5;6))",
        [[1, 2], [3, 4], [5, 6]]
    )
    
    run_example(
        "Mixed types in list",
        '(1;"hello";3.14;true)',
        [1, "hello", 3.14, True]
    )
    
    section("10. Dictionary Operations")
    
    run_example(
        "Create dictionary",
        '["a":1;"b":2;"c":3]',
        {"a": 1, "b": 2, "c": 3}
    )
    
    run_example(
        "Dictionary lookup (single key)",
        ['["x":10;"y":20;"z":30]', "$", '"x"'],
        10
    )
    
    run_example(
        "Dictionary lookup (multiple keys)",
        ['["x":10;"y":20;"z":30]', "$", ['"x"', '"z"']],
        [10, 30]
    )
    
    section("11. Type Information")
    
    run_example(
        "Get type of scalar",
        ["$", 42],
        "i"
    )
    
    run_example(
        "Get type of float",
        ["$", 3.14],
        "f"
    )
    
    run_example(
        "Get types of list elements",
        ["$", [1, 3.14, '"hello"', True]],
        ["i", "f", "s", "b"]
    )
    
    section("12. Logical Operations")
    
    run_example(
        "Bitwise AND",
        [12, "&", 10],  # 1100 & 1010 = 1000 = 8
        8
    )
    
    run_example(
        "Bitwise OR",
        [12, "|", 10],  # 1100 | 1010 = 1110 = 14
        14
    )
    
    run_example(
        "Boolean AND on vectors",
        [[True, True, False, False], "&", [True, False, True, False]],
        [True, False, False, False]
    )
    
    section("13. Modulo Operation")
    
    run_example(
        "Modulo scalar",
        [3, "!", 10],
        1
    )
    
    run_example(
        "Modulo on vector",
        [3, "!", [10, 11, 12, 13, 14, 15]],
        [1, 2, 0, 1, 2, 0]
    )
    
    section("14. Variable Assignment")
    
    print("Testing variable assignment and usage...")
    print()
    
    # Clear variables
    global_variables.clear()
    
    # Assign variables
    global_variables["x"] = 10
    run_example(
        "Use variable x",
        ["x", "+", 5],
        15
    )
    
    global_variables["nums"] = [1, 2, 3, 4, 5]
    run_example(
        "Sum of variable nums",
        ["+", "nums"],
        15
    )
    
    global_variables["data"] = [10, 20, 30]
    run_example(
        "Operations with variables",
        ["data", "*", 2],
        [20, 40, 60]
    )
    
    section("15. Coalesce (First Non-Null)")
    
    # Note: Python None represents null
    global_variables["values"] = [None, None, 42, None, 99]
    run_example(
        "First non-null value",
        [":", "values"],
        42
    )
    
    section("16. Advanced Examples")
    
    run_example(
        "Sum of squares (1² + 2² + ... + 10²)",
        ["+", [["!", 10], "*", ["!", 10]]],
        285
    )
    
    global_variables["matrix"] = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    run_example(
        "Sum each row of matrix",
        ["+", "matrix"],  # This will give the monadic sum
        [1, 2, 3, 4, 5, 6, 7, 8, 9]  # Flattened sum
    )
    
    run_example(
        "Filter even numbers (positions where x mod 2 = 0)",
        ["^", [[2, "!", ["!", 10]], "=", 0]],
        [0, 2, 4, 6, 8]
    )
    
    section("17. String Repetition")
    
    run_example(
        "Repeat string",
        ['"ab"', "*", 3],
        "ababab"
    )
    
    section("18. Boolean Operations")
    
    run_example(
        "Negate booleans",
        ["-", [True, False, True]],
        [False, True, False]
    )
    
    run_example(
        "Boolean addition (OR)",
        [[True, False], "+", [False, True]],
        [True, True]
    )
    
    run_example(
        "Boolean multiplication (AND)",
        [[True, True, False], "*", [True, False, True]],
        [True, False, False]
    )
    
    section("Summary")
    
    print("Examples completed!")
    print()
    print("Try these expressions in the REPL:")
    print("  !10                    # Generate sequence 0..9")
    print("  +/!10                  # Sum of 0..9 (using fold, if implemented)")
    print("  3#(1;2;3;4;5)          # Take first 3 elements")
    print("  x:10                   # Assign variable")
    print("  x+5                    # Use variable")
    print("  (1;2;3)+(4;5;6)        # Vector addition")
    print("  |\"hello\"             # Reverse string")
    print("  3?(1;3;2;3;4;3;5)      # Find all occurrences of 3")
    print()


if __name__ == "__main__":
    main()
