# firstclass.py
# Functional Patterns — 1. First-Class Functions
#
# Demonstrates that functions are ordinary values in Python:
# they can be passed, returned, stored, and iterated over.
#
# Run:  python firstclass.py


# 1. Passing a function as an argument

def square(x):
    return x * x

def negate(x):
    return -x

def increment(x):
    return x + 1

def apply(f, x):
    """Apply f to x.  f is received as an ordinary value."""
    return f(x)

print("-- 1. Passing a function as an argument --")
print(apply(square,    5))   # 25
print(apply(negate,    5))   # -5
print(apply(increment, 5))   # 6


# 2. Storing functions in a data structure (dispatch table)

operations = {
    'square':    square,
    'negate':    negate,
    'increment': increment,
    'double':    lambda x: x * 2,
}

def dispatch(name, value):
    """Look up an operation by name and apply it."""
    if name not in operations:
        raise KeyError(f"Unknown operation: {name!r}")
    return operations[name](value)

print("\n-- 2. Dispatch table --")
for name in operations:
    print(f"  {name}(5) = {dispatch(name, 5)}")



# 3. Returning a function (factory)

def make_multiplier(n):
    """Return a function that multiplies its argument by n."""
    def multiply(x):
        return x * n
    return multiply

double = make_multiplier(2)
triple = make_multiplier(3)

print("\n-- 3. Returning a function --")
print(f"  double(7)  = {double(7)}")    # 14
print(f"  triple(7)  = {triple(7)}")    # 21



# 4. Functions stored in a list and iterated (pipeline)

def pipeline(*funcs):
    """
    Return a function that applies each function in funcs in sequence.
    Each function receives the output of the previous one.
    """
    def run(value):
        for f in funcs:
            value = f(value)
        return value
    return run

process = pipeline(
    increment,          # 5 + 1 = 6
    double,             # 6 * 2 = 12
    negate,             # -12
)

print("\n-- 4. Pipeline of functions --")
print(f"  process(5) = {process(5)}")   # -12



# 5. Functions are objects: inspectable, comparable

print("\n-- 5. Functions as objects --")
print(f"  type(square)     = {type(square)}")
print(f"  square.__name__  = {square.__name__}")
print(f"  callable(square) = {callable(square)}")

# Functions can be elements of a set (they are hashable)
func_set = {square, negate, increment}
print(f"  square in func_set: {square in func_set}")



# 6. Late binding: the choice of function happens at call time

def make_reporter(transform):
    """
    Return a function that applies transform and prints the result.
    The choice of transform is bound when make_reporter is called,
    not when the returned function is later invoked.
    """
    def report(value):
        print(f"  transform({value}) = {transform(value)}")
    return report

print("\n-- 6. Late binding --")
report_square = make_reporter(square)
report_negate = make_reporter(negate)

report_square(4)   # transform(4) = 16
report_negate(4)   # transform(4) = -4

# We can swap in a completely different transform without changing report's body.
report_custom = make_reporter(lambda x: x ** 3)
report_custom(4)   # transform(4) = 64



# 7. Higher-order selection: choosing a strategy from outside

def apply_to_all(f, values):
    """Apply f to every element in values and return a new list."""
    return [f(v) for v in values]

nums = [1, 2, 3, 4, 5]

print("\n-- 7. Applying a function to a collection --")
print(f"  squares:  {apply_to_all(square, nums)}")
print(f"  negated:  {apply_to_all(negate, nums)}")
print(f"  doubled:  {apply_to_all(double, nums)}")
