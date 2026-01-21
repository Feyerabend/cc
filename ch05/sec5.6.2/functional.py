class Environment:
    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent
    
    def bind(self, name, value):
        self.bindings[name] = value
    
    def lookup(self, name):
        if name in self.bindings:
            return self.bindings[name]
        elif self.parent:
            return self.parent.lookup(name)
        return None
    
    def extend(self):
        return Environment(parent=self)
    
    def display(self, level=0):
        indent = "  " * level
        print(f"{indent}Environment Level {level}:")
        for name, value in self.bindings.items():
            print(f"{indent}  {name} = {value}")
        if self.parent:
            self.parent.display(level + 1)

class Closure:
    """Represents a function with its captured environment"""
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env  ## Captured environment
    
    def __repr__(self):
        return f"<closure {self.params}>"

## Simulate this functional program:
## let x = 5
## let make_adder = λn. λy. n + y
## let add5 = make_adder 5
## add5 10  // Should return 15

global_env = Environment()

## let x = 5
global_env.bind('x', 5)

## let make_adder = λn. λy. n + y
## (For simplicity, we'll represent this as a Python function)
def make_adder(n, env):
    """Returns a closure that adds n to its argument"""
    adder_env = env.extend()
    adder_env.bind('n', n)
    
    def adder(y):
        return adder_env.lookup('n') + y
    
    ## In a real implementation, we'd return a Closure object
    return Closure(['y'], 'n + y', adder_env), adder

global_env.bind('make_adder', make_adder)

## let add5 = make_adder 5
closure_obj, add5_func = make_adder(5, global_env)
global_env.bind('add5', closure_obj)

## add5 10
result = add5_func(10)
print(f"Result: {result}")  ## 15

print("\nEnvironment after all bindings:")
global_env.display()
