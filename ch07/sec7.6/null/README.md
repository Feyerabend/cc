
## The Null Pattern or All About Nothing

__The Core Problem__

Every type system faces an uncomfortable question:
*what value does a variable hold when it holds "nothing"?*

Tony Hoare, who invented the null reference in 1965, later
called it his "billion-dollar mistake". Not because the
concept is wrong, but because most languages implement
it in a way that silently infects every type.

The fundamental issue is *implicit nullability*. When a `String`
in Java might secretly be `null`, you don't have a `String`--you
have a `String | null` with no compiler enforcement telling 
you which one you're dealing with at any given moment.



### Two Different Solutions to "Nothing"

Before going further, it is important to separate
two ideas that are often conflated:
1. *Absence-as-Type* (`Option`, `Maybe`, `Optional`)
2. *Absence-as-Object* (Null Object pattern)

They solve different problems.

* `Option<T>` forces the caller to *handle* absence.
* `Null Object` removes the need to branch by making
  absence behave like a valid value.

One increases explicitness. The other increases behavioral continuity.

They are not interchangeable--and the tradeoffs matter.



### Absence as a Type: Option / Maybe

The *good* version of the null pattern is a *typed container for optionality*--you
force the programmer to explicitly acknowledge that a value might
be absent before they can use it.

The absence of a value becomes part of the type signature, not a hidden landmine.

The pattern goes by many names: `Option`, `Maybe`, `Optional`, `Nullable<T>`.
They all say the same thing:

*This value is either Something or Nothing, and you must handle both cases.*

This is how modern type systems try to make illegal states unrepresentable.



### Language by Language

#### Haskell - the gold standard

```haskell
data Maybe a = Nothing | Just a

safeDivide :: Int -> Int -> Maybe Int
safeDivide _ 0 = Nothing
safeDivide x y = Just (x `div` y)

case safeDivide 10 2 of
  Nothing -> "Can't divide"
  Just n  -> "Result: " ++ show n
```

`Maybe` is baked into the type system. There's no way to get the inner
value without acknowledging `Nothing`.

Chaining is clean via `>>=` (bind), so `Nothing` propagates automatically
through a chain of operations without explicit checks.



#### Rust - null does not exist

```rust
fn find_user(id: u32) -> Option<User> {
    // ...
}

match find_user(42) {
    Some(user) => println!("{}", user.name),
    None       => println!("Not found"),
}

let user = find_user(42)?;
```

Rust has no `null`. `Option<T>` is the only way to express absence.

The `?` operator makes propagation terse without hiding it.



#### Java - a retrofit

```java
Optional<String> name = Optional.ofNullable(getName());

name.map(String::toUpperCase)
    .ifPresent(System.out::println);
```

Java's `Optional` is opt-in. The underlying `null` still exists everywhere.

You can call `.get()` on an empty `Optional` and get a runtime exception.
It is a convention, not a guarantee.



#### Kotlin - nullability in the type system

```kotlin
var name: String? = null
var name: String  = "hi"

name?.length
name ?: "default"
name!!.length
```

Kotlin encodes nullability directly in the type (`String` vs `String?`).

It is pragmatic rather than pure, but it closes most of
the holes that Java leaves open.



#### TypeScript - structural but leaky

```typescript
function find(id: number): User | undefined { ... }

const user = find(42);

if (user) {
  user.name;
}
```

With `strictNullChecks`, `null` and `undefined` become explicit types.

But safety stops at runtime boundaries - APIs, `JSON.parse`, poorly typed libraries.



#### JavaScript - two nothings

JavaScript has both `null` and `undefined`.

They are conceptually distinct but practically inconsistent.

```javascript
typeof null        // "object"
typeof undefined   // "undefined"

null == undefined  // true
null === undefined // false
```

Without TypeScript strict mode, absence is entirely discipline-driven.



### The Deeper Lesson

The core idea behind `Option`-style solutions is:

*Make illegal states unrepresentable.*

A function returning `Maybe<User>` is honest.
A function returning `User` but sometimes giving `null` is lying.

Typed optionality preserves information:
* `Some(value)`
* `None`

The absence is explicit and cannot be ignored.



### C's Sentinel Problem

Before exploring how C handles absence, it helps to see *why* the baseline
is fragile. The standard library uses at least four different sentinel
conventions, with no unified rule:

| Function          | Sentinel on failure | Ambiguity                                         |
|-------------------|---------------------|---------------------------------------------------|
| `fopen`           | `NULL`              | None - pointer identity is unambiguous            |
| `strcmp("a","a")` | `0` means *equal*   | `0` is not failure here; it is success            |
| `atoi("bad")`     | `0`                 | Indistinguishable from `atoi("0")`                |
| `getchar()` at EOF| `-1` (`EOF`)        | Requires cast to `unsigned char` before comparing |

```c
int n = atoi(user_input);
/* "0" and "bad" both produce 0.
   There is no way to distinguish them without reparsing the string. */
```

Each function documents its own convention. The compiler enforces none of them.
This is the practical consequence of having no type-level representation of absence:
the distinction between *zero as a valid value* and *zero as a failure signal*
is invisible to the type system and has to be reconstructed by the programmer
at every call site.



### Absence as an Object: Null Object in C

Now we pivot.

In C, we cannot encode optionality in the type system. There is no `Option<T>`.
The traditional approach is to return `NULL` and require callers to check it.

```c
void* mem_malloc(size_t size) {
    return NULL;
}

void mem_free(void* ptr) {
    if (ptr == NULL)
        return;
}
```

This spreads defensive checks everywhere.

The Null Object pattern attempts a different solution:

Instead of returning `NULL`, return a valid object whose behaviour is neutral.

This is not absence-as-type.
This is absence-as-behaviour.



#### Structural Changes

1. Extend `BlockHeader` with `is_null_object`
2. Introduce a global singleton null block
3. Provide `is_null_object()` for detection

Clients must not rely on pointer identity directly.
The abstraction boundary should be:

```c
if (is_null_object(ptr)) {
    // handle if necessary
}
```

This avoids leaking implementation details.



#### Behavioral Changes

* `mem_malloc` returns null object instead of `NULL`
* `mem_free` becomes a no-op for null object
* `mem_realloc` treats null object as fresh allocation
* `machine_store` ignores writes
* `machine_load` returns 0



### A Critical Semantic Tradeoff

Returning 0 from `machine_load` introduces a major shift.

"Out of memory" becomes indistinguishable from "Memory contains zero."

Information is erased.

In type-theoretic terms:
* `Maybe<int>` preserves failure information
* Null Object collapses failure into default behaviour

This is not inherently wrong--but it is a deliberate loss of semantic precision.



#### A Concrete Failure: The Silent Logger

The same tradeoff appears at higher abstraction levels, and the cost
is easier to see in Python.

A common application of Null Object is a no-op logger used when the caller
wants to suppress output - in tests, for example:

```python
class NullLogger:
    def log(self, msg):
        pass          # deliberate no-op

class RealLogger:
    def log(self, msg):
        print(msg)

def transfer(amount, logger=NullLogger()):
    try:
        result = execute_transfer(amount)
        logger.log(f"Transfer OK: {result}")
        return result
    except Exception as e:
        logger.log(f"Transfer FAILED: {e}")   # swallowed silently
        return None                            # caller receives None, not a reason
```

In tests, `NullLogger` suppresses noise. In production with a misconfigured
default, the exception is caught, handed to the null logger, and discarded.
The caller receives `None` with no indication of what failed.

Compare with making absence explicit at the type boundary:

```python
class TransferError(Exception):
    pass

def transfer(amount) -> int:
    try:
        return execute_transfer(amount)
    except Exception as e:
        raise TransferError(f"Failed: {e}") from e
```

There is no longer a logger to absorb the failure. The error propagates
and must be handled by the caller, which now knows *why* it failed and
can choose its own policy: retry, alert, rollback.

The Null Object removed the `if result is None:` checks at call sites.
But it also removed the information that those checks were supposed to act on.



#### When This Pattern Makes Sense

Appropriate:
* Logging subsystems
* Metrics collection
* Caches
* Optional instrumentation

Dangerous:
* Transaction engines
* Filesystem metadata
* Cryptographic buffers
* Systems where allocation failure is catastrophic

If allocation failure is unrecoverable, silent degradation
may hide fatal conditions.

You traded segmentation faults for behavioral continuity.
That trade is sometimes elegant, sometimes reckless.



#### Sentinel vs NULL vs Null Object

C already uses related techniques:
* Sentinel nodes in linked lists
* Dummy head nodes
* Error codes

Comparison:
* `NULL` - explicit absence, requires branching
* Sentinel - structural simplification inside a data structure
* Null Object - behavioral simplification across an interface

The Null Object generalises the sentinel idea to an entire
abstraction boundary.



#### Alternative: Explicit Error Propagation in C

Another approach is to return error codes alongside pointers:

```c
int mem_malloc(size_t size, void** out_ptr);
```

This preserves failure information explicitly.

Compared to Null Object:
* Explicit error propagation increases verbosity
* Null Object reduces branching but may hide failure

Again: clarity vs continuity.



### Conclusion

In typed languages, absence is encoded into the type.
In this C implementation, absence is encoded into behaviour.

One makes illegal states unrepresentable.
The other makes illegal states survivable.

The Null Object pattern in C can make systems more robust by
eliminating null dereferences and centralising failure handling.

But it does so by collapsing failure into neutral behavior.

Whether that is an improvement depends entirely on the semantic
weight of failure in your system.

That is the real design decision hiding underneath the pattern.

