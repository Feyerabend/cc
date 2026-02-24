
## Continuation-Passing Style (CPS)

Continuation-Passing Style (CPS) is a programming technique where functions
don't return values directly to their callers. Instead, they receive an
additional parameter--a "continuation"--which is a function that specifies
"what to do next" with the result. This inverts the normal flow of control
and makes it explicit.


### Core Concept

In direct style (normal programming), functions return values:

```python
def add(x, y):
    return x + y

result = add(3, 4)
print(result)  ## 7
```

In continuation-passing style, functions pass results to continuations:

```python
def add_cps(x, y, continuation):
    continuation(x + y)

def print_result(result):
    print(result)

add_cps(3, 4, print_result)  ## 7
```

Instead of saying "compute the answer and give it back," we say "compute
the answer and give it to this function."


### Understanding Continuations

A *continuation* represents "the rest of the computation"--everything
that will happen after the current function completes.

#### Example: Building Intuition

```python
# Direct style
def calculate():
    x = 5
    y = x + 3      # continuation: "take result, assign to y, then.."
    z = y * 2      # continuation: "take result, assign to z, then.."
    return z       # continuation: "take result, return it"

result = calculate()
print(result)  # 16
```

In CPS, we make these continuations explicit:

```python
# Continuation-passing style
def calculate_cps(continuation):
    def after_x(x):
        def after_y(y):
            def after_z(z):
                continuation(z)
            multiply_cps(y, 2, after_z)
        add_cps(x, 3, after_y)
    return_cps(5, after_x)

calculate_cps(print)  # 16
```

Each continuation captures "what happens next" as an explicit function.


### Key Characteristics

#### 1. No Return Statements

Functions in CPS never use `return` to give values back. They always call
a continuation with the result.

```python
# Direct style
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)

# Continuation-passing style
def factorial_cps(n, continuation):
    if n == 0:
        continuation(1)  # No return!
    else:
        def after_recursive(result):
            continuation(n * result)
        factorial_cps(n - 1, after_recursive)
```

#### 2. Explicit Control Flow

All control flow becomes explicit function calls:
- What to do on success
- What to do on error
- What to do after async operations
- Order of operations

#### 3. Tail Position

CPS naturally places all function calls in tail position. The last thing
a function does is call the continuation--there's no "work after the call."

```python
def example_cps(x, cont):
    if x > 0:
        cont(x)  # tail position: last thing we do
    else:
        process_cps(x, cont)  # tail position: last thing we do
```

This is why CPS and [trampolines](./../trampoline/) work well together.


### CPS by Example

#### Example 1: Simple Arithmetic

*Direct Style*:
```python
def compute():
    a = 5
    b = a + 3
    c = b * 2
    return c

print(compute())  # 16
```

*Continuation-Passing Style*:
```python
def compute_cps(continuation):
    def after_a(a):
        def after_b(b):
            def after_c(c):
                continuation(c)
            multiply_cps(b, 2, after_c)
        add_cps(a, 3, after_b)
    identity_cps(5, after_a)

def identity_cps(value, cont):
    cont(value)

def add_cps(x, y, cont):
    cont(x + y)

def multiply_cps(x, y, cont):
    cont(x * y)

compute_cps(print)  # 16
```

*Insight*: Each "step" becomes a continuation that captures what to do
with the result.

#### Example 2: List Processing

*Direct Style*:
```python
def sum_list(lst):
    if not lst:
        return 0
    return lst[0] + sum_list(lst[1:])

print(sum_list([1, 2, 3, 4]))  # 10
```

*Continuation-Passing Style*:
```python
def sum_list_cps(lst, continuation):
    if not lst:
        continuation(0)
    else:
        def after_rest(rest_sum):
            continuation(lst[0] + rest_sum)
        sum_list_cps(lst[1:], after_rest)

sum_list_cps([1, 2, 3, 4], print)  # 10
```

*Insight*: The continuation `after_rest` captures "add the first element
to the sum of the rest."

#### Example 3: Tree Traversal

*Direct Style*:
```python
class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

def tree_sum(node):
    if node is None:
        return 0
    return node.value + tree_sum(node.left) + tree_sum(node.right)

tree = Node(10, Node(5), Node(15))
print(tree_sum(tree))  # 30
```

*Continuation-Passing Style*:
```python
def tree_sum_cps(node, continuation):
    if node is None:
        continuation(0)
    else:
        # First, compute sum of left subtree
        def after_left(left_sum):
            # Then, compute sum of right subtree
            def after_right(right_sum):
                # Finally, combine everything
                total = node.value + left_sum + right_sum
                continuation(total)
            tree_sum_cps(node.right, after_right)
        tree_sum_cps(node.left, after_left)

tree = Node(10, Node(5), Node(15))
tree_sum_cps(tree, print)  # 30
```

*Insight*: Continuations naturally express "do A, then with that result
do B, then with both results do C."

### Benefits of CPS

#### 1. Explicit Control Flow

All control flow is visible as function calls. No hidden returns or
implicit stack unwinding.

```python
# It's clear what happens at each step
def process_cps(data, on_success, on_error):
    if validate(data):
        on_success(data)
    else:
        on_error("Invalid data")
```

#### 2. Custom Control Structures

You can build your own control flow patterns:

```python
def try_cps(action, success_cont, error_cont):
    """Custom try/catch in CPS"""
    def safe_action():
        try:
            result = action()
            success_cont(result)
        except Exception as e:
            error_cont(e)
    safe_action()

def loop_cps(n, body, continuation):
    """Custom loop in CPS"""
    if n <= 0:
        continuation(None)
    else:
        def after_iteration(result):
            loop_cps(n - 1, body, continuation)
        body(n, after_iteration)
```

#### 3. Composable Asynchronous Operations

CPS naturally models async operations:

```python
def fetch_user_cps(user_id, continuation):
    # Simulate async fetch
    user = database.get(user_id)
    continuation(user)

def fetch_posts_cps(user, continuation):
    posts = database.get_posts(user.id)
    continuation(posts)

def display_user_posts(user_id):
    def after_user(user):
        def after_posts(posts):
            display(user, posts)
        fetch_posts_cps(user, after_posts)
    fetch_user_cps(user_id, after_user)
```

#### 4. First-Class Control Flow

Continuations are just functions, so you can:
- Store them in variables
- Pass them around
- Call them multiple times
- Choose between different continuations

```python
def choose_continuation(value, cont_a, cont_b):
    if value > 0:
        cont_a(value)  # Go this way
    else:
        cont_b(value)  # Go that way
```

### CPS and Trampolines: A Perfect Match

CPS and [trampolines](./../trampoline/) complement each other.

#### The Problem: Stack Overflow in CPS

CPS functions call continuations, which call more continuations. This builds
up the call stack just like regular recursion:

```python
def factorial_cps(n, continuation):
    if n == 0:
        continuation(1)  # Calls continuation
    else:
        def after_recursive(result):
            continuation(n * result)  # Calls continuation
        factorial_cps(n - 1, after_recursive)  # Recursive call
```

For `factorial_cps(10000, print)`, you still get stack overflow!

#### The Solution: CPS + Trampolines

Combine CPS with trampolines to get both explicit control flow AND
stack safety:

```python
from dataclasses import dataclass
from typing import Callable, Union

@dataclass
class Bounce:
    thunk: Callable

@dataclass
class Done:
    value: any

Trampoline = Union[Bounce, Done]

def trampoline(fn):
    """Run a CPS function with trampolining"""
    def trampolined(*args):
        result = fn(*args)
        while isinstance(result, Bounce):
            result = result.thunk()
        if isinstance(result, Done):
            return result.value
        return result
    return trampolined

def factorial_cps_trampoline(n, continuation):
    """CPS factorial with trampolines"""
    if n == 0:
        # Don't call continuation directly - bounce it!
        return Bounce(lambda: continuation(1))
    else:
        def after_recursive(result):
            # Don't call continuation directly - bounce it!
            return Bounce(lambda: continuation(n * result))
        # Don't recurse directly - bounce it!
        return Bounce(lambda: factorial_cps_trampoline(n - 1, after_recursive))

@trampoline
def factorial(n):
    """Trampolined wrapper"""
    return factorial_cps_trampoline(n, lambda x: Done(x))

print(factorial(10000))  # No stack overflow!
```

#### How They Work Together

*CPS* provides:
- Explicit control flow
- Composable operations
- "What to do next" as a parameter

*Trampolines* provide:
- Stack safety
- Iterative execution of continuations
- Elimination of deep call chains

*Together*:
```
CPS: "Here's what to do next" (explicit control)
Trampoline: "I'll do it iteratively" (stack safety)
Result: Explicit control flow + no stack overflow!
```

#### Visual Comparison

*CPS without Trampoline*:
```
factorial_cps(3, cont)
  └─> factorial_cps(2, after_2)
        └─> factorial_cps(1, after_1)
              └─> factorial_cps(0, after_0)
                    └─> after_0(1)
                          └─> after_1(1)
                                └─> after_2(2)
                                      └─> cont(6)
        [STACK DEPTH: 7+]
```

*CPS with Trampoline*:
```
Loop iteration 1: BOUNCE(factorial_cps(3, cont))
Loop iteration 2: BOUNCE(factorial_cps(2, after_2))
Loop iteration 3: BOUNCE(factorial_cps(1, after_1))
Loop iteration 4: BOUNCE(factorial_cps(0, after_0))
Loop iteration 5: BOUNCE(after_0(1))
Loop iteration 6: BOUNCE(after_1(1))
Loop iteration 7: BOUNCE(after_2(2))
Loop iteration 8: DONE(6)
[STACK DEPTH: constant!]
```

### Real-World Example: Async Pipeline

Let's build a data processing pipeline using CPS + trampolines:

```python
def fetch_data_cps(url, continuation):
    """Simulate fetching data"""
    data = f"Data from {url}"
    return Bounce(lambda: continuation(data))

def parse_data_cps(data, continuation):
    """Parse the fetched data"""
    parsed = {"content": data.upper()}
    return Bounce(lambda: continuation(parsed))

def validate_data_cps(parsed, continuation):
    """Validate parsed data"""
    if "content" in parsed:
        return Bounce(lambda: continuation(parsed))
    else:
        return Bounce(lambda: continuation(None))

def save_data_cps(parsed, continuation):
    """Save to database"""
    if parsed:
        result = f"Saved: {parsed['content']}"
        return Bounce(lambda: continuation(result))
    else:
        return Bounce(lambda: continuation("Nothing to save"))

@trampoline
def process_url(url):
    """Complete pipeline: fetch -> parse -> validate -> save"""
    def after_fetch(data):
        def after_parse(parsed):
            def after_validate(validated):
                def after_save(result):
                    return Done(result)
                return save_data_cps(validated, after_save)
            return validate_data_cps(parsed, after_validate)
        return parse_data_cps(data, after_parse)
    return fetch_data_cps(url, after_fetch)

result = process_url("https://api.example.com/data")
print(result)  # "Saved: DATA FROM HTTPS://API.EXAMPLE.COM/DATA"
```

*Key Points*:
- Each stage explicitly passes its result to the next stage
- Continuations capture "what to do with the result"
- Trampolines keep the stack shallow despite the chain of operations
- Easy to insert logging, error handling, or retries at any stage

### Advanced CPS Patterns

#### 1. Multiple Continuations (Success/Failure)

```python
def divide_cps(x, y, on_success, on_error):
    if y == 0:
        return Bounce(lambda: on_error("Division by zero"))
    else:
        return Bounce(lambda: on_success(x / y))

@trampoline
def safe_divide(x, y):
    return divide_cps(
        x, y,
        on_success=lambda result: Done(f"Result: {result}"),
        on_error=lambda error: Done(f"Error: {error}")
    )

print(safe_divide(10, 2))   # "Result: 5.0"
print(safe_divide(10, 0))   # "Error: Division by zero"
```

#### 2. CPS Loops

```python
def for_each_cps(items, body, continuation):
    """Process each item with body, then call continuation"""
    if not items:
        return Bounce(lambda: continuation([]))
    else:
        def after_current(current_result):
            def after_rest(rest_results):
                all_results = [current_result] + rest_results
                return Bounce(lambda: continuation(all_results))
            return for_each_cps(items[1:], body, after_rest)
        return body(items[0], after_current)

def square_cps(x, continuation):
    return Bounce(lambda: continuation(x * x))

@trampoline
def square_all(numbers):
    return for_each_cps(
        numbers,
        square_cps,
        lambda results: Done(results)
    )

print(square_all([1, 2, 3, 4, 5]))  # [1, 4, 9, 16, 25]
```

#### 3. CPS State Machines

```python
@dataclass
class State:
    value: int
    status: str

def state_transition_cps(state, continuation):
    """State machine with explicit continuations"""
    if state.status == "init":
        new_state = State(state.value + 1, "processing")
        return Bounce(lambda: continuation(new_state))
    
    elif state.status == "processing":
        if state.value > 5:
            new_state = State(state.value, "done")
            return Bounce(lambda: continuation(new_state))
        else:
            new_state = State(state.value + 1, "processing")
            return Bounce(lambda: state_transition_cps(new_state, continuation))
    
    else:  # done
        return Bounce(lambda: continuation(state))

@trampoline
def run_state_machine(initial_value):
    initial = State(initial_value, "init")
    return state_transition_cps(initial, lambda s: Done(s))

final = run_state_machine(0)
print(f"Final value: {final.value}, Status: {final.status}")
# Final value: 6, Status: done
```

### Comparison Table

| Aspect | Direct Style | CPS | CPS + Trampoline |
|--------|--------------|-----|------------------|
| *Control Flow* | Implicit (returns) | Explicit (continuations) | Explicit (continuations) |
| *Stack Usage* | Builds up | Builds up | Constant |
| *Recursion Depth* | Limited by stack | Limited by stack | Unlimited |
| *Readability* | ***** | ** | *** |
| *Control* | ** | ***** | ***** |
| *Composability* | *** | ***** | ***** |
| *Performance* | Fast | Moderate | Moderate |
| *Best For* | Simple cases | Complex control | Deep recursion |

### When to Use CPS

#### Use CPS When..

1. *Complex Control Flow*: Multiple paths, error handling, retries
   ```python
   fetch_cps(url,
       on_success=process,
       on_error=retry,
       on_retry_failed=log_error)
   ```

2. *Composing Operations*: Building pipelines of transformations
   ```python
   fetch → parse → validate → transform → save
   ```

3. *Custom Control Structures*: Implementing your own loops, conditionals
   ```python
   custom_while_cps(condition, body, continuation)
   ```

4. *Deep Recursion*: Combine with trampolines for stack safety
   ```python
   factorial_cps(10000, cont)  # With trampoline: OK!
   ```

5. *Explicit Async*: Making asynchronous flow explicit
   ```python
   async_op_1(data, lambda r1:
       async_op_2(r1, lambda r2:
           async_op_3(r2, final_continuation)))
   ```

#### Avoid CPS When..

1. *Simple Sequential Code*: Direct style is clearer
   ```python
   # Don't do this:
   add_cps(2, 3, lambda x: multiply_cps(x, 4, print))
   
   # Just do this:
   print((2 + 3) * 4)
   ```

2. *No Deep Recursion*: Stack depth isn't an issue

3. *Performance Critical*: CPS adds overhead with extra function calls

4. *Team Unfamiliar*: CPS has a learning curve

### CPS in the Wild

CPS appears in many real-world contexts:

#### JavaScript Callbacks (Pre-Promises)
```javascript
// Classic callback hell - this is CPS!
fetchUser(userId, function(user) {
    fetchPosts(user.id, function(posts) {
        fetchComments(posts[0].id, function(comments) {
            render(user, posts, comments);
        });
    });
});
```

#### Scheme/Lisp call/cc
```scheme
; Continuation captured and used
(call/cc
  (lambda (continuation)
    (continuation 42)))
```

#### Async/Await (Hidden CPS)
```python
# This is CPS under the hood!
async def process():
    user = await fetch_user()
    posts = await fetch_posts(user)
    return await render(posts)
```

#### Compiler Transformations
Many compilers convert code to CPS internally for optimisation and analysis.

### Practical Implementation Guide

#### Step 1: Identify "What Comes Next"

For any function, ask: "What happens with my result?"

```python
def original(x):
    result = compute(x)
    # What happens here? <- This becomes the continuation
    return result
```

#### Step 2: Add Continuation Parameter

```python
def cps_version(x, continuation):
    result = compute(x)
    continuation(result)  # Pass result to "what comes next"
```

#### Step 3: Convert Recursive Calls

```python
# Original
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)

# Step 1: Add continuation
def factorial_cps(n, cont):
    if n == 0:
        cont(1)
    else:
        # Step 2: "What comes next" after recursive call?
        # Answer: multiply by n, then call original continuation
        def after_recursion(result):
            cont(n * result)
        factorial_cps(n - 1, after_recursion)
```

#### Step 4: Add Trampolining (If Needed)

```python
def factorial_cps(n, cont):
    if n == 0:
        return Bounce(lambda: cont(1))  # Bounce instead of direct call
    else:
        def after_recursion(result):
            return Bounce(lambda: cont(n * result))
        return Bounce(lambda: factorial_cps(n - 1, after_recursion))
```

### Conclusion

Continuation-Passing Style transforms how we think about program flow:

*Direct Style*: "Do this, then do that, then return"
*CPS*: "Do this, then pass the result to a function that knows what to do next"

#### Insights

1. *Continuations = "What comes next"*: Every continuation captures the
   rest of the computation.

2. *All control flow becomes explicit*: No hidden returns or stack unwinding.

3. *Composable by nature*: Easy to chain operations, handle errors, or
   build custom control structures.

4. *Perfect match with trampolines*: CPS gives explicit control, trampolines
   give stack safety.

5. *Foundation of advanced features*: Understanding CPS illuminates async/await,
   generators, coroutines, and more.

#### The Big Picture

```
Direct Style:    x = f(a); y = g(x); z = h(y); return z
                 v (implicit control flow)

CPS:            f(a, λx. g(x, λy. h(y, λz. return z)))
                 v (explicit control flow)

CPS + Trampoline: BOUNCE(f(a, λx. BOUNCE(g(x, λy. BOUNCE(h(y, λz. DONE(z)))))))
                  v (explicit + stack-safe)

Result: Total control over program flow with no stack limitations!
```

CPS is powerful but has a learning curve. Start with small examples,
combine with trampolines for recursion, and use it when you need
fine-grained control over program flow. When you do, you'll have
the tools to express arbitrarily complex control patterns while
keeping your stack shallow.


### References

- "LISP 1.5 Programmer's Manual"--Early CPS concepts
- "Compiling with Continuations" by Andrew Appel
- "Representing Control in the Presence of First-Class Continuations" 
- Scheme's call/cc (call-with-current-continuation)
- JavaScript Promise chains and async/await

Given project: Implement continuation in one the LISP / Scheme
we have already implemented before.

