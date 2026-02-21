
## Designing & Specifying a Programming Language

Programming languages are typically studied either from a theoretical
perspective (semantics, type theory, verification) or from a systems
perspective (compilers, runtimes, optimisation).
*This project intentionally bridges these viewpoints.*

Concepts such as operational semantics, type safety, intermediate
representations, and abstract machine execution models are not
treated as isolated topics but as mutually reinforcing components
of a single system. This connects to [ch05](./../../../ch05/).

This project presents the design and implementation of a small,
statically typed programming language together with its compiler
and virtual machine. The work combines practical engineering with
formal foundations, aiming to demonstrate how high-level language
constructs are specified, analysed, translated, and executed.

The system is structured as a complete toolchain:
- __Language Definition__ – Syntax, semantics, and type system
- *Frontend* – Lexical analysis, parsing, and AST construction
- *Static Analysis* – Type checking and semantic validation
- *Intermediate Representation (IR)* – Platform-independent program model
- *Backend* – Translation from IR to bytecode
- *Virtual Machine (VM)* – Execution of compiled programs

The project emphasises clarity, correctness, and traceability
between theory and implementation. Formal semantics and type
rules guide the design, while the compiler and VM provide a
concrete realisation of those principles.

The primary objectives are:
- To design a coherent and minimal language
- To implement a working compiler pipeline
- To define and execute a custom bytecode format
- To connect theoretical concepts with executable artifacts
- To provide a platform suitable for experimentation and extension


- *[DESIGN.md](./DESIGN.md)*
  Language design, semantics, type system, and compilation strategy  
- *[VM-SPECIFICATION.md](./VM-SPECIFICATION.md)*
  Instruction set architecture and execution model  
- *[PROJECT.md](./VM-SPECIFICATION.md)*
  Development roadmap, implementation guidance, and evaluation criteria  


