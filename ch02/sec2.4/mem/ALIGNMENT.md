
## Alignment

Alignment in computer systems refers to the way data is arranged and accessed in memory,
ensuring that data boundaries conform to specific rules set by the hardware. It plays a
role in processor efficiency, memory access speed, and instruction handling.


### What is alignment?

Memory alignment ensures that data is stored at memory addresses that are multiples of
the data size or a specific alignment requirement. For example:

- A 4-byte integer is typically stored at an address divisible by 4 (e.g. 0x0000, 0x0004, 0x0008).

- An 8-byte double is often stored at an address divisible by 8 (e.g. 0x0008, 0x0010, 0x0018).



### Why do we have/need alignment?

Processors often fetch data from memory in fixed-sized chunks (word size) that align with
their internal architecture. Misaligned accesses can create inefficiencies or even cause
exceptions on certain systems. The reasons alignment is important include:

1. Performance optimisation:
   - Aligned data can be fetched in a single memory access cycle because the address corresponds
     directly to the processor's memory-fetch granularity.
   - Misaligned data might require multiple cycles to assemble the required bytes from different
     memory locations.

2. Hardware Simplification:
   - Processors with alignment requirements can simplify hardware designs since aligned memory
     access maps naturally to cache lines and bus transactions.

3. Compatibility:
   - Many instruction sets, like those in RISC architectures (e.g. ARM, MIPS), enforce strict
     alignment rules. This ensures consistent performance and predictable behavior.


### How do processor instructions work with alignment?

Processors access memory in words (such as 32-bit or 64-bit) based on their architecture.
When an instruction requests a specific memory address:
- If the data is aligned, the processor fetches it directly in one operation.
- If the data is misaligned, there are different possibilities:
- Some processors handle misalignment automatically by fetching multiple aligned chunks of memory and combining them.
- Others generate a hardware exception, leaving it to the operating system or application to handle the misaligned access.
- Fetching misaligned data often takes more cycles because additional memory accesses are needed.

For example, suppose you have a 4-byte value at address 0x0001:
- A misaligned 4-byte fetch might require reading two memory locations
  (0x0000-0x0003 and 0x0004-0x0007) and then combining the relevant bytes.

### Are alignments a problem for memory?

Alignment isn't inherently a problem but can lead to inefficiencies or errors if not managed:
- Performance penalty: Misaligned accesses require extra processing cycles, slowing down applications.
- Compatibility issues: On some architectures, misaligned accesses are forbidden and will cause runtime exceptions.
- Wasted space: Strict alignment requirements can lead to "padding" in memory structures, increasing the memory footprint.

### How do alignments work in practice?

__1. Structure Padding__

Compilers often insert padding into data structures to ensure proper alignment of each field. For instance:

```c
struct Example {
    char a;      // 1 byte
    int b;       // 4 bytes
};
```

The compiler may add 3 bytes of padding after a to align b to a 4-byte boundary.

__2. Compiler Directives__

In languages like C or C++, programmers can control alignment using directives (#pragma pack) or attributes
to optimize memory usage or enforce specific alignment.

__3. Memory Allocators__

Allocators like malloc typically return memory aligned to the largest primitive type for the platform.


### Potential misalignment in MEM?

The `mem_malloc` function simply returns a pointer offset by the size of the
`BlockHeader` struct without ensuring the returned address aligns with the size
of the requested data type. If the start address of `memory_pool` plus the
`BlockHeader` size is not a multiple of the alignment requirement of the data
type, it will result in misaligned access.

Misaligned access is thus when a program attempts to read from or write to a memory
address that isn't aligned according to the requirements of the data type being
accessed. This can lead to inefficiencies, as some CPUs require additional cycles
to handle misaligned data, or even critical errors, as certain architectures,
such as ARM and older versions of SPARC, can crash or throw exceptions on
misaligned access.


## Project: Aligned memory allocator with misalignment detection

*Create a custom memory allocator in C that aligns memory allocations for different
data types and includes a mechanism to detect and report misaligned accesses.*

This project will help you understand data alignment, memory management, and the
performance implications of misaligned access on different architectures.

You will learn:
- How to align memory allocations correctly.
- How different architectures handle misaligned access and the consequences for performance and stability.
- How to debug and detect misalignment issues in memory-heavy applications.

Skills and pratice:
- C programming and memory management
- Understanding of data structures, pointers, and type sizes
- Debugging techniques for low-level memory issues
- Comparative performance analysis across architectures

### Outline

##### Part 1: Basic aligned memory allocator

- Write a simple memory allocator that guarantees allocations are aligned to the nearest multiple of a
  specified alignment (e.g. 4, 8, or 16 bytes).
- Allow allocations of different sizes, and ensure that each allocation meets the alignment requirement.
- Calculate the necessary padding to achieve the required alignment.
- Provide examples of allocating various data types (int, float, double) and ensure they align correctly.

##### Part 2: Misalignment Detection and Reporting

- Extend the allocator to track memory allocations and detect misaligned accesses.
- Implement a function that verifies whether a given pointer is aligned for a specific data type and alignment.
- Simulate misaligned access by intentionally misaligning some data and observing the results on different
  architectures (e.g. x86 vs. ARM, where ARM may throw alignment errors).
- Write a test suite that attempts to read/write misaligned data and catches and reports these errors.

##### Part 3: Performance Testing and Analysis (Optional)
- Compare the performance of aligned vs. misaligned memory access by running benchmarks (e.g. accessing
  arrays of aligned vs. misaligned integers).
- Record the difference in CPU cycles or execution time and analyze the performance impact of misaligned
  memory access.


