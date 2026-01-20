#  Transforms a recursive function into a tail-recursive version.
#    Args:
#        base_case_check: Checks if the base case is met.
#        base_case_value: Value to return when base case is met.
#        update_accumulator: Updates the accumulator.
#        compute_next_args: Computes the next arguments for recursion.

def make_tail_recursive(base_case_check, base_case_value, update_accumulator, compute_next_args):
    def tail_recursive_wrapper(*args, accumulator=None, memo=None):
        print(f"Debug: args = {args}, accumulator = {accumulator}")
        
        # Init memoization dictionary
        if memo is None:
            memo = {}

        # Base case: check if the base case condition is met
        if base_case_check(*args):
            print("Debug: Base case reached")
            return accumulator if accumulator is not None else base_case_value
        
        # Check if the result is already in memo (dynamic programming)
        if args in memo:
            return memo[args]
        
        # Recursive case: compute the next step
        if accumulator is None:
            accumulator = base_case_value  # Init accumulator
        
        # Update accumulator and prepare next arguments
        accumulator = update_accumulator(accumulator, *args)
        next_args = compute_next_args(*args)

        # Tail-recursive call with memoization
        result = tail_recursive_wrapper(*next_args, accumulator=accumulator, memo=memo)

        # Store result in memo to avoid redundant calculations
        memo[args] = result
        return result
    
    return tail_recursive_wrapper

# Example 1: Factorial
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)

# Tail-recursive factorial
factorial_tail_recursive = make_tail_recursive(
    base_case_check=lambda n: n == 0,  # Base case check
    base_case_value=1,                 # Base case value
    update_accumulator=lambda acc, n: acc * n,  # Update accumulator
    compute_next_args=lambda n: (n - 1,)        # Compute next arguments
)

# Example 2: Fibonacci with Dynamic Programming (Memoization)
def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)

# Tail-recursive Fibonacci with memoization
fibonacci_tail_recursive = make_tail_recursive(
    base_case_check=lambda n: n <= 1,  # Base case check
    base_case_value=1,                 # Base case value
    update_accumulator=lambda acc, n: acc + n,  # Update accumulator
    compute_next_args=lambda n: (n - 1,)        # Compute next arguments
)

# Example 3: Sum of digits
def sum_of_digits(n):
    if n == 0:
        return 0
    else:
        return n % 10 + sum_of_digits(n // 10)

# Tail-recursive sum of digits
sum_of_digits_tail_recursive = make_tail_recursive(
    base_case_check=lambda n: n == 0,  # Base case check
    base_case_value=0,                 # Base case value
    update_accumulator=lambda acc, n: acc + (n % 10),  # Update accumulator
    compute_next_args=lambda n: (n // 10,)            # Compute next arguments
)

# Test transformed functions
print(factorial_tail_recursive(5))          # Output: 120
print(fibonacci_tail_recursive(10))         # Output: 55
print(sum_of_digits_tail_recursive(12345))  # Output: 15
