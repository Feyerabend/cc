
## Scope in Programming

*Scope* refers to the region of a program where a particular variable, function, or identifier is accessible.
It defines the visibility and lifetime of entities within a program. There are several types of scope, each
with different rules and principles. We'll examine *lexical scope* (as seen in PL/0) and provide an overview
of other types of scope.


### 1. Lexical Scope (Static Scope)

Lexical scope means that the visibility of a variable is determined by its physical location in the source code.
This scope is established at compile time and does not change during runtime.

1. *Block-Level Scoping*: Variables declared in a block (e.g., `{ ... }` in C or `begin ... end` in PL/0) are only
   accessible within that block and its nested sub-blocks.

2. *Outer and Inner Scopes*: Inner blocks can access variables from their outer (enclosing) blocks, but outer blocks
   cannot access variables declared in inner blocks.

3. *Symbol Table Maintenance*: During parsing, a symbol table is maintained to map identifiers to their corresponding
   declarations. When a block is exited, its variables are removed from the table.


*Example in PL/0*

```pl0
const x = 5;

begin
  var y;
  procedure foo;
  begin
    var z;
    z := x + y;   // `x` is accessed from the outer scope, `y` from the immediate outer block
  end;
  y := x + 10;
  call foo;
end.
```

In this example:
- x is accessible globally because it is defined in the outermost scope.
- y is accessible within the begin ... end block and to foo, but not outside.
- z is local to the foo procedure.


#### Lexical Scope in Practice

Languages like C, JavaScript (modern ES6+ with let and const), and Python use lexical scope. A function defined
in a specific block can access variables from that block and its parent blocks.


### 2. Other Types of Scope

*Dynamic Scope*
- Definition: The visibility of variables is determined by the runtime call stack rather than the program's lexical structure.
- Principles: Variables are resolved by searching the call stack, starting from the most recently called function.
- Example (Conceptual, not supported in most modern languages):

```lisp
(defun foo ()
  (print x))   ; `x` is not declared in `foo`

(let ((x 42))
  (foo))        ; Prints `42` because `x` is dynamically resolved
```

- Languages: Older languages like Lisp (original) and Bash use dynamic scoping.

*Global Scope*
- Definition: Variables declared in the global scope are accessible throughout the entire program unless shadowed by a local variable.
- Example:

```c
int globalVar = 10;

void func() {
    printf("%d\n", globalVar); // Accesses the global variable
}
```


*Local Scope*
- Definition: Variables declared within a function or block are only accessible within that specific context.
- Example:

```python
def func():
    x = 5  # Local to `func`
    print(x)

print(x)  # Error: `x` is not defined
```


*Function Scope*
- Definition: Variables are visible within the function where they are declared (common in older JavaScript with var).
- Example:

```javascript
function foo() {
    if (true) {
        var x = 10; // Scoped to `foo`, not the `if` block
    }
    console.log(x); // 10
}
```


*Module Scope*
- Definition: Variables are scoped to a module or file and cannot be accessed outside it.
- Languages: Python, JavaScript (ES6 Modules).

*Namespace Scope*
- Definition: Variables are scoped within a specific namespace, used to avoid name collisions.
- Example in C++:

```c++
namespace A {
    int x = 5;
}

namespace B {
    int x = 10;
}

int main() {
    std::cout << A::x << " " << B::x; // Outputs: 5 10
}
```

__Considerations Across Scopes__
1. Shadowing: When a local variable in an inner scope has the same name as a variable in an outer scope, the local variable takes precedence.

```python
x = 10
def func():
    x = 5  # Shadows the global `x`
    print(x)  # 5
print(x)  # 10
```

2. Encapsulation: Proper use of scope enforces encapsulation, limiting unintended interactions between parts of a program.
3. Lifetime: While scope determines visibility, lifetime defines how long a variable exists in memory. A variable's lifetime
   may extend beyond its scope (e.g. closures in functional programming).


### Comparison of Lexical and Dynamic Scoping

|Feature|	Lexical Scope|	Dynamic Scope|
|--|--|--|
|Resolution|	Determined by code structure|	Determined by call stack|
|Runtime Impact|	Faster (resolved at compile-time)|	Slower (resolved at runtime)|
|Debugging|	Easier|	Harder|
|Usage|	Modern languages (C, Python)|	Older languages (Lisp)|

