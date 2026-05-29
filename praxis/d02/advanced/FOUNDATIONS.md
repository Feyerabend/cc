## Foundations: Levels of Abstraction in Computation

### 1. The VM as a Contract

A virtual machine is not primarily a piece of software. It is a specification.
The software that implements it matters, but what matters more is the set of
guarantees it makes about how programs will behave.

When a language targets a VM, it acquires a kind of portability that did not
previously exist: not just the ability to run on different hardware, but the
ability to reason about execution in hardware-independent terms. The VM defines
a model of computation that is precise enough to write programs against, and
abstract enough to be realised on many different physical machines.

This idea has a name: the *abstract machine*. An abstract machine specifies
states and transitions without committing to how those states are physically
represented. It defines what a program *means* independently of any particular
implementation. The fetch-decode-execute cycle is one such abstraction, but
abstract machines can be far more refined, describing memory models, type
safety guarantees, exception semantics, or concurrency rules.

The SECD machine (see `ch05/addition/am/secd`), the Warren Abstract Machine
(see `ch05/addition/am/wam`), and the JVM are all examples. Each makes explicit
a different set of commitments about what a language guarantees to the programmer.


### 2. Stack vs. Register: Two Ways to Structure Computation

The choice between stack and register machines is not merely an implementation
detail. It reflects a deeper choice about where the *locus of state* should be.

In a stack machine, the operand stack is the central data structure. Every
intermediate result lives there. The VM has very few moving parts: a stack, a
program counter, and an instruction stream. This simplicity makes it easy to
implement and easy to reason about. The cost is that intermediate values can
only be accessed by position, not by name, and the stack grows and shrinks in
ways that can be difficult to optimise.

In a register machine, intermediate values are held in named registers. The
compiler must allocate values to registers efficiently. This produces more
complex bytecode but allows more direct mapping to the underlying hardware.
Lua's VM moved from stack to register-based precisely for performance reasons.
The Dalvik VM (Android) was designed as a register machine from the start.

Neither design is inherently superior. The tradeoff is between implementation
simplicity (stack) and optimization potential (register). For teaching, stack
machines expose the essence of computation more clearly: every operation takes
its arguments from exactly one place.


### 3. Memory Models

A VM's memory model determines what programs can rely on about the lifetime,
locality, and visibility of data.

The simplest model has three regions:
- *Static* storage for global data and code.
- The *stack* for local variables and return addresses, managed automatically.
- The *heap* for dynamically allocated objects, managed explicitly or by GC.

The stack and heap grow toward each other from opposite ends of the address
space. When they meet, the program fails. This is a fundamental constraint
that VMs expose, even when hiding almost everything else about the hardware.

The *Harvard architecture* introduces a more radical separation: instruction
memory and data memory are completely distinct. Programs cannot write to the
instruction space, which prevents a class of attacks (code injection through
data buffers). Most real CPUs are von Neumann at the hardware level but impose
a Harvard-like separation through privilege levels and page permissions.


### 4. Interpretation vs. Compilation

There is a spectrum between pure interpretation and pure compilation, and
most modern language implementations sit somewhere in the middle.

A *pure interpreter* reads source code and executes it directly, performing
no translation. Each construct is evaluated anew each time it is encountered.
This is simple and flexible but slow.

A *bytecode compiler and VM* translates source code to a lower-level
representation once, then interprets that representation. The translation is
fast and cheap; the bytecode is more regular than source code, enabling some
optimisations. CPython, the Ruby MRI, and the original JVM all worked this way.

A *just-in-time compiler* (JIT) goes further: it identifies frequently executed
code ("hot paths") and compiles them to native machine code at runtime. The JVM
has used JIT since early versions; V8 (JavaScript) is a notable example. The
`ch05/addition/jit/hotspot.py` gives a small demonstration of the profiling step.

A *ahead-of-time compiler* (AOT) translates everything before execution. There
is no interpretation overhead at runtime, but the binary is platform-specific.
C, Go, and Rust use this model.

The choice between these is a tradeoff between startup time, peak performance,
portability, and implementation complexity.


### 5. Self-Modifying Code and the Limits of the Abstraction

One of the most revealing ways to probe a VM is to ask: *can a program running
inside it modify its own instructions?*

In a pure von Neumann model, data and instructions share a memory space. Nothing
prevents a program from writing to the address where the next instruction is stored.
Self-modifying code is possible. Early programs used this to save memory or to
implement dynamic dispatch. Modern systems still use it, most visibly in JIT
compilers, which write machine code into executable memory pages at runtime.

A Harvard VM makes this impossible by design. The instruction space is read-only
from the program's perspective. This is not a limitation but a guarantee: programs
can reason about what code will execute because no code can change it.

This tension — between expressiveness and verifiability — recurs throughout the
later chapters. In ch08, formal verification assumes exactly this kind of
constraint: that a program cannot rewrite its own rules while running.


### 6. Historical Context

The idea of a virtual machine is old enough to have several independent
reinventions.

The UCSD p-System (1974) compiled Pascal to P-code for a P-machine, allowing
programs to run on any hardware for which a P-machine interpreter existed. This
was the direct ancestor of the JVM's portability model.

Smalltalk (1972–80) pioneered the use of a VM with garbage collection and
reflection as a fundamental part of the language design.

The LISP Machine (1970s–80s) took the opposite direction: build hardware that
natively executes a high-level VM, rather than simulating it in software.

The JVM (1995) made VMs mainstream by targeting the web: applets that could run
in any browser on any machine.

The .NET CLR (2000) generalised the idea further, targeting multiple languages
with a shared runtime and type system.

More recently, WebAssembly (2019) defines a VM as an explicit target for
compiler toolchains, achieving near-native performance in the browser while
retaining the portability and sandboxing guarantees of a VM.

Each of these systems made different choices about the contract they offered.
Understanding those choices, and why they were made, gives a much richer sense
of what a VM is than any single implementation can.
