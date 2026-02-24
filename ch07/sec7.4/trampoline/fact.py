def factorial_trampoline(n):
    def step(n, accumulator):
        if n == 0:
            return accumulator
        else:
            return lambda: step(n - 1, n * accumulator)
    
    result = step(n, 1)
    while callable(result):
        result = result()  # next step
    return result  # final

# Example
print(factorial_trampoline(5))  # Output: 120

# This implementation uses a trampoline to avoid deep recursion
# and allows us to compute factorials of large numbers without hitting a recursion limit.
