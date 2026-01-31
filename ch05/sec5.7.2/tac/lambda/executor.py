# executor.py
# Executor for lambda calculus: interpreter with beta-reduction.
# Can execute both AST and TAC representations.

from parser import Var, Lam, App

class Closure:
    """Closure for lambda with captured environment."""
    def __init__(self, lam, env):
        self.lam = lam
        self.env = env.copy() if env else {}
    
    def __repr__(self):
        return f"Closure({self.lam.param}, ...)"

def evaluate(ast, env=None):
    """
    Evaluate lambda AST with beta-reduction.
    
    This implements call-by-value evaluation strategy:
    1. Evaluate arguments before substitution
    2. Use closures to capture environments
    3. Perform beta-reduction when applying lambdas
    """
    if env is None:
        env = {}

    if isinstance(ast, Var):
        # Look up variable in environment
        if ast.name in env:
            val = env[ast.name]
            # If it's still a Var, return it; if it's a value, return it
            return val
        return ast  # Free variable
    
    elif isinstance(ast, Lam):
        # Lambda creates a closure
        return Closure(ast, env)
    
    elif isinstance(ast, App):
        # Evaluate function and argument
        func_val = evaluate(ast.func, env)
        arg_val = evaluate(ast.arg, env)

        # Apply function to argument
        if isinstance(func_val, Closure):
            # Beta-reduction: substitute argument for parameter
            lam = func_val.lam
            new_env = func_val.env.copy()
            new_env[lam.param] = arg_val
            return evaluate(lam.body, new_env)
        else:
            # Can't reduce further - return application
            return App(func_val, arg_val)
    
    elif isinstance(ast, Closure):
        # Already a value
        return ast
    
    raise ValueError(f"Unknown AST node type: {type(ast)}")

def print_value(value):
    """Print evaluated value in readable form."""
    if isinstance(value, Var):
        return value.name
    elif isinstance(value, Closure):
        lam = value.lam
        return f"λ{lam.param}.{print_value(lam.body)}"
    elif isinstance(value, Lam):
        return f"λ{value.param}.{print_value(value.body)}"
    elif isinstance(value, App):
        func_str = print_value(value.func)
        arg_str = print_value(value.arg)
        # Add parens if needed
        if isinstance(value.func, App):
            return f"({func_str} {arg_str})"
        return f"({func_str} {arg_str})"
    return str(value)

def execute_tac(instructions, final_var):
    """
    Execute TAC instructions to evaluate lambda expression.
    
    This demonstrates how TAC can be directly interpreted.
    Each instruction is executed in sequence, building up
    the final result.
    """
    env = {}  # Maps temp variables to values
    
    for instr in instructions:
        if instr.op == 'VAR':
            # Load variable reference
            env[instr.result] = Var(instr.arg1)
        
        elif instr.op == 'LAM':
            # Create lambda (parameter, body_temp)
            body = env.get(instr.arg2, Var(instr.arg2))
            lam = Lam(instr.arg1, body)
            env[instr.result] = Closure(lam, {})
        
        elif instr.op == 'APP':
            # Apply function to argument
            func = env.get(instr.arg1, Var(instr.arg1))
            arg = env.get(instr.arg2, Var(instr.arg2))
            
            if isinstance(func, Closure):
                # Perform beta-reduction
                lam = func.lam
                new_env = {lam.param: arg}
                result = evaluate(lam.body, new_env)
                env[instr.result] = result
            else:
                env[instr.result] = App(func, arg)
    
    return env.get(final_var, Var(final_var))
