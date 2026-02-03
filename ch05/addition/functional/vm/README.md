
## FunLang

*FunLang* is a purely functional programming language (with ML-inspired syntax),
compiling to a custom virtual machine built on functional programming primitives.

Early functional languages (exmplified by [interpreter](./../../interpreter/))
maximised expressive freedom. Later languages maximise semantic guarantees,
and that reflects a deep change in how we think about correctness, responsibility,
but also the role of the compiler.

- *Pure functional* - Immutable data, no side effects
- *First-class functions* - Functions are values
- *Algebraic data types* - Maybe, Result, Lists
- *Pattern matching* - Structural pattern matching
- *Pipe operator* - Clean data transformation pipelines
- *Currying* - Automatic partial application
- *Type inference* - (planned) Hindley-Milner type system
- *REPL* - Interactive development environment

Grammar:
```ebnf
program     ::= expr

expr        ::= pipe_expr

pipe_expr   ::= binop (|> binop)*

binop       ::= application (operator application)*

application ::= atom+

atom        ::= literal
              | data_constructor
              | list_literal
              | lambda
              | let_expr
              | if_expr
              | case_expr
              | variable
              | ( expr )

lambda      ::= fn identifier+ -> expr

let_expr    ::= let identifier = expr in expr

if_expr     ::= if expr then expr else expr

case_expr   ::= case expr of case_branch+

case_branch ::= pattern -> expr ;?

pattern     ::= _
              | identifier
              | integer
              | Some ( pattern )
              | Nothing
              | Ok ( pattern )
              | Err ( pattern )
```

__Reserved Words__: Reserved words cannot be used as identifiers:

```
fn let in if then else case of
True False Some Nothing Ok Err
```


__Type System__: FunLang is currently dynamically typed.
Runtime values include:

- *Integers* - Arbitrary precision
- *Floats* - IEEE 754 double precision
- *Strings* - UTF-8 encoded
- *Booleans* - True and False
- *Functions* - First-class closures
- *Maybe[A]* - Some(value) | Nothing
- *Result[A, E]* - Ok(value) | Err(error)
- *List[A]* - Immutable lists

FunLang is designed to be:
- *Simple* - Easy to understand and extend
- *Functional* - Pure and immutable
- *Practical* - Useful for real programs
- *Pedagogical* - Useful for learning FP concepts



### Run a Program

```python
from funlang_parser import run_funlang

result = run_funlang("""
    let double = fn x -> x * 2
    in 5 |> double
""")

print(result)  # => 10
```

### Start the REPL

```bash
python funlang_repl.py
```

```
>>> 2 + 3
=> 5

>>> let add = fn a -> fn b -> a + b
>>> add 10 5
=> 15

>>> 10 |> add 5 |> fn x -> x * 2
=> 30
```


__REPL Commands__

```
:help              Show help
:quit, :q, :exit   Exit REPL
:clear             Clear screen
:env               Show all variables
:reset             Reset environment
:load <file>       Load and execute file
:debug on|off      Toggle debug mode
```

Usage:

```
>>> let double = fn x -> x * 2

>>> double 21
=> 42

>>> :env
Environment:
  double = <closure x>

>>> 5 |> double |> fn x -> x + 1
=> 11
```

---

### Use From Python

```python
from funlang_parser import run_funlang, compile_funlang
from functional_vm import FunctionalVM

# Quick run
result = run_funlang("2 + 3")
print(result)  # => 5

# Compile to AST
ast = compile_funlang("fn x -> x * 2")

# Run with VM
vm = FunctionalVM(debug=False)
result = vm.run(ast)
```




---

### Comments

```funlang
-- This is a single-line comment
```

### Literals

```funlang
42          -- Integer
3.14        -- Float
"Hello"     -- String
True        -- Boolean
False       -- Boolean
```

### Variables and Let Bindings

```funlang
-- Simple binding
let x = 42 in x + 1

-- Multiple bindings
let x = 10
in let y = 20
in x + y

-- Function binding
let square = fn x -> x * x
in square 7
```

### Lambda Functions

```funlang
-- Single parameter
fn x -> x + 1

-- Multiple parameters (curried)
fn x -> fn y -> x + y

-- Shorthand
let add = fn a -> fn b -> a + b
```

### Function Application

```funlang
-- Simple
double 21

-- Multiple arguments
add 5 10

-- Partial application
let add5 = add 5
in add5 10  -- => 15
```

### The Pipe Operator

The pipe operator `|>` feeds a value into a function:

```funlang
-- Basic pipe
5 |> double  -- Same as: double 5

-- Pipe chain (left to right)
10 
  |> increment 
  |> double 
  |> square
-- Same as: square(double(increment(10)))

-- With partial application
10 
  |> add 5      -- add is curried
  |> multiply 2
-- Same as: multiply 2 (add 5 10)
```

### If Expressions

```funlang
if x > 0
then "positive"
else "non-positive"

-- Nested
if x > 10
then "big"
else if x > 5
     then "medium"
     else "small"
```

### Pattern Matching

```funlang
-- Match on Maybe
case maybeValue of
    Some(x) -> x * 2;
    Nothing -> 0;

-- Match on Result
case result of
    Ok(val) -> val + 1;
    Err(msg) -> 0;

-- Nested patterns
case value of
    Some(Ok(x)) -> x;
    Some(Err(e)) -> 0;
    Nothing -> -1;
```

### Data Constructors

```funlang
-- Maybe type
Some(42)
Nothing

-- Result type
Ok("success")
Err("error message")

-- Lists
[]
[1, 2, 3, 4, 5]
```

### Operators

```funlang
-- Arithmetic
2 + 3
10 - 5
4 * 6
20 / 4

-- Comparison
5 == 5
3 < 10
10 > 5
x <= y
x >= y

-- List cons
1 :: [2, 3]  -- [1, 2, 3]

-- Pipe
value |> function
```

### Operator Precedence

From highest to lowest:
1. Function application (left-associative)
2. `*`, `/`
3. `+`, `-`  
4. `::` (cons)
5. `|>` (pipe)
6. `<`, `>`, `==`, `<=`, `>=`


---

### Pipe Chains

```funlang
let double = fn x -> x * 2
in let increment = fn x -> x + 1
in let square = fn x -> x * x
in 5 
  |> increment  -- 6
  |> double     -- 12
  |> square     -- 144
-- Result: 144
```

### Railway-Oriented Programming

```funlang
let validate = fn x ->
    if x > 0
    then Ok(x)
    else Err("Not positive")

in let double = fn x -> Ok(x * 2)

in let result = 10 
      |> validate
      
in case result of
    Ok(val) -> double val;
    Err(e) -> Err(e);
```

### Function Composition with Pipes

```funlang
let compose = fn f -> fn g -> fn x -> f (g x)

-- With pipes (clearer!)
let pipeline = fn x ->
    x 
    |> increment
    |> double
    |> square

in pipeline 5
```

### Maybe Monad

```funlang
case Some(10) of
    Some(x) -> 
        case Some(x * 2) of
            Some(y) -> Some(y + 5);
            Nothing -> Nothing;
        ;
    Nothing -> Nothing;
-- Result: Some(25)
```

### Church Encodings

```funlang
-- Church numeral 3
let three = fn f -> fn x -> f (f (f x))
in let increment = fn x -> x + 1
in three increment 0
-- Result: 3

-- Church booleans
let true_fn = fn t -> fn f -> t
in let false_fn = fn t -> fn f -> f
in true_fn 42 0
-- Result: 42
```

### Currying and Partial Application

All multi-argument functions are automatically curried:

```funlang
let add = fn a -> fn b -> a + b

-- Partial application
let add5 = add 5

-- Full application
add5 10  -- => 15

-- Can also write
add 5 10  -- => 15
```

### Point-Free Style

```funlang
-- Pointful
fn x -> double (increment x)

-- Point-free (using composition)
compose double increment
```

### Combinators

```funlang
-- K combinator
let k = fn x -> fn y -> x

-- I combinator
let i = fn x -> x

-- S combinator
let s = fn x -> fn y -> fn z -> (x z) (y z)

-- SKK = I
let skk = s k k
```

---

### Available Patterns

```funlang
_                -- Wildcard (matches anything)
x                -- Variable (binds to name)
42               -- Literal
Some(pattern)    -- Constructor with nested pattern
Nothing          -- Constructor without argument
Ok(pattern)      -- Result success
Err(pattern)     -- Result error
```

Examples:
```funlang
-- Simple
case Some(42) of
    Some(x) -> x;
    Nothing -> 0;

-- Nested
case Some(Ok(5)) of
    Some(Ok(n)) -> n;
    Some(Err(_)) -> 0;
    Nothing -> -1;

-- Literal matching
case x of
    0 -> "zero";
    1 -> "one";
    n -> "other";  -- Variable pattern
```

---

### Runtime Errors

```funlang
-- Division by zero returns Result
case (10 / 0) of
    Ok(x) -> x;
    Err(e) -> 0;
```

### Parse Errors

```python
try:
    result = run_funlang("let x = ")
except SyntaxError as e:
    print(f"Parse error: {e}")
```

---

### Error Handling with Result

```funlang
let parse = fn x -> Ok(x)
in let validate = fn x ->
    if x > 0
    then Ok(x)
    else Err("Must be positive")
    
in case parse 10 of
    Ok(x) -> validate x;
    Err(e) -> Err(e);
```

### Option Handling with Maybe

```funlang
let safeDivide = fn a -> fn b ->
    if b == 0
    then Nothing
    else Some(a / b)

in case safeDivide 10 2 of
    Some(x) -> x;
    Nothing -> 0;
```

### List Processing

```funlang
-- Cons
1 :: 2 :: 3 :: []

-- Pattern match on lists (planned)
case list of
    [] -> "empty";
    x :: xs -> "non-empty";
```

### Higher-Order Functions

```funlang
let map = fn f -> fn list ->
    case list of
        [] -> [];
        x :: xs -> (f x) :: (map f xs);

let filter = fn pred -> fn list ->
    case list of
        [] -> [];
        x :: xs ->
            if pred x
            then x :: (filter pred xs)
            else filter pred xs;
```

---

### Use Pipes for Clarity

```funlang
-- Instead of
square (double (increment 5))

-- Write
5 |> increment |> double |> square
```

### Handle Errors Explicitly

```funlang
-- Good: explicit error handling
case parseNumber input of
    Ok(n) -> process n;
    Err(e) -> handleError e;

-- Avoid: ignoring errors
```

### Prefer Pattern Matching

```funlang
-- Good
case maybeValue of
    Some(x) -> x;
    Nothing -> 0;

-- Less clear
if is_some maybeValue
then get_value maybeValue
else 0
```


---


### Projects: Performance & Enhancements

- The parser is interpreted (not compiled)
- Function calls have overhead
- Pipes are syntactic sugar (no performance cost)
- Tail recursion is limited by Python stack
- For performance-critical code, consider:
  - Caching compiled ASTs
  - Minimising nested function calls
  - Using iteration over recursion

It has some similarities to ML/Elm/Haskell, e.g.:
- Functional purity
- First-class functions
- Pattern matching
- Currying
- Algebraic data types

Some differences are:
- Dynamic typing (no static type checker, yet)
- No module system
- Limited built-in types (Maybe, Result, List)
- No custom type definitions
- No records/tuples
- No list comprehensions
- Simplified syntax

In summary lacking features:
- Hindley-Milner type inference
- Static type checking
- Module system
- Custom algebraic data types
- Record types
- List comprehensions
- Do-notation for monads
- Lazy evaluation
- Optimising compiler
- Better error messages
- Standard library
- Package manager



