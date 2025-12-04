
## MEM Overview

This program implements a simple *memory allocator* and a *machine simulation*
that manages memory allocations dynamically, similar to how `malloc`, `free`,
and `realloc` work in C. It demonstrates how memory blocks can be allocated, freed,
reallocated, and manipulated. The allocator uses a fixed-size memory pool and manages
free blocks using a linked list. The machine structure provides a higher-level
interface to perform memory allocations, store and retrieve values in allocated 
emory, and handle reallocation.


### Breakdown of the Code

1. *Memory allocator (`mem_malloc`, `mem_free`, `mem_realloc`)*
   - The memory allocator uses a *fixed memory pool* (`memory_pool`) of 1024 bytes.
   - Memory blocks are tracked by *block headers* (`BlockHeader`), which store the
     block size, whether the block is free, and a pointer to the next block in the free list.
   - The allocator supports basic functions:
     - `mem_malloc`: Allocates memory from the pool.
     - `mem_free`: Frees the memory and merges adjacent free blocks to avoid fragmentation.
     - `mem_realloc`: Changes the size of an allocated block by either reallocating it to 
        a larger/smaller block or leaving it if the size is already sufficient.

2. *Machine structure*
   - The `Machine` structure simulates a basic machine that manages memory dynamically.
   - The machine can allocate memory using `machine_alloc`, free it with `machine_free`,
     and reallocate with `machine_realloc`.
   - It also provides functions `machine_store` and `machine_load` to store and retrieve
     integers at specific offsets within a block, mimicking a basic "dynamic array."

3. *Sample*
   - The main function demonstrates the steps of using the machine to:
     - Allocate memory for an array of integers.
     - Store and retrieve values in the memory block.
     - Reallocate the block to expand it and add more values.
     - Modify specific values in the block.
     - Finally, free the allocated memory.

### Key operations

- *Memory allocation*: The allocator searches for free blocks that can accommodate the
  requested size. When found, the block is marked as used, and a pointer to the usable
  memory is returned.
- *Memory reallocation*: If a larger block is needed, the old data is copied to a new,
  larger block, and the old block is freed.
- *Memory deallocation*: Freed memory is merged with adjacent free blocks to reduce
  fragmentation and ensure efficient use of the memory pool.
  
### Example walkthrough

1. *Allocating memory*: A small block is allocated for three integers using `machine_alloc`.
   This is done by searching the free list for a block large enough to hold the requested size.
   
2. *Storing values*: The `machine_store` function is used to store integers at specific offsets
   within the allocated block. This simulates creating and filling a dynamic array.

3. *Reallocation*: The block is expanded using `machine_realloc`, which may involve copying
   the contents of the old block to a new larger one if necessary.

4. *Retrieving values*: The stored values are retrieved using `machine_load`, simulating array access.

5. *Modifying values*: The program demonstrates modifying a specific value in the block.

6. *Freeing memory*: The memory block is freed using `machine_free`, which marks it as
   free and merges it with adjacent free blocks if possible.


### Summary

This program is a basic simulation of a memory allocator and a machine that manages dynamic
memory. The allocator efficiently manages a fixed-size memory pool, allowing for allocation,
deallocation, and reallocation of memory blocks. The machine interface simplifies the process
of interacting with allocated memory by allowing storage and retrieval of values at specific
offsets within memory blocks.

This could serve as a foundation for building more advanced memory management systems or
for understanding how low-level memory operations like malloc, free, and realloc work
behind the scenes.
