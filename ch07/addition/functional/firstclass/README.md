
## 1. First-Class Functions


A function is *first-class* when the language treats it as an ordinary value.
It can be passed to another function, returned from a function, assigned to a
variable, and stored in a data structure--exactly as you would an integer or a
string.

This is not a minor syntactic convenience. It is a change in what abstraction
means. In purely procedural code, abstraction is always over *data*. First-class
functions add abstraction over *behavior*.



### Why It Exists

Traditional procedural code separates what to compute from how to compute it.
The procedure is baked into the structure of the program. If you want to do
something different, you add a branch, a flag, or a new function name--the
logic of selection lives in the caller.

First-class functions let you move the selection outward. Instead of a function
that checks a flag and picks a path, you pass in a function that *is* the path.
Instead of a class hierarchy in which each subclass overrides a method, you pass
a replacement behavior directly.

This is the foundation on which higher-order functions, closures, and function
composition are all built. Without first-class functions, none of those patterns
exist.



### Python: The Exposition Language

#### Passing a Function as an Argument

```python
def square(x):
    return x * x

def apply(f, x):
    return f(x)

print(apply(square, 5))   # 25
```

`apply` does not know what `f` is. It knows only that `f` is callable and takes
one argument. The decision of *which* function to call is made by the caller, not
inside `apply`. This separates the *mechanism* of application from the *choice*
of operation.

#### Storing Functions in a Dictionary

```python
operations = {
    'double':    lambda x: x * 2,
    'negate':    lambda x: -x,
    'square':    lambda x: x * x,
}

def dispatch(name, value):
    return operations[name](value)

print(dispatch('square', 7))   # 49
```

A dictionary of functions is a lookup table for behavior. This pattern appears
constantly: command tables, event handlers, plugin registries. The key insight is
that the *what-to-do* is stored as data and retrieved at runtime.

#### Returning a Function

```python
def make_multiplier(n):
    def multiply(x):
        return x * n
    return multiply

triple = make_multiplier(3)
print(triple(10))   # 30
```

Here we construct behavior at runtime and return it as a value. `triple` is a
perfectly ordinary variable that holds a callable object. The behavior it
represents was chosen by passing `3` to `make_multiplier`. This is the first
step toward closures; the full picture of environment capture is in section 2.

#### A More Involved Example: Pipelines

```python
def pipeline(*funcs):
    def run(value):
        for f in funcs:
            value = f(value)
        return value
    return run

process = pipeline(
    lambda x: x + 1,
    lambda x: x * 2,
    lambda x: x - 3,
)

print(process(5))   # ((5+1)*2)-3 = 9
```

`pipeline` takes any number of functions and returns a new function that applies
them in sequence. Each step receives the result of the previous one. This is
a direct consequence of functions being values: they can be collected, iterated
over, and called like any other item in a list.



### Key Discussion Points

#### Functions Are Objects

In Python, a function has a type, an identity, and inspectable attributes. It
is not a special language construct that evaporates at runtime--it is a real
object.

```python
print(type(square))        # <class 'function'>
print(square.__name__)     # 'square'
print(callable(square))    # True
```

You can introspect it, wrap it, replace it. This is what "first-class" means in
concrete terms.

#### Late Binding

When you pass a function as an argument, the decision of which function to call
is deferred. It is not resolved at the site where `apply` is defined, but at the
site where `apply` is *called*. This is *late binding*: the binding between the
parameter name `f` and its concrete value is made at call time.

Late binding is both the power and the cost. It enables reusable, generic code.
It also means that reasoning about what will execute requires following the flow
of values, not just reading the control flow of a single function.

#### Dynamic Dispatch Through Function Objects

Calling a function stored in a variable is *dynamic dispatch*: the runtime
resolves the call target at the moment of the call, rather than having the
address fixed at compile time.

In Python this is always the case. In a language like C, it requires an explicit
function pointer. The mechanism is the same; the syntax and cost differ.



### Under the Hood: C

In C, functions are not first-class in the Python sense. You cannot assign a
function to a variable the way you assign an `int`. But you *can* store a
*pointer to a function*, and a function pointer is the C mechanism underlying
what Python does automatically.

#### Function Pointer Syntax

```c
typedef int (*func)(int);
```

This declares `func` as a type alias: a pointer to a function that takes one
`int` and returns one `int`. With this typedef, a function pointer looks and
behaves much like any other variable.

#### The apply Pattern in C

```c
#include <stdio.h>

typedef int (*func)(int);

int square(int x)    { return x * x; }
int negate(int x)    { return -x; }
int increment(int x) { return x + 1; }

int apply(func f, int x) {
    return f(x);
}

int main(void) {
    printf("%d\n", apply(square,    5));   /* 25 */
    printf("%d\n", apply(negate,    5));   /* -5 */
    printf("%d\n", apply(increment, 5));   /*  6 */
    return 0;
}
```

The call `f(x)` inside `apply` is an *indirect call*: the processor loads the
address stored in `f`, then jumps to it. The target is not encoded in the
instruction; it is read from memory at runtime.

#### Dispatch Table

A common C idiom is an array of function pointers indexed by an integer:

```c
func ops[] = { square, negate, increment };

int dispatch(int op_index, int x) {
    return ops[op_index](x);
}
```

This is structurally what a C++ vtable is: an array of function pointers used
to implement virtual method dispatch. Python's attribute lookup for methods works
on the same idea, mediated through dictionaries rather than fixed arrays.

#### The Limit: No Environment Capture

A raw C function pointer carries no environment. `square` works because it
depends only on its argument. But `make_multiplier(3)`--a function that
*remembers* the value `3`--cannot be expressed with a plain function pointer.
The pointer can carry the *code*, but not the *data* it closed over.

This is the boundary between first-class functions and closures. Crossing it
requires passing a context struct alongside the pointer. That pattern is the
subject of section 2.



### Cost Model

An indirect call through a function pointer costs more than a direct call:

- The target address must be loaded from memory.
- The branch predictor cannot reliably predict where the jump goes.
- The compiler cannot inline across the call boundary.

In Python, the cost is larger still: every call involves dictionary lookup,
type verification, reference count updates, and frame allocation.

The trade-off is the same one that runs through this entire series:
*expressiveness has a cost in indirection*. Understanding that cost is what
allows you to make deliberate choices about when to use it.



### Concurrency Link

If you pass a function as an argument rather than reading a shared mutable
variable to decide which operation to perform, you have removed one source of
contention. Two threads that each receive their own function value and apply it
to their own data share nothing, and therefore cannot race.

First-class functions allow behavior to travel with data rather than living in
shared locations. Shared mutable state shrinks. This is the first step toward a
style where concurrency becomes easier to reason about--not because concurrency
is simpler, but because fewer things need coordination.



*Next: [2. Closures](../closure/README.md)--what happens when a function
remembers the environment it was created in.*
