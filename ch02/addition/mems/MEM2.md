
## Project

*Explore memory in relation to application or a e.g. VM. Make a simple garbage
collector, and handle memory with some functions for memory management. Explore
how a second memeory may expand the primary, and how virtual memory can function.*

*Prerequisties: Familiary with garbage collectors function in general, how
virtual memory works in principal, and how memory management works.*


### Code

The provided code simulates a simple memory management system and a basic virtual
machine (VM) with an object model.

1. *Memory Allocator:*
   - It manages a fixed pool of memory (`memory_pool`), implemented using a simple *free list* strategy.
   - Blocks of memory are allocated and freed dynamically using `mem_malloc()` and `mem_free()`, respectively.
   - If a block is larger than requested, the `split_block()` function splits it into a smaller block,
     and merging adjacent free blocks is handled by `merge_free_blocks()`.

2. *Virtual Machine (VM):*
   - The `SimpleVM` struct manages an array of object references. These objects can be of different types:
     integers, floats, or strings.
   - Objects are allocated using `mem_malloc()` and added to the VM with the `simple_vm_add()` function.
     The VM can display its contents with `simple_vm_display()` and delete objects using `simple_vm_delete()`.
   - The VM has a basic object model (`IntObject`, `FloatObject`, `StringObject`), allowing for different
     types of objects to be stored and managed.

3. *Object Management:*
   - Each object has a base type (`INT_OBJECT`, `FLOAT_OBJECT`, `STRING_OBJECT`) to allow the VM to interpret
     and manage different data types.
   - Memory is allocated for objects (e.g., `IntObject`, `FloatObject`) and strings are duplicated in memory
     with `strdup()` to ensure they are properly managed.


### Memory management in Virtual Machines

In virtual machines (VMs), memory management plays a crucial role in ensuring efficient resource usage
and application stability.

1. *Manual memory management:*
   - This is seen in the provided code. The VM manually allocates and frees memory as needed using a
     simple allocator. Objects are allocated with `mem_malloc()` and released with `mem_free()`.
   - Memory fragmentation can occur, and merging adjacent free blocks helps mitigate it.

2. *Garbage Collection (GC):*
   - VMs often use garbage collection to automatically manage memory, which eliminates the need for
     explicit `mem_free()` calls.
   - A garbage collector can automatically reclaim unused memory by detecting objects that are no
     longer referenced by the program.


### Extending the code with a garbage collector

It is possible to extend this VM with a *garbage collector* (GC) at the VM level. This could replace
or work alongside the manual `mem_free()` calls to automatically reclaim memory. A garbage collector
would track which objects are still in use and free those that are not.


### General principles for implementing a garbage collector

1. *Reference counting:*
   A simple form of GC where each object keeps track of how many references point to it. When the
   reference count drops to zero, the object is deallocated.

   - *Implementation:*
     - Add a reference count field to the `Object` struct.
     - Increment the reference count when a new reference to the object is created.
     - Decrement the reference count when a reference is removed. If it reaches zero, free the object.

   *Advantages:*
   - Simple to implement.
   
   *Disadvantages:*
   - Cannot detect cyclic references (e.g., two objects referencing each other but no other objects reference them).

2. *Mark-and-sweep:*
   This is a two-phase algorithm where the VM "marks" all objects that are reachable (i.e., still in use)
   and then "sweeps" through the memory, freeing objects that were not marked.

   - *Implementation:*
     - The VM would traverse all known references (like the array in `SimpleVM`) and mark each object as "in use."
     - Any object not marked after a traversal would be swept and its memory reclaimed.
     - The `Object` struct would need a flag (e.g., `is_marked`) to track whether the object is reachable.

   *Advantages:*
   - Can handle cyclic references.

   *Disadvantages:*
   - The GC process (marking and sweeping) might pause the program, affecting performance.

3. *Generational Garbage Collection:*
   This type of GC is based on the observation that most objects are short-lived. It divides objects into "young"
   and "old" generations and collects younger objects more frequently.

   - *Implementation:*
     - Objects are initially allocated in a young generation and, if they survive several GCs, are promoted to an old generation.
     - The young generation is collected more often since most objects die quickly.

   *Advantages:*
   - Efficient in environments where most objects are short-lived.

   *Disadvantages:*
   - More complex to implement.


### How it might be implemented in the code

1. *Tracking roots:*
   - The GC needs to start from known roots, i.e., objects that are actively being used.
     In this case, the `SimpleVM` array serves as a root, holding references to active objects.
   - The GC can mark all objects directly or indirectly reachable from this array as "in use."

2. *Marking objects:*
   - Each object would need a new field, such as `is_marked`. During the "mark" phase, the GC
     would traverse all objects starting from the VM's root (the `SimpleVM` array) and mark objects as reachable.

3. *Sweeping:*
   - After marking, the GC would traverse the memory (i.e., the free list) and deallocate any object that wasn't marked.
   - Objects could be freed using the `mem_free()` function once they're identified as unreachable.

4. *Handling cyclic references:*
   - A mark-and-sweep collector would automatically handle cyclic references, as all unreachable
     objects (even if part of a cycle) would be freed during the sweep phase.


### Conclusion

The code can be extended with a garbage collector at the VM level, either by implementing
reference counting or a more sophisticated mark-and-sweep algorithm. This would improve memory
management by automating the freeing of unused objects and reducing the risk of memory leaks.
However, the specific GC strategy depends on the application's needs, with trade-offs between
simplicity, performance, and the ability to handle cyclic references.
