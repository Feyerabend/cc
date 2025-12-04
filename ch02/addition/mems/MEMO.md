
## MEMO overview

Imagine we are simulating a simple object-oriented system using this memory pool. We'll create objects
like `Person` and `Computer`, which are dynamically allocated in the pool. Each object has multiple
fields (such as strings or integers), and these objects may share memory (i.e., reference the same
memory block).


We will simulate:

1. Allocating memory for different types of objects (e.g. Person, Computer).
2. Retaining and releasing references (e.g. sharing memory between objects).
3. Automatically freeing memory when it's no longer in use.


### Breakdown of code

1. Memory pool initialisation:
- The memory pool is initialised, and each block is marked as free, with a reference count of zero.
- The `memory_pool_init()` function prepares the pool and links all blocks into a free list.

2. Automatic allocation and deallocation:
- `create_person()` and `create_car()` simulate allocating memory for objects such as Person and Computer.
   Each time memory is allocated from the pool, the reference count starts at 1.
- `pool_retain()` and `pool_release()` manage the reference count for each object. If an object is *shared*,
  `pool_retain()` is called to increase the reference count. When an object
  is no longer needed, `pool_release()` decrements the count. If the count reaches zero, the memory is freed.

3. Sharing memory (retaining references):
- In the example, we simulate sharing memory by retaining references to alice and zx81. Their reference counts
  are incremented by calling `pool_retain()`.
- The memory is only freed when the reference count drops to zero, ensuring that objects are only deallocated
  when no part of the program is using them.

4. Real use:
- The scenario simulates creating two types of objects (Person and Computer), retaining references to them,
  and releasing them when no longer needed.
- By using reference counting, memory is managed automatically, and we don't need to explicitly call `free()`
  to deallocate objects. This is useful in real-world scenarios where objects are shared between different parts of the program.


### Advantages

- Automatic deallocation: Memory is automatically returned to the pool when no longer used, reducing the risk of memory leaks.
- Efficient reuse: Freed memory is returned to the pool and can be reused for other objects.
- Reference c: This simple form of garbage collection allows shared objects to be safely deallocated only when they are no longer referenced.

