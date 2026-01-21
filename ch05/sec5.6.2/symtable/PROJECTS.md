
## Hands-On Projects


1. *Symbol tables are fundamental* to programming language
   implementation: they bridge source code and execution

2. *Different paradigms need different approaches:*
   - Procedural: Focus on mutable state and block scopes
   - Functional: Focus on immutable bindings and closures
   - Logical: Focus on unification and backtracking

3. *Core operations are universal:*
   - Insert/bind a symbol
   - Lookup a symbol
   - Enter/exit scopes

4. *Scope management is critical:*
   - Always balance enter_scope/exit_scope calls
   - Search from innermost to outermost
   - Handle shadowing correctly

5. *Optimisation matters:*
   - Use hash tables for each scope level
   - Consider caching for deep nesting
   - Two-pass compilation for forward references


### Project 1: Expression Calculator with Variables

*Goal:* Build a calculator that supports variables.

*Example:*
```
> x = 5
> y = 3
> x + y * 2
11
```

*Tasks:*
1. Implement a symbol table to store variable values
2. Parse expressions and variable assignments
3. Evaluate expressions using the symbol table
4. Add support for functions: `square(n) = n * n`

*Starter Code:*
```python
class Calculator:
    def __init__(self):
        self.symbol_table = SymbolTable()
    
    def execute(self, statement):
        if '=' in statement:
            # Assignment
            name, expr = statement.split('=')
            value = self.evaluate(expr.strip())
            self.symbol_table.insert(name.strip(), {'value': value})
        else:
            # Expression
            return self.evaluate(statement)
    
    def evaluate(self, expr):
        # TODO: Parse and evaluate expression
        # Hint: Handle numbers, variables, and operators
        pass
```

### Project 2: Mini Python Interpreter

*Goal:* Implement a subset of Python that handles functions and scopes.

*Supported Features:*
```python
x = 10
y = 20

def add(a, b):
    result = a + b
    return result

print(add(x, y))
```

*Tasks:*
1. Parse function definitions and add them to the symbol table
2. Create new scopes when entering functions
3. Bind parameters to arguments
4. Handle return statements
5. Support nested function definitions

*Starter Code:*
```python
class MiniPythonInterpreter:
    def __init__(self):
        self.global_env = SymbolTable()
        self.current_env = self.global_env
    
    def execute_assignment(self, name, value):
        self.current_env.insert(name, {'value': self.evaluate(value)})
    
    def execute_function_def(self, name, params, body):
        func = {
            'type': 'function',
            'params': params,
            'body': body,
            'env': self.current_env  # Capture defining environment
        }
        self.current_env.insert(name, func)
    
    def call_function(self, func_name, args):
        func = self.current_env.lookup(func_name)
        if func['type'] != 'function':
            raise RuntimeError(f"{func_name} is not a function")
        
        # Create new scope for function call
        self.current_env.enter_scope()
        
        # Bind parameters to arguments
        for param, arg in zip(func['params'], args):
            self.current_env.insert(param, {'value': arg})
        
        # Execute function body
        result = self.execute_statements(func['body'])
        
        # Exit function scope
        self.current_env.exit_scope()
        
        return result
    
    def execute_statements(self, statements):
        # TODO: Implement statement execution
        pass
    
    def evaluate(self, expr):
        # TODO: Implement expression evaluation
        pass
```

### Project 3: Scope Visualiser

*Goal:* Build a tool that visualizes symbol table changes as code executes.

*Example Output:*
```
Step 1: x = 5
┌─────────────────┐
│ Global Scope    │
│  x = 5          │
└─────────────────┘

Step 2: def foo():
┌─────────────────┐
│ Global Scope    │
│  x = 5          │
│  foo = <func>   │
└─────────────────┘

Step 3: foo() called
┌─────────────────┐
│ Global Scope    │
│  x = 5          │
│  foo = <func>   │
│ ┌─────────────┐ │
│ │ foo() Scope │ │
│ │  y = 10     │ │
│ └─────────────┘ │
└─────────────────┘
```

*Tasks:*
1. Hook into symbol table operations (insert, lookup, enter_scope, exit_scope)
2. Generate visual representation after each operation
3. Highlight which variable is being accessed
4. Show shadowing relationships
5. Add step-by-step execution mode


### Project 4: Type Checker

*Goal:* Build a static type checker using symbol tables.

*Example:*
```python
# Good code
x: int = 5
y: int = 10
z: int = x + y  # OK: int + int = int

# Bad code
a: int = 5
b: str = "hello"
c: int = a + b  # ERROR: Cannot add int and str
```

*Tasks:*
1. Extend symbol table entries to include type information
2. Implement type checking for:
   - Variable assignments
   - Function calls (argument types match parameters)
   - Binary operations (compatible operand types)
   - Return statements (match function return type)
3. Report type errors with line numbers and helpful messages

*Starter Code:*
```python
class TypeChecker:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.type_rules = {
            ('int', '+', 'int'): 'int',
            ('float', '+', 'float'): 'float',
            ('str', '+', 'str'): 'str',
            # Add more rules...
        }
    
    def check_assignment(self, var_name, var_type, expr_type):
        if var_type != expr_type:
            raise TypeError(
                f"Cannot assign {expr_type} to {var_type} variable '{var_name}'"
            )
    
    def check_binary_op(self, left_type, op, right_type):
        if (left_type, op, right_type) not in self.type_rules:
            raise TypeError(
                f"Cannot apply {op} to {left_type} and {right_type}"
            )
        return self.type_rules[(left_type, op, right_type)]
    
    def check_function_call(self, func_name, arg_types):
        func_info = self.symbol_table.lookup(func_name)
        param_types = [p[0] for p in func_info['parameters']]
        
        if len(arg_types) != len(param_types):
            raise TypeError(
                f"{func_name} expects {len(param_types)} arguments, "
                f"got {len(arg_types)}"
            )
        
        for i, (arg_type, param_type) in enumerate(zip(arg_types, param_types)):
            if arg_type != param_type:
                raise TypeError(
                    f"Argument {i+1} to {func_name}: expected {param_type}, "
                    f"got {arg_type}"
                )
        
        return func_info['return_type']
```

### Project 5: Closure Debugger for Functional Languages

*Goal:* Visualize how closures capture their environment.

*Example:*
```javascript
function makeCounter() {
    let count = 0;        // Captured by increment
    
    function increment() {
        count = count + 1;
        return count;
    }
    
    return increment;
}

let counter1 = makeCounter();
let counter2 = makeCounter();

counter1();  // Returns 1
counter1();  // Returns 2
counter2();  // Returns 1 (different environment!)
```

*Visualisation:*
```
counter1 environment:
  count = 2  (captured)

counter2 environment:
  count = 1  (captured)

Global environment:
  makeCounter = <function>
  counter1 = <closure with env1>
  counter2 = <closure with env2>
```

*Tasks:*
1. Track which variables each closure captures
2. Show separate environment instances for each closure
3. Visualize environment chains (closure -> parent -> grandparent)
4. Demonstrate that each closure has its own copy of captured variables

### Project 6: Prolog Unification Visualizer

*Goal:* Step through the unification process visually.

*Example Query:* `?- append([1,2], [3,4], X).`

*Visualization Steps:*
```
Step 1: Try to unify with: append([], L, L)
  [1,2] ≠ []  ✗ Failed

Step 2: Try to unify with: append([H|T], L, [H|R]) :- append(T, L, R)
  [1,2] = [H|T]  ✓ H=1, T=[2]
  [3,4] = L      ✓ L=[3,4]
  X = [H|R]      ✓ X=[1|R]
  
  Now solve subgoal: append([2], [3,4], R)
  
  Step 2a: Try append([], L, L)
    [2] ≠ []  ✗ Failed
  
  Step 2b: Try append([H|T], L, [H|R]) :- append(T, L, R)
    [2] = [H|T]  ✓ H=2, T=[]
    [3,4] = L    ✓ L=[3,4]
    R = [H|R2]   ✓ R=[2|R2]
    
    Now solve: append([], [3,4], R2)
    
    Step 2b-i: Try append([], L, L)
      [] = []    ✓
      [3,4] = L  ✓ L=[3,4]
      R2 = L     ✓ R2=[3,4]
    
    Backtrack and substitute:
    R = [2|R2] = [2|[3,4]] = [2,3,4]
    X = [1|R] = [1|[2,3,4]] = [1,2,3,4]

Solution: X = [1,2,3,4]
```

*Tasks:*
1. Implement the unification algorithm with step-by-step tracking
2. Show bindings at each step
3. Visualize backtracking when unification fails
4. Display the final solution with all substitutions applied
5. Handle multiple solutions (choice points)

### Project 7: Multi-Paradigm Language

*Goal:* Create a language that supports procedural, functional, and logical features.

*Example Program:*
```
# Procedural
x = 10
y = 20

# Functional
let add = λa b. a + b
let result = add x y

# Logical
fact: parent(tom, bob)
fact: parent(bob, ann)
query: parent(X, ann)?
```

*Tasks:*
1. Design a unified symbol table that handles:
   - Mutable variables (procedural)
   - Immutable bindings (functional)
   - Logical facts and unification
2. Implement mode switching between paradigms
3. Allow paradigms to interoperate (e.g., use logical query result in procedural code)
4. Compare how the same concept is expressed in each paradigm



### Questions and Solutions

#### Question 1: Implementing Nested Scopes

*Q:* Implement a symbol table that supports nested scopes with proper shadowing.

*Test Case:*
```python
x = 10
def foo():
    x = 20
    def bar():
        x = 30
        print(x)  # Should print 30
    bar()
    print(x)      # Should print 20
foo()
print(x)          # Should print 10
```

*Solution:*
```python
class SymbolTable:
    def __init__(self):
        self.scopes = [{}]
    
    def enter_scope(self):
        self.scopes.append({})
    
    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
    
    def insert(self, name, value):
        self.scopes[-1][name] = value
    
    def lookup(self, name):
        # Search from innermost to outermost
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def update(self, name, value):
        """Update existing variable (finds in outer scopes)"""
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name] = value
                return True
        return False

# Test
st = SymbolTable()
st.insert('x', 10)
print(st.lookup('x'))  # 10

st.enter_scope()
st.insert('x', 20)     # Shadows global x
print(st.lookup('x'))  # 20

st.enter_scope()
st.insert('x', 30)     # Shadows both
print(st.lookup('x'))  # 30

st.exit_scope()
print(st.lookup('x'))  # 20 (back to foo's x)

st.exit_scope()
print(st.lookup('x'))  # 10 (back to global x)
```

#### Question 2: Static vs Dynamic Scoping

*Q:* Explain the difference between static (lexical) and dynamic scoping. How does this affect the symbol table?

*Answer:*

*Static Scoping* (used by most languages):
- Variable binding determined by code structure
- Lookup uses the scope where the function was *defined*

```python
x = 10

def foo():
    print(x)  # Uses x from where foo was defined

def bar():
    x = 20
    foo()     # Prints 10 (lexical scope)

bar()
```

*Dynamic Scoping* (used by some older languages):
- Variable binding determined by call stack
- Lookup uses the scope where the function was *called*

```python
x = 10

def foo():
    print(x)  # Uses x from where foo was called

def bar():
    x = 20
    foo()     # Would print 20 (dynamic scope)

bar()
```

*Symbol Table Implementation:*

Static scoping:
```python
class StaticEnvironment:
    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent  # Captured at definition time
    
    def lookup(self, name):
        if name in self.bindings:
            return self.bindings[name]
        elif self.parent:
            return self.parent.lookup(name)
        return None
```

Dynamic scoping:
```python
class DynamicEnvironment:
    def __init__(self):
        self.call_stack = [{}]  # Stack of scopes
    
    def push_scope(self):
        self.call_stack.append({})
    
    def pop_scope(self):
        self.call_stack.pop()
    
    def lookup(self, name):
        # Search from top of call stack down
        for scope in reversed(self.call_stack):
            if name in scope:
                return scope[name]
        return None
```

#### Question 3: Detecting Undefined Variables

*Q:* Implement a function that detects if a variable is used before it's defined.

*Solution:*
```python
class SymbolTableWithTracking:
    def __init__(self):
        self.scopes = [{}]
        self.used_before_defined = []
    
    def declare(self, name):
        """Declare a variable (may not have value yet)"""
        self.scopes[-1][name] = {'defined': False, 'value': None}
    
    def define(self, name, value):
        """Define a variable (give it a value)"""
        var = self.lookup(name)
        if var is None:
            raise RuntimeError(f"Variable '{name}' not declared")
        var['defined'] = True
        var['value'] = value
    
    def use(self, name):
        """Use a variable (for reading)"""
        var = self.lookup(name)
        if var is None:
            raise RuntimeError(f"Variable '{name}' not declared")
        if not var['defined']:
            self.used_before_defined.append(name)
            raise RuntimeError(f"Variable '{name}' used before definition")
        return var['value']
    
    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

# Test
st = SymbolTableWithTracking()
st.declare('x')
# st.use('x')  # Would raise error: used before definition
st.define('x', 10)
print(st.use('x'))  # OK: 10
```

#### Question 4: Implementing Closures

*Q:* How do you implement closures in a symbol table? Show how a closure captures its environment.

*Solution:*
```python
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
        """Create child environment (for nested scope)"""
        return Environment(parent=self)

class Closure:
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env  # Captured environment!
    
    def call(self, args):
        # Create new environment extending the captured one
        call_env = self.env.extend()
        
        # Bind parameters
        for param, arg in zip(self.params, args):
            call_env.bind(param, arg)
        
        # Execute body in this environment
        return self.execute(self.body, call_env)
    
    def execute(self, body, env):
        # Simplified execution (just return a value)
        # In reality, would execute statements
        return env.lookup('result') if 'result' in body else None

# Example: makeAdder
global_env = Environment()

# function makeAdder(n) { return function(x) { return n + x } }
def make_adder(n):
    # Create environment for makeAdder call
    adder_env = global_env.extend()
    adder_env.bind('n', n)
    
    # Create closure that captures adder_env
    inner_func = Closure(['x'], 'n + x', adder_env)
    return inner_func

add5 = make_adder(5)
add10 = make_adder(10)

# Both closures have their own captured 'n'
print(add5.env.lookup('n'))   # 5
print(add10.env.lookup('n'))  # 10
```

#### Question 5: Optimising Symbol Table Lookups

*Q:* Symbol table lookups can be slow with deep nesting. How can you optimise them?

*Solutions:*

*1. Hash Each Scope Level*
```python
# Already doing this - each scope is a dict (O(1) lookup per level)
self.scopes = [{}]  # List of dicts
```

*2. Cache Lookup Results*
```python
class CachedSymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.cache = {}  # name -> (scope_level, value)
    
    def insert(self, name, value):
        self.scopes[-1][name] = value
        # Invalidate cache for this name
        if name in self.cache:
            del self.cache[name]
    
    def lookup(self, name):
        # Check cache first
        if name in self.cache:
            level, value = self.cache[name]
            # Verify cache is still valid
            if level < len(self.scopes) and name in self.scopes[level]:
                return value
        
        # Cache miss - do full lookup
        for i, scope in enumerate(reversed(self.scopes)):
            if name in scope:
                value = scope[name]
                level = len(self.scopes) - 1 - i
                self.cache[name] = (level, value)
                return value
        
        return None
```

*3. Display List (for compiler optimisation)*
```python
class DisplayListSymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.scope_depths = []  # Track function nesting depth
    
    def enter_scope(self, is_function=False):
        self.scopes.append({})
        if is_function:
            # New function - reset depth tracking
            self.scope_depths.append(len(self.scopes) - 1)
    
    def lookup_with_offset(self, name):
        """
        Returns (scope_offset, local_offset) for direct access.
        Useful for compiled code generation.
        """
        for i, scope in enumerate(reversed(self.scopes)):
            if name in scope:
                scope_level = len(self.scopes) - 1 - i
                local_names = list(scope.keys())
                local_offset = local_names.index(name)
                return (i, local_offset)  # (how many scopes up, index in that scope)
        return None
```

#### Question 6: Handling Forward References

*Q:* How do you handle cases where a function references another function defined later?

*Example:*
```python
def foo():
    return bar()  # bar not yet defined!

def bar():
    return 42
```

*Solution: Two-Pass Compilation*

```python
class TwoPassSymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.forward_refs = []  # Track unresolved references
    
    def first_pass(self, declarations):
        """First pass: collect all function declarations"""
        for decl in declarations:
            if decl['type'] == 'function':
                self.insert(decl['name'], {
                    'kind': 'function',
                    'defined': False,  # Declared but not yet processed
                    'params': decl['params'],
                    'body': None
                })
    
    def second_pass(self, declarations):
        """Second pass: process function bodies"""
        for decl in declarations:
            if decl['type'] == 'function':
                func = self.lookup(decl['name'])
                func['body'] = decl['body']
                func['defined'] = True
                
                # Verify all references in body are valid
                self.verify_references(decl['body'])
    
    def verify_references(self, body):
        """Check that all used names are defined"""
        for name in self.extract_names(body):
            if self.lookup(name) is None:
                raise RuntimeError(f"Undefined reference: {name}")
    
    def extract_names(self, body):
        # Extract all identifiers from body
        # (Simplified - real implementation would parse AST)
        pass

# Usage
st = TwoPassSymbolTable()

program = [
    {'type': 'function', 'name': 'foo', 'params': [], 'body': 'return bar()'},
    {'type': 'function', 'name': 'bar', 'params': [], 'body': 'return 42'}
]

st.first_pass(program)   # Collect all function names
st.second_pass(program)  # Process bodies (now bar is known)
```




### Garbage Collection and Symbol Tables

Symbol tables can help implement garbage collection by tracking variable lifetimes:

```python
class RefCountingSymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.ref_counts = {}  # Track how many references each object has
    
    def insert(self, name, value):
        self.scopes[-1][name] = value
        # Increment reference count
        if id(value) in self.ref_counts:
            self.ref_counts[id(value)] += 1
        else:
            self.ref_counts[id(value)] = 1
    
    def exit_scope(self):
        if len(self.scopes) > 1:
            # Decrement ref counts for variables going out of scope
            for name, value in self.scopes[-1].items():
                self.ref_counts[id(value)] -= 1
                if self.ref_counts[id(value)] == 0:
                    # Object can be garbage collected
                    self.collect(value)
            
            self.scopes.pop()
    
    def collect(self, value):
        print(f"Garbage collecting: {value}")
        # Actually free memory here
```

### Compile-Time vs Runtime Symbol Tables

*Compile-Time Symbol Table:*
- Used during compilation for type checking, optimization
- Can be discarded after compilation
- Stores static information (types, scopes, memory layouts)

*Runtime Symbol Table:*
- Used during execution for dynamic languages
- Must persist during program execution
- Stores actual values and runtime type information

```python
class CompileTimeSymbolTable:
    """Used by compiler for static analysis"""
    def __init__(self):
        self.symbols = {}
    
    def add_variable(self, name, var_type, scope):
        self.symbols[name] = {
            'type': var_type,
            'scope': scope,
            'memory_offset': self.allocate_memory(var_type)
        }
    
    def allocate_memory(self, var_type):
        # Assign stack offset for variable
        # This information goes into the compiled code
        pass

class RuntimeSymbolTable:
    """Used by interpreter during execution"""
    def __init__(self):
        self.symbols = {}
    
    def add_variable(self, name, value):
        self.symbols[name] = {
            'value': value,
            'type': type(value).__name__  # Runtime type
        }
```






### Best Practices

*1. Error Messages:*
```python
def lookup(self, name):
    result = self._lookup(name)
    if result is None:
        available = self.list_available_names()
        raise NameError(
            f"Name '{name}' is not defined.\n"
            f"Available names: {', '.join(available)}"
        )
    return result
```

*2. Defensive Programming:*
```python
def exit_scope(self):
    if len(self.scopes) <= 1:
        raise RuntimeError(
            "Cannot exit global scope. "
            "Check for unbalanced enter_scope/exit_scope calls."
        )
    self.scopes.pop()
```

*3. Testing:*
```python
def test_shadowing():
    st = SymbolTable()
    st.insert('x', 10)
    st.enter_scope()
    st.insert('x', 20)
    assert st.lookup('x') == 20
    st.exit_scope()
    assert st.lookup('x') == 10

def test_nested_scopes():
    st = SymbolTable()
    st.insert('x', 1)
    st.enter_scope()
    st.insert('y', 2)
    st.enter_scope()
    st.insert('z', 3)
    assert st.lookup('x') == 1  # Can see global
    assert st.lookup('y') == 2  # Can see parent
    assert st.lookup('z') == 3  # Can see local
```

*4. Documentation:*
```python
def lookup(self, name):
    """
    Look up a symbol by name, searching from innermost to outermost scope.
    
    Args:
        name: The identifier to look up
    
    Returns:
        The symbol's value/info if found, None otherwise
    
    Example:
        >>> st = SymbolTable()
        >>> st.insert('x', {'value': 42})
        >>> st.lookup('x')
        {'value': 42}
    """
    pass
```




### Conclusion

Symbol tables are the backbone of programming language implementation.
Start with simple implementations and gradually add complexity. Build
the projects, break things, fix them, and most importantly: experiment!
A very good way to learn symbol tables is to implement them yourself
in different contexts.

