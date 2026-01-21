
## Projects

### Project 1: Implement Type Coercion in TAC

*Goal*: Extend your TAC interpreter to handle mixed-type arithmetic.

*Learning Objectives:*
- Understand type promotion rules
- Implement automatic type conversion
- Track coercions for debugging

*Tasks:*

1. *Define Type Hierarchy*
   ```python
   TYPE_RANKS = {
       TypeKind.INT: 1,
       TypeKind.FLOAT: 2,
       TypeKind.STRING: 3
   }
   ```

2. *Implement Coercion Rules*
   ```python
   def determine_result_type(self, t1, t2, operation):
       """
       Rules:
       - int + int -> int
       - int + float -> float (coerce int)
       - float + float -> float
       - any + string -> string (coerce to string)
       """
   ```

3. *Track Coercions*
   - Log every implicit conversion
   - Show before/after types
   - Help users understand behavior

4. *Test Cases*
   ```python
   x = 5
   y = 3.14
   z = x + y      # z should be 8.14 (float)
   
   a = 10
   b = 20
   c = a + b      # c should be 30 (int, no coercion)
   ```

*Expected Output:*
```
Coercion: x (int) -> float in expression "x + y"
Result: z = 8.14 (float)
```



### Project 2: Add Static Type Checking

*Goal*: Implement pre-execution type validation.

*Learning Objectives:*
- Build type checking phase
- Report meaningful errors
- Understand compile-time analysis

*Implementation Steps:*

1. *Extend Syntax for Type Declarations*
   ```
   int x = 10
   float y = 3.14
   ```

2. *Build Symbol Table with Types*
   ```python
   class TypedSymbolTable:
       def declare(self, name, type_):
           if name in self.symbols:
               raise Error(f"Redeclaration of {name}")
           self.symbols[name] = {
               "type": type_,
               "initialized": False
           }
   ```

3. *Type Check Expressions*
   ```python
   def check_binary_op(self, left, op, right):
       left_type = self.get_type(left)
       right_type = self.get_type(right)
       
       if op in ['+', '-', '*', '/']:
           if not (left_type.is_numeric() and right_type.is_numeric()):
               raise TypeError(f"Cannot apply {op} to {left_type} and {right_type}")
   ```

4. *Report Errors with Context*
   ```
   Error on line 5: Type mismatch
       int x = "hello"
               ^^^^^^^
   Cannot assign string to int variable
   ```

*Test Cases:*
```python
# Should pass
int x = 10
int y = x + 5

# Should fail
int a = 10
a = 3.14  # Error: cannot assign float to int

# Should fail
float b = "text"  # Error: type mismatch
```



### Project 3: String Type Support

*Goal*: Add strings as first-class type.

*Tasks:*

1. *String Literals*
   ```python
   greeting = "Hello"
   name = "World"
   ```

2. *String Concatenation*
   ```python
   message = greeting + " " + name
   # Result: "Hello World"
   ```

3. *String Operations*
   ```python
   # Comparison
   if name == "World" goto label_1
   
   # Length (bonus)
   len_var = len(message)
   ```

4. *Type Checking*
   ```python
   x = "text" + 5  # Error in static mode
   y = 10 + "text" # Error in static mode
   ```

*Implementation:*
```python
class StringSupport:
    def parse_string_literal(self, token):
        if token.startswith('"') and token.endswith('"'):
            return {
                "type": "literal",
                "value": token[1:-1],
                "value_type": TypeKind.STRING
            }
    
    def eval_string_concat(self, left, right):
        # Convert both to strings
        left_str = str(left)
        right_str = str(right)
        return left_str + right_str
```



### Project 4: Type Inference Engine

*Goal*: Implement automatic type deduction.

*Learning Objectives:*
- Constraint generation
- Unification algorithm
- Type substitution

*Algorithm:*

1. *Generate Constraints*
   ```python
   # For: x = 5 + y
   constraints = [
       (type_of(5), INT),           # 5 is int
       (type_of(x), type_of(y)),    # x and y same type
       (type_of(5 + y), type_of(x)) # result type
   ]
   ```

2. *Unification*
   ```python
   def unify(t1, t2):
       if t1 == t2:
           return t1
       if is_type_var(t1):
           return substitute(t1, t2)
       if is_type_var(t2):
           return substitute(t2, t1)
       if compatible(t1, t2):
           return promote(t1, t2)
       raise TypeError(f"Cannot unify {t1} and {t2}")
   ```

3. *Solve Constraints*
   ```python
   def solve_constraints(self, constraints):
       substitutions = {}
       for c1, c2 in constraints:
           unified = self.unify(c1, c2)
           substitutions = self.compose(substitutions, unified)
       return substitutions
   ```

*Test Cases:*
```python
# Inference should work
x = 10        # x: int
y = x + 5     # y: int
z = y + 3.14  # z: float (promotion)

# Inference should detect conflict
a = 10        # a: int
a = a + 5     # a: int (consistent)
a = "text"    # ERROR: a cannot be both int and string
```



### Project 5: Gradual Typing System

*Goal*: Mix static and dynamic typing in one language.

*Concept:*
- Some variables typed (static checking)
- Some variables untyped (dynamic checking)
- Insert runtime checks at boundaries

*Implementation:*

1. *Optional Type Annotations*
   ```python
   int x = 10     # Statically typed
   y = 20         # Dynamically typed
   z = x + y      # Mixed: need runtime check
   ```

2. *Runtime Type Checks*
   ```python
   def add_with_check(left, right, expected_type):
       if not isinstance(left, expected_type):
           raise TypeError(f"Expected {expected_type}")
       if not isinstance(right, expected_type):
           raise TypeError(f"Expected {expected_type}")
       return left + right
   ```

3. *Blame Tracking*
   ```python
   # Track which part caused runtime error
   x: int = get_value()  # Assume int
   # If get_value() returns string:
   # "Blame: get_value() violated contract int"
   ```



### Project 6: Array Type System

*Goal*: Implement typed arrays with bounds checking.

*Features:*

1. *Typed Array Declaration*
   ```python
   int_array = int[10]
   float_array = float[5]
   ```

2. *Type-Safe Element Access*
   ```python
   int_array[0] = 42      # OK
   int_array[0] = 3.14    # Error: wrong type
   ```

3. *Bounds Checking*
   ```python
   int_array[10] = 5      # Error: index out of bounds
   ```

4. *Dependent Types (Advanced)*
   ```python
   # Size in type
   array<int, 10> a = ...
   array<int, 5> b = ...
   # Compiler prevents: a = b (size mismatch)
   ```

*Implementation:*
```python
class TypedArray:
    def check_access(self, array_name, index, value):
        array = self.symbol_table[array_name]
        
        # Bounds check
        if index >= array.size:
            raise IndexError(f"Index {index} out of bounds")
        
        # Type check
        value_type = self.infer_type(value)
        if value_type != array.base_type:
            raise TypeError(f"Cannot assign {value_type} to {array.base_type}[]")
```



### Project 7: Function Types and Polymorphism

*Goal*: Add typed functions with generic support.

*Features:*

1. *Function Type Signatures*
   ```python
   func add(int a, int b) -> int:
       return a + b
   ```

2. *Parametric Polymorphism*
   ```python
   func identity<T>(T x) -> T:
       return x
   
   x = identity<int>(5)      # T = int
   y = identity<float>(3.14) # T = float
   ```

3. *Type Checking Function Calls*
   ```python
   result = add(10, 20)    # OK
   result = add(10, 3.14)  # Error: arg 2 type mismatch
   ```

*Implementation:*
```python
class FunctionType:
    def __init__(self, param_types, return_type):
        self.param_types = param_types
        self.return_type = return_type
    
    def check_call(self, args):
        if len(args) != len(self.param_types):
            raise TypeError("Argument count mismatch")
        
        for arg, expected in zip(args, self.param_types):
            actual = infer_type(arg)
            if not compatible(actual, expected):
                raise TypeError(f"Expected {expected}, got {actual}")
```




### A1. Dependent Types ([Ch08](.))

Types that depend on runtime values:

```python
# Vector with compile-time size
Vec<T, n: Nat>

# Cannot compile:
v1: Vec<int, 3> = [1, 2]  # Wrong length!

# Type-safe concatenation:
def concat<T, n: Nat, m: Nat>(
    a: Vec<T, n>, 
    b: Vec<T, m>
) -> Vec<T, n+m>
```

*Implementation Challenges:*
- Type checking requires symbolic computation
- Types computed at compile time
- Proof obligations for type correctness

### A2. Subtyping and Variance

```python
class Animal: pass
class Dog(Animal): pass

# Covariance: Dog[] <: Animal[]?
animals: List[Animal] = [Dog()]  # Safe?

# Contravariance: Function types
f: Animal -> Dog
g: Dog -> Animal
# Is f <: g or g <: f?
```

### A3. Effect Systems

Track side effects in types:

```python
def read_file(path: str) -> str throws IOError:
    # Type indicates function can throw

def pure_function(x: int) -> int:
    # No effects - can be optimized freely
```

### A4. Refinement Types

Add predicates to types:

```python
# Type with constraint
type PositiveInt = {x: int | x > 0}

def sqrt(x: PositiveInt) -> float:
    # Guaranteed x > 0 at compile time
```




### What You've Learned

1. *Type System Fundamentals*
   - Static vs dynamic typing
   - Strong vs weak typing
   - Type inference mechanisms
   - Coercion rules

2. *Implementation Techniques*
   - Type checking algorithms
   - Constraint generation and solving
   - Symbol table management
   - Error reporting

3. *Advanced Concepts*
   - Generic types
   - Dependent types
   - Effect systems
   - Gradual typing

### Further (Project) Exploration

1. Study real language type systems (Rust, Haskell, TypeScript)
2. Implement full Hindley-Milner inference
3. Explore dependent type systems (Agda, Idris, Coq)
4. Build a gradual type system
5. Research effect systems and algebraic effects


