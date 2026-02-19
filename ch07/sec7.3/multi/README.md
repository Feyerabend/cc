
## Mol: A Simple OO & Functional Language

Mol has evolved from its [earlier](./../../../ch05/sec5.12/mol/) definition
into an extended, lightweight, interpreted programming language that blends
functional and object-oriented paradigms. It also incorporates selected
imperative elements beneath the surface. As a result, Mol can be characterised
as a multi-paradigm language.

It is implemented in C and supports features like first-class functions, closures,
recursion, lists, strings, structs, and a simple OOP system using virtual tables
(vtables) from before. Mol is designed for simplicity and expressiveness,
drawing some inspiration from languages like Scheme, Smalltalk (and Lua).

The language is executed via a C-based interpreter, which includes:
- A REPL (Read-Eval-Print Loop) for interactive coding.
- Support for running scripts from files (`.mol` extension recommended).
- A built-in test suite to verify language features.
- Demo mode for quick examples (move this if you want to).

Mol's syntax is expression-oriented, with infix operators for arithmetic and
comparisons, but it uses keywords like `let`, `fn`, and `if` for control structures.
All code is evaluated in a dynamic environment, and there is no static type
system--values are dynamically typed.

### Concepts
- *Functional Programming*: First-class functions, closures, higher-order
  functions (e.g., `map`, `filter`, `foldl`), recursion via `letrec`, and
  immutable data where possible (though structs support mutation).
- *Object-Oriented Programming*: Achieved via structs with a `vptr` field
  pointing to a vtable (a struct of methods). This allows polymorphism and method calls.
- *Dynamic Evaluation*: Everything is an expression that returns a value.
  Sequences (`;`-separated) evaluate to the last expression's value.
- *Truthiness*: Non-false values (e.g., non-zero ints, non-empty strings/lists)
  are truthy; `false`, `0`, `null`, empty lists/strings are falsy.
- *No Side Effects by Default*: Pure functions are encouraged,
  but mutation is possible on structs.
- *Built-in Functions*: Includes list operations
  (`cons`, `head`, `tail`, `nil?`, `len`, `map`, `filter`, `foldl`),
  string ops (`len`, `++`), and error handling (`error("msg")`).


### Installation and Running Mol

Mol is built from C source files (`main.c`, `mol_eval.c`,
and supporting headers like `mol.h`). To build and run use Makefile, or:

1. Compile the C code:
   ```
   gcc -o mol main.c mol_eval.c mol_parse.c mol_types.c  # Assuming all files are present
   ```

2. Run modes:
   - *Demo Mode* (default): `./mol`           -- Runs a set of example programs.
   - *REPL Mode*: `./mol --repl`              -- Interactive shell. Type expressions and press Enter. Exit with `exit` or `quit`.
   - *Run File*: `./mol script.mol`           -- Executes the code in `script.mol`.
   - *Evaluate Expression*: `./mol -e "expr"` -- Runs a single expression, e.g., `./mol -e "1 + 1"`.
   - *Run Tests*: `./mol --test`              -- Executes the built-in test suite.

Note: The interpreter has a maximum input size
(e.g., 4096 chars for REPL lines),
and errors cause the program to exit with messages.


### Syntax Overview

Mol code consists of expressions.
Programs are sequences of expressions separated by `;`.
Parentheses `()` control precedence.

#### Literals
- *Integers*: `42`, `-5` (64-bit signed).
- *Booleans*: `true`, `false`.
- *Strings*: `"hello world"` (double-quoted; no escapes yet).
- *Null*: `null`.
- *Lists*: `[]` (empty), `[1, 2, 3]` (comma-separated).
- *Structs*: `{field1: value1, field2: value2}` (comma-separated key-value pairs).

#### Operators
- *Arithmetic*: `+`, `-`, `*`, `/`, `%` (integers only; infix).
- *Unary*: `-` (negate int), `!` or `not` (logical not).
- *Comparisons*: `==`, `!=`, `<`, `>`, `<=`, `>=` (ints or strings for equality).
- *Logical*: `and` (short-circuit), `or` (short-circuit).
- *Concat/Append*: `++` (strings or lists).
- *Precedence*: Standard math ( `* / %` > `+ -` ); use `()` for grouping.

#### Bindings
- *Let (Non-Recursive)*: `let name = expr; body`    -- Binds `name` to `expr`'s value in `body`.
- *Letrec (Recursive)*: `letrec name = expr; body`  -- Allows `expr` to reference `name` (e.g., for recursive functions).

Bindings create a new scope;
variables are looked up dynamically.

#### Functions
- *Definition*: `fn(params) body` -- Anonymous lambda.
  - Params: Comma-separated, e.g., `fn(x, y) x + y`.
  - Variadic: `fn(x, ..rest) body` -- `rest` is a list of extra args.
- *Named Functions*: Use `let` or `letrec`, e.g., `let add = fn(a, b) a + b;`.
- *Calls*: `func(arg1, arg2)` -- Parentheses required.
- *Closures*: Functions capture their environment.
- *Higher-Order*: Functions can take/return functions.
- *Currying*: Nested functions, e.g., `fn(a) fn(b) a + b`.

#### Control Flow
- *If/Else*: `if cond then else els` -- `then` and `els` are expressions.
  - Nested: `if cond1 "big" else if cond2 "med" else "small"`.
- *Sequences*: `expr1; expr2; expr3` -- Evaluates all, returns last.
- No loops (use recursion instead).

#### Lists
- Built-ins:
  - `cons(head, tail)`: Creates a new list node.
  - `head(list)`: First element.
  - `tail(list)`: Rest of list.
  - `nil? (list)`: True if empty.
  - `len(list)`: Length.
  - `map(fn, list)`: Applies fn to each element.
  - `filter(fn, list)`: Keeps elements where fn returns truthy.
  - `foldl(fn, init, list)`: Left-fold (reduce).
- Append: `[1,2] ++ [3,4]` --> `[1,2,3,4]`.

#### Strings
- `len("str")`: Length.
- `"a" ++ "b"`: Concatenation.
- Equality: `"a" == "b"`.

#### Structs
- Creation: `{x: 10, y: 20}`.
- Access: `struct.field`.
- Mutation: `struct.field = value` (returns value).
- Nested: `{outer: {inner: 42}}.outer.inner`.

#### OOP with Vtables
- Vtable: A struct of methods, e.g., `{method: fn(self) ...}`.
- Object: `{vptr: vtable, field: value}`.
- Method Call: `obj.method(args)` -- Looks up in vptr, passes `self` as first arg.
- Polymorphism: Different objects can share method names via compatible vtables.

#### Error Handling
- `error("msg")`: Throws an error (exits interpreter).


### Writing Programs

Programs are files with sequences of expressions.
Use `let`/`letrec` for top-level definitions.
Focus on pure functions and recursion for computation.

#### Example 1: Factorial (Recursive)
```
letrec fact = fn(n) if n == 0 1 else n * fact(n-1);
fact(5)
```
Output: `120`

#### Example 2: List Processing
```
letrec even = fn(x) x % 2 == 0;
letrec double = fn(x) x * 2;
letrec sum = fn(a, b) a + b;

foldl(sum, 0, map(double, filter(even, [1,2,3,4,5,6])))
```
Output: `60` (sums 4+8+12 = 24? Wait, evens:2,4,6 --> doubles:4,8,12 --> sum:24)

#### Example 3: OOP with Vtables
```
let AnimalVT = {
  speak: fn(self) self.name ++ " says " ++ self.sound
};

let dog = {vptr: AnimalVT, name: "Dog", sound: "woof"};
let cat = {vptr: AnimalVT, name: "Cat", sound: "meow"};

dog.speak() ++ " and " ++ cat.speak()
```
Output: `Dog says woof and Cat says meow`

#### Example 4: Curried Adder
```
let makeAdder = fn(n) fn(x) x + n;
let add10 = makeAdder(10);
add10(32)
```
Output: `42`

#### Example 5: Variadic Sum
```
let sum_all = fn(..xs) foldl(fn(a,b) a+b, 0, xs);
sum_all(1, 2, 3, 4, 5)
```
Output: `15`


### Advanced Concepts
- *Tail Call Optimisation*: The evaluator uses a trampoline for tail calls in sequences,
  ifs, etc., reducing stack usage.
- *Closures and Environments*: Functions capture bindings; `letrec` enables self-reference.
- *Polymorphism*: Vtables allow duck-typing-like behavior.
- *Limitations*: No modules, no I/O (pure computation), no floats, limited error recovery.

### Testing and Debugging
Run `./mol --test` to execute ~40 built-in tests covering all features.
Tests print pass/fail with expected vs. actual output.

For debugging, use the REPL to test expressions incrementally.
Errors show line numbers (if parsed).

