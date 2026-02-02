
## References: Compilers

- Aho, A. V., Sethi, R., & Ullman, J. D. (1986).
  *Compilers: Principles, techniques, and tools*. Reading, MA: Addison-Wesley.

- Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D. (2007).
  *Compilers: Principles, techniques, and tools* (2nd ed.). Boston, MA: Pearson Addison-Wesley.

- Appel, A. W. (1997). *Modern compiler implementation in ML*.
  Cambridge, UK: Cambridge University Press.

- Appel, A. W. (1998). *Modern compiler implementation in Java*.
  Cambridge, UK: Cambridge University Press.

- Appel, A. W. (1998). *Modern compiler implementation in C*.
  Cambridge, UK: Cambridge University Press.

- Appel, A. W. (2002). *Modern compiler implementation in ML*
  (2nd ed.). Cambridge, UK: Cambridge University Press.

- Appel, A. W. (2002). *Modern compiler implementation in Java*
  (2nd ed.). Cambridge, UK: Cambridge University Press.

- Appel, A. W. (2002). *Modern compiler implementation in C*
  (2nd ed.). Cambridge, UK: Cambridge University Press.

---

![Beginners](./../../assets/image/farmer.png)

#### Legacy

The first book that I bought and studied compiler constructions from, was:
- Farmer, M. (1984). Compiler physiology for beginners. Chartwell-Bratt.

It is now very dated, as it focuses on building a working Mini-Pascal compiler
using LEX and YACC. But with straightforward explanations, concrete examples,
and useful end-of-chapter exercises, it remains a solid, hands-on resource
for grasping how compilers could be built.



![Dragon Book 1st](./../../assets/image/compilers.png)

#### Compilers: Principles, Techniques, and Tools

*First Edition (1986)*

The first edition (1986) of Compilers by Aho, Sethi, and Ullman is one of
the foundational texts in compiler theory. It is often called the "red
dragon book", a nickname derived from the dragon on its cover and to
distinguish it from other related books in the "dragon book" lineage.

The first edition presents a structured and rigorous introduction to
compiler design. It covers:
- Compiler structure and overall pipeline
- Lexical analysis, regular expressions, finite automata
- Syntax analysis, context-free grammars, LL and LR parsing
- Syntax-directed translation
- Semantic analysis
- Run-time environments and symbol tables
- Intermediate code generation
- Code optimization and generation

The material is theoretical and formal with a focus on fundamental algorithms
and the classic pipeline model of compilers.

![Dragon Book 2nd](./../../assets/image/compilers2.png)

*Second Edition (2006)*

The second edition adds Monica S. Lam as a co-author and is often referred to
as the "purple dragon book". Every chapter was revised since the first edition
to reflect developments that occurred in the two decades after the first edition.

In addition to the core material of the first edition, the second edition includes:
- Updated syntax-directed translation methods
- Expanded data-flow analysis techniques
- Chapters on instruction-level parallelism, parallelism and locality optimisation,
  and interprocedural analysis
- Discussions of just-in-time (JIT) compiling, garbage collection, and modern case studies
- Broader treatment of optimization and back-end issues than the first edition.



![Modern Compilers](./../../assets/image/appel.png) ![Modern Compiler Implementation in Java](./../../assets/image/modern.png)

#### Modern Compiler Implementation

Andrew W. Appel's *Modern Compiler Implementation* series is best understood
as a single book expressed in three programming languages (ML, Java, and C),
all sharing the same structure and compiler design. Its main strength is that
it guides the reader through the construction of a complete, realistic compiler
for a non-trivial language, covering everything from lexical analysis and parsing
to intermediate representation, register allocation, and machine code generation.
In contrast to the Dragon Book by Aho et al., which is primarily a theoretical
and encyclopedic reference, Appel is fundamentally practical and implementation-driven.
You are not just learning algorithms; you are building a real compiler with
clear phase boundaries and concrete data structures.

In terms of "modernity," Appel is architecturally closer to how contemporary
compilers are organized. The central role of an explicit intermediate representation,
control-flow graphs, modular separation between front end and back end, and
graph-coloring register allocation mirrors the design of systems like GCC and
LLVM much more closely than the classical pipeline model emphasized by Aho et al.
Even though the books predate SSA-based infrastructures and LLVM, their structural
approach to compiler engineering remains highly relevant, whereas the Dragon Book
feels more rooted in the tradition of formal language theory and parsing technology.

Together, the two works complement each other. Aho et al. explains the theoretical
foundations and gives breadth and rigor, while Appel shows how those ideas turn into
a working piece of software. If Aho teaches why compiler techniques are correct and
powerful, Appel teaches how they are assembled into an actual compiler that runs on
real machines. For anyone serious about compiler construction, reading both gives a
much more complete picture than either alone.


