
## MEM3

This program simulates a *custom memory allocator* and a simple virtual machine that uses it,
showcasing fundamental principles of memory management, dynamic allocation, and defragmentation.
The allocator manages a memory pool in which it allocates memory in variable-sized chunks,
dynamically assigned to different data structures such as integer blocks, floating-point blocks,
and strings. When blocks are freed, the allocator employs a defragmentation process to merge
adjacent free memory spaces, thus minimizing fragmentation and optimizing memory reuse.

Memory management in low-level systems like embedded devices or virtual machines requires efficient
handling of limited resources. A significant challenge here is fragmentation, where free memory
is divided into small, non-contiguous blocks that cannot satisfy larger allocation requests. This
program demonstrates a strategy for managing dynamic memory allocations in a constrained environment,
including defragmentation techniques to optimize space usage.

The program is composed of two main components:

1.	*Memory allocator*: Handles allocation, freeing, and defragmentation of memory blocks within
    a fixed memory pool. Memory allocations are tracked within a simple header structure, which
    records each block's size and occupancy status. When blocks are freed, the allocator scans
    the memory pool for adjacent free blocks and merges them to create larger, contiguous spaces.

2.	*Virtual Machine*: Uses the memory allocator to manage memory dynamically as needed for different
    data types. Rather than directly storing raw integers or strings, the VM references blocks that
    represent different object types (integers, floats, and strings), allowing for varied data and
    emulating object-oriented storage within the memory pool.


### Benefits of defragmentation

*Defragmentation* provides several critical benefits for memory-constrained systems:

- *Increased usable memory*: By merging adjacent free blocks, the allocator reduces fragmentation,
  allowing more significant allocations that would otherwise fail in a fragmented space.

- *Enhanced performance*: Consolidating free memory blocks reduces the time needed to find space
  for new allocations, as the memory pool contains larger contiguous regions, which can be
  efficiently allocated.

- *Improved predictability*: Defragmentation provides a more stable and predictable memory landscape,
  essential for applications where memory allocation failures could impact reliability and performance.

In an embedded context, this defragmentation approach simulates the operation of a basic memory
management unit (MMU), teaching core concepts of heap management, dynamic memory allocation, and
fragmentation handling. This design ensures that even in constrained environments, memory can be
efficiently reused, reducing the need for constant memory expansion or reallocations.


### Conclusion

This program provides an efficient and practical illustration of managing memory dynamically in
a simple virtual machine, complete with defragmentation. By handling references to objects, it
achieves the flexibility needed for varied data types and minimizes fragmentation, making it an
ideal foundational approach for low-level memory management systems.
