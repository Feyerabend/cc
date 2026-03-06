
## 2. Closures


A closure is a function together with the environment it was defined in.
When a function is created inside another function and refers to variables in
the outer scope, it *captures* those variables. The inner function and the
captured environment travel together as a single unit.

In practice: if you return a function that uses a local variable from its
enclosing call, that variable does not disappear when the enclosing call
returns. Its lifetime is extended by the closure.



### Why It Exists

Without closures, first-class functions are limited to pure computation--they
can only use their explicit arguments. Closures let a function carry a piece of
its creation context forward in time. This enables stateful abstractions without
global variables, configurable behavior without extra parameters at every call
site, and private state without a class.

Closures are the minimum machinery needed to simulate objects. A counter, a
cache, a parser, an event handler--all of these can be written as a closure
rather than as a class, and often more clearly so.



### Python: The Exposition Language

#### Basic Closure

```python
def make_adder(n):
    def adder(x):
        return x + n
    return adder

add5 = make_adder(5)
print(add5(10))   # 15
print(add5(3))    # 8
```

`n` is a local variable of `make_adder`. When `make_adder(5)` returns, the
call frame is gone--but `adder` still holds a reference to `n`. The value
`5` lives on, bound inside `add5`.

Two calls to `make_adder` produce two independent closures:

```python
add5  = make_adder(5)
add10 = make_adder(10)
print(add5(1))    # 6
print(add10(1))   # 11
```

Each closure has its own captured environment. They do not share `n`.

#### Mutable State Inside a Closure

A closure can also hold *mutable* state:

```python
def make_counter(start=0):
    count = [start]          # list cell--mutable, captured by reference
    def increment():
        count[0] += 1
        return count[0]
    def reset():
        count[0] = start
    return increment, reset

inc, rst = make_counter()
print(inc())   # 1
print(inc())   # 2
print(inc())   # 3
rst()
print(inc())   # 1
```

Note the list wrapper. In Python 2 and in Python 3 before `nonlocal`, a
plain integer cannot be rebound inside a nested function without declaring
it `nonlocal`. Using a mutable container sidesteps that. With `nonlocal` the
intent is clearer:

```python
def make_counter(start=0):
    count = start
    def increment():
        nonlocal count
        count += 1
        return count
    return increment
```

#### Closures Sharing an Environment

Two functions returned from the same enclosing scope share the same captured
variables:

```python
def make_account(balance):
    def deposit(amount):
        nonlocal balance
        balance += amount
        return balance
    def withdraw(amount):
        nonlocal balance
        balance -= amount
        return balance
    def get_balance():
        return balance
    return deposit, withdraw, get_balance

dep, wit, bal = make_account(100)
dep(50)    # balance -> 150
wit(30)    # balance -> 120
print(bal())   # 120
```

`deposit`, `withdraw`, and `get_balance` all operate on the same `balance`
variable. This is closure-based encapsulation: private state with a public
interface, no class required.

#### The Loop Capture Gotcha

A classic error illustrates what "capture" really means:

```python
# Wrong--all closures capture the same variable i
funcs_wrong = [lambda: i for i in range(3)]
print([f() for f in funcs_wrong])   # [2, 2, 2]

# Right--bind the value at creation time via a default argument
funcs_right = [lambda i=i: i for i in range(3)]
print([f() for f in funcs_right])   # [0, 1, 2]
```

Closures capture *variables*, not *values*. The wrong version captures one
shared variable `i`; by the time the lambdas are called, `i` is `2`. The fix
forces a value copy at lambda-creation time by exploiting default argument
evaluation.



### Key Discussion Points

#### Lexical Scoping

Python (and most modern languages) uses *lexical scoping*: the environment a
function captures is determined by where the function is *written* in the
source, not where it is called. This makes closures predictable--you can
read the source and know exactly what is captured.

Dynamic scoping, the alternative, captures the environment at the call site.
It is almost universally rejected for general-purpose languages because it
makes program behavior depend on the call stack at runtime, which is much
harder to reason about.

#### Environment Capture

What exactly is captured? In CPython, each closure cell holds a reference to
the variable's cell object, not a copy of its value at the moment of capture.
That is why the loop gotcha happens: all lambdas share one cell, and the cell
holds the last value the loop assigned to `i`.

Understanding this distinction--reference to a cell vs. copy of a value --
is essential when closures interact with mutation.

#### Lifetime Extension

A local variable normally lives on the stack frame that created it. When the
function returns, the frame is gone. A closure keeps a reference to the
captured variable, which forces the runtime to allocate it on the heap (in
CPython, via a cell object) rather than on the stack. The variable's lifetime
is extended to at least as long as the closure lives.

This is automatic in Python. In C it is the programmer's responsibility.



### Under the Hood: C

C has no lexical environment capture. A function pointer carries only an
address--no data. To simulate a closure in C, you bundle the function
pointer and its captured data into a struct.

#### The Closure Pair

```c
typedef int (*fn_with_ctx)(void *ctx, int x);

typedef struct {
    fn_with_ctx fn;
    void       *ctx;
} closure;
```

A `closure` is a pair: the code to run, and the environment it runs in.
Calling it looks like:

```c
int call(closure c, int x) {
    return c.fn(c.ctx, x);
}
```

#### Simulating make_adder

```c
typedef struct { int n; } adder_ctx;

int adder_fn(void *ctx, int x) {
    adder_ctx *c = (adder_ctx *)ctx;
    return x + c->n;
}

closure make_adder(adder_ctx *c, int n) {
    c->n = n;
    return (closure){ adder_fn, c };
}
```

The caller must provide storage for `adder_ctx`. Two independent closures
require two separate context structs--they cannot share one.

#### Heap Allocation and Lifetime

In Python, the runtime allocates cell objects on the heap automatically. In C,
you decide where the context lives:

- Stack: simple, but the closure must not outlive the enclosing function.
- Heap (`malloc`): flexible, but you own the lifetime and must `free` it.

Failing to match allocation to lifetime is a classic C bug: returning a closure
whose context is a local struct, then calling it after the stack frame is gone,
produces undefined behavior.

#### Mutable State in a C Closure

A mutable counter stored in a context struct:

```c
typedef struct { int count; } counter_ctx;

int increment_fn(void *ctx, int x) {
    (void)x;
    counter_ctx *c = (counter_ctx *)ctx;
    c->count += 1;
    return c->count;
}
```

Both the mutation and the shared state are explicit in the struct. Nothing is
hidden. This is more verbose but also more transparent: the entire environment
is visible in the type definition.

#### Why GC Languages Simplify This

A garbage-collected language can allocate the environment on the heap and keep
it alive as long as any closure references it, without the programmer tracking
lifetimes. The code that creates the closure does not need to know how long the
closure will live. In C, that information must be known at the call site.

This is one of the most concrete costs of manual memory management: closures
are possible, but their lifetime contract must be explicit and correct.



### Cost Model

A C closure call goes through two levels of indirection:

1. Load the context pointer from the struct.
2. Load the function pointer from the struct, then call through it.

Compare to a direct call, which is one instruction. The overhead is small in
absolute terms but significant in tight loops. Python closures add further
cost: cell-object lookup, reference counting, and frame allocation per call.

The pattern is consistent with the rest of the series: each additional level
of abstraction--from direct call, to function pointer, to closure pair --
adds one more load and one more level of indirection.



### Concurrency Link

A closure that captures only immutable values is thread-safe by construction.
Multiple threads can call the same closure simultaneously without locking,
because there is nothing to mutate.

A closure that captures mutable state is *not* thread-safe unless access is
synchronized. Two threads calling `increment` on the same counter context will
race on `count`. The closure makes the shared state explicit in the struct, but
it does not protect it.

The safe pattern is: closures capture immutable configuration; mutable shared
state is pushed outward to an explicitly synchronized boundary.

This connects directly to the discussion of data races in the low-level
chapters: the race is on the *environment*, not on the function itself.



*Next: [3. Immutability](../immutability/README.md)--what it means for data to
never change, and why that simplifies reasoning about concurrent programs.*
