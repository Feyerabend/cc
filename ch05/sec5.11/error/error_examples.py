#!/usr/bin/env python3
"""
Demonstration of the compiler's comprehensive error reporting system.
This file contains various test cases showing different types of errors.
"""

from compiler import compile_and_run

def test_case(name, code, verbose=False):
    """Run a test case and display results"""
    print("=" * 70)
    print(f"TEST CASE: {name}")
    print("=" * 70)
    print("Source Code:")
    print("-" * 70)
    print(code)
    print("-" * 70)
    print()
    
    success = compile_and_run(code, verbose=verbose)
    
    print()
    return success

def main():
    # Test 1: Multiple lexical errors
    test_case("Lexical Errors", '''
Let x = 42;
let y = "unterminated string;
let z = 3.14.159;
let @ = 5;
''')

    # Test 2: Multiple syntax errors
    test_case("Syntax Errors", '''
let x = 42
let y = 20;
print("Missing semicolon above")

if x > y {
    print("Missing closing brace"

while x < 100 {
    x = x + 1;
''')

    # Test 3: Semantic errors
    test_case("Semantic Errors", '''
let x = 42;
y = 10;
print(x + z);
let x = 5;
let unused = 100;
''')

    # Test 4: Mixed errors from multiple phases
    test_case("Mixed Errors", '''
Let x = 42
y = 10;
print(z + "test);

if x > y {
    let x = 5;
    print(a + b)
}

while k < 10 {
    k = k + 1;
''')

    # Test 5: Division by zero warning
    test_case("Runtime Warnings", '''
let x = 10;
let y = 0;
let z = x / 0;
print(z);
''')

    # Test 6: Successful compilation (no errors)
    print("\n" + "=" * 70)
    print("TEST CASE: Successful Compilation")
    print("=" * 70)
    test_case("Valid Program", '''
let x = 10;
let y = 20;

if x < y {
    print("x is smaller than y");
} else {
    print("x is greater or equal to y");
}

let i = 0;
while i < 5 {
    print(i);
    i = i + 1;
}

print("Done!");
''', verbose=True)

    # Test 7: Error recovery demonstration
    test_case("Error Recovery", '''
let a = 5;
let b
let c = 10;
d = 15;
print(a + c);
''')

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                COMPILER ERROR REPORTING DEMONSTRATION                 ║
║                                                                      ║
║  This demonstration shows how the compiler handles various types     ║
║  of errors across all compilation phases:                            ║
║                                                                      ║
║  1. Lexical Errors    - Invalid tokens, unterminated strings, etc.   ║
║  2. Syntax Errors     - Missing semicolons, braces, etc.             ║
║  3. Semantic Errors   - Undeclared variables, redeclarations, etc.   ║
║  4. Runtime Errors    - Division by zero, etc.                       ║
║                                                                      ║
║  The compiler attempts to:                                           ║
║  - Collect multiple errors before stopping                           ║
║  - Provide helpful suggestions for fixing errors                     ║
║  - Show context (source line) for each error                         ║
║  - Recover from errors to continue analysis                          ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    main()
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("""
Key Features Demonstrated:

✓ Multi-phase error collection (lexer → parser → semantic analyzer)
✓ Helpful error messages with line/column information
✓ Context display showing the problematic code
✓ Actionable suggestions for fixing each error
✓ Error recovery to find multiple issues in one compilation
✓ Warning system for non-fatal issues
✓ Clean separation of error reporting logic
✓ Configurable error reporting (verbose mode, stop-on-error)

The error reporting system helps developers quickly identify and fix
issues by providing clear, actionable feedback at every stage of
compilation.
""")

if __name__ == "__main__":
    main()
