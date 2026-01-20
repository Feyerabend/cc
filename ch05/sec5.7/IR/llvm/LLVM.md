
## LLVM

LLVM (Low-Level Virtual Machine) is a compiler framework and toolchain designed for the generation,
optimisation, and compilation of code. It provides a robust intermediate representation (IR) that
serves as the foundation for building and analysing software systems. LLVM’s modular design makes
it a powerful tool for compiler developers, researchers, and industry practitioners.


1. Intermediate Representation (IR):
 - LLVM IR is a low-level, strongly-typed, RISC-like programming language.
 - It is designed to be target-independent, making it suitable for cross-platform compilation.
 - The IR supports three forms: in-memory (used during compilation), textual (human-readable),
   and binary (compact storage).

2. Modularity:
 - LLVM separates the frontend, optimisation passes, and backend, enabling developers to
   focus on individual components.
 - The frontend converts source code into LLVM IR, optimisation passes improve the IR,
   and the backend generates machine code for specific architectures.

3. Optimisations:
 - Offers a rich suite of optimisation passes for performance improvement, including dead
   code elimination, inlining, loop unrolling, and vectorisation.
 - Optimisations can be performed at compile-time, link-time, and runtime (Just-In-Time compilation).

4. Target Independence:
 - By abstracting hardware specifics, LLVM IR allows compilers to support multiple hardware targets seamlessly.
 - Backend code generators convert LLVM IR into machine code for specific CPUs or GPUs.

5. Just-In-Time (JIT) Compilation:
 - LLVM supports JIT compilation, which allows dynamic code generation and execution.
 - Useful in runtime environments like interpreters or when executing dynamically generated code.

6. Language Support:
 - LLVM is language-agnostic and supports numerous languages, including C, C++, Rust, Swift, Python, Julia, and more.
 - New language frontends can be built to emit LLVM IR.

7. Tooling and Extensibility:
 - LLVM includes tools like Clang (a C/C++/Objective-C frontend), llc (a backend code generator),
   and opt (an optimiser for LLVM IR).
 - The framework is extensible, allowing developers to create custom optimisation passes, backends, or tools.

Timeline:
- 2000: LLVM began as a research project by Chris Lattner at the
  University of Illinois at Urbana-Champaign.
- 2003: The first public release of LLVM provided a novel framework for
  SSA-based (Static Single Assignment) compilation and optimisation.
- 2005: Apple adopted LLVM, using it as the backend for its developer tools.
- 2010s: LLVM became an industry standard for compiler toolchains,
  powering modern languages like Rust and Swift.
- 2020s: LLVM continues to evolve with advancements in hardware support
  (e.g., GPUs, FPGAs), machine learning integration, and runtime adaptability.

Use:
- Compilers: Serving as the foundation for high-performance language compilers like Clang and Rust.
- Dynamic Code Execution: Powering JIT engines in tools like Julia and PyTorch.
- Research: A platform for experimenting with new compiler techniques and architectures.
- Hardware Design: Supporting domain-specific architectures and accelerators with custom backends.
- Code Analysis: Providing a rich environment for static and dynamic code analysis.

LLVM’s combination of flexibility, performance, and extensibility has
made it one of the most influential projects in compiler and programming language design.

