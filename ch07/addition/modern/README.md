
## A Modern Approach to Compilers

It is notoriously difficult to convey the scale and structure of large software systems--whether
complex servers, operating systems, or even compilers themselves. These programs often involve
millions of lines of code, intricate interactions between components, and layers of abstraction
that are hard to visualise. Yet, among these, compilers provide a particularly clear lens through
which to observe the growth of software complexity over time. 

This is the second part in a series of two. We have already explored in [ch05](./../../ch05/)
an attempt at constructing a simple compiler using [classical](./../../ch05/classic/) techniques.
Here we will use the introduced different concepts such as design patterns frequent in
object-oriented design, using Packrat as the parser (in contrast to e.g. recursive decent),
and a plugin architecture to make flexible and dynamic modules possible, without altering
the main program. It might not be the ultimate solution to compiler design (which it is not),
but still illustrate clearly how *programming in general but also theory have changed during
the decades*.


```mermaid
gantt
    dateFormat  YYYY
    axisFormat  %Y
    title GCC and LLVM: Key Breakthroughs

    section GCC
    GCC 1.0 (GNU C Compiler, retargetable)       :a1, 1987, 1y
    GCC becomes "Collection" (C++, Fortran)      :a2, 1988, 1y
    Ports enable Linux on SPARC, MIPS, ARM       :a3, 1992, 1y
    EGCS fork, later merged back                 :a4, 1997, 1y
    GCC 3.0 (new optimisers, C++98 support)      :a5, 2001, 1y
    GCC 4.0 (SSA GIMPLE IR, redesigned middle)   :a6, 2004, 1y
    Graphite loop optimisation framework         :a7, 2007, 1y

    section LLVM
    LLVM project begins (Lattner, PhD)           :b1, 2000, 1y
    LLVM 1.0 released (SSA IR, modular passes)   :b2, 2003, 1y
    Clang front end starts                       :b3, 2005, 1y
    Apple adopts LLVM/Clang                      :b4, 2007, 1y
    LLVM JIT support matures                     :b5, 2010, 1y
    Rust adopts LLVM backend                     :b6, 2012, 1y
    LLVM 3.7 (SPIR-V, OpenCL support)            :b7, 2015, 1y
    MLIR project begins (AI/ML workloads)        :b8, 2019, 1y
    LLVM expands to WebAssembly, RISC-V, GPUs    :b9, 2020, 2y
```


### From GCC to LLVM: The Evolution of Compiler Modularity

The late 1980s marked a turning point in compiler history. Until then, most compilers were monolithic creatures:
each new language for each new machine required almost an entirely new compiler. What Richard Stallman and his
collaborators achieved with the GNU Compiler Collection (GCC) was to break this rigid pattern by introducing
retargetability. Twenty years later, Chris Lattner’s LLVM would take this idea even further, transforming the
compiler from a mere tool into a reusable infrastructure.


#### GCC: Retargetability through Separation

When Stallman released the first version of GCC in 1987, it was called the GNU C Compiler. Its defining innovation
was separating front ends from back ends. Instead of writing “a compiler for C on VAX” and another for "C on MIPS,"
GCC provided:
1. Front ends: parse and analyse source code for a particular language (C, later C++, Fortran, Ada, etc.).
2. Middle end: apply machine-independent optimisations.
3. Back ends: generate code for specific target architectures (x86, ARM, MIPS, SPARC), described by machine definition files.

The central trick was to use an internal representation, first RTL (Register Transfer Language) and later GIMPLE,
so that front ends and back ends could meet in the middle.

For example, compiling a trivial function in C:

```c
int add(int a, int b) {
    return a + b;
}
```

In GCC’s middle end, this might become a simplified GIMPLE form:

```gimple
# GIMPLE
add (int a, int b)
{
  int _1;
  _1 = a + b;
  return _1;
}
```

From there, the back end maps it to machine-specific assembly:
- On x86:
```asm
add:
    mov eax, edi
    add eax, esi
    ret
```
- On ARM:
```asm
add:
    add r0, r0, r1
    bx lr
```

The same high-level program, once passed through GCC’s middle end, could be retargeted to any supported
architecture by providing only the back-end descriptions.

This modularity made GCC the universal toolchain of the free software world. It powered Linux distributions
across architectures from Intel servers to tiny embedded controllers. Yet GCC’s design, written in C and
developed incrementally over decades, became hard to extend. Its internal representations were not originally
meant for external use, and experimenting with GCC internals required wading through a large, complex codebase.



#### LLVM: Infrastructure, Not Just a Compiler

Chris Lattner's LLVM (Low Level Virtual Machine), begun in 2000 as a research project, reimagined modularity.
Where GCC separated front ends and back ends, LLVM introduced an intermediate representation (LLVM IR) that was:
- Typed (with explicit integer, floating, and pointer types),
- In SSA form (Static Single Assignment, making optimisation cleaner),
- Stable and documented (meant to be read, written, and stored).

Unlike GCC’s internal GIMPLE/RTL, LLVM IR was first-class: you could write it to disk, inspect it, reload it,
and even hand-edit it.

The same C function from above, compiled with Clang (LLVM’s C front end), becomes:

```llvm
; LLVM IR
define i32 @add(i32 %a, i32 %b) {
entry:
  %sum = add i32 %a, %b
  ret i32 %sum
}
```

This intermediate code is machine-independent, yet precise enough to lower efficiently to many targets.
The LLVM toolchain allows you to transform and optimise this IR using the opt command, and finally emit
native code with llc.

For example:

```
clang -S -emit-llvm add.c -o add.ll
opt -O2 add.ll -o add_opt.ll
llc add_opt.ll -o add.s
```

The design philosophy is clear: LLVM is not just a compiler, but a framework. Languages as diverse as Swift,
Rust, Julia, and Haskell all use LLVM as their back end. Hardware vendors (e.g., Apple for ARM64, NVIDIA
for GPUs, WebAssembly groups) also adopt it to avoid reinventing optimisation and codegen pipelines.



#### GCC vs LLVM: Philosophical Differences

- GCC pioneered separation. Its retargetable structure made it possible to support many languages and
  architectures in one collection. But GCC’s IRs were internal tools, not external artefacts.
- LLVM made IR central. LLVM IR is human-readable, language-agnostic, and usable across compile-time
  and runtime. It is the “lingua franca” of modern compiler design.
- GCC is a compiler collection. Each language plugs into a shared, but historically monolithic, middle/back end.
- LLVM is compiler infrastructure. It provides libraries, APIs, and tools that let anyone build a compiler,
  JIT engine, or analysis tool.



Broader Impact

- GCC’s modularity enabled UNIX and Linux portability in the 1990s. Without it, Linux would not have spread
  across dozens of architectures so quickly.
- LLVM’s infrastructure enabled new languages and tooling in the 2000s and 2010s. Without it, languages
  like Rust, Swift, and Julia might never have gained high-performance back ends so quickly.

The transition from GCC to LLVM marks a shift from thinking of compilers as monolithic programs to viewing
them as reusable ecosystems. GCC showed the power of modularity; LLVM demonstrated the power of infrastructure
built around a universal IR.


### Complexity and Size[^LOC]

```mermaid
classDiagram
    class Software_Projects {
        FORTRAN_Compiler_1957 : 0.025M LOC █
        Apache_HTTP_Server : 1.65M LOC ███
        MySQL_Database : 2.38M LOC ████
        GCC_13_Compiler : 15M LOC ███████████████████████████
        LLVM_Clang : 20M LOC ████████████████████████████████████
        Firefox_Browser : 33M LOC ████████████████████████████████████████████████████
        Chromium_Browser : 36M LOC ████████████████████████████████████████████████████████
        Linux_Kernel_2025 : 40M LOC █████████████████████████████████████████████████████████████
        Windows_OS : 50M LOC ████████████████████████████████████████████████████████████████████████
    }
    style Software_Projects fill:#f9f9f9,stroke:#333,stroke-width:1px
```

[^LOC]: Lines of Code (LOC) can be misleading and potentially inaccurate. LOC is a notoriously unreliable metric for software size, as it can vary widely based on counting methodology and what is included (e.g., comments, tests, third-party libraries).
Here the inclusion of LOCs is only to *indicate* the size of compilers can be huge in relation to other programs.

Today, compilers like GCC and LLVM are no longer mere tools but sprawling platforms that underpin vast swaths
of the software world. GCC remains the bedrock of the GNU/Linux ecosystem, while as we learned above that LLVM
powers languages like Swift, Rust, and Julia, as well as GPU toolchains and MLIR for machine learning frameworks.
Yet, for most programmers, compilers operate invisibly, quietly transforming every line of code into machine
instructions. They are the unsung engines of software development, enabling performance portability through
frameworks like OpenMP, OpenCL, and CUDA, enhancing security with tools like AddressSanitizer, and driving AI/ML
innovation through projects like MLIR, XLA for TensorFlow, and TVM. Compilers even power the web, with WebAssembly
compilers embedded in browsers, enabling high-performance applications in JavaScript environments.

The story of compilers is, at its core, a narrative of abstraction and scalability. In the 1950s, they made
programming accessible to humans beyond the elite few who could wrestle with assembly. By the 1970s, they
enabled structured programming, laying the foundation for modern software engineering. In the 1990s, retargetable
compilers like GCC made portability across architectures practical. From the 2000s to today, infrastructure
compilers like LLVM have managed the complexity of language innovation and hardware heterogeneity, enabling
developers to write code in high-level languages like Python or Rust while achieving efficient execution on
CPUs, GPUs, or cloud clusters. Compilers are not just tools; they are the guardians of abstraction, the quiet
architects that make the diversity and dynamism of modern programming possible.

In essence, compilers have grown from modest 20,000-line experiments into multi-million-line ecosystems that
stand at the heart of both computer science and computing itself. They bridge the theoretical and the practical,
the language and the machine, enabling the software and hardware innovations that define our digital age.
Invisible yet indispensable, compilers continue to shape the future of technology, quietly empowering every
line of code that drives our world.

