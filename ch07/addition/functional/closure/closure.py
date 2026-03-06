# closure.py
# Functional Patterns -- 2. Closures
#
# Demonstrates closures: functions that carry their creation environment.
#
# Run:  python closure.py


# 1. Basic closure -- captured value from enclosing scope

def make_adder(n):
    """Return a function that adds n to its argument.
    n is captured from make_adder's scope."""
    def adder(x):
        return x + n
    return adder

add5  = make_adder(5)
add10 = make_adder(10)

print("-- 1. Basic closure --")
print(f"  add5(3)   = {add5(3)}")    # 8
print(f"  add10(3)  = {add10(3)}")   # 13
print(f"  add5 and add10 are different objects: {add5 is not add10}")
# Each call to make_adder produces a new closure with its own copy of n.



# 2. Mutable state inside a closure (nonlocal)

def make_counter(start=0):
    """Return a pair of functions sharing a mutable count variable."""
    count = start

    def increment(step=1):
        nonlocal count
        count += step
        return count

    def reset():
        nonlocal count
        count = start

    return increment, reset

inc, rst = make_counter(0)

print("\n-- 2. Mutable state (nonlocal) --")
print(f"  inc()    = {inc()}")    # 1
print(f"  inc()    = {inc()}")    # 2
print(f"  inc(5)   = {inc(5)}")   # 7
rst()
print(f"  after reset, inc() = {inc()}")  # 1


# 3. Two closures sharing the same environment

def make_account(initial_balance):
    """Bank account: deposit and withdraw share one balance variable."""
    balance = initial_balance

    def deposit(amount):
        nonlocal balance
        balance += amount
        return balance

    def withdraw(amount):
        nonlocal balance
        if amount > balance:
            raise ValueError("insufficient funds")
        balance -= amount
        return balance

    def get_balance():
        return balance

    return deposit, withdraw, get_balance

dep, wit, bal = make_account(100)

print("\n-- 3. Shared environment (account) --")
print(f"  initial balance: {bal()}")    # 100
print(f"  after deposit(50):  {dep(50)}")   # 150
print(f"  after withdraw(30): {wit(30)}")   # 120
print(f"  balance: {bal()}")               # 120



# 4. The loop capture gotcha

print("\n-- 4. Loop capture gotcha --")

# Wrong: all lambdas capture the same variable i
funcs_wrong = [lambda: i for i in range(4)]
print(f"  wrong (all see last i): {[f() for f in funcs_wrong]}")  # [3,3,3,3]

# Right: bind the value at creation time via a default argument
funcs_right = [lambda i=i: i for i in range(4)]
print(f"  right (each sees own i): {[f() for f in funcs_right]}")  # [0,1,2,3]

# Alternative: wrap in a factory function
def make_fn(i):
    return lambda: i

funcs_factory = [make_fn(i) for i in range(4)]
print(f"  factory (same result): {[f() for f in funcs_factory]}")  # [0,1,2,3]



# 5. Closure as a lightweight object (encapsulation without a class)

def make_stack():
    """A stack implemented entirely as closures over a list."""
    _data = []

    def push(value):
        _data.append(value)

    def pop():
        if not _data:
            raise IndexError("pop from empty stack")
        return _data.pop()

    def peek():
        if not _data:
            raise IndexError("peek at empty stack")
        return _data[-1]

    def size():
        return len(_data)

    return push, pop, peek, size

push, pop, peek, size = make_stack()

print("\n-- 5. Closure as object (stack) --")
push(10)
push(20)
push(30)
print(f"  size after 3 pushes: {size()}")   # 3
print(f"  peek: {peek()}")                  # 30
print(f"  pop:  {pop()}")                   # 30
print(f"  pop:  {pop()}")                   # 20
print(f"  size now: {size()}")              # 1



# 6. Closure capturing a function (decorator-like wrapping)

def logged(f):
    """Return a new function that logs calls to f."""
    def wrapper(*args):
        result = f(*args)
        print(f"  called {f.__name__}{args} -> {result}")
        return result
    return wrapper

def add(a, b):
    return a + b

logged_add = logged(add)

print("\n-- 6. Closure capturing a function (logged wrapper) --")
logged_add(3, 4)   # called add(3, 4) -> 7
logged_add(10, 1)  # called add(10, 1) -> 11



# 7. Lexical scope vs. dynamic scope -- illustration

print("\n-- 7. Lexical scope --")

x = "global"

def outer():
    x = "outer"
    def inner():
        # inner sees x from outer's scope (lexical), not from the call site
        return x
    return inner

fn = outer()
x = "modified global"   # changing the global does not affect fn
print(f"  fn() = {fn()!r}")   # 'outer'  -- lexical scope, not dynamic
