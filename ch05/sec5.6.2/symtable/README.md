
## Symbol Tables

Imagine writing a simple program:

```python
x = 5
y = x + 3
print(y)
```

When the compiler or interpreter processes this code, it needs to answer questions like:
- Has `x` been declared before we use it in line 2?
- What type is `x`? Can we add it to `3`?
- Where in memory should we store `y`?

A *symbol table* is the data structure that answers these questions.
It's essentially a dictionary that maps identifiers (variable names,
function names, etc.) to information about them.


#### The Role in Compilation

```
Source Code > Lexer > Parser > Symbol Table Builder > Type Checker > Code Generator
                                        |
                                [Symbol Table]
                                        |
                             Used by later stages
```

The symbol table is built during parsing and then used by:
- *Type checking*: Verify that operations are type-safe
- *Scope resolution*: Find which declaration a name refers to
- *Code generation*: Determine memory addresses for variables

#### A Motivating Example: The Problem of Name Collisions

```python
x = 10        ## Global x

def foo():
    x = 20    ## Local x - same name, different variable!
    print(x)  ## Should print 20, not 10

foo()
print(x)      ## Should print 10, not 20
```

Without proper scope management in the symbol table, we couldn't distinguish
between these two different variables named `x`.
This is why symbol tables use a *scope stack*.




### Core Concepts


#### What Information Does a Symbol Table Store?

For each identifier, we typically store:
- *Name*: The identifier itself (`x`, `foo`, `calculate`)
- *Type*: Data type (`int`, `float`, `function`)
- *Scope*: Where it's accessible (`global`, `local`, `block`)
- *Attributes*: Additional properties (`const`, `static`, `mutable`)
- *Location*: Memory address or offset (for variables)
- *Parameters*: For functions, their parameter list
- *Return Type*: For functions, what they return


#### The Scope Stack Model

Think of scopes as nested boxes:

```
┌─────────────────────────────────────┐
│ Global Scope                        │
│  x = 10                             │
│  ┌───────────────────────────────┐  │
│  │ Function 'foo' Scope          │  │
│  │  x = 20  (shadows global x)   │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │ Block Scope             │  │  │
│  │  │  y = 30                 │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

When looking up a name, we search from *innermost to outermost* scope.


#### Basic Symbol Table Operations

Every symbol table needs these core operations:
1. *enter_scope()*: Create a new scope (entering a function, block, etc.)
2. *exit_scope()*: Leave the current scope
3. *insert(name, info)*: Add a symbol to the current scope
4. *lookup(name)*: Find a symbol, searching current and outer scopes



### Symbol Tables in Procedural Languages

Procedural languages like C, Java, and Python focus on:
- *Mutable state*: Variables can change their values
- *Sequential execution*: Statements execute in order
- *Functions as subroutines*: Functions are called to perform actions


#### Characteristics

*Variables are mutable:*
```c
int x = 5;
x = 10;  // x changes value
```

*Scopes define visibility and lifetime:*
```c
int global_x = 1;  // Lives for entire program

void foo() {
    int local_y = 2;  // Lives only during function call
}
```

*Functions are first-class but not values:*
```c
void add(int a, int b) { return a + b; }  // Defined once
add(3, 4);  // Called many times
```

#### Implementation

Let's build a symbol table step by step, starting simple:

__Step 1: Single Scope__

```python
class SymbolTable:
    def __init__(self):
        self.symbols = {}  ## Just one dictionary
    
    def insert(self, name, info):
        self.symbols[name] = info
    
    def lookup(self, name):
        return self.symbols.get(name)

## Example usage
st = SymbolTable()
st.insert('x', {'type': 'int', 'value': 5})
print(st.lookup('x'))  ## {'type': 'int', 'value': 5}
```

*Problem*: This can't handle multiple scopes.

__Step 2: Adding Scope Stack__

```python
class SymbolTable:
    def __init__(self):
        self.scopes = [{}]  ## Stack of scopes, starting with global
    
    def enter_scope(self):
        """Create a new scope (for function, block, etc.)"""
        self.scopes.append({})
    
    def exit_scope(self):
        """Leave the current scope"""
        if len(self.scopes) > 1:
            self.scopes.pop()
        else:
            raise RuntimeError("Cannot exit global scope")
    
    def insert(self, name, info):
        """Add symbol to current (innermost) scope"""
        self.scopes[-1][name] = info
    
    def lookup(self, name):
        """Search from innermost to outermost scope"""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def current_scope_has(self, name):
        """Check if name exists in current scope only"""
        return name in self.scopes[-1]
```

__Step 3: Adding Helper Functions__

```python
def create_variable_entry(var_type, scope_level, value=None, 
                         is_const=False, memory_location=None):
    """Create a symbol table entry for a variable"""
    return {
        'kind': 'variable',
        'type': var_type,
        'scope': scope_level,
        'value': value,
        'const': is_const,
        'location': memory_location
    }

def create_function_entry(return_type, parameters, scope_level):
    """Create a symbol table entry for a function"""
    return {
        'kind': 'function',
        'return_type': return_type,
        'parameters': parameters,  ## List of (type, name) tuples
        'scope': scope_level
    }
```

#### Complete Example (procedural.py)

```python
class SymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.scope_level = 0
    
    def enter_scope(self):
        self.scopes.append({})
        self.scope_level += 1
    
    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
            self.scope_level -= 1
        else:
            raise RuntimeError("Cannot exit global scope")
    
    def insert(self, name, info):
        if name in self.scopes[-1]:
            raise RuntimeError(f"Symbol '{name}' already defined in current scope")
        self.scopes[-1][name] = info
    
    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def display(self):
        for i, scope in enumerate(self.scopes):
            print(f"\nScope Level {i}:")
            for name, info in scope.items():
                print(f"  {name}: {info}")

## Helper functions
def create_variable_entry(var_type, scope_level, value=None, is_const=False):
    return {
        'kind': 'variable',
        'type': var_type,
        'scope': scope_level,
        'value': value,
        'const': is_const
    }

def create_function_entry(return_type, parameters, scope_level):
    return {
        'kind': 'function',
        'return_type': return_type,
        'parameters': parameters,
        'scope': scope_level
    }

## Example: Simulating this program
## int x = 10;
## int add(int a, int b) {
##     int result = a + b;
##     return result;
## }

st = SymbolTable()

## Global scope
st.insert('x', create_variable_entry('int', 0, value=10))
st.insert('add', create_function_entry('int', [('int', 'a'), ('int', 'b')], 0))

## Enter function 'add' scope
st.enter_scope()
st.insert('a', create_variable_entry('int', 1, is_const=True))  ## parameter
st.insert('b', create_variable_entry('int', 1, is_const=True))  ## parameter
st.insert('result', create_variable_entry('int', 1))

st.display()
st.exit_scope()
```

*Output:*
```
Scope Level 0:
  x: {'kind': 'variable', 'type': 'int', 'scope': 0, 'value': 10, 'const': False}
  add: {'kind': 'function', 'return_type': 'int', 'parameters': [('int', 'a'), ('int', 'b')], 'scope': 0}

Scope Level 1:
  a: {'kind': 'variable', 'type': 'int', 'scope': 1, 'value': None, 'const': True}
  b: {'kind': 'variable', 'type': 'int', 'scope': 1, 'value': None, 'const': True}
  result: {'kind': 'variable', 'type': 'int', 'scope': 1, 'value': None, 'const': False}
```

#### Using Symbol Tables for Type Checking

```python
def type_check_assignment(symbol_table, var_name, new_value, new_value_type):
    """Verify that an assignment is type-safe"""
    var_info = symbol_table.lookup(var_name)
    
    if var_info is None:
        raise RuntimeError(f"Variable '{var_name}' not declared")
    
    if var_info['const']:
        raise RuntimeError(f"Cannot assign to const variable '{var_name}'")
    
    if var_info['type'] != new_value_type:
        raise TypeError(f"Cannot assign {new_value_type} to {var_info['type']} variable")
    
    ## Update the value
    var_info['value'] = new_value
    return True

## Example usage
st = SymbolTable()
st.insert('x', create_variable_entry('int', 0, value=10))
st.insert('PI', create_variable_entry('float', 0, value=3.14, is_const=True))

type_check_assignment(st, 'x', 20, 'int')      ## OK
## type_check_assignment(st, 'x', 3.14, 'float')  ## TypeError
## type_check_assignment(st, 'PI', 3.0, 'float')  ## RuntimeError: const
```



### Symbol Tables in Functional Languages

Functional languages like Haskell, Lisp, and ML emphasize:
- *Immutability*: Once bound, values don't change
- *Functions as values*: Functions can be passed around like data
- *Closures*: Functions "capture" their environment

#### Characteristics

*Immutability:*
```haskell
let x = 5
-- x = 10  -- Not allowed! Can't reassign x
let x = 10  -- This creates a NEW binding that shadows the old one
```

*Functions are first-class values:*
```javascript
const add = (a, b) => a + b;
const apply = (f, x, y) => f(x, y);  // Pass function as argument
apply(add, 3, 4);  // Returns 7
```

*Closures capture environment:*
```javascript
function makeCounter() {
    let count = 0;  // Captured by inner function
    return () => {
        count += 1;
        return count;
    };
}
```

#### Implementation: Environment-Based Symbol Table

In functional languages, we often call the symbol table an "environment":

```python
class Environment:
    def __init__(self, parent=None):
        """
        Create an environment, optionally with a parent environment.
        This supports lexical scoping and closures.
        """
        self.bindings = {}
        self.parent = parent  ## Link to enclosing scope
    
    def bind(self, name, value):
        """Create a new binding (immutable)"""
        if name in self.bindings:
            raise RuntimeError(f"Cannot rebind '{name}' - immutable binding")
        self.bindings[name] = value
    
    def lookup(self, name):
        """Search this environment and parent environments"""
        if name in self.bindings:
            return self.bindings[name]
        elif self.parent:
            return self.parent.lookup(name)
        else:
            return None
    
    def extend(self):
        """Create a child environment (for nested scopes)"""
        return Environment(parent=self)

## Example: Demonstrating closures
global_env = Environment()

## Define: let x = 10
global_env.bind('x', 10)

## Define function: let add_x = λy. x + y
## The function captures 'x' from its defining environment
def make_add_x(env):
    ## Capture the current environment
    closure_env = env
    def add_x(y):
        x = closure_env.lookup('x')
        return x + y
    return add_x

add_x_func = make_add_x(global_env)
print(add_x_func(5))  ## 15 (uses captured x=10)

## Even if we create a new scope where x is different...
inner_env = global_env.extend()
inner_env.bind('x', 100)

## ...the original function still uses its captured x=10
print(add_x_func(5))  ## Still 15!
```

#### Complete Example (functional.py)

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
```

#### Shadowing vs Mutation

A key concept in functional languages:

```python
env = Environment()
env.bind('x', 10)
print(env.lookup('x'))  ## 10

## Create a new scope that shadows x
inner = env.extend()
inner.bind('x', 20)
print(inner.lookup('x'))  ## 20 (finds inner x first)
print(env.lookup('x'))    ## 10 (outer x unchanged!)
```

This is *shadowing* (new binding in inner scope), not *mutation* (changing existing binding).



### Symbol Tables in Logical Languages

Logical languages like Prolog work very differently:
- *Declarative*: You state facts and rules, not steps
- *Unification*: Variables are bound through pattern matching
- *Backtracking*: The system tries different bindings to find solutions


#### Characteristics

*Facts and rules:*
```prolog
parent(tom, bob).       % Fact: tom is parent of bob
parent(tom, liz).       % Fact: tom is parent of liz
grandparent(X, Z) :- parent(X, Y), parent(Y, Z).  % Rule
```

*Unification binds variables:*
```prolog
?- parent(tom, X).      % Query: who is tom's child?
X = bob ;               % First solution
X = liz.                % Second solution (through backtracking)
```

*Backtracking explores alternatives:*
```prolog
?- parent(X, bob), parent(X, liz).  % Who is parent of BOTH bob and liz?
X = tom.                             % Only one solution
```

#### Unification and the Symbol Table

In Prolog, the symbol table tracks variable bindings during unification:

```python
class LogicSymbolTable:
    def __init__(self):
        self.bindings = {}  ## Maps variables to values or other variables
    
    def bind(self, var, value):
        """Bind a variable to a value"""
        if var in self.bindings:
            ## Variable already bound - check if consistent
            return self.unify(self.bindings[var], value)
        else:
            self.bindings[var] = value
            return True
    
    def lookup(self, var):
        """Get the binding of a variable, following chains"""
        if var not in self.bindings:
            return var  ## Unbound variable
        
        value = self.bindings[var]
        
        ## Follow chains: if X->Y and Y->5, then X should resolve to 5
        if isinstance(value, str) and value in self.bindings:
            return self.lookup(value)
        
        return value
    
    def unify(self, term1, term2):
        """
        Attempt to unify two terms.
        Returns True if successful, False otherwise.
        """
        ## Resolve both terms
        term1 = self.lookup(term1) if isinstance(term1, str) else term1
        term2 = self.lookup(term2) if isinstance(term2, str) else term2
        
        ## Same term - always unifies
        if term1 == term2:
            return True
        
        ## If either is an unbound variable, bind it
        if isinstance(term1, str) and term1 not in self.bindings:
            self.bindings[term1] = term2
            return True
        
        if isinstance(term2, str) and term2 not in self.bindings:
            self.bindings[term2] = term1
            return True
        
        ## Different constants - cannot unify
        return False
    
    def display(self):
        print("Bindings:")
        for var, value in self.bindings.items():
            resolved = self.lookup(var)
            print(f"  {var} = {resolved}")

## Example: Unifying loves(X, mary) with loves(john, Y)
## Should result in: X = john, Y = mary

st = LogicSymbolTable()

## Process: loves(X, mary) = loves(john, Y)
## Unify X with john
st.unify('X', 'john')
## Unify mary with Y
st.unify('mary', 'Y')

st.display()
## Output:
## Bindings:
##   X = john
##   Y = mary
```

#### Complete Example (logic.py)

```python
class LogicSymbolTable:
    def __init__(self):
        self.bindings = {}
        self.facts = []
    
    def add_fact(self, fact):
        """Add a fact to the knowledge base"""
        self.facts.append(fact)
    
    def bind(self, var, value):
        if var in self.bindings:
            return self.unify(self.bindings[var], value)
        self.bindings[var] = value
        return True
    
    def lookup(self, var):
        if var not in self.bindings:
            return var
        value = self.bindings[var]
        if isinstance(value, str) and value in self.bindings:
            return self.lookup(value)
        return value
    
    def unify(self, term1, term2):
        term1 = self.lookup(term1) if isinstance(term1, str) else term1
        term2 = self.lookup(term2) if isinstance(term2, str) else term2
        
        if term1 == term2:
            return True
        
        if isinstance(term1, str) and term1 not in self.bindings:
            self.bindings[term1] = term2
            return True
        
        if isinstance(term2, str) and term2 not in self.bindings:
            self.bindings[term2] = term1
            return True
        
        ## Handle compound terms like parent(tom, bob)
        if isinstance(term1, tuple) and isinstance(term2, tuple):
            if len(term1) != len(term2):
                return False
            return all(self.unify(t1, t2) for t1, t2 in zip(term1, term2))
        
        return False
    
    def query(self, pattern):
        """Find all facts that unify with the pattern"""
        solutions = []
        
        for fact in self.facts:
            ## Create a fresh copy of bindings for each attempt
            saved_bindings = self.bindings.copy()
            
            if self.unify(pattern, fact):
                ## Found a solution - record the bindings
                solution = {k: self.lookup(k) for k in self.bindings 
                           if isinstance(k, str) and k.isupper()}
                solutions.append(solution)
            
            ## Restore bindings for next attempt (backtracking)
            self.bindings = saved_bindings
        
        return solutions
    
    def display(self):
        print("Knowledge Base:")
        for fact in self.facts:
            print(f"  {fact}")
        print("\nCurrent Bindings:")
        for var, value in self.bindings.items():
            print(f"  {var} = {self.lookup(var)}")

## Example: Family relationships
## Facts: parent(tom, bob), parent(tom, liz), parent(bob, ann)

kb = LogicSymbolTable()
kb.add_fact(('parent', 'tom', 'bob'))
kb.add_fact(('parent', 'tom', 'liz'))
kb.add_fact(('parent', 'bob', 'ann'))

## Query: parent(tom, X)? (Who are tom's children?)
print("Query: parent(tom, X)?")
results = kb.query(('parent', 'tom', 'X'))
for result in results:
    print(f"  Solution: {result}")

## Query: parent(X, ann)? (Who is ann's parent?)
print("\nQuery: parent(X, ann)?")
results = kb.query(('parent', 'X', 'ann'))
for result in results:
    print(f"  Solution: {result}")
```

*Output:*
```
Query: parent(tom, X)?
  Solution: {'X': 'bob'}
  Solution: {'X': 'liz'}

Query: parent(X, ann)?
  Solution: {'X': 'bob'}
```

*Note:* The logic example above has a subtle bug - it doesn't properly isolate bindings between solution attempts. Here's a corrected version:

```python
class LogicSymbolTable:
    def __init__(self):
        self.facts = []
    
    def add_fact(self, fact):
        self.facts.append(fact)
    
    def unify(self, term1, term2, bindings):
        """
        Unify two terms with the given bindings.
        Returns updated bindings if successful, None if unification fails.
        """
        ## Dereference variables
        term1 = self.deref(term1, bindings)
        term2 = self.deref(term2, bindings)
        
        if term1 == term2:
            return bindings
        
        if self.is_variable(term1):
            new_bindings = bindings.copy()
            new_bindings[term1] = term2
            return new_bindings
        
        if self.is_variable(term2):
            new_bindings = bindings.copy()
            new_bindings[term2] = term1
            return new_bindings
        
        if isinstance(term1, tuple) and isinstance(term2, tuple):
            if len(term1) != len(term2):
                return None
            
            current_bindings = bindings
            for t1, t2 in zip(term1, term2):
                current_bindings = self.unify(t1, t2, current_bindings)
                if current_bindings is None:
                    return None
            return current_bindings
        
        return None
    
    def is_variable(self, term):
        """Variables start with uppercase letters"""
        return isinstance(term, str) and term[0].isupper()
    
    def deref(self, term, bindings):
        """Follow variable bindings to get the final value"""
        if self.is_variable(term) and term in bindings:
            return self.deref(bindings[term], bindings)
        return term
    
    def query(self, pattern):
        """Find all solutions that unify with the pattern"""
        solutions = []
        
        for fact in self.facts:
            result = self.unify(pattern, fact, {})
            if result is not None:
                ## Extract only the variables from the original pattern
                solution = {var: self.deref(var, result) 
                           for var in self.extract_variables(pattern)}
                solutions.append(solution)
        
        return solutions
    
    def extract_variables(self, term):
        """Extract all variables from a term"""
        if self.is_variable(term):
            return {term}
        elif isinstance(term, tuple):
            vars = set()
            for t in term:
                vars.update(self.extract_variables(t))
            return vars
        return set()

## Corrected example
kb = LogicSymbolTable()
kb.add_fact(('parent', 'tom', 'bob'))
kb.add_fact(('parent', 'tom', 'liz'))
kb.add_fact(('parent', 'bob', 'ann'))

print("Query: parent(tom, X)?")
results = kb.query(('parent', 'tom', 'X'))
for result in results:
    print(f"  X = {result['X']}")

print("\nQuery: parent(X, ann)?")
results = kb.query(('parent', 'X', 'ann'))
for result in results:
    print(f"  X = {result['X']}")
```

*Corrected Output:*
```
Query: parent(tom, X)?
  X = bob
  X = liz

Query: parent(X, ann)?
  X = bob
```

---

### Comparison Across Paradigms

| Aspect | Procedural | Functional | Logical |
|--------|------------|------------|---------|
| *Primary Purpose* | Track mutable state | Track immutable bindings | Track unification bindings |
| *Variables* | Mutable, can be reassigned | Immutable, shadowing only | Unified through pattern matching |
| *Scope Model* | Block/function scopes | Lexical scopes + closures | Logical scopes + backtracking |
| *Function Storage* | Reference to code | Closure (code + environment) | Predicates (patterns + rules) |
| *Update Pattern* | Modify existing entries | Create new scope with shadowing | Bind then unbind (backtrack) |
| *Key Operations* | insert, update, lookup | bind, extend, lookup | unify, bind, backtrack |
| *Complexity* | Moderate | Higher (closure capture) | Highest (unification + backtracking) |

---

### Common Pitfalls and Debugging {#pitfalls}

#### Pitfall 1: Variable Shadowing

*Problem:*
```python
x = 10

def foo():
    print(x)  ## Might expect 10, but...
    x = 20    ## This makes 'x' local throughout foo!
```

This causes an error because Python sees `x = 20` and makes `x` local for the entire function, including the `print(x)` line that comes before it.

*Solution in Symbol Table:*
```python
def check_usage_before_definition(symbol_table, var_name, scope):
    """Verify variable isn't used before it's defined"""
    if not symbol_table.current_scope_has(var_name):
        parent_value = symbol_table.lookup(var_name)
        if parent_value:
            raise Warning(f"'{var_name}' used before local definition - will shadow outer variable")
```

#### Pitfall 2: Forgetting to Exit Scopes

*Problem:*
```python
st = SymbolTable()
st.enter_scope()
st.insert('x', {'type': 'int'})
## Forgot to call exit_scope()!
st.enter_scope()  ## Now we're 2 levels deep
```

*Solution:* Use context managers:
```python
from contextlib import contextmanager

@contextmanager
def scope(symbol_table):
    symbol_table.enter_scope()
    try:
        yield symbol_table
    finally:
        symbol_table.exit_scope()

## Usage
st = SymbolTable()
with scope(st):
    st.insert('x', {'type': 'int'})
    ## Automatically exits scope when block ends
```

#### Pitfall 3: Confusing Declaration and Definition

*Problem:*
In C, these are different:
```c
int x;        // Declaration (symbol table entry created)
x = 10;       // Definition (value assigned)
```

*Solution in Symbol Table:*
```python
def create_variable_entry(var_type, defined=False):
    return {
        'type': var_type,
        'defined': defined,  ## Track if value has been assigned
        'value': None
    }

def assign_value(symbol_table, var_name, value):
    var_info = symbol_table.lookup(var_name)
    if var_info is None:
        raise RuntimeError(f"Variable '{var_name}' not declared")
    var_info['value'] = value
    var_info['defined'] = True
```

#### Pitfall 4: Scope Lifetime vs Variable Lifetime

*Problem:* Students confuse when a scope exists vs when variables in it are accessible.

```python
def outer():
    x = 10
    def inner():
        return x  ## x is still accessible here!
    return inner

f = outer()  ## outer's scope has "ended"
print(f())   ## But x is still accessible through closure!
```

*Explanation:* In closures, the variable outlives the scope that created it. The symbol table (environment) is captured by the closure.

#### Debugging Tips

*1. Always Print the Symbol Table State*
```python
def debug_display(symbol_table):
    print("\n=== SYMBOL TABLE STATE ===")
    for i, scope in enumerate(symbol_table.scopes):
        print(f"Scope {i}:")
        for name, info in scope.items():
            print(f"  {name}: {info}")
    print("=========================\n")
```

*2. Trace Lookups*
```python
def traced_lookup(symbol_table, name):
    print(f"Looking up '{name}'...")
    for i, scope in enumerate(reversed(symbol_table.scopes)):
        level = len(symbol_table.scopes) - 1 - i
        print(f"  Checking scope {level}...")
        if name in scope:
            print(f"  Found in scope {level}!")
            return scope[name]
    print(f"  Not found!")
    return None
```

*3. Validate Scope Balance*
```python
def validate_scopes(enter_count, exit_count):
    """After parsing, should have equal enters and exits"""
    if enter_count != exit_count:
        raise RuntimeError(f"Unbalanced scopes: {enter_count} enters, {exit_count} exits")
```
