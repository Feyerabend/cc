
## AST Delta Debugger

An implementation of Zeller's delta debugging algorithm for Python AST
(Abstract Syntax Tree) minimization. This tool automatically reduces
failing code to its minimal form while preserving the failure condition.

This implementation achieves:
- *Example 1*: 75% reduction (12 -> 3 lines)
- *Example 2*: 35% reduction (17 -> 11 lines) 
- *Example 3*: 60% reduction (5 -> 2 lines)
- *Average*: ~57% code reduction while maintaining the bug

All reductions are *1-minimal*: removing any single statement causes the test to pass.

Delta debugging is an automated debugging technique that systematically reduces
a failing test case to a minimal form while preserving the failure. This implementation
works on Python source code by manipulating its AST representation.

An Abstract Syntax Tree (AST) is a tree representation of the structure of source code.
We will explore AST much more in chapter 5 [ch05](./../../../ch05/) in relation to e.g.
compilers. Python parses your code into an AST before executing it, where each node
represents a construct like a function definition, loop, or expression.
For example, x = 1 + 2 becomes:
```
Assign
├── targets: [Name(id='x')]
└── value: BinOp
    ├── left: Constant(value=1)
    ├── op: Add()
    └── right: Constant(value=2)
```
Working with ASTs allows us to programmatically understand and modify code structure,
making it perfect for automated minimisation. We can remove statements, simplify
expressions, and restructure code while maintaining syntactic validity.



### What is Delta Debugging?

Delta debugging answers the question:
*"What is the minimal test case that still exhibits the bug?"*

The algorithm works by:
1. *Divide*: Split the input into chunks
2. *Remove*: Try removing each chunk
3. *Test*: Check if the failure still occurs
4. *Recurse*: If removal works, repeat with the smaller input
5. *Refine*: Increase granularity (smaller chunks) if no chunk can be removed

This process continues until no further reduction is possible, yielding a
*1-minimal* result where removing any single element causes the test to pass.

Delta debugging was introduced by Andreas Zeller in:
Zeller, A. (1999). "Yesterday, my program worked. Today, it does not. Why?"
Proceedings of the 7th European Software Engineering Conference.

Key insights:
- *Automated Debugging*: Reduces manual effort in isolating bugs
- *Language Agnostic*: Applicable to any structured input
- *Provable Minimality*: Guarantees 1-minimal results
- *Practical Efficiency*: Logarithmic behavior on typical inputs


__ddmin Algorithm; Zeller's Original__

Given a failing input split into chunks `c₁, c₂, ..., cₙ`:

1. *Reduce to Complement*: Try removing each chunk `cᵢ`.
   If the complement `{c₁...cₙ} \ {cᵢ}` still fails, recurse on the complement.

2. *Reduce to Subset*: Try each chunk `cᵢ` alone. If it fails,
   recurse on just that chunk.

3. *Increase Granularity*: If neither works, split into smaller
   chunks (double the number of chunks) and repeat.

4. *Terminate*: When granularity equals input size and no reduction
   works, return the minimal failing input.


__The Test Predicate__

The core of delta debugging is the *test function* that returns:
- `True` if the program *fails* (exhibits the bug)
- `False` if the program *passes* (bug absent or syntax error)

```python
def test_source(source: str) -> bool:
    """Returns True if the bug is present."""
    try:
        exec(source)
        return False  # Executed without error - no bug
    except ZeroDivisionError:
        return True  # This is the bug we're looking for!
    except:
        return False  # Other errors don't count
```

*Important*: The test should check for a *specific failure condition*,
not just any output. For example:
- Good: Testing for a ZeroDivisionError, AssertionError, or wrong exception type
- Good: Testing that a specific function crashes
- Bad: Testing that `result == 9` (this just checks output, not a bug)

The difference is that a bug-focused test allows the algorithm to *remove
unnecessary code* that doesn't affect *whether the bug occurs*,
even if that code affects the final result.

Delta debugging assumes *monotonicity*: if a subset of the input fails,
removing more elements won't suddenly make it pass (in the way we care about).
This holds for most bugs but can fail for complex interdependencies.



### AST-Specific Adaptations

This implementation extends ddmin for Python AST structures:
- *Top-Level Minimisation*: First applies ddmin to module-level statements
- *Recursive Descent*: Then processes nested statement lists (function bodies, if/else blocks, loops)
- *Statement Focus*: Concentrates on statement-level reduction rather than expression simplification
- *Syntax Validation*: Ensures reduced ASTs remain syntactically valid Python
- *AST Preservation*: Maintains valid AST structure throughout the process

Main class implementing the delta debugging algorithm.

*Key Methods*
- `minimise()`: Entry point that returns minimized AST
- `_ddmin_statements()`: Core ddmin algorithm for statement lists  
- `_minimize_tree()`: Orchestrates top-level then nested minimization
- `_minimize_nested_statements()`: Recursively processes nested blocks
- `_test()`: Wrapper for test predicate with AST validation
- `_test_with_nested_modification()`: Tests modifications to nested structures

*Helpers*
- `to_source(tree)`: Convert AST to Python source code
- `clone(tree)`: Deep copy an AST
- `is_valid_ast(tree)`: Check syntactic validity

Use:
```python
# Define your test predicate
def test_source(source: str) -> bool:
    """Test for division by zero bug."""
    try:
        exec(source)
        return False  # No error - bug not present
    except ZeroDivisionError:
        return True  # Bug found!
    except:
        return False  # Wrong error type

# Your buggy program with extra code
program = """
def setup():
    x = 10
    return x

def compute(x):
    temp = x + 1
    result = 100 / (x - 10)  # Division by zero!
    return result

value = setup()
result = compute(10)
unused = 42
"""

# Run delta debugging
tree = ast.parse(program)
debugger = ASTDeltaDebugger(tree, test_source)
reduced = debugger.minimise()

print("Minimal failing program:")
print(ast.unparse(reduced))
# Output will remove setup(), temp, unused, etc.
# Keeping only what's needed for the division by zero
```


__Limitations and Considerations__

Statement-Level Minimisation:
- Removes unused top-level statements effectively
- Removes unused assignments and dead code
- Minimises function bodies by removing unnecessary operations

What Works Well:
- *Simple cases*: Reduces to minimal crashing code (e.g., `x / 0`)
- *Unused code*: Removes variables and statements that don't affect the bug
- *Function bodies*: Simplifies internal logic while preserving the crash

Current Limitations:
1. *Statement-Level Focus*: Minimizes statement lists but doesn't simplify
   expressions (e.g., won't change `x + 1 - 1` to `x`)

2. *Dependency Preservation*: Keeps code needed for syntactic validity
   (e.g., can't remove a function definition if it's called,
   even if the function itself isn't needed for the bug)

3. *Semantic Understanding*: Doesn't understand that `unused_function()`
   is truly unused if never called - it may keep function definitions
   that aren't necessary

4. *1-Minimality*: Achieves 1-minimal results (removing any single statement
   breaks the test), but not necessarily globally minimal

Assumptions:
- *Deterministic Tests*: Test predicate must be deterministic
- *Unambiguous Failure*: Clear definition of failure vs. pass
- *Monotonicity*: Bug doesn't require specific combinations of removed elements

Performance:
- *Time Complexity*: O(n²) in worst case for n-element input
- *Test Count*: Typically logarithmic in practice due to divide-and-conquer
- *Trade-off*: Can tune granularity for speed vs. reduction quality


__Possible Projects__

1. *Hierarchical Delta Debugging (HDD)*: Exploits input structure more effectively
2. *Parallel Testing*: Run test cases in parallel for speed
3. *Caching*: Memoize test results for identical subtrees
4. *Smart Simplification*: Use more sophisticated AST transformations
5. *Multi-Bug Support*: Handle multiple independent bugs

This is a simple educational implementation.
Areas for improvement:
- Expression-level simplification (not just statements)
- Better handling of semantic dependencies
- Parallel test execution
- Caching of test results




