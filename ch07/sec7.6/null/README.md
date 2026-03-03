
## Null Object

The [code](./../../../ch02/mem/mem.c) from chapter 2 implements a simple memory management
system in C with the following components:

1. *Memory Pool*: A fixed-size array (`memory_pool`) that serves as the memory resource.

2. *Block Header*: A structure that tracks memory allocation metadata (size, free status,
   next block).

3. *Free List*: A linked list tracking available memory blocks.

4. *Memory Operations*: Functions for allocation (`mem_malloc`), deallocation (`mem_free`),
   and reallocation (`mem_realloc`).

5. *Machine Interface*: A higher-level abstraction providing memory management services.

In the original implementation, failed memory allocations return `NULL`, requiring explicit
null checks throughout the codebase:

```c
// original mem_malloc returns NULL on failure
void* mem_malloc(size_t size) {
    // ..
    return NULL; // when allocation fails
}

// original mem_free requires NULL check
void mem_free(void* ptr) {
    if (ptr == NULL)
        return;
    // ..
}
```

This approach follows standard C programming practices but introduces several issues:
- Functions must include defensive NULL checks
- Missing NULL checks can lead to segmentation faults
- Error handling becomes scattered throughout the codebase


## Null Object Pattern Implementation

The refactored code implements the `Null Object` pattern to address these issues.
Despite C *not* being an object-oriented language, the pattern can be adapted effectively.
That is, the pattern is *usually* used in object-orientation.


### New Structural Changes

1. *Extended Block Header*
   - Added an `is_null_object` flag to the `BlockHeader` structure to identify null objects
   - This flag distinguishes between regular memory blocks and the special null object

2. *Null Object Singleton*
   - Created a global singleton null object (`null_block_header` and `null_block`)
   - The null object represents failed allocations or empty memory
   - It serves as a safe placeholder that responds to operations with neutral behavior

3. *Type Checking*
   - Added an `is_null_object()` function to safely identify null object references
   - This function handles both the null object and regular pointers correctly


### Behavioral Changes

1. *Memory Allocation*
   - Modified `mem_malloc` to return the null object instead of `NULL` when allocation fails
   - This ensures all functions receive a valid object even after failed allocations

2. *Memory Operations*
   - `mem_free`: No-operation when given the null object
   - `mem_realloc`: Treats the null object as an empty block, effectively converting to `mem_malloc`
   - `machine_store`: Safely ignores store operations on the null object
   - `machine_load`: Returns 0 when attempting to read from the null object

3. *Error Reporting*
   - Added verbose messaging when operations involve the null object
   - This provides clearer feedback about failed allocations


### Test Cases

The implementation adds specific test cases demonstrating the null object's behaviour:
- Attempting allocations beyond memory capacity
- Performing operations on the null object
- Reallocating from a null object
- Freeing a null object


### Pros

1. *Robustness*
   - Eliminates null pointer dereferences
   - All functions can safely operate on any memory pointer
   - Reduces the risk of segmentation faults

2. *Simplified Code*
   - Centralises null handling logic
   - Removes scattered conditional null checks
   - Makes client code cleaner and more focused on business logic

3. *Better Error Handling*
   - Failed operations become no-ops instead of potential crashes
   - Provides consistent behaviour for error conditions
   - Creates clear indication when allocation fails through console messages

4. *Design Pattern in C*
   - Demonstrates how object-oriented design patterns can be adapted to C
   - Shows how structural changes can improve code quality even in procedural languages


### Cons

1. *Memory Overhead*
   - The null object consumes a small amount of memory
   - Extra flag in every block header slightly increases memory usage

2. *Performance Impact*
   - Additional type checking adds minor computational overhead
   - Extra conditional logic in each function

3. *Debugging Challenges*
   - Silent failures may mask bugs in some cases
   - Error conditions don't immediately halt execution

4. *C Language Constraints*
   - Implementation is more verbose than in true OO languages
   - Pattern must be explicitly maintained rather than enforced by language


### In Practice

This output demonstrates how the Null Object pattern works in practice:

```shell
-- Testing Null Object Pattern --
Failed to allocate 2048 bytes, using null object
Attempted to store value 100 at null object (no-op)
Attempted to load from null object, returning 0
Loaded value from null object: 0
Reallocated from null object to 0x1006d4420, new size: 10 bytes
Attempted to free null object (no-op)
```

- When trying to allocate more memory than available (2048 bytes when the
  pool is only 1024 bytes), the code returns the null object instead of NULL
  and reports the failure.

- When attempting to store the value 100 to this null object, the operation
  becomes a no-op (no operation) rather than causing a segmentation fault.

- Similarly, when loading from the null object, it safely returns 0 rather than crashing.

- When reallocating the null object with a size of 10 bytes, it successfully
  converts this into a regular allocation (effectively treating it as a malloc
  call), demonstrating how the null object can smoothly transition to a real object.

- Finally, attempting to free the null object is also handled safely as a no-op.

This output confirms that the `Null Object` pattern implementation is working correctly,
providing graceful degradation instead of crashes when operations fail. It makes the
code more robust while maintaining a clean interface that doesn't require constant NULL
checking throughout the codebase.


### Conclusion

The `Null Object` pattern implementation successfully transforms a traditional C memory
allocator into a more robust system with better error handling. By replacing `NULL`
returns with a special null object that implements neutral behaviours, the code becomes
more resilient against common memory-related errors while maintaining the original
functionality.

This implementation demonstrates how object-oriented design patterns can be effectively
adapted to procedural languages like C, bringing their benefits even when the language
doesn't directly support object-oriented constructs.
