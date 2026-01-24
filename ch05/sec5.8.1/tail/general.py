# Generic automatic tail recursion transformer using AST analysis
# This code analyzes a given recursive function's AST to extract
# its base case, recursive case, and argument transformations,
# and then constructs a tail-recursive version with an accumulator.

import ast
import inspect
from typing import Callable, Any

class RecursionAnalyzer(ast.NodeVisitor):
    """Analyses recursive function structure from AST."""
    
    def __init__(self, func_name: str):
        self.func_name = func_name
        self.base_condition = None
        self.base_value = None
        self.recursive_op = None
        self.recursive_value = None
        self.arg_transform = None
        self.param_names = []
        self.num_params = 0
        
    def visit_FunctionDef(self, node):
        """Extract parameter names."""
        self.param_names = [arg.arg for arg in node.args.args]
        self.num_params = len(self.param_names)
        self.generic_visit(node)
        
    def visit_If(self, node):
        """Extract base case condition and values."""
        # Base case condition (the test)
        self.base_condition = node.test
        
        # Base case return value
        if node.body and isinstance(node.body[0], ast.Return):
            self.base_value = node.body[0].value
        
        # Recursive case (in else)
        if node.orelse and isinstance(node.orelse[0], ast.Return):
            self._analyze_recursive_case(node.orelse[0].value)
        
        self.generic_visit(node)
    
    def _analyze_recursive_case(self, node):
        """Analyse the recursive return statement."""
        if isinstance(node, ast.BinOp):
            # Pattern: value OP recursive_call or recursive_call OP value
            self.recursive_op = node.op
            
            # Determine which side has recursive call
            if self._is_recursive_call(node.right):
                self.recursive_value = node.left
                self._extract_arg_transform(node.right)
            elif self._is_recursive_call(node.left):
                self.recursive_value = node.right
                self._extract_arg_transform(node.left)
        elif isinstance(node, ast.Call):
            # Direct recursive call (no operation) - like gcd
            self._extract_arg_transform(node)
    
    def _is_recursive_call(self, node):
        """Check if node is a recursive call."""
        return (isinstance(node, ast.Call) and 
                isinstance(node.func, ast.Name) and 
                node.func.id == self.func_name)
    
    def _extract_arg_transform(self, call_node):
        """Extract how arguments are transformed in recursive call."""
        if isinstance(call_node, ast.Call) and call_node.args:
            self.arg_transform = call_node.args

def ast_to_lambda(node, param_names):
    """Convert an AST node to a lambda function."""
    if isinstance(param_names, str):
        param_names = [param_names]
    params_str = ', '.join(param_names)
    lambda_str = f"lambda {params_str}: {ast.unparse(node)}"
    return eval(lambda_str)

def ast_to_check(condition, param_names):
    """Convert condition AST to a check function."""
    if isinstance(param_names, str):
        param_names = [param_names]
    params_str = ', '.join(param_names)
    check_str = f"lambda {params_str}: {ast.unparse(condition)}"
    return eval(check_str)

def auto_tail_recursion(func: Callable) -> Callable:
    """
    Automagically converts a recursive function to tail-recursive form
    by analysing its AST structure.
    
    Args:
        func: Recursive function to transform
        
    Returns:
        Tail-recursive version with accumulator
    """
    # Parse the function's source
    source = inspect.getsource(func)
    tree = ast.parse(source)
    func_def = tree.body[0]
    
    # Analyze the structure
    analyzer = RecursionAnalyzer(func.__name__)
    analyzer.visit(func_def)
    
    # Extract components
    params = analyzer.param_names
    
    # Build check functions from AST
    base_check = ast_to_check(analyzer.base_condition, params)
    
    # Extract base value
    if isinstance(analyzer.base_value, ast.Constant):
        base_val = analyzer.base_value.value
    elif isinstance(analyzer.base_value, ast.Num):
        base_val = analyzer.base_value.n
    elif isinstance(analyzer.base_value, ast.Name):
        # Base case returns a parameter (like fibonacci or gcd)
        base_val_func = ast_to_lambda(analyzer.base_value, params)
        base_val = None  # Will be computed dynamically
    else:
        base_val = 0
    
    # Build accumulator update based on operation
    if isinstance(analyzer.recursive_op, ast.Mult):
        if analyzer.num_params == 1:
            update_acc = lambda acc, n: acc * n
        else:
            # Multi-param like power(base, exp) -> base * power(base, exp-1)
            expr_func = ast_to_lambda(analyzer.recursive_value, params)
            update_acc = lambda acc, *args: acc * expr_func(*args)
    elif isinstance(analyzer.recursive_op, ast.Add):
        # Check if it's adding the parameter or a derived value
        if isinstance(analyzer.recursive_value, ast.BinOp):
            # Complex expression like n % 10
            expr_func = ast_to_lambda(analyzer.recursive_value, params)
            update_acc = lambda acc, *args: acc + expr_func(*args)
        else:
            update_acc = lambda acc, *args: acc + args[0]
    elif isinstance(analyzer.recursive_op, ast.Sub):
        update_acc = lambda acc, *args: acc - args[0]
    elif analyzer.recursive_op is None:
        # No operation (like gcd) - just pass through
        update_acc = lambda acc, *args: acc
    else:
        update_acc = lambda acc, *args: acc
    
    # Build next args computation
    if analyzer.arg_transform:
        if len(analyzer.arg_transform) == 1:
            # Single param transformation
            next_args_func = ast_to_lambda(analyzer.arg_transform[0], params)
            compute_next = lambda *args: (next_args_func(*args),)
        else:
            # Multiple params (like gcd(b, a % b))
            next_funcs = [ast_to_lambda(arg, params) for arg in analyzer.arg_transform]
            compute_next = lambda *args: tuple(f(*args) for f in next_funcs)
    else:
        compute_next = lambda *args: tuple(a - 1 for a in args)
    
    # Create the tail-recursive wrapper
    def tail_recursive(*args, accumulator=None, memo=None):
        if memo is None:
            memo = {}
        
        # Base case
        if base_check(*args):
            if accumulator is not None:
                return accumulator
            # Handle cases like fibonacci/gcd where base returns a parameter
            if base_val is None and isinstance(analyzer.base_value, ast.Name):
                return base_val_func(*args)
            return base_val
        
        # Memoization check
        if args in memo:
            return memo[args]
        
        # Init accumulator
        if accumulator is None:
            accumulator = base_val if base_val is not None else 1
        
        # Update accumulator and compute next args
        accumulator = update_acc(accumulator, *args)
        next_args = compute_next(*args)
        
        # Tail recursive call
        result = tail_recursive(*next_args, accumulator=accumulator, memo=memo)
        memo[args] = result
        return result
    
    return tail_recursive

# Generic transformer that works with the original pattern
def make_tail_recursive_generic(func: Callable) -> dict:
    """
    Analyses a function and returns the components needed for
    the make_tail_recursive pattern.
    
    Returns:
        dict with: base_case_check, base_case_value, 
                   update_accumulator, compute_next_args
    """
    source = inspect.getsource(func)
    tree = ast.parse(source)
    func_def = tree.body[0]
    
    analyzer = RecursionAnalyzer(func.__name__)
    analyzer.visit(func_def)
    
    params = analyzer.param_names
    
    # Build components
    components = {
        'base_case_check': ast_to_check(analyzer.base_condition, params),
        'base_case_value': None,
        'update_accumulator': None,
        'compute_next_args': None
    }
    
    # Base value
    if isinstance(analyzer.base_value, ast.Constant):
        components['base_case_value'] = analyzer.base_value.value
    elif isinstance(analyzer.base_value, ast.Name):
        # For functions that return a parameter in base case
        components['base_case_value'] = 0  # Placeholder
    
    # Update accumulator
    if isinstance(analyzer.recursive_op, ast.Mult):
        if analyzer.num_params == 1:
            components['update_accumulator'] = lambda acc, n: acc * n
        else:
            expr_func = ast_to_lambda(analyzer.recursive_value, params)
            components['update_accumulator'] = lambda acc, *args: acc * expr_func(*args)
    elif isinstance(analyzer.recursive_op, ast.Add):
        if isinstance(analyzer.recursive_value, ast.BinOp):
            expr_func = ast_to_lambda(analyzer.recursive_value, params)
            components['update_accumulator'] = lambda acc, *args: acc + expr_func(*args)
        else:
            components['update_accumulator'] = lambda acc, *args: acc + args[0]
    elif analyzer.recursive_op is None:
        # Direct recursion (like gcd)
        components['update_accumulator'] = lambda acc, *args: args[0]
    
    # Compute next args
    if analyzer.arg_transform:
        if len(analyzer.arg_transform) == 1:
            next_args_func = ast_to_lambda(analyzer.arg_transform[0], params)
            components['compute_next_args'] = lambda *args: (next_args_func(*args),)
        else:
            next_funcs = [ast_to_lambda(arg, params) for arg in analyzer.arg_transform]
            components['compute_next_args'] = lambda *args: tuple(f(*args) for f in next_funcs)
    
    return components


# original pattern (see tail.py)

def make_tail_recursive(base_case_check, base_case_value, update_accumulator, compute_next_args):
    """Original pattern."""
    def tail_recursive_wrapper(*args, accumulator=None, memo=None):
        if memo is None:
            memo = {}
        
        if base_case_check(*args):
            return accumulator if accumulator is not None else base_case_value
        
        if args in memo:
            return memo[args]
        
        if accumulator is None:
            accumulator = base_case_value
        
        accumulator = update_accumulator(accumulator, *args)
        next_args = compute_next_args(*args)
        
        result = tail_recursive_wrapper(*next_args, accumulator=accumulator, memo=memo)
        memo[args] = result
        return result
    
    return tail_recursive_wrapper



# examples

def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)

def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)

def sum_of_digits(n):
    if n == 0:
        return 0
    else:
        return n % 10 + sum_of_digits(n // 10)

def countdown(n):
    if n <= 0:
        return 0
    else:
        return n + countdown(n - 1)

def power(base, exp):
    if exp == 0:
        return 1
    else:
        return base * power(base, exp - 1)

def gcd(a, b):
    if b == 0:
        return a
    else:
        return gcd(b, a % b)



# Test automatic transformation
print("Automatic Tail Recursion Transformation\n")

factorial_tr = auto_tail_recursion(factorial)
print(f"factorial(5) = {factorial_tr(5)}")  # 120

sum_digits_tr = auto_tail_recursion(sum_of_digits)
print(f"sum_of_digits(12345) = {sum_digits_tr(12345)}")  # 15

countdown_tr = auto_tail_recursion(countdown)
print(f"countdown(10) = {countdown_tr(10)}")  # 55


print("\nUsing Original Pattern with Auto-Extracted Components\n")

# Extract components and use with original pattern
fact_comp = make_tail_recursive_generic(factorial)
factorial_manual = make_tail_recursive(**fact_comp)
print(f"factorial_manual(5) = {factorial_manual(5)}")

sum_comp = make_tail_recursive_generic(sum_of_digits)
sum_manual = make_tail_recursive(**sum_comp)
print(f"sum_manual(12345) = {sum_manual(12345)}")


print("\nMulti-Parameter Functions\n")

# GCD example
gcd_comp = make_tail_recursive_generic(gcd)
print(f"GCD components extracted:")
print(f"  base_case_check(48, 0) = {gcd_comp['base_case_check'](48, 0)}")
print(f"  base_case_value = {gcd_comp['base_case_value']}")

# Power example  
power_comp = make_tail_recursive_generic(power)
print(f"\nPower components extracted:")
print(f"  base_case_check(2, 0) = {power_comp['base_case_check'](2, 0)}")
print(f"  base_case_value = {power_comp['base_case_value']}")
print(f"  update_accumulator(1, 2, 3) = {power_comp['update_accumulator'](1, 2, 3)}")


print("\nExtracted Components (Factorial)\n")

# Show extracted components for factorial
fact_components = make_tail_recursive_generic(factorial)
print("Factorial components:")
print(f"  base_case_check(0) = {fact_components['base_case_check'](0)}")
print(f"  base_case_check(5) = {fact_components['base_case_check'](5)}")
print(f"  base_case_value = {fact_components['base_case_value']}")
print(f"  update_accumulator(1, 5) = {fact_components['update_accumulator'](1, 5)}")
print(f"  compute_next_args(5) = {fact_components['compute_next_args'](5)}")


print("\nAST Visualisation\n")

# Show detailed AST analysis for each function
for func, name in [(factorial, 'factorial'), (gcd, 'gcd'), (power, 'power')]:
    print(f"\n{name.upper()}:")
    analyzer = RecursionAnalyzer(name)
    tree = ast.parse(inspect.getsource(func))
    analyzer.visit(tree)
    
    print(f"  Parameters: {analyzer.param_names}")
    print(f"  Base condition: {ast.unparse(analyzer.base_condition)}")
    print(f"  Base value: {ast.unparse(analyzer.base_value)}")
    if analyzer.recursive_op:
        print(f"  Operation: {analyzer.recursive_op.__class__.__name__}")
        print(f"  Recursive value: {ast.unparse(analyzer.recursive_value)}")
    if analyzer.arg_transform:
        print(f"  Arg transforms: {[ast.unparse(a) for a in analyzer.arg_transform]}")
    print()
