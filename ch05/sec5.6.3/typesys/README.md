
## Type Systems

This project is an educational implementation of several fundamental type system
concepts, built by extending a very small TAC (Three-Address Code--like) interpreter.
We will actually return to more details TAC later on, but here demonstrate one way
to handle types through the use of TAC, which is one way to represent a program
through the compiler.

TAC (Three-Address Code) is an intermediate representation commonly used in compilers
where each instruction performs a single simple operation and uses at most three operands,
typically in the form `result = operand1 op operand2`. Instead of complex expressions,
computations are broken down into small, explicit steps using temporary variables, which
makes program behavior easier to analyze, transform, and optimize. Because TAC has a very
regular and simple structure, it is ideal for demonstrating core compiler concepts such
as symbol tables, expression evaluation, control flow, and especially type systems,
since each operation exposes exactly which values interact and what types must be checked,
inferred, or coerced.

Each "parser" in our program demonstrates a different philosophy of typing and type
handling found in real programming languages. The goal is not performance or completeness,
but clarity: each part isolates one idea and shows how it can be implemented.

This project demonstrates:
- Runtime vs compile-time typing
- Explicit vs inferred types
- Type compatibility
- Type coercion
- Error detection strategies
- Symbol table design
- Type inference basics
- Compiler front-end concepts


### Overview

The code is divided into conceptual parts:

1. Type system foundations  
2. Dynamic typing  
3. Static typing with type checking  
4. Type inference  
5. Type coercion  
6. Demonstration programs

Each part builds on the same minimal language:

- Assignment:  
```
x = 10
```
- Binary expressions:  
```
t = x + 5
```
- Literals: integers, floats, strings  
- Simple symbol table  
- Line-based parsing

This makes it easy to compare how different type systems treat the *same* program.



### Part 1. Type System Foundations

```python
class TypeKind(Enum):
class Type:
```
This is the abstract model of a type system.

`TypeKind`

Defines all supported types:
- INT
- FLOAT
- BOOL
- STRING
- ARRAY
- UNKNOWN
- ERROR

This is the vocabulary of the language.

`Type`

Wraps a `TypeKind` and optionally extra metadata:
- base_type and size for arrays
- Utility methods:
- is_numeric()
- can_coerce_to(other)

This models how real compilers treat types as structured objects, not just labels.

Example rule:
* int -> float is allowed
* float -> int is not (unless explicitly defined)

This single class is reused by the static checker, inference engine, and coercion engine.



### Part 2. Dynamic Typing

```
class DynamicTACParser:
```
This behaves like Python or JavaScript.

Key properties:
- No types exist before execution.
- Variables can change type freely.
- Type is inferred from the runtime value.

Example:
```
x = 10      -> x is int
x = 3.14    -> x is float
```
Symbol table structure:
```
{
  "x": {
    "type": TypeKind.INT,
    "value": 10
  }
}
```
Characteristics

|Property|Dynamic System|
|--------|--------------|
|When types are known|Runtime|
|Type errors caught|During execution|
|Variable retyping|Allowed|
|Safety|Low|
|Flexibility|High|

This demonstrates late binding of types.



### Part 3. Static Typing with Type Checking
```
class StaticTACParser:
```
This behaves like C, Java, Rust.

Key ideas:
- Variables must be declared with a type:
```
int x = 10
```

- Assignments are checked against that type.
- Errors are found before execution.

Two-phase model:
1. Parse -> build AST
2. Type check -> validate AST

Example Errors
```
int x = 10
x = 3.14
```
Produces:
```
Type mismatch: Cannot assign float to int
```

__Type Checking Algorithm__

For each statement:
1. Infer expression type
2. Compare against declared type
3. Check:
- Compatibility
- Required coercions
- Undeclared variables

This mimics real compiler front-ends.

__Characteristics__

|Property|Static System|
|--------|-------------|
|When types are known|Before execution|
|Type errors caught|Compile time|
|Variable retyping|Forbidden|
|Safety|High|
|Flexibility|Lower|




### Part 4. Type Inference
```
class TypeInferenceParser:
```
This is a simplified version of Hindley-Milner style inference.

No explicit type declarations:
```
x = 10
y = 3.14
z = x + y
```
Types are deduced automatically:
```
x : int
y : float
z : float
```
__How It Works__

For each assignment:
1. Infer type of the right-hand expression
2. If variable is new -> assign that type
3. If variable already exists -> check compatibility

Compatibility rules:
- Same type -> OK
- int <-> float -> OK
- Anything else -> error

This is how languages like:
- ML
- Haskell
- Rust (partially)
- Kotlin (partially)

can avoid explicit annotations.



### Part 5. Type Coercion
```
class TypeCoercionTACParser:
```
This models weak typing with automatic conversions.

Hierarchy:
```
int -> float
```
Example:
```
x = 5
y = 3.14
t = x + y
```
Internally becomes:
```
float(x) + y
```
And the coercion is logged:
```
Coercion in 'x + y': int + float -> float
```
Coercion Pipeline
1. Evaluate left operand
2. Evaluate right operand
3. Determine result type
4. Coerce both operands upward
5. Perform operation

This mirrors behavior found in:
- C arithmetic
- Java numeric promotion
- Many scripting languages



### Comparison of All Systems

|Feature|Dynamic|Static	Inference|Coercion|
|-------|-------|----------------|--------|
|Explicit types|No|Yes|No|No|
|Type safety|Low|High|High|Medium|
|Flexibility|High|Low|High|High|
|Error detection time|Runtime|Compile-time|Compile-time|Runtime|
|Implicit conversion|Yes|Limited|Limited|Strong|

Each class is a different answer to the same question:

When should types be known, and how strict should the language be?



### Why This Code?

This file is effectively a mini textbook:
- Same syntax
- Same evaluator
- Same language
- Different type systems

By switching parser classes, you are switching programming language philosophy.

You can think of it as:

|Parser Class|Language Style|
|------------|--------------|
|DynamicTACParser|Python, JS|
|StaticTACParser|C, Java|
|TypeInferenceParser|ML, Haskell|
|TypeCoercionTACParser|C arithmetic|



