
## Intermediate Representations (IRs) in Compilers

Intermediate Representation (IR), serve as a bridge in the compilation process,
transforming high-level source code into machine-readable instructions. They allow
compilers to perform optimisations and analyses in a standardised form. 


### [ILOC](./iloc/): An Educational Tool

ILOC stands out as an educational intermediate representation, designed to mimic
assembly language in a simplified way that makes it accessible for teaching compiler
concepts. It features explicit control flow, where jumps and branches are directly
stated, and uses virtual registers to handle data without tying to specific hardware.
This setup keeps things low-level yet abstract, avoiding the complexities of actual
machine code, which makes it ideal for straightforward analysis and basic optimisations.

ILOC bridges the gap between high-level languages and hardware by providing a clear,
step-by-step view of program execution, much like a blueprint for beginners to
experiment with transformations.


### [LLVM IR](./llvm/): For Industrial Optimisation

In contrast, LLVM IR represents an industrial-grade intermediate representation, built
with a focus on scalability and performance in professional compiler toolchains.
It's strongly typed to ensure safety and efficiency, and employs SSA. Being platform-independent,
it sits as a versatile middle layer: numerous frontend languages (like C++ or Rust)
can compile to it, and various backends then generate code for diverse architectures.
As a canonical low-level IR, LLVM powers tools like Clang and has become a standard for
projects requiring portability and high-performance tweaks, clarifying why it's favoured
in large-scale software development over simpler alternatives.
