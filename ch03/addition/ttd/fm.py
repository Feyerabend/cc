
class LispError(Exception):
    """Custom exception for Lisp interpreter errors."""
    pass

class Environment:
    """Represents an environment for variable bindings."""
    def __init__(self, parent=None):
        self.bindings = {}
        self.functions = {}
        self.parent = parent

    def set(self, name, value):
        """Set a variable in the current environment."""
        self.bindings[name] = value

    def get(self, name):
        """Get a variable from the current environment or its parent."""
        if name in self.bindings:
            return self.bindings[name]
        elif name in self.functions:
            return self.functions[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            raise LispError(f"Undefined variable: {name}")

    def snapshot(self):
        """Take a snapshot of the current environment state."""
        return (self.bindings.copy(), self.functions.copy())

    def restore(self, snapshot):
        """Restore the environment to a previous state."""
        self.bindings, self.functions = snapshot

class Lisp:
    """Represents a simple Lisp interpreter."""
    def __init__(self):
        self.env = Environment()  # global
        self._initialize_builtins()

    def _initialize_builtins(self):
        """Initialize built-in functions."""
        self.env.set('+', self._add)
        self.env.set('-', self._subtract)
        self.env.set('*', self._multiply)
        self.env.set('/', self._divide)

    def _add(self, args):
        return sum(self.eval(arg) for arg in args)

    def _subtract(self, args):
        return self.eval(args[0]) - sum(self.eval(arg) for arg in args[1:])

    def _multiply(self, args):
        product = 1
        for arg in args:
            product *= self.eval(arg)
        return product

    def _divide(self, args):
        if len(args) == 0:
            raise LispError("Division by zero.")
        result = self.eval(args[0])
        for arg in args[1:]:
            result /= self.eval(arg)
        return result

    def eval(self, expr, env=None):
        """Evaluate an expression."""
        if env is None:
            env = self.env
        if isinstance(expr, int) or isinstance(expr, float):  # numeric literals
            return expr
        elif isinstance(expr, str):  # variable
            return env.get(expr)
        elif isinstance(expr, list):  # list represents expression
            if expr[0] == 'define':  # define a new variable or function
                return self.eval_define(expr, env)
            elif expr[0] == 'lambda':  # create a function
                return self.eval_lambda(expr)
            else:
                func = self.eval(expr[0], env)  # evaluate function
                args = [self.eval(arg, env) for arg in expr[1:]]  # evaluate arguments
                return self.apply(func, args)  # apply function to arguments
        raise LispError(f"Unknown expression: {expr}")

    def eval_define(self, expr, env):
        """Evaluate a define expression."""
        _, name, value = expr
        env.set(name, self.eval(value, env))  # bind value in given environment
        return None

    def eval_lambda(self, expr):
        """Evaluate a lambda expression."""
        _, params, body = expr  # expecting three parts (ignore one)
        return (params, body, self.env)  # return tuple representing closure

    def apply(self, func, args):
        """Apply a function to given arguments."""
        if isinstance(func, tuple):  # check if closure
            params, body, closure_env = func
            new_env = Environment(closure_env)
            for param, arg in zip(params, args):
                new_env.set(param, arg)
            return self.eval(body, new_env)  # evaluate function body in new environment
        else:
            return func(args)  # call built-in functions

# example
if __name__ == '__main__':
    lisp = Lisp()

    # define simple addition function
    lisp.eval(['define', 'add', ['lambda', ['x', 'y'], ['+', 'x', 'y']]])

    # define a "double" function
    lisp.eval(['define', 'double',
                ['lambda', ['x'],
                    ['*', 'x', 'x']  # return x multiplied by itself
                ]
            ]
    )

    # call add function
    result_add = lisp.eval(['add', 10, 5])
    print(f"10 + 5 = {result_add}")  # output: 10 + 5 = 15

    # call double function
    result_double = lisp.eval(['double', 4])
    print(f"double(4) = {result_double}")  # output: double(4) = 16

    # call additional arithmetic
    result_subtract = lisp.eval(['-', 10, 5])
    print(f"10 - 5 = {result_subtract}")  # output: 10 - 5 = 5

    result_multiply = lisp.eval(['*', 10, 5])
    print(f"10 * 5 = {result_multiply}")  # output: 10 * 5 = 50

    result_divide = lisp.eval(['/', 10, 5])
    print(f"10 / 5 = {result_divide}")  # output: 10 / 5 = 2.0

    # call compound expression using both user-defined and built-in functions
    result_compound = lisp.eval(['*', ['+', 2, 3], 4])
    print(f"(2 + 3) * 4 = {result_compound}")  # output: (2 + 3) * 4 = 20

    # snapshot of current environment state
    snapshot = lisp.env.snapshot()

    # now restore initial state, which does not include user-defined functions
    lisp.env.restore(snapshot)

    # try call add function after restoring environment
    try:
        lisp.eval(['add', 10, 5])
    except LispError as e:
        print(f"Error after restoring to initial state: {e}")

    # show current environment state after restoration
    print("\nCurrent Environment State after Restoration:")
    print("Variable Bindings:")
    for name, value in lisp.env.bindings.items():
        print(f"  - {name}: {value}")
    
    print("Function Definitions:")
    for name, func in lisp.env.functions.items():
        print(f"  - {name}: {func.__name__}")

    # final state of environment
    print("\nFinal Environment State:")
    print("Variable Bindings:")
    for name, value in lisp.env.bindings.items():
        print(f"  - {name}: {value}")

    print("Function Definitions:")
    for name, func in lisp.env.functions.items():
        print(f"  - {name}: {func.__name__}")

    # double function can still be used!
    result_new_function = lisp.eval(['double', 6])
    print(f"double(6) = {result_new_function}")  # output: double(6) = 36
