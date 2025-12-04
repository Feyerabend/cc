
## POOL

Pooling is a memory management technique that pre-allocates a fixed amount of memory to
reduce the overhead of frequent allocation and deallocation. In systems where memory is
frequently allocated and freed (like in embedded systems or real-time applications),
pooling allows you to reuse blocks of memory instead of constantly allocating new ones
 which can be costly in terms of performance.

In the context of the C code you provided, pooling could be implemented by pre-allocating
fixed-size blocks of memory and reusing them when needed.

#### Key ideas

	1.	Pre-allocation: At the start, a fixed amount of memory is allocated. This memory is
        split into equal-sized blocks that can be reused.
	2.	Fixed-size Blocks: Every allocation request is for a block of a specific size. If an
        allocation request exceeds the block size, another solution (like using multiple blocks) is needed.
	3.	Freeing Blocks: When memory is freed, the block is marked as available but not actually
        deallocated. It can be used again for future allocations.

In MEM, we are already managing a block-based system, but it allows dynamic resizing of blocks
(mem_realloc). With pooling, we simplify things by enforcing fixed block sizes and reusing the
memory without dynamic resizing.


#### How it works

1. Pre-allocation: We allocate a pool of memory (`memory_pool[MEMORY_POOL_SIZE]`), which is divided
   into fixed-size blocks (`BLOCK_SIZE`).
2. Fixed-size Allocation: `pool_malloc()` finds the first available block, marks it as allocated, and
   returns it. No resizing or dynamic allocation happens. Every allocation returns a fixed-size block.
3. Freeing and Reuse: When you free a block using `pool_free()`, it is marked as free and can be reused
   in the next allocation request. This reduces fragmentation and eliminates the overhead of repeatedly
   allocating and deallocating memory dynamically.


#### Benefits

- Efficiency: Since memory is pre-allocated, the cost of allocating and deallocating memory is low, making
  this approach suitable for performance-sensitive applications, embedded systems, or real-time systems.
- Reduced fragmentation: Blocks are reused, which limits fragmentation, unlike typical malloc-based memory
  management, where freed memory might not always be efficiently reused.
- Control: Pooling gives you fine-grained control over memory usage, which is important in systems with
  constrained resources (like microcontrollers or virtual machines).


#### Virtual Machine context:

- If you're simulating a VM or managing an embedded system, pooling can be a very efficient way to handle
  frequent memory allocations without suffering from the performance hit of using system-level memory allocators.
- In a virtual machine, memory management is crucial since you often have limited resources and need to ensure
  that memory is efficiently allocated and freed without frequent calls to the OS's memory allocator.
