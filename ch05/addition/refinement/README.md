
## Introduction to Refinement Types

Refinement types are a way to make type systems more precise by
attaching logical predicates to base types. Instead of just saying
"this is an integer," you can say "this is an integer between 1 and 10"
or "this is a non-empty list."

The basic idea is:

*{x: T | P(x)}*

This reads as: "values x of type T such that predicate P(x) holds"
(see [THEORY.md](./THEORY.md)).

For example:
- `{n: int | n > 0}` - positive integers
- `{s: string | len(s) > 0}` - non-empty strings
- `{arr: list | len(arr) == 10}` - lists of exactly length 10

### Why Refinement Types Matter

They catch bugs at compile time that normal type systems miss:
- Division by zero (require non-zero divisor)
- Array bounds errors (require index < length)
- Invalid states (require valid state transitions)

Languages like Liquid Haskell and F* have built-in refinement type systems.
In languages without native support, we can simulate them at runtime.

### Python Implementation

Here's a practical implementation using decorators and runtime checks:

```python
from typing import TypeVar, Callable, Any
from functools import wraps

T = TypeVar('T')

class RefinementError(TypeError):
    """Raised when a refinement type constraint is violated"""
    pass

class Refined:
    """A refinement type wrapper"""
    def __init__(self, base_type: type, predicate: Callable[[Any], bool], 
                 description: str = ""):
        self.base_type = base_type
        self.predicate = predicate
        self.description = description
    
    def check(self, value: Any) -> Any:
        """Validate that value satisfies the refinement"""
        if not isinstance(value, self.base_type):
            raise RefinementError(
                f"Expected {self.base_type.__name__}, got {type(value).__name__}"
            )
        if not self.predicate(value):
            desc = self.description or "predicate"
            raise RefinementError(
                f"Value {value} does not satisfy {desc}"
            )
        return value
    
    def __repr__(self):
        desc = self.description or "custom predicate"
        return f"{{x: {self.base_type.__name__} | {desc}}}"

## Common refinement types
Positive = Refined(int, lambda x: x > 0, "x > 0")
NonZero = Refined(int, lambda x: x != 0, "x != 0")
NonEmpty = Refined(str, lambda x: len(x) > 0, "len(x) > 0")
Percentage = Refined(float, lambda x: 0 <= x <= 100, "0 <= x <= 100")

def refined(*param_refinements, return_refinement=None):
    """Decorator to add refinement type checking to functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ## Check parameters
            for i, (arg, refinement) in enumerate(zip(args, param_refinements)):
                if refinement is not None:
                    try:
                        refinement.check(arg)
                    except RefinementError as e:
                        raise RefinementError(
                            f"Parameter {i} of {func.__name__}: {e}"
                        )
            
            ## Call function
            result = func(*args, *kwargs)
            
            ## Check return value
            if return_refinement is not None:
                try:
                    return_refinement.check(result)
                except RefinementError as e:
                    raise RefinementError(
                        f"Return value of {func.__name__}: {e}"
                    )
            
            return result
        return wrapper
    return decorator

## Example usage
@refined(Positive, NonZero, return_refinement=Positive)
def safe_divide(numerator: int, denominator: int) -> int:
    """Divide two positive integers, denominator must be non-zero"""
    return numerator // denominator

@refined(NonEmpty, return_refinement=Positive)
def string_length(s: str) -> int:
    """Get length of non-empty string"""
    return len(s)

## Demonstration
if __name__ == "__main__":
    print("Testing refinement types...")
    
    ## Valid calls
    print(f"safe_divide(10, 2) = {safe_divide(10, 2)}")
    print(f"string_length('hello') = {string_length('hello')}")
    
    ## Invalid calls - these will raise RefinementError
    try:
        safe_divide(10, 0)  ## Violates NonZero
    except RefinementError as e:
        print(f"Error: {e}")
    
    try:
        safe_divide(-5, 2)  ## Violates Positive
    except RefinementError as e:
        print(f"Error: {e}")
    
    try:
        string_length("")  ## Violates NonEmpty
    except RefinementError as e:
        print(f"Error: {e}")
```

### C Implementation

C doesn't have runtime type introspection, so we use macros and assertions:

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <assert.h>
#include <string.h>

// Refinement type checking macros
#define REFINE_CHECK(condition, message) \
    do { \
        if (!(condition)) { \
            fprintf(stderr, "Refinement error: %s\n", message); \
            fprintf(stderr, "  at %s:%d in %s\n", __FILE__, __LINE__, __func__); \
            abort(); \
        } \
    } while(0)

// Common refinement predicates
#define IS_POSITIVE(x) ((x) > 0)
#define IS_NON_ZERO(x) ((x) != 0)
#define IS_IN_RANGE(x, min, max) ((x) >= (min) && (x) <= (max))
#define IS_NON_NULL(x) ((x) != NULL)
#define IS_NON_EMPTY(s) (IS_NON_NULL(s) && strlen(s) > 0)

// Type definitions with refinements encoded in names
typedef int positive_int;    // {x: int | x > 0}
typedef int non_zero_int;    // {x: int | x != 0}
typedef char* non_empty_str; // {s: string | len(s) > 0}

// Constructor functions that enforce refinements
positive_int make_positive(int value) {
    REFINE_CHECK(IS_POSITIVE(value), "Expected positive integer");
    return value;
}

non_zero_int make_non_zero(int value) {
    REFINE_CHECK(IS_NON_ZERO(value), "Expected non-zero integer");
    return value;
}

non_empty_str make_non_empty_str(char* str) {
    REFINE_CHECK(IS_NON_EMPTY(str), "Expected non-empty string");
    return str;
}

// Functions using refinement types
positive_int safe_divide(positive_int numerator, non_zero_int denominator) {
    // Refinements checked by caller through constructors
    // But we can add runtime assertions for extra safety
    REFINE_CHECK(IS_POSITIVE(numerator), "Numerator must be positive");
    REFINE_CHECK(IS_NON_ZERO(denominator), "Denominator must be non-zero");
    
    int result = numerator / denominator;
    
    // Post-condition: result should be non-negative for positive inputs
    REFINE_CHECK(result >= 0, "Result should be non-negative");
    
    return result;
}

size_t string_length(non_empty_str str) {
    REFINE_CHECK(IS_NON_EMPTY(str), "String must be non-empty");
    size_t len = strlen(str);
    REFINE_CHECK(len > 0, "Length must be positive");
    return len;
}

// Array bounds checking with refinement types
typedef struct {
    int* data;
    size_t length;
} array;

int array_get(array* arr, size_t index) {
    REFINE_CHECK(IS_NON_NULL(arr), "Array must not be null");
    REFINE_CHECK(IS_NON_NULL(arr->data), "Array data must not be null");
    REFINE_CHECK(index < arr->length, "Index out of bounds");
    return arr->data[index];
}

void array_set(array* arr, size_t index, int value) {
    REFINE_CHECK(IS_NON_NULL(arr), "Array must not be null");
    REFINE_CHECK(IS_NON_NULL(arr->data), "Array data must not be null");
    REFINE_CHECK(index < arr->length, "Index out of bounds");
    arr->data[index] = value;
}

// Example with percentage type
typedef float percentage; // {x: float | 0 <= x <= 100}

percentage make_percentage(float value) {
    REFINE_CHECK(IS_IN_RANGE(value, 0.0f, 100.0f), 
                 "Percentage must be between 0 and 100");
    return value;
}

void print_progress(percentage pct) {
    REFINE_CHECK(IS_IN_RANGE(pct, 0.0f, 100.0f), 
                 "Percentage must be between 0 and 100");
    printf("Progress: %.1f%%\n", pct);
}

int main() {
    printf("Testing refinement types in C...\n\n");
    
    // Valid operations
    positive_int a = make_positive(10);
    non_zero_int b = make_non_zero(2);
    printf("safe_divide(%d, %d) = %d\n", a, b, safe_divide(a, b));
    
    non_empty_str str = make_non_empty_str("hello");
    printf("string_length(\"%s\") = %zu\n", str, string_length(str));
    
    percentage pct = make_percentage(75.5);
    print_progress(pct);
    
    // Array example
    int data[] = {1, 2, 3, 4, 5};
    array arr = {data, 5};
    printf("array_get(arr, 2) = %d\n", array_get(&arr, 2));
    
    printf("\nTesting invalid operations...\n");
    
    // Uncomment to test error cases:
    // make_positive(-5);           // Will abort: not positive
    // make_non_zero(0);            // Will abort: is zero
    // make_non_empty_str("");      // Will abort: empty string
    // make_percentage(150.0);      // Will abort: out of range
    // array_get(&arr, 10);         // Will abort: out of bounds
    
    printf("All valid operations completed successfully!\n");
    
    return 0;
}
```

### Differences

*Python approach:*
- Runtime checking with exceptions
- Decorator-based for clean syntax
- Type hints for documentation
- Graceful error handling

*C approach:*
- Compile-time documentation via typedefs
- Runtime checking via macros and assertions
- Aborts on violation (no exception handling)
- More verbose but explicit

Both *simulate* refinement types, but true refinement type systems
(like in Liquid Haskell) prove correctness at compile time using
SMT solvers, eliminating runtime overhead.

