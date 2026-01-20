
## References: Interpreters

- Abelson, H., & Sussman, G. J. (1985). *Structure and Interpretation of Computer Programs*. Cambridge, MA: MIT Press.
- Abelson, H., Sussman, G. J., & Sussman, J. (1996). *Structure and Interpretation of Computer Programs* (2nd ed.). Cambridge, MA: MIT Press.

- Abelson, H., Sussman, G. J., & Sussman, J. (2022). *Structure and interpretation of computer programs: JavaScript edition*. MIT Press.

- Friedman, D. P., & Felleisen, M. (1974). *The Little LISPer*. Chicago, IL: Science Research Associates.
- Friedman, D. P., & Felleisen, M. (1986). *The Little LISPer* (3rd ed.). New York, NY: Macmillan Publishing Company.

- Nystrom, R. (2021). *Crafting interpreters*. Genever Benning.

- Queinnec, C. (1996). *Lisp in Small Pieces*. Cambridge, UK: Cambridge University Press.

---

![The Anatomy of LISP](./../../assets/image/anatomy.png)

#### Legacy

The first book that I really studied some interpreter concepts from was:
- Allen, J. (1978). *The anatomy of LISP*. McGraw-Hill.

The Anatomy of LISP gives a precise, low-level explanation of how the LISP language is implemented,
focusing on memory structures, list representation, and evaluation mechanics. It connects the abstract
semantics of LISP with concrete machine-level execution, making the language understandable as a real
computational system rather than just a notation. It is now very dated.


![SICP](./../../assets/image/sicp.png)

#### Structure and Interpretation of Computer Programs

*First Edition (1985)*

The first edition (1985) of *Structure and Interpretation of Computer Programs* by Abelson and Sussman
is one of the foundational texts in programming language interpretation and computer science education.
It is often called the "Wizard Book," a nickname derived from the wizard on its cover and to distinguish
it from other influential texts.

The first edition presents a structured introduction to programming concepts using Scheme,
a dialect of Lisp. It covers:
- Building abstractions with procedures and data
- Metalinguistic abstraction, including building evaluators (interpreters) for Scheme itself
- Streams and lazy evaluation
- Nondeterministic computing and logic programming
- Register machines and compilation (though the focus is more on interpretation)

The material emphasizes elegance, abstraction, and the idea that programs are to be read by humans as
much as executed by machines, with a strong focus on interpreters as a way to understand language semantics.



*Second Edition (1996)*

The second edition includes Julie Sussman as a co-author and updates the text to use a more standard
Scheme dialect. Every chapter was revised to reflect developments in the decade since the first edition.

In addition to the core material, the second edition includes:
- Expanded treatment of state and assignment
- Updated examples and exercises
- Discussions of concurrency and parallelism
- Continued emphasis on metacircular evaluators and variations on interpreters



![JS of SICP](./../../assets/image/sicpjs.png)

*JavaScript edition (2022)*

The JavaScript edition of SICP preserves the original book’s depth and conceptual rigor while replacing
Scheme with a carefully restricted subset of JavaScript. It makes the classic ideas about abstraction,
interpretation, and computation accessible to modern programmers without diluting the mathematical and
philosophical core of the work.


![Nystrom](./../../assets/image/interpreters.png)

#### Crafting Interpreters

Robert Nystrom's Crafting Interpreters is a modern introductions to language implementation. It balances theory,
software engineering practice, and readability. Instead of presenting interpreters as abstract mathematical objects,
it treats them as real programs that must be designed, debugged, extended, and maintained. The book walks the
reader step by step through the construction of two complete systems: a simple tree-walk interpreter and a
more efficient bytecode virtual machine, showing how design decisions change as performance requirements grow.

What makes the book especially strong is its pedagogy. Each concept is introduced only when it becomes necessary,
and every feature of the language being built (expressions, variables, control flow, functions, classes) is
motivated by concrete implementation concerns. The code is clean, idiomatic, and heavily explained, which makes
the book approachable even for readers without a compiler background. At the same time, it never feels
superficial: core ideas such as parsing, scoping, memory management, and dispatch are handled with real rigour.




#### Lisp in Small Pieces

Christian Queinnec's *Lisp in Small Pieces* (1996) is a comprehensive exploration of Lisp
and Scheme implementation, focusing heavily on interpreters. It describes eleven interpreters
and two compilers, covering topics like evaluation, macros, continuations, reflection, and
compilation techniques. This book bridges interpretation and compilation, making it a natural
extension for those coming from SICP or EOPL (Essentials of Programming Languages),[^eopl]
with a practical emphasis on how Lisp's homoiconicity enables powerful metaprogramming through
interpreters.

[^eopl]: Friedman, D.P., Wand, M. & Haynes, C.T. (1992). *Essentials of programming languages*. Cambridge, Mass.: MIT Press.
A book which I have not yet personally read or even looked at, but is one of the foundational books
that is recommended for this field.

