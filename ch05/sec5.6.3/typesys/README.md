
## Type Systems: Projects

As we have learned, and will continue to see, *types* play a central role in
programming and the design of programming languages.

Would you like to learn a little more about *type systems*, a starter can be
an introduction into [lambda calculus and type systems](./../calculus/).

This project is an educational resource for understanding *type systems*
in programming languages. It provides hands-on implementations of four
fundamental typing approaches, allowing you to see how the same code behaves
under different type system philosophies.


Ideas introduced:
- *Core Concepts*: Static vs dynamic typing, strong vs weak typing, type inference
- *Implementation*: How type checkers, inference engines, and coercion systems work
- *Practical Skills*: Reading compiler errors, designing APIs, choosing the right type system

Languages used:
- *Python* (`type_systems.py`): High-level implementations with detailed explanations
- *C* (`type_systems.c`): Low-level perspective on types and memory


The Type System Hierarchy (examples):
```
Dynamic Typing <> Type Inference <> Static Typing <> Strong Typing
                  + Coercion

Python            ML/Haskell        Java             Rust
JavaScript        TypeScript        C                Ada
Ruby              Swift             C++
```



__Learning Path:__


Project Difficulty Guide:

|Project|Difficulty|Time Estimate|Prerequisites|
|-------|----------|-------------|-------------|
| 1.    | *        | 2-3h        | -           |
| 2.    | **       | 4-6h        | Project 1   |
| 3.    | *        | 2-3h        | Project 1   |
| 4.    | ***      | 8-12h       | Project 1-2 |


Beginner:
```
 1. Run all demonstrations
 2. Modify code examples
 3. Understand error messages
 4. Compare outputs
```
Intermediate:
```
 5. Implement Project 1 (Type Coercion)
 6. Implement Project 2 (Static Checking)
 7. Add new operators
 8. Extend type system (arrays, functions)
```
Advanced (you have to make the project plans):
```
 9. Implement Project 4 (Type Inference)
10. Add polymorphism
11. Study Hindley-Milner algorithm
12. Implement gradual typing
```


---


### Dynamic Typing

*Philosophy*: "I'll figure out types when I run the code"

```python
x = 10      # x is int
x = 3.14    # x is now float (allowed!)
x = "hi"    # x is now string (also allowed!)
```

#### Characteristics

| Property | Dynamic System |
|----------|----------------|
| Type declarations | None required |
| Type checking time | Runtime |
| Variable re-typing | Allowed |
| Safety | Low |
| Flexibility | High |
| Performance | Slower (runtime checks) |

#### Use Cases

- Rapid prototyping
- Scripting and automation
- Domain-specific languages
- REPL environments

*Languages*: Python, JavaScript, Ruby, PHP




### Static Typing

*Philosophy*: "Tell me all types upfront, I'll check before running"

```c
int x = 10;     // x is declared as int
x = 20;         // OK: still int
x = 3.14;       // ERROR: cannot assign float to int
```

#### Characteristics

| Property | Static System |
|----------|---------------|
| Type declarations | Required |
| Type checking time | Compile time |
| Variable re-typing | Forbidden |
| Safety | High |
| Flexibility | Lower |
| Performance | Fast (no runtime checks) |

#### Two-Phase Model

1. Parse -> Build AST
2. Type Check -> Validate att types (before execution)

#### Use Cases

- Large-scale systems
- Performance-critical code
- Safety-critical applications
- Long-term maintenance

*Languages*: C, Java, Rust, Go, Swift



### Type Inference

*Philosophy*: "Don't tell me types, I'll figure them out myself"

```haskell
x = 10          -- Inferred: x : Int
y = 3.14        -- Inferred: y : Float
z = x + y       -- Inferred: z : Float (int promoted)
```

#### Characteristics

| Property | Inference System |
|----------|------------------|
| Type declarations | Optional |
| Type checking time | Compile time |
| Type deduction | Automatic |
| Safety | High |
| Flexibility | High |
| Performance | Fast |

#### How It Works

*Constraint Generation*:
```python
# For: x = 5 + y
constraints = [
    (type_of(5), INT),           # 5 is int
    (type_of(x), type_of(y)),    # x and y compatible
    (type_of(5 + y), type_of(x)) # result matches x
]
```

*Constraint Solving*:
```python
def unify(t1, t2):
    if t1 == t2:
        return t1
    if compatible(t1, t2):
        return promote(t1, t2)
    raise TypeError(f"Cannot unify {t1} and {t2}")
```

#### Use Cases

- Functional programming
- Generic programming
- When you want both safety and convenience

*Languages*: ML, Haskell, Rust (partial), TypeScript, Kotlin



### Type Coercion

*Philosophy*: "Convert types automatically when it makes sense"

```c
int x = 5;
float y = 3.14;
float z = x + y;  // x automatically converted to float
```

#### Type Hierarchy

```
bool -> char -> int -> float -> string
 |       |       |       |         |
 1       2       3       4         5
 
(Lower rank can coerce to higher rank)
```

#### Characteristics

| Property | Coercion System |
|----------|-----------------|
| Implicit conversions | Yes |
| Logs conversions | Optional |
| Type safety | Medium |
| Convenience | High |

#### Example with Logging

```python
x = 5           # int
y = 3.14        # float
z = x + y       # Result: 8.14

# Coercion Log:
# -> Coercion: int -> float (left operand of '+')
# -> Result type: float
```

#### Use Cases

- Numeric computing
- When conversion is unambiguous
- Reducing verbosity in safe contexts

*Languages*: C (arithmetic), Java (numeric promotion), Python (implicit)


### When to Use Each System

*Dynamic Typing*: 
- Data science notebooks (Jupyter)
- Web scraping scripts
- Configuration files
- Quick prototypes

*Static Typing*:
- Operating systems
- Databases
- Compilers
- Financial systems

*Type Inference*:
- Functional programs
- Mathematical computing
- Generic libraries
- DSL implementations

*Coercion*:
- Numeric algorithms
- Graphics programming
- Scientific computing
- Calculator implementations



---



### Project 1: Type Coercion System

*Difficulty*: * Beginner  
*Time*: 2-3 hours  
*Goal*: Implement automatic type conversion with detailed logging

#### Learning Objectives

- Understand type promotion hierarchies
- Implement implicit type conversions
- Track and log coercions for debugging
- Handle edge cases in numeric operations

#### Background

Type coercion is the automatic conversion between compatible types.
For example, when you add an `int` and a `float`, the `int` is
promoted to `float` before the operation.

*Type Hierarchy:*
```
bool (rank 1) -> char (rank 2) -> int (rank 3) -> float (rank 4) -> string (rank 5)
```


#### Implementation Guide

##### Step 1: Define Type Ranks

```python
TYPE_RANKS = {
    TypeKind.BOOL: 1,
    TypeKind.CHAR: 2,
    TypeKind.INT: 3,
    TypeKind.FLOAT: 4,
    TypeKind.STRING: 5
}

def get_rank(type_kind: TypeKind) -> int:
    """Get the promotion rank of a type."""
    return TYPE_RANKS.get(type_kind, 0)
```

##### Step 2: Determine Result Type

```python
def determine_result_type(self, left_type: Type, right_type: Type, 
                         operation: str) -> Type:
    """
    Determine the result type for a binary operation.
    
    Rules:
    - int + int -> int
    - int + float -> float (coerce int to float)
    - float + float -> float
    - any + string -> string (coerce to string)
    - bool + int -> int (coerce bool to int)
    
    Args:
        left_type: Type of left operand
        right_type: Type of right operand
        operation: The operator ('+', '-', etc.)
    
    Returns:
        The result type after coercion
    """
    # Special case: string concatenation
    if operation == '+':
        if left_type.kind == TypeKind.STRING or right_type.kind == TypeKind.STRING:
            return Type(TypeKind.STRING)
    
    # Numeric operations: promote to higher rank
    left_rank = get_rank(left_type.kind)
    right_rank = get_rank(right_type.kind)
    
    if left_rank >= right_rank:
        return left_type
    else:
        return right_type
```

##### Step 3: Implement Value Coercion

```python
def coerce_value(self, value: Any, from_type: Type, to_type: Type,
                context: str) -> Any:
    """
    Coerce a value from one type to another.
    
    Args:
        value: The value to coerce
        from_type: Current type of the value
        to_type: Target type
        context: Description of where coercion occurs (for logging)
    
    Returns:
        The coerced value
    """
    # No coercion needed
    if from_type == to_type:
        return value
    
    # Log the coercion
    self.coercion_log.append(
        f"Coercion: {from_type} -> {to_type} in {context}"
    )
    
    # Perform the coercion
    if to_type.kind == TypeKind.INT:
        return int(value)
    elif to_type.kind == TypeKind.FLOAT:
        return float(value)
    elif to_type.kind == TypeKind.STRING:
        return str(value)
    elif to_type.kind == TypeKind.BOOL:
        return bool(value)
    
    raise TypeError(f"Cannot coerce {from_type} to {to_type}")
```

##### Step 4: Apply Coercion in Operations

```python
def evaluate_binary_op(self, left: Value, op: str, right: Value) -> Value:
    """
    Evaluate a binary operation with automatic coercion.
    
    Example:
        5 + 3.14
        -> Coerce 5 (int) to 5.0 (float)
        -> Compute 5.0 + 3.14 = 8.14
        -> Return Value(8.14, float)
    """
    # Determine the result type
    result_type = self.determine_result_type(left.type, right.type, op)
    
    # Coerce operands to result type
    left_value = self.coerce_value(
        left.value, left.type, result_type, 
        f"left operand of '{op}'"
    )
    right_value = self.coerce_value(
        right.value, right.type, result_type,
        f"right operand of '{op}'"
    )
    
    # Perform the operation
    if op == '+':
        result_value = left_value + right_value
    elif op == '-':
        result_value = left_value - right_value
    elif op == '*':
        result_value = left_value * right_value
    elif op == '/':
        result_value = left_value / right_value
    else:
        raise ValueError(f"Unknown operator: {op}")
    
    return Value(result_value, result_type)
```

#### Test Cases

```python
def test_type_coercion():
    """Test suite for type coercion system."""
    
    # Test 1: Integer arithmetic (no coercion)
    code1 = """
    x = 10
    y = 20
    z = x + y
    """
    # Expected: z = 30 (int), no coercions
    
    # Test 2: Mixed int and float
    code2 = """
    x = 5
    y = 3.14
    z = x + y
    """
    # Expected: z = 8.14 (float), coercion: int -> float
    
    # Test 3: Boolean to int
    code3 = """
    flag = true
    count = 10
    total = flag + count
    """
    # Expected: total = 11 (int), coercion: bool -> int
    
    # Test 4: String concatenation
    code4 = """
    name = "Result: "
    value = 42
    message = name + value
    """
    # Expected: message = "Result: 42" (string), coercion: int -> string
    
    # Test 5: Complex expression
    code5 = """
    a = 2
    b = 3.5
    c = true
    result = (a + b) * c
    """
    # Expected: 
    # - a + b: coerce 2 -> 2.0, result = 5.5 (float)
    # - 5.5 * true: coerce true -> 1.0, result = 5.5 (float)
```

#### Expected Output

```
Coercion Log:
  1 int -> float (left operand of '+') in expression "x + y"
  2 Result: z = 8.14 : float

Symbol Table:
  x: int = 5
  y: float = 3.14
  z: float = 8.14
```

#### Extensions

1. *Lossy Coercion Warnings*: Warn when coercion loses precision (e.g., float -> int)
2. *Custom Coercion Rules*: Allow user-defined type conversions
3. *Coercion Cost*: Track and minimize the number of coercions
4. *Explicit Casting*: Add syntax for explicit type casts



### Project 2: Static Type Checker

*Difficulty*: ** Intermediate  
*Time*: 4-6 hours  
*Goal*: Build a compile-time type verification system

#### Learning Objectives

- Implement type checking algorithms
- Build symbol tables with type information
- Report meaningful type errors
- Understand two-phase compilation

#### Background

Static type checking happens *before* execution. The type checker:
1. Builds a symbol table of declared types
2. Validates that operations are type-safe
3. Reports errors with useful context

#### Implementation Guide

##### Step 1: Extend Syntax for Type Declarations

```python
# Support syntax like:
int x = 10
float y = 3.14
string message = "hello"
```

*Parser modification:*

```python
def parse_typed_declaration(self, line: str) -> AssignmentNode:
    """
    Parse: <type> <name> = <expr>
    
    Example: "int x = 10"
    """
    parts = line.split(maxsplit=1)
    type_name = parts[0]  # "int"
    rest = parts[1]       # "x = 10"
    
    var_name, expr = rest.split('=', 1)
    var_name = var_name.strip()
    expr = expr.strip()
    
    # Create type object
    declared_type = Type(TypeKind[type_name.upper()])
    
    return AssignmentNode(
        target=var_name,
        value=self.parse_expression(expr),
        declared_type=declared_type
    )
```

##### Step 2: Build Type-Aware Symbol Table

```python
class TypedSymbolTable:
    """Symbol table that tracks type information."""
    
    def __init__(self):
        self.symbols: Dict[str, SymbolInfo] = {}
    
    def declare(self, name: str, type_: Type, line: int = 0) -> None:
        """
        Declare a new variable with a type.
        
        Raises TypeError if variable already declared.
        """
        if name in self.symbols:
            existing = self.symbols[name]
            raise TypeError(
                f"Redeclaration of '{name}' at line {line}\n"
                f"  Previously declared at line {existing.line_declared}"
            )
        
        self.symbols[name] = SymbolInfo(
            name=name,
            type_=type_,
            line_declared=line,
            is_initialized=False
        )
    
    def get_type(self, name: str) -> Type:
        """Get the declared type of a variable."""
        if name not in self.symbols:
            raise NameError(f"Undefined variable '{name}'")
        return self.symbols[name].type_
    
    def mark_initialized(self, name: str) -> None:
        """Mark a variable as initialised."""
        if name in self.symbols:
            self.symbols[name].is_initialized = True
```

##### Step 3: Type Check Expressions

```python
def check_expression(self, expr: ASTNode) -> Type:
    """
    Type check an expression and return its type.
    
    This is the core type checking function.
    """
    if isinstance(expr, LiteralNode):
        # Literals have known types
        return expr.type_
    
    elif isinstance(expr, VariableNode):
        # Look up variable type
        return self.symbol_table.get_type(expr.name)
    
    elif isinstance(expr, BinaryOpNode):
        # Check both operands
        left_type = self.check_expression(expr.left)
        right_type = self.check_expression(expr.right)
        
        # Type check the operation
        return self.check_binary_operation(
            expr.operator, left_type, right_type, expr
        )
    
    elif isinstance(expr, UnaryOpNode):
        operand_type = self.check_expression(expr.operand)
        return self.check_unary_operation(
            expr.operator, operand_type, expr
        )
    
    raise TypeError(f"Cannot type check {type(expr).__name__}")
```

##### Step 4: Type Check Binary Operations

```python
def check_binary_operation(self, op: str, left: Type, right: Type,
                          node: ASTNode) -> Type:
    """
    Check if a binary operation is type-safe.
    
    Returns the result type if valid, raises TypeError otherwise.
    """
    # Arithmetic operations: +, -, *, /
    if op in ['+', '-', '*', '/']:
        # Special case: string concatenation
        if op == '+' and (left.kind == TypeKind.STRING or 
                         right.kind == TypeKind.STRING):
            return Type(TypeKind.STRING)
        
        # Numeric operations require numeric types
        if not (left.is_numeric() and right.is_numeric()):
            raise TypeError(
                f"Operator '{op}' requires numeric types\n"
                f"  Got: {left} and {right}\n"
                f"  In expression: {node}"
            )
        
        # Result is wider of the two types
        if left.kind == TypeKind.FLOAT or right.kind == TypeKind.FLOAT:
            return Type(TypeKind.FLOAT)
        return Type(TypeKind.INT)
    
    # Comparison operations: ==, !=, <, >, <=, >=
    elif op in ['<', '>', '<=', '>=']:
        # Ordering requires comparable types
        if not (left.is_numeric() and right.is_numeric()):
            raise TypeError(
                f"Operator '{op}' requires numeric types\n"
                f"  Got: {left} and {right}"
            )
        return Type(TypeKind.BOOL)
    
    elif op in ['==', '!=']:
        # Equality works on most types
        if not left.is_compatible_with(right, strict=False):
            self.warnings.append(
                f"Comparing incompatible types: {left} and {right}"
            )
        return Type(TypeKind.BOOL)
    
    raise ValueError(f"Unknown operator: {op}")
```

##### Step 5: Type Check Assignments

```python
def check_assignment(self, node: AssignmentNode) -> None:
    """
    Type check an assignment statement.
    
    Cases:
    1. New declaration: int x = 10
    2. Re-assignment: x = 20
    """
    # Get the type of the right-hand side
    value_type = self.check_expression(node.value)
    
    if node.declared_type:
        # New declaration with explicit type
        # Check: declared type matches value type
        if not value_type.is_compatible_with(node.declared_type, strict=True):
            # Check if coercion is possible
            if value_type.can_coerce_to(node.declared_type):
                self.warnings.append(
                    f"Implicit coercion: {value_type} -> {node.declared_type}\n"
                    f"  In initialization of '{node.target}'"
                )
            else:
                raise TypeError(
                    f"Type mismatch in declaration of '{node.target}'\n"
                    f"  Declared type: {node.declared_type}\n"
                    f"  Value type: {value_type}\n"
                    f"  Expression: {node.value}"
                )
        
        # Add to symbol table
        self.symbol_table.declare(node.target, node.declared_type)
    
    else:
        # Assignment to existing variable
        declared_type = self.symbol_table.get_type(node.target)
        
        # Check: value type matches declared type
        if not value_type.is_compatible_with(declared_type, strict=True):
            if value_type.can_coerce_to(declared_type):
                self.warnings.append(
                    f"Implicit coercion: {value_type} -> {declared_type}\n"
                    f"  In assignment to '{node.target}'"
                )
            else:
                raise TypeError(
                    f"Type mismatch in assignment to '{node.target}'\n"
                    f"  Variable type: {declared_type}\n"
                    f"  Value type: {value_type}\n"
                    f"  Expression: {node.value}"
                )
    
    # Mark variable as initialised
    self.symbol_table.mark_initialized(node.target)
```

##### Step 6: Report Errors with Context

```python
class TypeErrorReporter:
    """Beautiful error reporting for type errors."""
    
    def report_error(self, error: TypeError, line_num: int, 
                    source_line: str) -> None:
        """
        Report a type error with context.
        
        Example output:
            Error at line 5: Type mismatch
                int x = "hello"
                        ^^^^^^^
            Cannot assign string to int variable
        """
        print(f"\n  Type Error at line {line_num}:")
        print(f"  {source_line}")
        
        # Point to the error location
        # (This is simplified; real implementation would track positions: your task!)
        print(f"  {' ' * 10}^^^^^^^")
        
        print(f"  {str(error)}")
        print()
```

#### Test Cases

```python
# Test 1: Valid program
code_valid = """
int x = 10
float y = 3.14
int z = x + 5
float w = x + y
"""
# Expected:   Type check passes
#             Warning: implicit coercion int -> float in "x + y"

# Test 2: Type mismatch in declaration
code_invalid1 = """
int x = 10
x = 3.14
"""
# Expected:   Error: Cannot assign float to int variable 'x'

# Test 3: Type mismatch in initialisation
code_invalid2 = """
int x = "hello"
"""
# Expected:   Error: Cannot initialise int with string

# Test 4: Undefined variable
code_invalid3 = """
int x = y + 5
"""
# Expected:   Error: Undefined variable 'y'

# Test 5: Type incompatible operation
code_invalid4 = """
string s = "hello"
int x = s - 5
"""
# Expected:   Error: Operator '-' requires numeric types
```

#### Expected Output

**Valid Program:**
```
  Type Check: PASSED

Warnings:
    Implicit coercion: int -> float
    In expression "x + y" on line 4

Symbol Table:
  x: int
  y: float
  z: int
  w: float
```

**Invalid Program:**
```
  Type Error at line 2:
  x = 3.14
      ^^^^
  Type mismatch in assignment to 'x'
    Variable type: int
    Value type: float
    
Cannot assign float to int variable

Type Check: FAILED
```

#### Extensions

1. *Type Aliases*: Support `type MyInt = int`
2. *Const Correctness*: Track immutable variables
3. *Null Safety*: Add optional types with `int?`
4. *Better Error Recovery*: Continue checking after errors



### Project 3: String Type Support

*Difficulty*: * Beginner  
*Time*: 2-3 hours  
*Goal*: Add strings as a first-class type with operations

#### Learning Objectives

- Extend type system with new types
- Implement type-specific operations
- Handle string literals and escaping
- Support string comparison and concatenation

#### Implementation Guide

##### Step 1: String Literals

```python
def parse_string_literal(self, token: str) -> LiteralNode:
    """
    Parse string literals with escape sequences.
    
    Supports:
    - Double quotes: "hello"
    - Single quotes: 'hello'
    - Escape sequences: \n, \t, \", \\
    """
    if (token.startswith('"') and token.endswith('"')) or \
       (token.startswith("'") and token.endswith("'")):
        
        # Extract content
        content = token[1:-1]
        
        # Process escape sequences
        content = content.replace('\\n', '\n')
        content = content.replace('\\t', '\t')
        content = content.replace('\\\\', '\\')
        content = content.replace('\\"', '"')
        content = content.replace("\\'", "'")
        
        return LiteralNode(content, Type(TypeKind.STRING))
    
    raise SyntaxError(f"Invalid string literal: {token}")
```

##### Step 2: String Operations

```python
class StringOperations:
    """String-specific operations."""
    
    @staticmethod
    def concat(left: str, right: str) -> str:
        """Concatenate two strings."""
        return left + right
    
    @staticmethod
    def length(s: str) -> int:
        """Get string length."""
        return len(s)
    
    @staticmethod
    def substring(s: str, start: int, end: int) -> str:
        """Extract substring."""
        return s[start:end]
    
    @staticmethod
    def compare(left: str, right: str) -> int:
        """
        Compare strings lexicographically.
        Returns: -1 if left < right, 0 if equal, 1 if left > right
        """
        if left < right:
            return -1
        elif left > right:
            return 1
        return 0
```

##### Step 3: String Type Checking

```python
def check_string_operation(self, op: str, left: Type, right: Type) -> Type:
    """
    Type check string operations.
    
    Rules:
    - string + string -> string
    - string + any -> string (coerce to string)
    - string == string -> bool
    - string < string -> bool (lexicographic)
    """
    if op == '+':
        # Concatenation: coerce other type to string
        return Type(TypeKind.STRING)
    
    elif op in ['==', '!=', '<', '>', '<=', '>=']:
        # Comparison: both must be strings
        if left.kind != TypeKind.STRING or right.kind != TypeKind.STRING:
            raise TypeError(
                f"String comparison requires both operands to be strings\n"
                f"  Got: {left} and {right}"
            )
        return Type(TypeKind.BOOL)
    
    else:
        raise TypeError(f"Operator '{op}' not supported for strings")
```

#### Test Cases

```python
# Test 1: String literals
code1 = """
string greeting = "Hello"
string name = "World"
"""

# Test 2: String concatenation
code2 = """
string first = "Hello"
string second = " World"
string message = first + second
"""
# Expected: message = "Hello World"

# Test 3: String comparison
code3 = """
string a = "apple"
string b = "banana"
bool result = a < b
"""
# Expected: result = true

# Test 4: Mixed type concatenation
code4 = """
string label = "Count: "
int value = 42
string message = label + value
"""
# Expected: message = "Count: 42" (with coercion warning in static mode)
```

#### Extensions

1. *String Methods*: Add `.length()`, `.substring()`, `.toUpper()`
2. *String Interpolation*: Support `f"Hello {name}"`
3. *Regular Expressions*: Add pattern matching
4. *Unicode Support*: Handle multi-byte characters



### Project 4: Type Inference Engine

*Difficulty*: *** Advanced  
*Time*: 8-12 hours  
*Goal*: Implement Hindley-Milner style type inference (look it up!)

#### Learning Objectives

- Understand constraint-based typing
- Implement unification algorithm
- Handle type variables and substitutions
- Build a complete inference system

#### Background

Type inference automatically deduces types from usage without explicit annotations.
This is the foundation of languages like ML, Haskell, and Rust's inference.

*Key Concept: Constraints*

Instead of requiring types upfront, we:
1. Generate type constraints from the code
2. Solve the constraints through unification
3. Substitute solutions back into the program

#### Implementation Guide

##### Step 1: Type Variables

```python
class TypeVariable:
    """
    Represents an unknown type to be inferred.
    
    Example: If we see `x = 10`, we create:
        - Type variable α for x
        - Constraint: α = int
    """
    _counter = 0
    
    def __init__(self, name: str = None):
        if name is None:
            TypeVariable._counter += 1
            name = f"t{TypeVariable._counter}"
        self.name = name
    
    def __str__(self):
        return f"'{self.name}"
    
    def __repr__(self):
        return f"TypeVar({self.name})"
    
    def __eq__(self, other):
        return isinstance(other, TypeVariable) and self.name == other.name
    
    def __hash__(self):
        return hash(self.name)
```

##### Step 2: Constraint Generation

```python
class ConstraintGenerator:
    """
    Generate type constraints from AST.
    
    For each expression, we create:
    - Type variables for unknowns
    - Equality constraints
    - Compatibility constraints
    """
    
    def __init__(self):
        self.constraints: List[Tuple[Type, Type, str]] = []
        self.type_env: Dict[str, Type] = {}
    
    def generate(self, node: ASTNode) -> Type:
        """Generate constraints for a node."""
        
        if isinstance(node, LiteralNode):
            # Literals have concrete types
            return node.type_
        
        elif isinstance(node, VariableNode):
            # Look up or create type variable
            if node.name not in self.type_env:
                self.type_env[node.name] = Type(
                    TypeKind.TYPEVAR,
                    type_var_name=TypeVariable().name
                )
            return self.type_env[node.name]
        
        elif isinstance(node, BinaryOpNode):
            # Generate constraints for operands
            left_type = self.generate(node.left)
            right_type = self.generate(node.right)
            
            # Create result type variable
            result_type = Type(
                TypeKind.TYPEVAR,
                type_var_name=TypeVariable().name
            )
            
            # Add constraints based on operator
            if node.operator in ['+', '-', '*', '/']:
                # Numeric operation
                self.add_numeric_constraint(left_type, node.operator)
                self.add_numeric_constraint(right_type, node.operator)
                
                # Result type depends on operands
                self.add_result_constraint(
                    left_type, right_type, result_type, node.operator
                )
            
            return result_type
        
        elif isinstance(node, AssignmentNode):
            # Variable type must match value type
            value_type = self.generate(node.value)
            var_type = self.generate(VariableNode(node.target))
            
            # Add equality constraint
            self.constraints.append((
                var_type, value_type,
                f"assignment to {node.target}"
            ))
            
            return value_type
        
        return Type(TypeKind.UNKNOWN)
    
    def add_numeric_constraint(self, type_: Type, context: str):
        """Add constraint that type must be numeric."""
        # Type must be int or float
        numeric_var = TypeVariable()
        self.constraints.append((
            type_,
            Type(TypeKind.TYPEVAR, type_var_name=numeric_var.name),
            f"numeric operation {context}"
        ))
```

##### Step 3: Unification Algorithm

```python
class Unifier:
    """
    Unification algorithm for type inference.
    
    Given two types, find a substitution that makes them equal.
    """
    
    def __init__(self):
        self.substitutions: Dict[str, Type] = {}
    
    def unify(self, t1: Type, t2: Type, context: str = "") -> Dict[str, Type]:
        """
        Unify two types.
        
        Returns a substitution that makes t1 = t2, or raises TypeError.
        
        Rules:
        1. unify(α, τ) = {α ↦ τ}     (if α not in τ)
        2. unify(τ, α) = {α ↦ τ}     (if α not in τ)
        3. unify(int, int) = {}       (same type)
        4. unify(int, float) = error  (incompatible)
        """
        # Apply existing substitutions
        t1 = self.apply_substitution(t1)
        t2 = self.apply_substitution(t2)
        
        # Same type - trivial unification
        if t1 == t2:
            return {}
        
        # Type variable on left
        if t1.kind == TypeKind.TYPEVAR:
            return self.bind(t1.type_var_name, t2, context)
        
        # Type variable on right
        if t2.kind == TypeKind.TYPEVAR:
            return self.bind(t2.type_var_name, t1, context)
        
        # Compatible concrete types (e.g., int and float)
        if self.compatible(t1, t2):
            ## Promote to wider type
            return {t1: self.promote(t1, t2)}
        
        # Cannot unify
        raise TypeError(
            f"Cannot unify {t1} and {t2}\n"
            f"  Context: {context}"
        )
    
    def bind(self, var_name: str, type_: Type, context: str) -> Dict[str, Type]:
        """
        Bind a type variable to a type.
        
        Checks occur check: type variable cannot appear in type.
        """
        # Occur check
        if self.occurs_in(var_name, type_):
            raise TypeError(
                f"Infinite type: {var_name} occurs in {type_}\n"
                f"  Context: {context}"
            )
        
        # Add substitution
        sub = {var_name: type_}
        self.substitutions.update(sub)
        return sub
    
    def occurs_in(self, var_name: str, type_: Type) -> bool:
        """Check if type variable occurs in type."""
        if type_.kind == TypeKind.TYPEVAR:
            return type_.type_var_name == var_name
        # Check in compound types (arrays, functions, etc.)
        # ..
        return False
    
    def apply_substitution(self, type_: Type) -> Type:
        """Apply current substitutions to a type."""
        if type_.kind == TypeKind.TYPEVAR:
            if type_.type_var_name in self.substitutions:
                return self.substitutions[type_.type_var_name]
        return type_
    
    def compatible(self, t1: Type, t2: Type) -> bool:
        """Check if two concrete types are compatible."""
        # Numeric types are compatible
        if t1.is_numeric() and t2.is_numeric():
            return True
        return False
    
    def promote(self, t1: Type, t2: Type) -> Type:
        """Promote to wider type."""
        if t1.kind == TypeKind.FLOAT or t2.kind == TypeKind.FLOAT:
            return Type(TypeKind.FLOAT)
        return Type(TypeKind.INT)
```

##### Step 4: Constraint Solver

```python
class ConstraintSolver:
    """
    Solve type constraints using unification.
    """
    
    def __init__(self, constraints: List[Tuple[Type, Type, str]]):
        self.constraints = constraints
        self.unifier = Unifier()
    
    def solve(self) -> Dict[str, Type]:
        """
        Solve all constraints.
        
        Returns a substitution mapping type variables to concrete types.
        """
        for t1, t2, context in self.constraints:
            try:
                self.unifier.unify(t1, t2, context)
            except TypeError as e:
                raise TypeError(f"Type inference failed:\n  {e}")
        
        return self.unifier.substitutions
```

##### Step 5: Complete Inference Algorithm

```python
class TypeInferenceEngine:
    """
    Complete type inference system.
    
    Usage:
        engine = TypeInferenceEngine()
        inferred_types = engine.infer(ast)
    """
    
    def infer(self, ast: List[ASTNode]) -> Dict[str, Type]:
        """
        Infer types for an entire program.
        
        Steps:
        1. Generate constraints from AST
        2. Solve constraints via unification
        3. Apply substitutions to get concrete types
        """
        # Step 1: Generate constraints
        generator = ConstraintGenerator()
        for node in ast:
            generator.generate(node)
        
        print(f"Generated {len(generator.constraints)} constraints")
        
        # Step 2: Solve constraints
        solver = ConstraintSolver(generator.constraints)
        substitutions = solver.solve()
        
        print(f"Found {len(substitutions)} type substitutions")
        
        # Step 3: Apply substitutions
        inferred_types = {}
        for var_name, var_type in generator.type_env.items():
            concrete_type = self.apply_substitutions(var_type, substitutions)
            inferred_types[var_name] = concrete_type
        
        return inferred_types
    
    def apply_substitutions(self, type_: Type, 
                          substitutions: Dict[str, Type]) -> Type:
        """Apply substitutions to get concrete type."""
        if type_.kind == TypeKind.TYPEVAR:
            if type_.type_var_name in substitutions:
                return substitutions[type_.type_var_name]
        return type_
```

#### Test Cases

```python
# Test 1: Simple inference
code1 = """
x = 10
y = 3.14
z = x + y
"""
# Expected:
#   x: int
#   y: float
#   z: float (promoted)

# Test 2: Inference from usage
code2 = """
x = 10
y = x + 5
z = y * 2
"""
# Expected:
#   x: int
#   y: int
#   z: int

# Test 3: Type conflict detection
code3 = """
x = 10
x = x + 5
x = "hello"
"""
# Expected: Error - x cannot be both int and string

# Test 4: Complex inference
code4 = """
a = 1
b = 2.0
c = a + b
d = c * 3
"""
# Expected:
#   a: int
#   b: float
#   c: float
#   d: float
```

#### Expected Output

```
Generated 8 constraints:
  1. t1 = int (literal 10)
  2. t2 = float (literal 3.14)
  3. t3 = numeric (x in x + y)
  4. t4 = numeric (y in x + y)
  5. t1 = t3 (x type consistency)
  6. t2 = t4 (y type consistency)
  7. t5 = result(t3, t4) (result of x + y)
  8. t5 = t6 (z = x + y)

Solving constraints..
  t1 -> int
  t2 -> float
  t3 -> int
  t4 -> float
  t5 -> float (promotion)
  t6 -> float

Inferred types:
  x: int
  y: float
  z: float
```

#### Extensions

1. *Let Polymorphism*: Allow `let f = λx. x` to be polymorphic
2. *Recursive Types*: Support self-referential types
3. *Type Classes*: Add ad-hoc polymorphism (like Haskell)
4. *Bidirectional Inference*: Combine synthesis and checking



### Readings

- Pierce, B.C. (2002). *Types and programming languages*. [electronic resource] (1). MIT Press.
- Benjamin C. Pierce (ed) & Pierce, B.C. (2005). *Advanced Topics in Types and Programming Languages* [electronic resource].
- [Type Theory Study Group Materials](https://github.com/type-theory)


