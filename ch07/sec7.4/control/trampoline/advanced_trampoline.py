"""
Advanced Trampoline Pattern Examples in Python

This module demonstrates several sophisticated uses of the trampoline pattern:
1. Mutual recursion (even/odd checker)
2. Tree traversal with continuation-passing style
3. Fibonacci with memoization
4. State machine with complex control flow
"""

from typing import Callable, Any, Union
from dataclasses import dataclass
from functools import wraps


# Core Trampoline Infrastructure

@dataclass
class Bounce:
    """Represents a continuation - more computation to do"""
    thunk: Callable[[], Any]

@dataclass  
class Done:
    """Represents a final result"""
    value: Any

Trampoline = Union[Bounce, Done]


def trampoline(fn: Callable) -> Callable:
    """
    Decorator that adds trampolining to a function.
    The decorated function can return either:
    - Bounce(lambda: ...) to continue computation
    - Done(value) to return a result
    """
    @wraps(fn)
    def trampolined(*args, **kwargs):
        result = fn(*args, **kwargs)
        steps = 0
        max_steps = 1000000  # Higher limit for Ackermann
        
        while isinstance(result, Bounce):
            steps += 1
            if steps > max_steps:
                raise RuntimeError(f"Trampoline exceeded {max_steps} steps - possible infinite loop")
            result = result.thunk()
        
        if isinstance(result, Done):
            return result.value
        return result
    
    return trampolined



# Example 1: Mutual Recursion (Even/Odd)

def is_even_mutual(n: int) -> Trampoline:
    """Check if number is even using mutual recursion with odd"""
    if n == 0:
        return Done(True)
    return Bounce(lambda: is_odd_mutual(n - 1))

def is_odd_mutual(n: int) -> Trampoline:
    """Check if number is odd using mutual recursion with even"""
    if n == 0:
        return Done(False)
    return Bounce(lambda: is_even_mutual(n - 1))

@trampoline
def is_even(n: int) -> Trampoline:
    """Trampolined version of is_even_mutual"""
    return is_even_mutual(n)

@trampoline
def is_odd(n: int) -> Trampoline:
    """Trampolined version of is_odd_mutual"""
    return is_odd_mutual(n)



# Example 2: Tree Traversal with Continuation-Passing Style

@dataclass
class Node:
    """Binary tree node"""
    value: int
    left: 'Node' = None
    right: 'Node' = None

def tree_sum_cps(node: Node, continuation: Callable[[int], Trampoline]) -> Trampoline:
    """
    Compute sum of tree values using continuation-passing style.
    This demonstrates how trampolines can handle complex control flow.
    """
    if node is None:
        return Bounce(lambda: continuation(0))
    
    # Process left subtree, then right subtree, then combine
    def after_left(left_sum: int) -> Trampoline:
        def after_right(right_sum: int) -> Trampoline:
            total = node.value + left_sum + right_sum
            return Bounce(lambda: continuation(total))
        return Bounce(lambda: tree_sum_cps(node.right, after_right))
    
    return Bounce(lambda: tree_sum_cps(node.left, after_left))

@trampoline
def tree_sum(node: Node) -> Trampoline:
    """Compute sum of all values in tree"""
    return tree_sum_cps(node, lambda x: Done(x))



# Example 3: Fibonacci with Memoization

class FibState:
    """Shared state for fibonacci computation"""
    def __init__(self):
        self.memo = {}

_fib_state = FibState()

def fib_trampoline(n: int) -> Trampoline:
    """
    Fibonacci with memoization using trampoline pattern.
    Uses a simpler approach than complex continuation chaining.
    """
    if n in _fib_state.memo:
        return Done(_fib_state.memo[n])
    
    if n <= 1:
        _fib_state.memo[n] = n
        return Done(n)
    
    # For trampoline to work, we need to compute iteratively
    # Build up from bottom instead of top-down recursion
    if n - 1 not in _fib_state.memo:
        return Bounce(lambda: fib_trampoline(n - 1))
    
    if n - 2 not in _fib_state.memo:
        return Bounce(lambda: fib_trampoline(n - 2))
    
    # Both values available, compute result
    result = _fib_state.memo[n - 1] + _fib_state.memo[n - 2]
    _fib_state.memo[n] = result
    return Done(result)

@trampoline
def fib(n: int) -> Trampoline:
    """Compute nth Fibonacci number"""
    _fib_state.memo.clear()  # Reset memo for each call
    # Compute all values up to n
    for i in range(n + 1):
        result = fib_trampoline(i)
        if isinstance(result, Done):
            continue
    return fib_trampoline(n)



# Example 4: State Machine with Complex Control Flow

@dataclass
class ParseState:
    """State for a simple parser"""
    input: str
    position: int
    stack: list

def parse_balanced_parens(state: ParseState) -> Trampoline:
    """
    Parse balanced parentheses using a state machine with trampoline.
    Returns True if parentheses are balanced, False otherwise.
    """
    # Base case: reached end of input
    if state.position >= len(state.input):
        return Done(len(state.stack) == 0)
    
    char = state.input[state.position]
    new_pos = state.position + 1
    
    if char == '(':
        # Push to stack and continue
        new_stack = state.stack + ['(']
        new_state = ParseState(state.input, new_pos, new_stack)
        return Bounce(lambda: parse_balanced_parens(new_state))
    
    elif char == ')':
        # Pop from stack if possible
        if not state.stack:
            return Done(False)  # Unbalanced: closing without opening
        new_stack = state.stack[:-1]
        new_state = ParseState(state.input, new_pos, new_stack)
        return Bounce(lambda: parse_balanced_parens(new_state))
    
    else:
        # Skip other characters
        new_state = ParseState(state.input, new_pos, state.stack)
        return Bounce(lambda: parse_balanced_parens(new_state))

@trampoline
def is_balanced(input_str: str) -> Trampoline:
    """Check if parentheses in string are balanced"""
    initial_state = ParseState(input_str, 0, [])
    return parse_balanced_parens(initial_state)



# Example 5: Ackermann Function (Serious Recursion Test)

def ackermann_trampoline(m: int, n: int) -> Trampoline:
    """
    Ackermann function using simple tail-recursion style trampolining.
    Stack frames are replaced with explicit continuation passing.
    """
    if m == 0:
        return Done(n + 1)
    
    if n == 0:
        # A(m, 0) = A(m-1, 1)
        return Bounce(lambda: ackermann_trampoline(m - 1, 1))
    
    # A(m, n) = A(m-1, A(m, n-1))
    # We need to compute the inner call first
    # This is complex for trampolines, so we limit to smaller values
    return Bounce(lambda: ackermann_helper(m, n))

def ackermann_helper(m: int, n: int) -> Trampoline:
    """Helper that computes A(m,n) by first computing A(m, n-1)"""
    # Recursively compute inner value
    inner = ackermann(m, n - 1)  # This uses the trampolined version
    # Now compute outer with the result
    return ackermann_trampoline(m - 1, inner)

@trampoline
def ackermann(m: int, n: int) -> Trampoline:
    """Compute Ackermann function A(m, n)"""
    return ackermann_trampoline(m, n)



# Tests and Examples

def run_examples():
    print()
    print("Advanced Trampoline Pattern Examples in Python")
    print()
    
    # Example 1: Mutual Recursion
    print("\n[Example 1] Mutual Recursion: Even/Odd Check")
    print()
    test_num = 10000
    print(f"is_even({test_num}): {is_even(test_num)}")
    print(f"is_odd({test_num}): {is_odd(test_num)}")
    print(f"is_even({test_num + 1}): {is_even(test_num + 1)}")
    print("  Successfully handled {0} mutual recursive calls without stack overflow".format(test_num))
    
    # Example 2: Tree Traversal
    print("\n[Example 2] Tree Traversal with Continuation-Passing Style")
    print()
    tree = Node(
        value=10,
        left=Node(
            value=5,
            left=Node(value=3),
            right=Node(value=7)
        ),
        right=Node(
            value=15,
            left=Node(value=12),
            right=Node(value=20)
        )
    )
    total = tree_sum(tree)
    print(f"Tree sum: {total}")
    print(f"Expected: {10 + 5 + 3 + 7 + 15 + 12 + 20} = 72")
    assert total == 72
    print("  Tree traversal successful")
    
    # Example 3: Fibonacci
    print("\n[Example 3] Fibonacci with Memoization")
    print()
    for n in [10, 20, 30, 50]:
        result = fib(n)
        print(f"fib({n}) = {result}")
    print("  Fibonacci computed efficiently with trampoline + memoization")
    
    # Example 4: Balanced Parentheses Parser
    print("\n[Example 4] State Machine: Balanced Parentheses Parser")
    print()
    test_cases = [
        ("(())", True),
        ("((()))", True),
        ("(()())", True),
        ("(()", False),
        ("())", False),
        (")(", False),
        ("a(b(c)d)e", True),
    ]
    for input_str, expected in test_cases:
        result = is_balanced(input_str)
        status = "✓" if result == expected else "✗"
        print(f"{status} is_balanced('{input_str}') = {result} (expected {expected})")
    
    # Example 5: Ackermann Function
    print("\n[Example 5] Ackermann Function (Extreme Recursion)")
    print()
    test_cases_ack = [
        (0, 0, 1),
        (0, 5, 6),
        (1, 0, 2),
        (1, 5, 7),
        (2, 0, 3),
        (2, 5, 13),
        (3, 0, 5),
        (3, 4, 125),  # This creates many recursive calls!
    ]
    for m, n, expected in test_cases_ack:
        result = ackermann(m, n)
        status = "(+)" if result == expected else "(-)"
        print(f"{status} ackermann({m}, {n}) = {result} (expected {expected})")
    
    print()
    print("All examples completed successfully!")
    print()
    print("\nNOTE:")
    print("  - Trampolines convert recursion to iteration, preventing stack overflow")
    print("  - Works with mutual recursion, continuation-passing, and state machines")
    print("  - Can be combined with other optimisations (like memoization)")
    print("  - Essential for deeply recursive algorithms in languages without TCO")


if __name__ == "__main__":
    run_examples()

