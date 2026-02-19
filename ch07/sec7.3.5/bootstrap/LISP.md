
## History of Self-Hosting in Lisp


### Early Beginnings (1958–1960)

John McCarthy invented Lisp in the late 1950s as a practical implementation of ideas
from lambda calculus, primarily for AI research. The language was formally described
in his 1960 paper *"Recursive Functions of Symbolic Expressions and Their Computation by Machine"*.

The first Lisp system was implemented by Steve Russell in 1958–1959 on an IBM 704.
Russell hand-translated McCarthy's `eval` function into machine code, creating the
original Lisp *interpreter*. At this stage, Lisp execution was purely interpretive.


### The First Self-Hosting Compiler (1962)

In 1962, Tim Hart and Mike Levin at MIT developed the *first complete Lisp compiler written in Lisp itself*.
This is widely regarded as the *world's first self-hosting compiler* for any high-level
programming language (excluding assemblers).

Key points:

- The compiler was initially run under the existing Lisp interpreter.
- It compiled Lisp source code to machine code.
- When the compiler compiled its own source code, it produced a standalone native-code compiler.
- This resulted in dramatic performance improvements (approximately 40× speedup over interpretation).
- The technique relied heavily on Lisp's homoiconicity: code and data have the same representation
  (S-expressions), making it easy to write programs that manipulate programs.

In their AI Memo No. 39, they wrote:  
*"The compiler as it exists on the standard compiler tape is a machine language program
that was obtained by having the S-expression definition of the compiler work on itself
through the interpreter."*

This marked the birth of true *bootstrapping* in high-level languages.


### Evolution Through Dialects (1960s–1980s)

Lisp evolved into multiple dialects, most of which embraced self-hosting:

- *Lisp 1.5* (early 1960s): The baseline system from which many branches grew.
- *MacLisp* (late 1960s–1970s, MIT): Focused on efficient compilation;
  became the dominant dialect on PDP-10 systems and was fully self-hosting.
- *Interlisp* (1970s, BBN): Emphasized interactive development environments;
  self-hosted on various platforms including Xerox workstations.
- *ZetaLisp / Lisp Machine Lisp* (1980s, Symbolics and LMI): Ran on dedicated
  Lisp machines with hardware support; highly optimized, fully self-hosted compilers.
- *Scheme* (1975 onward): Minimalist dialect designed for teaching and research;
  many early implementations were bootstrapped in similar ways.

The ability to incrementally compile parts of the system while interpreting
others became a defining feature of Lisp development environments.


### Standardization and Modern Era (1980s–Present)

Efforts in the 1980s led to *Common Lisp* (standardised in 1984, ANSI standard
in 1994), which unified features from MacLisp, ZetaLisp, and others.
Common Lisp implementations typically include sophisticated self-hosting compilers.

Modern examples:

- *SBCL* (Steel Bank Common Lisp): Almost entirely written in Common Lisp;
  bootstraps from a host compiler (often itself or another Lisp) with a small C runtime.
- *Clozure CL*: Largely self-hosted.
- Many Scheme implementations (e.g., Chez Scheme, Racket) follow similar bootstrapping patterns.


### Significance

Lisp's early achievement of self-hosting demonstrated the power of homoiconicity and
metaprogramming. It solved the classic "chicken-and-egg" problem of compiler construction elegantly:

1. Start with an interpreter (written in a lower-level language).
2. Write the compiler in the target language.
3. Use the interpreter to run the compiler on its own source.
4. Obtain a native compiler capable of compiling itself and all future code.

This pattern influenced compiler design across many languages and remains one of the
most iconic accomplishments in programming language history.

### Reference

* Allen, J. (1978). *The Anatomy of Lisp*. McGraw-Hill.

* McCarthy, J. (1960). Recursive functions of symbolic expressions and their computation by machine, Part I. *Communications of the ACM*, 3(4), 184–195.

* Hart, T. P., & Levin, M. I. (1962). The Lisp compiler. Massachusetts Institute of Technology, Artificial Intelligence Memo. (Some bibliographies specify it as AI Memo 39.)

![Allen](anatomy.png)