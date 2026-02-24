"""
Continuation-Passing Style (CPS) Examples
Demonstrates CPS both standalone and combined with trampolines
"""

from dataclasses import dataclass
from typing import Callable, Union, Any, List
from functools import wraps


# Trampoline Infrastructure

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
    """Decorator that runs CPS functions with trampolining"""
    @wraps(fn)
    def trampolined(*args, **kwargs):
        result = fn(*args, **kwargs)
        steps = 0
        max_steps = 1000000
        
        while isinstance(result, Bounce):
            steps += 1
            if steps > max_steps:
                raise RuntimeError(f"Exceeded {max_steps} steps")
            result = result.thunk()
        
        if isinstance(result, Done):
            return result.value
        return result
    
    return trampolined


# Part 1: CPS Without Trampolines (For Comparison)

print()
print("Part 1: Basic CPS (No Trampolines)")
print()

# Example 1.1: Simple arithmetic in CPS
def add_cps(x, y, continuation):
    """Add two numbers and pass result to continuation"""
    continuation(x + y)

def multiply_cps(x, y, continuation):
    """Multiply two numbers and pass result to continuation"""
    continuation(x * y)

def compute_no_trampoline():
    """Compute (5 + 3) * 2 using CPS"""
    def after_add(sum_result):
        def after_multiply(final_result):
            print(f"(5 + 3) * 2 = {final_result}")
        multiply_cps(sum_result, 2, after_multiply)
    add_cps(5, 3, after_add)

compute_no_trampoline()

# Example 1.2: List sum in CPS (warning: will overflow for large lists!)
def sum_list_cps(lst, continuation):
    """Sum a list using CPS - NO trampoline"""
    if not lst:
        continuation(0)
    else:
        def after_rest(rest_sum):
            continuation(lst[0] + rest_sum)
        sum_list_cps(lst[1:], after_rest)

def print_sum(result):
    print(f"Sum: {result}")

print("\nList sum (small list):")
sum_list_cps([1, 2, 3, 4, 5], print_sum)

# This would overflow for large lists:
# sum_list_cps(list(range(10000)), print_sum)  # ← Stack overflow!

print()
print("Part 2: CPS With Trampolines (Stack Safe)")
print()

# Example 2.1: Factorial with CPS + Trampoline
def factorial_cps_impl(n, continuation):
    """Factorial using CPS with trampolines"""
    if n == 0:
        return Bounce(lambda: continuation(1))
    else:
        def after_recursive(result):
            return Bounce(lambda: continuation(n * result))
        return Bounce(lambda: factorial_cps_impl(n - 1, after_recursive))

@trampoline
def factorial_cps(n):
    """Trampolined factorial"""
    return factorial_cps_impl(n, lambda x: Done(x))

print(f"\nfactorial(10) = {factorial_cps(10)}")
print(f"factorial(100) = {factorial_cps(100)}")

# Example 2.2: List sum with CPS + Trampoline
def sum_list_cps_impl(lst, continuation):
    """Sum list using CPS with trampolines"""
    if not lst:
        return Bounce(lambda: continuation(0))
    else:
        def after_rest(rest_sum):
            return Bounce(lambda: continuation(lst[0] + rest_sum))
        return Bounce(lambda: sum_list_cps_impl(lst[1:], after_rest))

@trampoline
def sum_list_safe(lst):
    """Stack-safe list sum"""
    return sum_list_cps_impl(lst, lambda x: Done(x))

print(f"\nSum of [1..10]: {sum_list_safe(list(range(1, 11)))}")
print(f"Sum of [1..1000]: {sum_list_safe(list(range(1, 1001)))}")  # No overflow!


# Part 3: Advanced CPS Patterns

print()
print("Part 3: Advanced CPS Patterns")
print()

# Example 3.1: Multiple continuations (success/error)
def divide_cps(x, y, on_success, on_error):
    """Division with success and error continuations"""
    if y == 0:
        return Bounce(lambda: on_error("Division by zero"))
    else:
        return Bounce(lambda: on_success(x / y))

@trampoline
def safe_divide(x, y):
    """Trampolined division with error handling"""
    return divide_cps(
        x, y,
        on_success=lambda result: Done(f"Result: {result}"),
        on_error=lambda error: Done(f"Error: {error}")
    )

print(f"\n10 / 2 = {safe_divide(10, 2)}")
print(f"10 / 0 = {safe_divide(10, 0)}")

# Example 3.2: Async-style pipeline
def fetch_data_cps(url, continuation):
    """Simulate fetching data"""
    data = f"Data from {url}"
    return Bounce(lambda: continuation(data))

def parse_data_cps(data, continuation):
    """Parse the fetched data"""
    parsed = {"content": data.upper(), "length": len(data)}
    return Bounce(lambda: continuation(parsed))

def validate_data_cps(parsed, continuation):
    """Validate parsed data"""
    if parsed.get("length", 0) > 0:
        return Bounce(lambda: continuation(parsed))
    else:
        return Bounce(lambda: continuation(None))

def save_data_cps(parsed, continuation):
    """Save to database"""
    if parsed:
        result = f"Saved: {parsed['content'][:50]}..."
        return Bounce(lambda: continuation(result))
    else:
        return Bounce(lambda: continuation("Nothing to save"))

@trampoline
def process_pipeline(url):
    """Complete pipeline: fetch → parse → validate → save"""
    def after_fetch(data):
        def after_parse(parsed):
            def after_validate(validated):
                def after_save(result):
                    return Done(result)
                return save_data_cps(validated, after_save)
            return validate_data_cps(parsed, after_validate)
        return parse_data_cps(data, after_parse)
    return fetch_data_cps(url, after_fetch)

print(f"\nPipeline result:")
print(process_pipeline("https://api.example.com/users"))

# Example 3.3: CPS loops
def for_each_cps(items, body, continuation):
    """Process each item with body, then call continuation"""
    if not items:
        return Bounce(lambda: continuation([]))
    else:
        def after_current(current_result):
            def after_rest(rest_results):
                all_results = [current_result] + rest_results
                return Bounce(lambda: continuation(all_results))
            return Bounce(lambda: for_each_cps(items[1:], body, after_rest))
        return body(items[0], after_current)

def square_cps(x, continuation):
    """Square a number in CPS"""
    return Bounce(lambda: continuation(x * x))

@trampoline
def square_all(numbers):
    """Square all numbers in a list"""
    return for_each_cps(
        numbers,
        square_cps,
        lambda results: Done(results)
    )

print(f"\nSquare [1..10]: {square_all(list(range(1, 11)))}")

# Example 3.4: Tree traversal with CPS
@dataclass
class TreeNode:
    value: int
    left: 'TreeNode' = None
    right: 'TreeNode' = None

def tree_sum_cps(node, continuation):
    """Sum all values in tree using CPS"""
    if node is None:
        return Bounce(lambda: continuation(0))
    else:
        def after_left(left_sum):
            def after_right(right_sum):
                total = node.value + left_sum + right_sum
                return Bounce(lambda: continuation(total))
            return Bounce(lambda: tree_sum_cps(node.right, after_right))
        return Bounce(lambda: tree_sum_cps(node.left, after_left))

@trampoline
def sum_tree(root):
    """Trampolined tree sum"""
    return tree_sum_cps(root, lambda x: Done(x))

# Build a tree
tree = TreeNode(
    value=10,
    left=TreeNode(
        value=5,
        left=TreeNode(value=3),
        right=TreeNode(value=7)
    ),
    right=TreeNode(
        value=15,
        left=TreeNode(value=12),
        right=TreeNode(value=20)
    )
)

print(f"\nTree sum: {sum_tree(tree)}")
print("Expected: 10 + 5 + 3 + 7 + 15 + 12 + 20 = 72")

# Example 3.5: CPS state machine
@dataclass
class State:
    counter: int
    status: str
    history: List[str]

def state_machine_cps(state, continuation):
    """State machine with CPS"""
    new_history = state.history + [f"{state.status}:{state.counter}"]
    
    if state.status == "init":
        new_state = State(state.counter + 1, "processing", new_history)
        return Bounce(lambda: state_machine_cps(new_state, continuation))
    
    elif state.status == "processing":
        if state.counter >= 5:
            new_state = State(state.counter, "done", new_history)
            return Bounce(lambda: continuation(new_state))
        else:
            new_state = State(state.counter + 1, "processing", new_history)
            return Bounce(lambda: state_machine_cps(new_state, continuation))
    
    else:  # done
        return Bounce(lambda: continuation(state))

@trampoline
def run_state_machine(initial_value):
    """Run state machine from initial value"""
    initial_state = State(initial_value, "init", [])
    return state_machine_cps(initial_state, lambda s: Done(s))

print("\nState machine:")
final_state = run_state_machine(0)
print(f"Final counter: {final_state.counter}")
print(f"Final status: {final_state.status}")
print(f"History: {' -> '.join(final_state.history)}")


# Part 4: Performance and Comparison

print()
print("Part 4: Performance Comparison")
print()

import time

def measure_time(fn, *args):
    """Measure execution time"""
    start = time.time()
    result = fn(*args)
    elapsed = time.time() - start
    return result, elapsed

# Direct style (for comparison)
def factorial_direct(n):
    if n == 0:
        return 1
    return n * factorial_direct(n - 1)

# Compare
n_test = 100

result_direct, time_direct = measure_time(factorial_direct, n_test)
result_cps, time_cps = measure_time(factorial_cps, n_test)

print(f"\nFactorial({n_test}):")
print(f"  Direct style: {time_direct*1000:.3f}ms")
print(f"  CPS + Trampoline: {time_cps*1000:.3f}ms")
print(f"  Overhead: {(time_cps/time_direct - 1)*100:.1f}%")
print(f"  Results match: {result_direct == result_cps}")

# Deep recursion test - only CPS can do this!
print(f"\nDeep recursion (1000 levels):")
try:
    factorial_direct(1000)
    print("  Direct style: Succeeded (unexpected!)")
except RecursionError:
    print("  Direct style: RecursionError ✗")

try:
    result = factorial_cps(1000)
    print(f"  CPS + Trampoline: Success! ✓")
    print(f"    (result has {len(str(result))} digits)")
except Exception as e:
    print(f"  CPS + Trampoline: Failed - {e}")



# CPS + Trampolines

# 1. CPS makes control flow explicit
#    - "What comes next" is passed as a function parameter
#    - No hidden returns or implicit stack unwinding

# 2. CPS enables powerful patterns
#    - Multiple continuations (success/error)
#    - Custom control structures (loops, conditionals)
#    - Composable async pipelines

# 3. CPS + Trampolines = Stack Safety
#    - CPS alone still builds up the stack
#    - Trampolines convert continuation calls to iterations
#    - Together: explicit control + no stack overflow

# 4. Trade-offs
#    - Pro: Total control over flow, stack-safe
#    - Con: More verbose, slight performance overhead
#    - Use when: deep recursion, complex control flow

# 5. Real-world applications
#    - Async/await (hidden CPS)
#    - Parser combinators
#    - State machines
#    - Compiler transformations
